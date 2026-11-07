"""Parquet snapshot storage engine with primary key deduplication.

Implements Section 6.4, Section 7.1, and Section 8 of docs/BUILD.md.
Schema matches SQL definition:
  PRIMARY KEY (entity_id, source, metric, obs_date)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.parquet as pq

from footfall.collectors.base import Snapshot, SnapshotQuality

if TYPE_CHECKING:
    from collections.abc import Sequence


SNAPSHOT_ARROW_SCHEMA = pa.schema(
    [
        ("entity_id", pa.string()),
        ("source", pa.string()),
        ("metric", pa.string()),
        ("obs_date", pa.string()),
        ("value", pa.float64()),
        ("quality", pa.string()),
        ("collected_at", pa.string()),
        ("collector_version", pa.string()),
    ]
)


class ParquetSnapshotStore:
    """Manages raw and derived snapshot tables in Parquet format with deduplication."""

    def __init__(self, file_path: Path | str) -> None:
        self.file_path = Path(file_path)

    def write_snapshots(self, snapshots: Sequence[Snapshot]) -> int:
        """Write snapshots to Parquet, deduplicating against any existing records.

        Primary key: (entity_id, source, metric, obs_date). Newer records overwrite
        older records for the same key.

        Returns:
            The total number of unique records in the resulting dataset.
        """
        if not snapshots and not self.file_path.exists():
            return 0

        # Load existing records into a dictionary keyed by primary key tuple
        records: dict[tuple[str, str, str, str], dict[str, object]] = {}

        if self.file_path.exists():
            existing_table = pq.read_table(self.file_path)
            for row in existing_table.to_pylist():
                pk = (
                    str(row["entity_id"]),
                    str(row["source"]),
                    str(row["metric"]),
                    str(row["obs_date"]),
                )
                records[pk] = row

        # Merge new snapshots (overwriting duplicates with latest value)
        for s in snapshots:
            pk = (s.entity_id, s.source, s.metric, s.obs_date)
            records[pk] = {
                "entity_id": s.entity_id,
                "source": s.source,
                "metric": s.metric,
                "obs_date": s.obs_date,
                "value": float(s.value),
                "quality": s.quality.value,
                "collected_at": s.collected_at,
                "collector_version": s.collector_version,
            }

        # Convert back to PyArrow Table
        sorted_rows = sorted(
            records.values(),
            key=lambda r: (str(r["obs_date"]), str(r["entity_id"])),
        )
        table = pa.Table.from_pylist(sorted_rows, schema=SNAPSHOT_ARROW_SCHEMA)

        # Write atomically using parent directory
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(table, self.file_path, compression="snappy")
        return len(sorted_rows)

    def read_snapshots(self) -> list[Snapshot]:
        """Read all snapshots from the Parquet dataset into validated Pydantic models."""
        if not self.file_path.exists():
            return []

        table = pq.read_table(self.file_path)
        snapshots: list[Snapshot] = []

        for row in table.to_pylist():
            snapshots.append(
                Snapshot(
                    entity_id=str(row["entity_id"]),
                    source=str(row["source"]),
                    metric=str(row["metric"]),
                    obs_date=str(row["obs_date"]),
                    value=float(row["value"]),
                    quality=SnapshotQuality(str(row["quality"])),
                    collected_at=str(row["collected_at"]),
                    collector_version=str(row["collector_version"]),
                )
            )
        return snapshots
