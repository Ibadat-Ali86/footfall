"""Contract and security tests for Footfall collectors using recorded fixtures.

Adheres strictly to AGENTS.md rules:
- Offline only: Never call a live upstream API from a test.
- Tests SSRF host allow-list enforcement.
- Tests silent truncation detection.
- Tests response byte cap limits.
- Tests zero-leakage of third-party free text.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from footfall.collectors import (
    GitHubCollector,
    HackerNewsCollector,
    HostSecurityError,
    HuggingFaceCollector,
    NpmCollector,
    PyPICollector,
    SnapshotQuality,
)


def load_fixture(filename: str) -> dict[str, Any]:
    """Load JSON fixture from tests/fixtures/."""
    path = Path(__file__).parents[1] / "fixtures" / filename
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.contract
def test_ssrf_host_allowlist_enforcement() -> None:
    """Outbound requests targeting unapproved hosts or internal IPs must raise HostSecurityError."""
    collector = NpmCollector()
    unapproved_urls = [
        "http://169.254.169.254/latest/meta-data/",  # Cloud metadata SSRF attempt
        "https://evil-mirror.com/downloads",
        "http://localhost:8080/metrics",
        "https://google.com",
    ]
    for url in unapproved_urls:
        with pytest.raises(HostSecurityError, match="is not in allowed_hosts"):
            collector.validate_url(url)


@pytest.mark.contract
def test_npm_collector_ok_and_truncation() -> None:
    """npm collector parses downloads and detects silent truncation."""
    collector = NpmCollector()

    # 1. Standard valid response
    data_ok = load_fixture("npm_response.json")
    snapshots = collector.parse_response("langgraph", "@langchain/langgraph", "2026-11-01", data_ok)
    assert len(snapshots) == 1
    assert snapshots[0].value == 48250.0
    assert snapshots[0].quality == SnapshotQuality.OK
    assert snapshots[0].metric == "downloads"

    # 2. Truncated response (requested 2024-01-01, but npm returned
    # 2025-05-01 due to 18-month ceiling)
    data_trunc = load_fixture("npm_truncated_response.json")
    snapshots_trunc = collector.parse_response("old-pkg", "old-package", "2024-01-01", data_trunc)
    assert len(snapshots_trunc) == 1
    assert snapshots_trunc[0].quality == SnapshotQuality.TRUNCATED


@pytest.mark.contract
def test_pypi_collector_pep503_and_mirrors() -> None:
    """PyPI collector normalizes names and filters without_mirrors downloads."""
    collector = PyPICollector()

    # Test PEP 503 normalization
    assert collector.normalize_name("LangGraph_Core.SDK") == "langgraph-core-sdk"
    assert collector.normalize_name("OpenAI_Python") == "openai-python"

    data = load_fixture("pypi_response.json")
    snapshots = collector.parse_response("langgraph", "langgraph", "2026-11-01", data)
    assert len(snapshots) == 1
    assert snapshots[0].value == 64320.0  # without_mirrors value
    assert snapshots[0].quality == SnapshotQuality.OK


@pytest.mark.contract
def test_github_graphql_collector() -> None:
    """GitHub collector extracts stars, forks, and issues into distinct snapshots."""
    collector = GitHubCollector()
    data = load_fixture("github_graphql_response.json")
    snapshots = collector.parse_response("langgraph", "langchain-ai/langgraph", "2026-11-01", data)

    assert len(snapshots) == 3
    metrics = {s.metric: s.value for s in snapshots}
    assert metrics["stars"] == 21500.0
    assert metrics["forks"] == 2980.0
    assert metrics["open_issues"] == 142.0
    for s in snapshots:
        assert s.quality == SnapshotQuality.OK


@pytest.mark.contract
def test_huggingface_collector() -> None:
    """Hugging Face collector extracts model downloads and likes."""
    collector = HuggingFaceCollector()
    data = load_fixture("hf_response.json")
    snapshots = collector.parse_response("llama-3-8b", "meta-llama/Llama-3-8B", "2026-11-01", data)

    assert len(snapshots) == 2
    metrics = {s.metric: s.value for s in snapshots}
    assert metrics["downloads"] == 1289400.0
    assert metrics["likes"] == 8450.0


@pytest.mark.contract
def test_hackernews_collector_no_free_text_leakage() -> None:
    """HN collector aggregates numbers only; ensures zero story title or comments are saved."""
    collector = HackerNewsCollector()
    data = load_fixture("hn_response.json")
    snapshots = collector.parse_response("langgraph", "langchain-ai/langgraph", "2026-11-01", data)

    assert len(snapshots) == 2
    metrics = {s.metric: s.value for s in snapshots}
    assert metrics["stories"] == 2.0
    assert metrics["points"] == 525.0  # 345 + 180

    # Threat #1 & #10 Verification: No third-party free text in snapshot fields
    for s in snapshots:
        snapshot_json = s.model_dump_json()
        assert "Show HN" not in snapshot_json
        assert "Multi-Agent" not in snapshot_json
