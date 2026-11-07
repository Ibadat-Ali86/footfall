"""Unit test for reproducible backtest pipeline (Section 11.5).

Follows AGENTS.md:
- Tests first
- Proves end-to-end reproduce run from raw snapshots
- Proves manifest verification
"""

from __future__ import annotations

from pathlib import Path

import pytest

from footfall.ledger.reproduce import (
    compute_file_sha256,
    run_reproduce_pipeline,
)


@pytest.mark.unit
def test_compute_file_sha256(tmp_path: Path) -> None:
    """Proves deterministic file hashing."""
    test_file = tmp_path / "hello.txt"
    test_file.write_text("Footfall reproducible backtest", encoding="utf-8")
    h1 = compute_file_sha256(test_file)
    h2 = compute_file_sha256(test_file)
    assert len(h1) == 64
    assert h1 == h2


@pytest.mark.unit
def test_reproduce_pipeline_end_to_end(tmp_path: Path) -> None:
    """Section 11.5: Rebuild derived tables and verify output hashes."""
    # Use existing snapshots if available, or skip if run in an environment without snapshots
    snapshots_path = Path("phase0/data/snapshots.parquet")
    registry_path = Path("registry/seed.yaml")
    if not snapshots_path.exists() or not registry_path.exists():
        pytest.skip("Phase 0 snapshots or seed registry not present")

    ledger_out = tmp_path / "calls.jsonl"
    backtest_out = tmp_path / "latest.json"
    manifest_out = tmp_path / "manifest.json"

    # 1. Initial run generates manifest
    manifest1 = run_reproduce_pipeline(
        snapshots_parquet=snapshots_path,
        registry_yaml=registry_path,
        ledger_output=ledger_out,
        backtest_output=backtest_out,
        manifest_path=manifest_out,
        verify=False,
    )

    assert manifest1["total_calls"] > 0
    assert manifest1["resolved_calls"] > 0
    assert manifest_out.exists()

    # 2. Verification run proves exact hash reproduction
    manifest2 = run_reproduce_pipeline(
        snapshots_parquet=snapshots_path,
        registry_yaml=registry_path,
        ledger_output=ledger_out,
        backtest_output=backtest_out,
        manifest_path=manifest_out,
        verify=True,
    )

    assert manifest1["calls_ledger_sha256"] == manifest2["calls_ledger_sha256"]
    assert manifest1["backtest_report_sha256"] == manifest2["backtest_report_sha256"]
