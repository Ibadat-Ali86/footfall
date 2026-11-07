"""Immutable daily raw store and publish quality gates (Task T1.2).

Implements Section 7.1 and Section 8 of docs/BUILD.md:
- Immutable daily files: data/raw/YYYY-MM-DD.parquet
- Idempotent and atomic writes using temporary swap
- Daily data-quality checks that block publishing on corrupted or low-coverage runs
"""

from __future__ import annotations

import math
import os
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from footfall.collectors.base import Snapshot, SnapshotQuality
from footfall.store.parquet import SNAPSHOT_ARROW_SCHEMA

if TYPE_CHECKING:
    from collections.abc import Sequence


class DailyQualityGateError(RuntimeError):
    """Raised when daily data-quality checks fail and block publishing."""


def validate_daily_snapshots(
    snapshots: Sequence[Snapshot],
    obs_date: str,
    total_active_entities: int,
    min_coverage_share: float = 0.80,
    max_error_share: float = 0.10,
) -> dict[str, Any]:
    """Validate daily collection run against publish quality gates.

    Blocks publish if:
    - Coverage of active entities is below min_coverage_share (default 80%)
    - Any metric value is negative, NaN, or infinite
    - Any snapshot obs_date differs from target obs_date
    - Error rate exceeds max_error_share (default 10%)
    - Duplicate (entity_id, source, metric, obs_date) primary keys exist
    """
    if not snapshots:
        raise DailyQualityGateError(f"No snapshots collected for {obs_date}!")

    unique_entities: set[str] = set()
    primary_keys: set[tuple[str, str, str, str]] = set()
    error_count = 0

    for s in snapshots:
        # 1. Date alignment
        if s.obs_date != obs_date:
            raise DailyQualityGateError(
                f"Snapshot date mismatch: expected {obs_date}, got {s.obs_date} ({s.entity_id})"
            )

        # 2. Finite non-negative check
        if math.isnan(s.value) or math.isinf(s.value) or s.value < 0.0:
            raise DailyQualityGateError(
                f"Negative or non-finite metric value: {s.value} for {s.entity_id}:{s.metric}"
            )

        # 3. Duplicate primary key check
        pk = (s.entity_id, s.source, s.metric, s.obs_date)
        if pk in primary_keys:
            raise DailyQualityGateError(f"Duplicate snapshot primary key detected: {pk}")
        primary_keys.add(pk)

        unique_entities.add(s.entity_id)
        if s.quality == SnapshotQuality.ERROR:
            error_count += 1

    # 4. Coverage check
    if total_active_entities > 0:
        coverage = len(unique_entities) / total_active_entities
        if coverage < min_coverage_share:
            raise DailyQualityGateError(
                f"Active entity coverage below required threshold: "
                f"{len(unique_entities)}/{total_active_entities} "
                f"({coverage:.1%} < {min_coverage_share:.1%})"
            )
    else:
        coverage = 1.0

    # 5. Error rate check
    error_share = error_count / len(snapshots)
    if error_share > max_error_share:
        raise DailyQualityGateError(
            f"Error share exceeds allowed ceiling: {error_count}/{len(snapshots)} "
            f"({error_share:.1%} > {max_error_share:.1%})"
        )

    return {
        "obs_date": obs_date,
        "total_snapshots": len(snapshots),
        "unique_entities": len(unique_entities),
        "coverage_share": round(coverage, 4),
        "error_count": error_count,
        "error_share": round(error_share, 4),
    }


class RawSnapshotStore:
    """Manages immutable daily raw Parquet files."""

    def __init__(self, raw_dir: Path | str) -> None:
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def get_daily_path(self, obs_date: str) -> Path:
        """Return canonical file path for a daily snapshot file."""
        return self.raw_dir / f"{obs_date}.parquet"

    def write_daily_file(
        self,
        obs_date: str,
        snapshots: Sequence[Snapshot],
        validate: bool = True,
        total_active_entities: int | None = None,
        min_coverage_share: float = 0.80,
    ) -> Path:
        """Write daily snapshots to immutable Parquet file atomically and idempotently."""
        if validate:
            active_count = (
                total_active_entities
                if total_active_entities is not None
                else len({s.entity_id for s in snapshots})
            )
            validate_daily_snapshots(
                snapshots=snapshots,
                obs_date=obs_date,
                total_active_entities=active_count,
                min_coverage_share=min_coverage_share,
            )

        target_file = self.get_daily_path(obs_date)

        # Build PyArrow Table
        record_dicts = [s.model_dump() for s in snapshots]
        table = pa.Table.from_pylist(record_dicts, schema=SNAPSHOT_ARROW_SCHEMA)

        # Atomic write via temporary file
        temp_name = f"{obs_date}.tmp.{uuid.uuid4().hex}.parquet"
        temp_file = self.raw_dir / temp_name

        try:
            pq.write_table(
                table,
                temp_file,
                compression="zstd",
                compression_level=7,
            )
            # Atomic swap
            os.replace(temp_file, target_file)
        finally:
            if temp_file.exists():
                temp_file.unlink(missing_ok=True)

        return target_file

    def read_daily_file(self, obs_date: str) -> list[Snapshot]:
        """Read daily snapshots from Parquet file."""
        target_file = self.get_daily_path(obs_date)
        if not target_file.is_file():
            raise FileNotFoundError(f"Daily snapshot file not found: {target_file}")

        table = pq.read_table(target_file)
        records = table.to_pylist()
        return [Snapshot.model_validate(r) for r in records]
