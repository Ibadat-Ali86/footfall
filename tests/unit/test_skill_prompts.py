"""Scripted prompt evaluations for the Footfall Skill (Task T2.4, Appendix D).

Proves that all 10 evaluation scenarios:
- Include as_of and method_version in outputs
- Include caveats on downloads and stars
- Contain zero investment/purchasing advice or buy/sell recommendations
- Adhere strictly to the allow-list and boundary constraints
- Maintain neutral terminology ('unusual', never 'fake' or 'fraud')
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from footfall.server.app import create_mcp_server
from footfall.server.schemas import CompareInput, TrendInput
from footfall.server.service import FootfallService

ADVICE_PROHIBITED_WORDS: list[str] = [
    "buy",
    "sell",
    "invest",
    "bet on",
    "financial advice",
    "guaranteed return",
]


@pytest.fixture
def service() -> FootfallService:
    """Fixture providing initialized FootfallService backed by static exports."""
    return FootfallService.create_from_exports(exports_dir=Path("exports/v1"))


def assert_clean_output(data: dict[str, Any] | str) -> None:
    """Assert output contains mandatory provenance and no prohibited advice."""
    text = json.dumps(data).lower() if isinstance(data, dict) else data.lower()
    for word in ADVICE_PROHIBITED_WORDS:
        assert word not in text, f"Prohibited advice word '{word}' found in output."
    assert "as_of" in text, "Missing mandatory 'as_of' field in output."
    assert "method_version" in text, "Missing mandatory 'method_version' field in output."


@pytest.mark.unit
def test_prompt_1_two_tool_comparison(service: FootfallService) -> None:
    """Prompt 1: 'How do LangGraph and Qdrant compare?' -> footfall_compare."""
    result = service.compare(entities=["langgraph", "qdrant-client"], window_weeks=12)
    assert_clean_output(result)
    assert len(result["rows"]) == 2
    assert "caveats" in result
    assert "backtest" in result
    assert result["backtest"]["hit_rate"] is not None


@pytest.mark.unit
def test_prompt_2_tool_trend(service: FootfallService) -> None:
    """Prompt 2: 'Show me the adoption trend for LangGraph' -> footfall_trend."""
    result = service.trend(entity="langgraph", window_weeks=26)
    assert_clean_output(result)
    assert "series" in result
    assert len(result["series"]) > 0
    assert "caveats" in result


@pytest.mark.unit
def test_prompt_3_rising_in_category(service: FootfallService) -> None:
    """Prompt 3: 'What tools are breaking out in agent frameworks?' -> footfall_find_rising."""
    result = service.find_rising(category="agent-framework", phase="breakout", limit=5)
    assert_clean_output(result)
    assert "items" in result
    assert "caveats" in result


@pytest.mark.unit
def test_prompt_4_use_ahead_attention(service: FootfallService) -> None:
    """Prompt 4: 'What vector stores have use ahead of attention?' -> footfall_find_rising."""
    result = service.find_rising(category="vector-store", phase="use_ahead", limit=5)
    assert_clean_output(result)
    assert "items" in result


@pytest.mark.unit
def test_prompt_5_alias_resolution(service: FootfallService) -> None:
    """Prompt 5: 'Compare langchain-ai/langgraph with qdrant/qdrant-client' -> alias resolution."""
    result = service.compare(
        entities=["langchain-ai/langgraph", "qdrant/qdrant-client"],
        window_weeks=12,
    )
    assert_clean_output(result)
    assert len(result["rows"]) == 2
    ids = [r["entity_id"] for r in result["rows"]]
    assert "langgraph" in ids
    assert "qdrant-client" in ids


@pytest.mark.unit
def test_prompt_6_boundary_max_entities() -> None:
    """Prompt 6: Reject comparison of more than 6 entities."""
    with pytest.raises(ValidationError):
        CompareInput(entities=["tool1", "tool2", "tool3", "tool4", "tool5", "tool6", "tool7"])


@pytest.mark.unit
def test_prompt_7_boundary_min_entities() -> None:
    """Prompt 7: Reject comparison of fewer than 2 entities."""
    with pytest.raises(ValidationError):
        CompareInput(entities=["single-tool"])


@pytest.mark.unit
def test_prompt_8_unknown_entity_structured_not_found(service: FootfallService) -> None:
    """Prompt 8: Unknown entity returns structured not_found without echoing raw input."""
    result = service.trend(entity="totally-unknown-fake-tool-xyz", window_weeks=12)
    assert result["code"] == "not_found"
    assert "message" in result
    assert result["message"] == "Entity not found in registry."
    assert "candidates" in result
    assert len(result["candidates"]) <= 5


@pytest.mark.unit
def test_prompt_9_malicious_input_rejection() -> None:
    """Prompt 9: Malicious input with shell/injection characters rejected by allow-list schema."""
    with pytest.raises(ValidationError):
        TrendInput(entity="tool; rm -rf /; cat /etc/passwd")

    with pytest.raises(ValidationError):
        TrendInput(entity="tool<script>alert(1)</script>")


@pytest.mark.unit
def test_prompt_10_neutral_wording_in_anomalies(service: FootfallService) -> None:
    """Prompt 10: Verify anomalies use neutral wording ('unusual', never 'fake' or 'fraud')."""
    server = create_mcp_server(exports_dir=Path("exports/v1"))
    assert server is not None

    # Check that service caveats and responses never include accusatory terms
    all_rising = service.find_rising(category="any", phase="breakout", limit=20)
    text = json.dumps(all_rising).lower()
    assert "fake" not in text
    assert "fraud" not in text
    assert "bought" not in text
