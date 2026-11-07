"""DuckDB query engine and views over Parquet snapshot datasets.

Implements Section 6.5 and Section 8 of docs/BUILD.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import duckdb

if TYPE_CHECKING:
    import pandas as pd
    import pyarrow as pa


class DuckDBStore:
    """Provides SQL analytical views and data-quality summaries over Parquet files."""

    def __init__(self, parquet_path: Path | str) -> None:
        self.parquet_path = Path(parquet_path)
        self.conn = duckdb.connect(database=":memory:")
        self._init_views()

    def _init_views(self) -> None:
        """Create analytical view over the Parquet file if it exists."""
        if self.parquet_path.exists():
            resolved = str(self.parquet_path.resolve())
            self.conn.read_parquet(resolved).to_view("snapshots")

    def query_arrow(self, sql: str) -> pa.Table:
        """Execute query and return PyArrow table natively."""
        table: pa.Table = self.conn.sql(sql).to_arrow_table()
        return table

    def query_records(self, sql: str) -> list[dict[str, Any]]:
        """Execute query and return list of row dictionaries."""
        table: pa.Table = self.conn.sql(sql).to_arrow_table()
        records: list[dict[str, Any]] = table.to_pylist()
        return records

    def query_df(self, sql: str) -> pd.DataFrame:
        """Execute analytical SQL and return pandas DataFrame (requires pandas)."""
        return self.conn.execute(sql).df()

    def get_quality_summary(self) -> dict[str, Any]:
        """Compute data-quality metrics, truncation flags, and date coverage."""
        if not self.parquet_path.exists():
            return {
                "total_rows": 0,
                "unique_entities": 0,
                "ok_count": 0,
                "truncated_count": 0,
                "partial_count": 0,
                "error_count": 0,
                "start_date": None,
                "end_date": None,
            }

        sql = """
        SELECT
            COUNT(*) as total_rows,
            COUNT(DISTINCT entity_id) as unique_entities,
            COUNT(CASE WHEN quality = 'ok' THEN 1 END) as ok_count,
            COUNT(CASE WHEN quality = 'truncated' THEN 1 END) as truncated_count,
            COUNT(CASE WHEN quality = 'partial' THEN 1 END) as partial_count,
            COUNT(CASE WHEN quality = 'error' THEN 1 END) as error_count,
            MIN(obs_date) as start_date,
            MAX(obs_date) as end_date
        FROM snapshots
        """
        row = self.conn.execute(sql).fetchone()
        if not row:
            return {}

        return {
            "total_rows": int(row[0]),
            "unique_entities": int(row[1]),
            "ok_count": int(row[2]),
            "truncated_count": int(row[3]),
            "partial_count": int(row[4]),
            "error_count": int(row[5]),
            "start_date": str(row[6]) if row[6] is not None else None,
            "end_date": str(row[7]) if row[7] is not None else None,
        }

    def get_coverage_by_entity(self) -> list[dict[str, Any]]:
        """Compute per-entity coverage statistics across sources and spans."""
        if not self.parquet_path.exists():
            return []

        sql = """
        SELECT
            entity_id,
            source,
            metric,
            COUNT(*) as days_count,
            MIN(obs_date) as first_date,
            MAX(obs_date) as last_date,
            COUNT(CASE WHEN quality = 'truncated' THEN 1 END) as truncated_days
        FROM snapshots
        GROUP BY entity_id, source, metric
        ORDER BY entity_id, source
        """
        rows = self.conn.execute(sql).fetchall()
        return [
            {
                "entity_id": str(r[0]),
                "source": str(r[1]),
                "metric": str(r[2]),
                "days_count": int(r[3]),
                "first_date": str(r[4]),
                "last_date": str(r[5]),
                "truncated_days": int(r[6]),
            }
            for r in rows
        ]
