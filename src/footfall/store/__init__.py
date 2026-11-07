"""Footfall storage package for Parquet raw snapshots and DuckDB views."""

from __future__ import annotations

from footfall.store.parquet import SNAPSHOT_ARROW_SCHEMA, ParquetSnapshotStore
from footfall.store.raw import DailyQualityGateError, RawSnapshotStore, validate_daily_snapshots
from footfall.store.views import DuckDBStore

__all__ = [
    "DailyQualityGateError",
    "DuckDBStore",
    "ParquetSnapshotStore",
    "RawSnapshotStore",
    "SNAPSHOT_ARROW_SCHEMA",
    "validate_daily_snapshots",
]
