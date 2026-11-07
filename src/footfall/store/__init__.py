"""Footfall storage package for Parquet raw snapshots and DuckDB views."""

from __future__ import annotations

from footfall.store.parquet import SNAPSHOT_ARROW_SCHEMA, ParquetSnapshotStore
from footfall.store.views import DuckDBStore

__all__ = [
    "DuckDBStore",
    "ParquetSnapshotStore",
    "SNAPSHOT_ARROW_SCHEMA",
]
