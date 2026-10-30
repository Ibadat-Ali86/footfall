"""Tests for the CLI entry point — smoke tests only at scaffold stage."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from footfall.cli import main


@pytest.mark.unit
def test_cli_help() -> None:
    """CLI help text should exit 0 and mention footfall."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "footfall" in result.output.lower()


@pytest.mark.unit
def test_collect_not_implemented() -> None:
    """collect command must raise NotImplementedError until T1.1 is done."""
    runner = CliRunner()
    result = runner.invoke(main, ["collect"])
    # Click wraps unhandled exceptions; exit code 1 is expected
    assert result.exit_code != 0


@pytest.mark.unit
def test_version_flag() -> None:
    """--version flag should exit 0 and print a version string."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
