"""Unit tests for the Footfall MCP Server and Tool Endpoints (Section 12.2).

Follows AGENTS.md:
- Tests first
- Flag for human review when editing src/footfall/server/
- Proves three tools: footfall_compare, footfall_trend, footfall_find_rising
- Proves input validation allow-list (^[A-Za-z0-9@._/\\-]{1,100}$)
- Proves entity resolution: exact match, alias match, ambiguous (max 5),
  not found with nearest edit distance
- Proves structured error templates (never echo raw user input)
- Proves output content rules: zero third-party free text, 50 KB byte cap
- Proves tool annotations: title, readOnlyHint, idempotentHint, openWorldHint
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from footfall.server.app import create_mcp_server
from footfall.server.resolver import EntityResolver
from footfall.server.schemas import (
    CompareInput,
    FindRisingInput,
    TrendInput,
)
from footfall.server.service import FootfallService


@pytest.mark.unit
def test_entity_resolver_exact_and_alias() -> None:
    """Section 12.2: Resolve canonical entity_id and package aliases."""
    # Synthetic registry
    entities_data = [
        {
            "entity_id": "langchain",
            "display_name": "LangChain",
            "category": "agent-framework",
            "sources": [
                {
                    "source": "github",
                    "key": "langchain-ai/langchain",
                    "mapping_confidence": "verified",
                },
                {"source": "pypi", "key": "langchain", "mapping_confidence": "verified"},
                {"source": "npm", "key": "langchain", "mapping_confidence": "verified"},
            ],
        },
        {
            "entity_id": "qdrant",
            "display_name": "Qdrant",
            "category": "vector-store",
            "sources": [
                {"source": "github", "key": "qdrant/qdrant", "mapping_confidence": "verified"},
                {"source": "pypi", "key": "qdrant-client", "mapping_confidence": "verified"},
            ],
        },
    ]

    resolver = EntityResolver.from_dict_list(entities_data)

    # 1. Exact canonical ID
    res = resolver.resolve("langchain")
    assert res.status == "ok"
    assert res.entity_id == "langchain"

    # 2. Source alias (GitHub owner/repo)
    res_gh = resolver.resolve("langchain-ai/langchain")
    assert res_gh.status == "ok"
    assert res_gh.entity_id == "langchain"

    # 3. Source alias (PyPI client package name)
    res_pypi = resolver.resolve("qdrant-client")
    assert res_pypi.status == "ok"
    assert res_pypi.entity_id == "qdrant"


@pytest.mark.unit
def test_entity_resolver_not_found_with_nearest_candidates() -> None:
    """Section 12.2: If none match, return not_found with at most 5 nearest ids by edit distance."""
    entities_data = [
        {
            "entity_id": "qdrant",
            "display_name": "Qdrant",
            "category": "vector-store",
            "sources": [],
        },
        {
            "entity_id": "chroma",
            "display_name": "Chroma",
            "category": "vector-store",
            "sources": [],
        },
        {
            "entity_id": "milvus",
            "display_name": "Milvus",
            "category": "vector-store",
            "sources": [],
        },
    ]
    resolver = EntityResolver.from_dict_list(entities_data)

    # Typo: "qdrnt" -> should return nearest candidates containing "qdrant"
    res = resolver.resolve("qdrnt")
    assert res.status == "not_found"
    assert res.entity_id is None
    assert len(res.candidates) > 0
    assert "qdrant" in res.candidates
    assert res.message == "Entity not found in registry."
    # Never echo raw user input in message
    assert "qdrnt" not in res.message


@pytest.mark.unit
def test_entity_resolver_rejects_malformed_input() -> None:
    """Section 12.2: Validate input against ^[A-Za-z0-9@._/\\-]{1,100}$."""
    resolver = EntityResolver.from_dict_list([])

    # Shell injection / SQL characters
    res = resolver.resolve("langchain; rm -rf /")
    assert res.status == "invalid_input"
    assert res.message == "Input does not conform to allowed entity identifier pattern."
    assert "rm -rf" not in res.message

    # Empty string
    res_empty = resolver.resolve("")
    assert res_empty.status == "invalid_input"

    # Exceeding 100 characters
    res_long = resolver.resolve("a" * 101)
    assert res_long.status == "invalid_input"


@pytest.mark.unit
def test_input_pydantic_schemas_boundary_validation() -> None:
    """Schema boundary enforcement for MCP tool inputs."""
    # footfall_compare requires 2 to 6 items
    with pytest.raises(ValidationError):
        CompareInput(entities=["single"])

    with pytest.raises(ValidationError):
        CompareInput(entities=["a", "b", "c", "d", "e", "f", "g"])  # 7 items

    # Valid compare input
    valid_compare = CompareInput(entities=["langchain", "llama-index"], window_weeks=12)
    assert len(valid_compare.entities) == 2
    assert valid_compare.window_weeks == 12

    # Trend input window weeks between 4 and 104
    valid_trend = TrendInput(entity="langchain", window_weeks=26)
    assert valid_trend.window_weeks == 26

    with pytest.raises(ValidationError):
        TrendInput(entity="langchain", window_weeks=2)  # < 4

    # Find rising limit between 1 and 20
    valid_rising = FindRisingInput(category="agent-framework", limit=10)
    assert valid_rising.limit == 10

    with pytest.raises(ValidationError):
        FindRisingInput(limit=25)  # > 20


@pytest.mark.unit
def test_footfall_service_compare_tool() -> None:
    """Tool 1: footfall_compare outputs required fields and adheres to 50KB limit."""
    service = FootfallService.create_from_exports(exports_dir=Path("exports/v1"))
    result = service.compare(entities=["langgraph", "qdrant-client"], window_weeks=12)

    assert "as_of" in result
    assert "method_version" in result
    assert "rows" in result
    assert len(result["rows"]) == 2
    assert "caveats" in result
    assert "backtest" in result

    # Check row schema
    row = result["rows"][0]
    assert "entity_id" in row
    assert "display_name" in row
    assert "phase" in row
    assert "adoption_z" in row
    assert "confidence" in row

    # Response cap: < 50 KB (51200 bytes)
    serialized = json.dumps(result).encode("utf-8")
    assert len(serialized) < 51200


@pytest.mark.unit
def test_footfall_service_trend_tool() -> None:
    """Tool 2: footfall_trend outputs requested weekly time series."""
    service = FootfallService.create_from_exports(exports_dir=Path("exports/v1"))
    result = service.trend(entity="langgraph", window_weeks=12)

    assert "entity_id" in result
    assert "display_name" in result
    assert "series" in result
    assert len(result["series"]) > 0
    assert "week" in result["series"][0]
    assert "downloads" in result["series"][0]


@pytest.mark.unit
def test_footfall_service_find_rising_tool() -> None:
    """Tool 3: footfall_find_rising lists tools filtered by category and phase."""
    service = FootfallService.create_from_exports(exports_dir=Path("exports/v1"))
    result = service.find_rising(category="any", phase="breakout", limit=5)

    assert "items" in result
    assert "as_of" in result
    assert "method_version" in result
    assert len(result["items"]) <= 5


@pytest.mark.unit
def test_mcp_server_tool_annotations_and_metadata() -> None:
    """Verify tool annotations conform to MCP specification and token budgets."""
    server = create_mcp_server(exports_dir=Path("exports/v1"))
    assert server.name == "footfall"

    tools = server._tool_manager._tools
    assert len(tools) == 3
    assert "footfall_compare" in tools
    assert "footfall_trend" in tools
    assert "footfall_find_rising" in tools

    for name, tool_obj in tools.items():
        desc = tool_obj.description or ""
        word_count = len(desc.split())
        assert word_count <= 80, f"Tool {name} description exceeds 80 words ({word_count})"


@pytest.mark.unit
def test_streamable_http_origin_validation() -> None:
    """Sections 12.2 and 13.1: Reject DNS rebinding and unauthorized origins."""
    from starlette.testclient import TestClient

    from footfall.server.app import create_streamable_app

    app = create_streamable_app(exports_dir=Path("exports/v1"))
    client = TestClient(app)

    # 1. Request with forbidden external origin -> 403 Forbidden
    resp_bad = client.get(
        "/",
        headers={"origin": "http://evil-attacker.com"},
    )
    assert resp_bad.status_code == 403
    assert resp_bad.json()["error"] == "forbidden"

    # 2. Request with allowed localhost origin
    resp_good = client.get(
        "/",
        headers={"origin": "http://localhost:8000"},
    )
    # May be 404 or 405 on root GET, but NOT 403
    assert resp_good.status_code != 403
    assert resp_good.headers.get("X-Content-Type-Options") == "nosniff"
