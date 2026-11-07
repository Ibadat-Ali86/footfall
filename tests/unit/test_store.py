"""Unit tests for the Parquet raw storage engine and DuckDB views.

Follows AGENTS.md rules:
- Tests first.
- Offline tests using temporary directories.
- Tests deduplication on (entity_id, source, metric, obs_date).
- Tests DuckDB query execution on Parquet files.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from footfall.collectors.base import Snapshot, SnapshotQuality
from footfall.store.parquet import ParquetSnapshotStore
from footfall.store.views import DuckDBStore


@pytest.fixture
def sample_snapshots() -> list[Snapshot]:
    """Sample daily snapshots across multiple dates."""
    return [
        Snapshot(
            entity_id="langgraph",
            source="npm",
            metric="downloads",
            obs_date="2026-11-01",
            value=45000.0,
            quality=SnapshotQuality.OK,
            collected_at="2026-11-02T00:00:00Z",
        ),
        Snapshot(
            entity_id="langgraph",
            source="npm",
            metric="downloads",
            obs_date="2026-11-02",
            value=46200.0,
            quality=SnapshotQuality.OK,
            collected_at="2026-11-03T00:00:00Z",
        ),
        Snapshot(
            entity_id="crewai",
            source="pypi",
            metric="downloads",
            obs_date="2026-11-01",
            value=82000.0,
            quality=SnapshotQuality.OK,
            collected_at="2026-11-02T00:00:00Z",
        ),
        Snapshot(
            entity_id="old-tool",
            source="npm",
            metric="downloads",
            obs_date="2024-01-01",
            value=10.0,
            quality=SnapshotQuality.TRUNCATED,
            collected_at="2026-11-02T00:00:00Z",
        ),
    ]


@pytest.mark.unit
def test_save_and_load_parquet(tmp_path: Path, sample_snapshots: list[Snapshot]) -> None:
    """Store writes snapshots to Parquet and reads them back losslessly."""
    store_file = tmp_path / "snapshots.parquet"
    store = ParquetSnapshotStore(store_file)

    count = store.write_snapshots(sample_snapshots)
    assert count == 4
    assert store_file.exists()

    loaded = store.read_snapshots()
    assert len(loaded) == 4
    entity_ids = {s.entity_id for s in loaded}
    assert entity_ids == {"langgraph", "crewai", "old-tool"}


@pytest.mark.unit
def test_idempotent_write_deduplication(tmp_path: Path, sample_snapshots: list[Snapshot]) -> None:
    """Writing identical snapshots twice must deduplicate rows."""
    store_file = tmp_path / "dedup.parquet"
    store = ParquetSnapshotStore(store_file)

    # First write: 4 records
    store.write_snapshots(sample_snapshots)

    # Write again with an updated value for langgraph on 2026-11-01
    updated_snapshot = Snapshot(
        entity_id="langgraph",
        source="npm",
        metric="downloads",
        obs_date="2026-11-01",
        value=50000.0,  # updated value
        quality=SnapshotQuality.OK,
        collected_at="2026-11-04T00:00:00Z",
    )
    store.write_snapshots([updated_snapshot])

    loaded = store.read_snapshots()
    # Total count should still be 4, not 5
    assert len(loaded) == 4

    # The updated value must replace the older record
    lg_record = next(s for s in loaded if s.entity_id == "langgraph" and s.obs_date == "2026-11-01")
    assert lg_record.value == 50000.0


@pytest.mark.unit
def test_duckdb_views_query(tmp_path: Path, sample_snapshots: list[Snapshot]) -> None:
    """DuckDB query engine queries parquet file and computes summary metrics."""
    store_file = tmp_path / "duckdb_test.parquet"
    parquet_store = ParquetSnapshotStore(store_file)
    parquet_store.write_snapshots(sample_snapshots)

    duck_store = DuckDBStore(store_file)
    records = duck_store.query_records(
        "SELECT source, COUNT(*) as cnt FROM snapshots GROUP BY source"
    )
    source_counts = {r["source"]: r["cnt"] for r in records}

    assert source_counts["npm"] == 3
    assert source_counts["pypi"] == 1


@pytest.mark.unit
def test_duckdb_data_quality_report(tmp_path: Path, sample_snapshots: list[Snapshot]) -> None:
    """DuckDB generates data quality statistics identifying truncations."""
    store_file = tmp_path / "quality_test.parquet"
    parquet_store = ParquetSnapshotStore(store_file)
    parquet_store.write_snapshots(sample_snapshots)

    duck_store = DuckDBStore(store_file)
    stats = duck_store.get_quality_summary()

    assert stats["total_rows"] == 4
    assert stats["unique_entities"] == 3
    assert stats["truncated_count"] == 1
    assert stats["ok_count"] == 3
