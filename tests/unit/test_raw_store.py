"""Unit tests for the raw snapshot store and publish quality gates (Task T1.2).

Follows AGENTS.md:
- Tests first
- Tests immutable daily files, idempotent writes, and data-quality checks that block publish
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from footfall.collectors.base import Snapshot, SnapshotQuality
from footfall.store.raw import (
    DailyQualityGateError,
    RawSnapshotStore,
    validate_daily_snapshots,
)


@pytest.fixture
def sample_valid_snapshots() -> list[Snapshot]:
    """10 valid snapshots for 5 entities across sources."""
    now_iso = datetime.now(UTC).isoformat()
    snaps: list[Snapshot] = []
    for i in range(5):
        eid = f"entity-{i}"
        snaps.append(
            Snapshot(
                entity_id=eid,
                source="pypi",
                metric="downloads",
                obs_date="2026-11-01",
                value=500.0 + i * 100,
                quality=SnapshotQuality.OK,
                collected_at=now_iso,
            )
        )
        snaps.append(
            Snapshot(
                entity_id=eid,
                source="github",
                metric="stars",
                obs_date="2026-11-01",
                value=1200.0 + i * 50,
                quality=SnapshotQuality.OK,
                collected_at=now_iso,
            )
        )
    return snaps


@pytest.mark.unit
def test_raw_store_writes_daily_parquet_idempotently(
    tmp_path: Path, sample_valid_snapshots: list[Snapshot]
) -> None:
    """Store writes data/raw/YYYY-MM-DD.parquet atomically and idempotently."""
    store = RawSnapshotStore(raw_dir=tmp_path / "raw")

    # First write
    written_path = store.write_daily_file("2026-11-01", sample_valid_snapshots)
    assert written_path.is_file()
    assert written_path.name == "2026-11-01.parquet"

    # Read back
    read_snaps = store.read_daily_file("2026-11-01")
    assert len(read_snaps) == 10

    # Second idempotent write
    written_path_2 = store.write_daily_file("2026-11-01", sample_valid_snapshots)
    assert written_path_2 == written_path
    read_snaps_2 = store.read_daily_file("2026-11-01")
    assert len(read_snaps_2) == 10


@pytest.mark.unit
def test_validate_daily_snapshots_blocks_publish_on_low_coverage() -> None:
    """Daily quality gate blocks publish when entity coverage is below threshold."""
    now_iso = datetime.now(UTC).isoformat()
    # 2 entities present out of 10 total active (20% coverage < 80% threshold)
    snaps = [
        Snapshot(
            entity_id="entity-1",
            source="pypi",
            metric="downloads",
            obs_date="2026-11-01",
            value=100.0,
            quality=SnapshotQuality.OK,
            collected_at=now_iso,
        ),
        Snapshot(
            entity_id="entity-2",
            source="pypi",
            metric="downloads",
            obs_date="2026-11-01",
            value=200.0,
            quality=SnapshotQuality.OK,
            collected_at=now_iso,
        ),
    ]

    with pytest.raises(DailyQualityGateError, match="coverage below required threshold"):
        validate_daily_snapshots(
            snapshots=snaps,
            obs_date="2026-11-01",
            total_active_entities=10,
            min_coverage_share=0.80,
        )


@pytest.mark.unit
def test_validate_daily_snapshots_blocks_on_negative_or_nan() -> None:
    """Daily quality gate blocks on invalid negative metric values."""
    now_iso = datetime.now(UTC).isoformat()
    snaps = [
        Snapshot(
            entity_id="entity-1",
            source="pypi",
            metric="downloads",
            obs_date="2026-11-01",
            value=-50.0,  # Negative
            quality=SnapshotQuality.OK,
            collected_at=now_iso,
        )
    ]

    with pytest.raises(DailyQualityGateError, match="Negative or non-finite"):
        validate_daily_snapshots(
            snapshots=snaps,
            obs_date="2026-11-01",
            total_active_entities=1,
            min_coverage_share=0.80,
        )
