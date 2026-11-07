"""Unit tests for Footfall Dependents Counts and Adoption Depth Engine (Phase 4 Backlog).

Proves:
- Ecosystem query parsing for PyPI and npm registries via ecosyste.ms.
- Mathematical computation of the Adoption Depth Ratio.
- Classification into 'deep', 'balanced', and 'shallow' adoption tiers.
- Resilient network handling with respx mocks (zero live network calls).
- CLI `footfall dependents` command execution.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import respx
from click.testing import CliRunner

from footfall.cli import main
from footfall.dependents.collector import DependentsCollector
from footfall.dependents.depth import AdoptionDepthCalculator


@pytest.fixture
def sample_pypi_response() -> dict[str, Any]:
    """Fixture providing simulated ecosyste.ms response for PyPI package."""
    return {
        "name": "langchain-core",
        "dependent_packages_count": 165,
        "dependent_repos_count": 168,
        "downloads": 144826657,
        "downloads_period": "last-month",
        "docker_dependents_count": 1,
    }


@pytest.fixture
def sample_shallow_response() -> dict[str, Any]:
    """Fixture providing simulated response for tool with high downloads but 0 dependents."""
    return {
        "name": "@modelcontextprotocol/sdk",
        "dependent_packages_count": 0,
        "dependent_repos_count": 0,
        "downloads": 256821715,
        "downloads_period": "last-month",
        "docker_dependents_count": 0,
    }


def test_depth_ratio_calculation() -> None:
    """Proves formula: log10(1 + dependents) / max(1.0, log10(1 + downloads))."""
    calc = AdoptionDepthCalculator()

    # Case 1: Deep ecosystem package (165 dependents, 144M downloads)
    # log10(166) = 2.220, log10(144826658) = 8.161 -> ratio ~ 0.272 (balanced)
    ratio_1 = calc.compute_depth_ratio(dependents=165, downloads=144826657)
    assert 0.25 <= ratio_1 <= 0.30

    # Case 2: Shallow package (0 dependents, 250M downloads)
    # log10(1) = 0.0 -> ratio == 0.0 (shallow)
    ratio_2 = calc.compute_depth_ratio(dependents=0, downloads=250000000)
    assert ratio_2 == 0.0

    # Case 3: Zero downloads edge case
    ratio_3 = calc.compute_depth_ratio(dependents=10, downloads=0)
    assert ratio_3 > 0.0  # uses denominator max(1.0, ...) without zero division error


def test_depth_tier_classification() -> None:
    """Proves classification into deep, balanced, and shallow tiers."""
    calc = AdoptionDepthCalculator(deep_threshold=0.35, shallow_threshold=0.15)

    assert calc.classify_tier(0.40) == "deep"
    assert calc.classify_tier(0.25) == "balanced"
    assert calc.classify_tier(0.05) == "shallow"
    assert calc.classify_tier(0.00) == "shallow"


@respx.mock
def test_collector_fetches_pypi_record(sample_pypi_response: dict[str, Any]) -> None:
    """Proves DependentsCollector querying PyPI packages with offline mock."""
    pkg_name = "langchain-core"
    url = f"https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/{pkg_name}"
    respx.get(url).respond(status_code=200, json=sample_pypi_response)

    collector = DependentsCollector()
    record = collector.fetch_dependents(
        entity_id="langchain-core",
        source="pypi",
        package_name=pkg_name,
    )

    assert record is not None
    assert record.entity_id == "langchain-core"
    assert record.dependent_packages_count == 165
    assert record.dependent_repos_count == 168
    assert record.monthly_downloads == 144826657
    assert record.depth_tier == "balanced"


@respx.mock
def test_collector_handles_scoped_npm_package(sample_shallow_response: dict[str, Any]) -> None:
    """Proves correct URL encoding and handling for scoped npm packages."""
    pkg_name = "@modelcontextprotocol/sdk"
    # Scoped package is URL-encoded as %40modelcontextprotocol%2Fsdk
    url = "https://packages.ecosyste.ms/api/v1/registries/npmjs.org/packages/%40modelcontextprotocol%2Fsdk"
    respx.get(url).respond(status_code=200, json=sample_shallow_response)

    collector = DependentsCollector()
    record = collector.fetch_dependents(
        entity_id="mcp-sdk",
        source="npm",
        package_name=pkg_name,
    )

    assert record is not None
    assert record.dependent_packages_count == 0
    assert record.depth_ratio == 0.0
    assert record.depth_tier == "shallow"


@respx.mock
def test_collector_handles_404_not_found() -> None:
    """Proves graceful handling when package is not found in registry."""
    url = "https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/unknown-pkg"
    respx.get(url).respond(status_code=404)

    collector = DependentsCollector()
    record = collector.fetch_dependents(
        entity_id="unknown",
        source="pypi",
        package_name="unknown-pkg",
    )

    assert record is None


def test_cli_dependents_command(tmp_path: Path, sample_pypi_response: dict[str, Any]) -> None:
    """Proves CLI `footfall dependents` execution and output formatting."""
    runner = CliRunner()

    with respx.mock:
        url = "https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/langchain-core"
        respx.get(url).respond(status_code=200, json=sample_pypi_response)

        result = runner.invoke(
            main,
            ["dependents", "--source", "pypi", "--package", "langchain-core"],
        )

        assert result.exit_code == 0
        assert "Ecosystem Adoption Depth: langchain-core" in result.output
        assert "Dependent Packages: 165" in result.output
        assert "Adoption Tier:      balanced" in result.output
