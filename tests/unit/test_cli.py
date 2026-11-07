"""Unit tests for the CLI commands."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
from click.testing import CliRunner

from footfall.cli import main
from footfall.collectors.base import Snapshot, SnapshotQuality
from footfall.store.raw import RawSnapshotStore

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.unit
def test_cli_help() -> None:
    """CLI help text should exit 0 and mention footfall."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "footfall" in result.output.lower()


@pytest.mark.unit
def test_version_flag() -> None:
    """--version flag should exit 0 and print a version string."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


@pytest.mark.unit
def test_validate_cli_success(tmp_path: Path) -> None:
    """Validate command passes on complete, valid daily raw snapshots."""
    raw_dir = tmp_path / "raw"
    store = RawSnapshotStore(raw_dir)
    obs_date = "2026-11-01"
    now_iso = datetime.now(UTC).isoformat()

    snaps = [
        Snapshot(
            entity_id=f"tool-{i}",
            source="pypi",
            metric="downloads",
            obs_date=obs_date,
            value=150.0,
            quality=SnapshotQuality.OK,
            collected_at=now_iso,
        )
        for i in range(5)
    ]
    store.write_daily_file(obs_date, snaps, validate=False)

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["validate", "--date", obs_date, "--raw-dir", str(raw_dir), "--min-coverage", "0.0"],
    )
    assert result.exit_code == 0
    assert "Validation passed" in result.output


@pytest.mark.unit
def test_validate_cli_failure_on_corrupt(tmp_path: Path) -> None:
    """Validate command fails and exits 1 on corrupted or negative snapshot values."""
    raw_dir = tmp_path / "raw"
    store = RawSnapshotStore(raw_dir)
    obs_date = "2026-11-01"
    now_iso = datetime.now(UTC).isoformat()

    snaps = [
        Snapshot(
            entity_id="tool-corrupt",
            source="pypi",
            metric="downloads",
            obs_date=obs_date,
            value=-50.0,  # Negative
            quality=SnapshotQuality.OK,
            collected_at=now_iso,
        )
    ]
    store.write_daily_file(obs_date, snaps, validate=False)

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["validate", "--date", obs_date, "--raw-dir", str(raw_dir)],
    )
    assert result.exit_code != 0
    assert "Validation failed" in result.output


@pytest.mark.unit
def test_collect_cli_runs_and_writes_raw(tmp_path: Path) -> None:
    """Collect command runs collectors and writes raw Parquet file."""
    raw_dir = tmp_path / "raw"
    obs_date = "2026-11-01"
    now_iso = datetime.now(UTC).isoformat()

    mock_snap = Snapshot(
        entity_id="langgraph",
        source="pypi",
        metric="downloads",
        obs_date=obs_date,
        value=500.0,
        quality=SnapshotQuality.OK,
        collected_at=now_iso,
    )

    patch_npm = patch("footfall.collectors.npm.NpmCollector.collect_entity", new_callable=AsyncMock)
    patch_pypi = patch(
        "footfall.collectors.pypi.PyPICollector.collect_entity", new_callable=AsyncMock
    )
    patch_gh = patch(
        "footfall.collectors.github.GitHubCollector.collect_entity", new_callable=AsyncMock
    )
    patch_hf = patch(
        "footfall.collectors.hf.HuggingFaceCollector.collect_entity", new_callable=AsyncMock
    )
    patch_hn = patch(
        "footfall.collectors.hn.HackerNewsCollector.collect_entity", new_callable=AsyncMock
    )

    with (
        patch_npm as m_npm,
        patch_pypi as m_pypi,
        patch_gh as m_gh,
        patch_hf as m_hf,
        patch_hn as m_hn,
    ):
        m_npm.return_value = []
        m_pypi.return_value = [mock_snap]
        m_gh.return_value = []
        m_hf.return_value = []
        m_hn.return_value = []

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["collect", "--date", obs_date, "--raw-dir", str(raw_dir)],
        )
        assert result.exit_code == 0
        assert "Collected" in result.output
        target_file = raw_dir / f"{obs_date}.parquet"
        assert target_file.is_file()
