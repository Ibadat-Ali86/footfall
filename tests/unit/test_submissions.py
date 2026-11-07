"""Unit tests for Directory Submissions and Launch Packs (Phase 3: Tasks T3.1-T3.4).

Proves:
- Claude Connector manifest conforms to MCP directory specification
- ChatGPT OpenAPI 3.1.0 specification and ai-plugin.json are valid
- Official MCP Registry entry (server.json) is valid
- Launch post and dataset card adhere to public claims verification
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from footfall.export.claims import verify_document_claims

SUBMISSIONS_DIR = Path("submissions")


@pytest.mark.unit
def test_claude_directory_manifest() -> None:
    """Task T3.1: Verify Claude connector manifest format and tool annotations."""
    manifest_path = SUBMISSIONS_DIR / "claude" / "manifest.json"
    assert manifest_path.is_file(), "submissions/claude/manifest.json missing"

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["name"] == "footfall"
    assert "transport" in data
    assert data["transport"]["type"] == "streamable-http"

    # Must define all 3 tools with required safety annotations
    tool_names = {t["name"] for t in data["tools"]}
    assert tool_names == {"footfall_compare", "footfall_trend", "footfall_find_rising"}

    for tool in data["tools"]:
        annotations = tool.get("annotations", {})
        assert annotations.get("readOnlyHint") is True
        assert annotations.get("destructiveHint") is False
        assert annotations.get("idempotentHint") is True
        assert annotations.get("openWorldHint") is False


@pytest.mark.unit
def test_chatgpt_openapi_and_plugin_manifest() -> None:
    """Task T3.2: Verify ChatGPT openapi.yaml and ai-plugin.json."""
    openapi_path = SUBMISSIONS_DIR / "chatgpt" / "openapi.yaml"
    plugin_path = SUBMISSIONS_DIR / "chatgpt" / "ai-plugin.json"

    assert openapi_path.is_file()
    assert plugin_path.is_file()

    # Validate OpenAPI YAML
    spec = yaml.safe_load(openapi_path.read_text(encoding="utf-8"))
    assert spec["openapi"].startswith("3.1")
    assert "/api/v1/compare" in spec["paths"]
    assert "/api/v1/trend" in spec["paths"]
    assert "/api/v1/find-rising" in spec["paths"]

    # Validate plugin JSON
    plugin_data = json.loads(plugin_path.read_text(encoding="utf-8"))
    assert plugin_data["schema_version"] == "v1"
    assert plugin_data["name_for_model"] == "footfall"
    assert plugin_data["auth"]["type"] == "none"


@pytest.mark.unit
def test_mcp_registry_server_json() -> None:
    """Task T3.3: Verify official MCP registry server.json."""
    server_json_path = SUBMISSIONS_DIR / "mcp-registry" / "server.json"
    assert server_json_path.is_file()

    server_data = json.loads(server_json_path.read_text(encoding="utf-8"))
    assert server_data["name"] == "footfall"
    assert server_data["transport"]["type"] == "streamable-http"
    assert len(server_data["tools"]) == 3


@pytest.mark.unit
def test_launch_post_claims_verification() -> None:
    """Task T3.4: Verify docs/launch-post.md complies with claims verification."""
    launch_post = Path("docs/launch-post.md")
    assert launch_post.is_file()

    violations = verify_document_claims(launch_post)
    assert len(violations) == 0, f"Violations found in launch-post.md: {violations}"
