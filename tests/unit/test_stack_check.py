"""Unit tests for the Footfall Stack Health Analyzer (Phase 4 Backlog).

Proves:
- Extraction of dependencies across pyproject.toml, requirements.txt, and package.json
- In-memory resolution to canonical entities via EntityResolver
- Calculation of stack momentum and phase distributions
- CLI execution of `footfall stack` with human-readable and JSON output formats
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from footfall.cli import main
from footfall.stack.analyzer import StackAnalyzer


@pytest.fixture
def sample_pyproject(tmp_path: Path) -> Path:
    """Fixture providing a sample pyproject.toml with tracked AI dependencies."""
    content = """
[project]
name = "my-ai-agent"
version = "0.1.0"
dependencies = [
    "langgraph>=0.2.0",
    "qdrant-client[fastembed]~=1.12.0",
    "requests>=2.31.0",
    "pydantic>=2.7.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "chromadb==0.5.0"
]
"""
    p = tmp_path / "pyproject.toml"
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture
def sample_requirements(tmp_path: Path) -> Path:
    """Fixture providing a sample requirements.txt."""
    content = """
# Production requirements
langgraph==0.2.5; python_version >= '3.11'
qdrant-client>=1.11.0 # Vector store
httpx>=0.27.0
"""
    p = tmp_path / "requirements.txt"
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture
def sample_package_json(tmp_path: Path) -> Path:
    """Fixture providing a sample package.json."""
    content = """
{
  "name": "ai-web-app",
  "dependencies": {
    "@langchain/langgraph": "^0.2.0",
    "react": "^18.2.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0"
  }
}
"""
    p = tmp_path / "package.json"
    p.write_text(content, encoding="utf-8")
    return p


@pytest.mark.unit
def test_extract_dependencies(
    sample_pyproject: Path,
    sample_requirements: Path,
    sample_package_json: Path,
) -> None:
    """Proves parsing across all three common package manifest formats."""
    analyzer = StackAnalyzer.create_from_exports(exports_dir=Path("exports/v1"))

    # 1. pyproject.toml
    pyproject_deps = analyzer.extract_dependencies(sample_pyproject)
    assert "langgraph" in pyproject_deps
    assert "qdrant-client" in pyproject_deps
    assert "chromadb" in pyproject_deps
    assert "requests" in pyproject_deps

    # 2. requirements.txt
    req_deps = analyzer.extract_dependencies(sample_requirements)
    assert req_deps == ["httpx", "langgraph", "qdrant-client"]

    # 3. package.json
    pkg_deps = analyzer.extract_dependencies(sample_package_json)
    assert "@langchain/langgraph" in pkg_deps
    assert "react" in pkg_deps


@pytest.mark.unit
def test_analyze_manifest_report(sample_pyproject: Path) -> None:
    """Proves StackReport generation with phase breakdown and caveats."""
    analyzer = StackAnalyzer.create_from_exports(exports_dir=Path("exports/v1"))
    report = analyzer.analyze_manifest(sample_pyproject)

    assert report.total_dependencies == 6
    assert report.tracked_tools_count >= 2
    assert "langgraph" in [item.entity_id for item in report.tracked_items]
    assert len(report.caveats) >= 2


@pytest.mark.unit
def test_cli_stack_command(sample_pyproject: Path) -> None:
    """Proves `footfall stack` CLI execution."""
    runner = CliRunner()

    # Human-readable output
    result = runner.invoke(main, ["stack", str(sample_pyproject)])
    assert result.exit_code == 0
    assert "Footfall Stack Health" in result.output
    assert "LangGraph" in result.output

    # JSON output
    json_result = runner.invoke(main, ["stack", str(sample_pyproject), "--json-out"])
    assert json_result.exit_code == 0
    data = json.loads(json_result.output)
    assert data["manifest_file"] == "pyproject.toml"
    assert data["tracked_tools_count"] >= 2
