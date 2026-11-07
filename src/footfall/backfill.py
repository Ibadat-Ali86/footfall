"""Historical backfill engine and data-quality report generator.

Implements Task T0.7 of docs/BUILD.md:
- Backfill up to 18 months of npm daily downloads
- Backfill PyPI download history with throttling
- Persist snapshots to Parquet with deduplication
- Generate automated data quality report
- Enforce "No truncation may go unflagged" rule
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from footfall.collectors import (
    GitHubCollector,
    HackerNewsCollector,
    HuggingFaceCollector,
    NpmCollector,
    PyPICollector,
    Snapshot,
)
from footfall.registry import Entity, load_registry
from footfall.store.parquet import ParquetSnapshotStore
from footfall.store.views import DuckDBStore

if TYPE_CHECKING:
    from collections.abc import Sequence


class BackfillEngine:
    """Orchestrates historical data backfills across all upstream registries."""

    def __init__(
        self,
        output_parquet: Path | str,
        entities: Sequence[Entity] | None = None,
        registry_path: Path | str | None = None,
    ) -> None:
        self.output_parquet = Path(output_parquet)
        if entities is not None:
            self.entities = list(entities)
        else:
            default_reg = Path(__file__).parents[2] / "registry" / "seed.yaml"
            reg_file = Path(registry_path or default_reg)
            self.entities = load_registry(reg_file)

        self.store = ParquetSnapshotStore(self.output_parquet)
        self.npm_collector = NpmCollector()
        self.pypi_collector = PyPICollector()
        self.github_collector = GitHubCollector()
        self.hf_collector = HuggingFaceCollector()
        self.hn_collector = HackerNewsCollector()

    async def run_npm_backfill(self, obs_date: str) -> int:
        """Backfill npm download telemetry for all npm-registered entities."""
        collected: list[Snapshot] = []

        for entity in self.entities:
            for source in entity.sources:
                if source.source.value == "npm":
                    snapshots = await self.npm_collector.collect_entity(
                        entity.entity_id, source.key, obs_date
                    )
                    collected.extend(snapshots)
                    # Gentle 100ms throttle between sequential npm calls
                    await asyncio.sleep(0.1)

        return self.store.write_snapshots(collected)

    async def run_pypi_backfill(self, obs_date: str) -> int:
        """Backfill PyPI download telemetry for all PyPI-registered entities."""
        collected: list[Snapshot] = []

        for entity in self.entities:
            for source in entity.sources:
                if source.source.value == "pypi":
                    snapshots = await self.pypi_collector.collect_entity(
                        entity.entity_id, source.key, obs_date
                    )
                    collected.extend(snapshots)
                    # Enforce strict 1 RPS throttle on pypistats.org
                    await asyncio.sleep(1.0)

        return self.store.write_snapshots(collected)

    async def run_github_backfill(self, obs_date: str) -> int:
        """Backfill GitHub repository metrics for all GitHub-registered entities."""
        collected: list[Snapshot] = []

        for entity in self.entities:
            for source in entity.sources:
                if source.source.value == "github":
                    snapshots = await self.github_collector.collect_entity(
                        entity.entity_id, source.key, obs_date
                    )
                    collected.extend(snapshots)

        return self.store.write_snapshots(collected)


def generate_quality_report(
    parquet_path: Path | str,
    report_md_path: Path | str,
) -> str:
    """Generate comprehensive markdown data quality report from DuckDB views."""
    parquet_file = Path(parquet_path)
    report_file = Path(report_md_path)

    duck_store = DuckDBStore(parquet_file)
    summary = duck_store.get_quality_summary()
    coverage = duck_store.get_coverage_by_entity()

    total_rows = summary.get("total_rows", 0)
    unique_entities = summary.get("unique_entities", 0)
    ok_count = summary.get("ok_count", 0)
    truncated_count = summary.get("truncated_count", 0)
    partial_count = summary.get("partial_count", 0)
    error_count = summary.get("error_count", 0)
    start_date = summary.get("start_date", "N/A")
    end_date = summary.get("end_date", "N/A")

    truncated_entities: list[str] = [
        f"`{row['entity_id']}` ({row['source']}, {row['truncated_days']} truncated days)"
        for row in coverage
        if row.get("truncated_days", 0) > 0
    ]

    truncation_section = "None detected. All observed spans are complete."
    if truncated_entities:
        truncation_section = (
            f"**WARNING: {len(truncated_entities)} entity spans flagged with silent truncation:**\n"
            + "\n".join(f"- {item}" for item in truncated_entities)
        )

    table_rows = "\n".join(
        f"| `{r['entity_id']}` | `{r['source']}` | `{r['metric']}` | "
        f"{r['days_count']} | {r['first_date']} | {r['last_date']} | {r['truncated_days']} |"
        for r in coverage[:50]  # Cap preview at 50 rows in report
    )

    now_iso = datetime.now(UTC).isoformat()
    report_md = f"""# Footfall Data Quality Report (Task T0.7)

**Generated:** {now_iso}
**Dataset:** `{parquet_file.name}`
**Rule Compliance:** "No truncation may go unflagged." (Section 7.1 & Section 16)

---

## 1. Executive Summary

| Metric | Value | Notes |
|---|---|---|
| **Total Snapshot Records** | {total_rows} | Primary key: (entity_id, source, metric, obs_date) |
| **Unique Tracked Entities** | {unique_entities} | Across 6 categories |
| **Date Range Covered** | `{start_date}` to `{end_date}` | UTC |
| **Valid (OK) Snapshots** | {ok_count} | Complete daily observation |
| **Truncated Snapshots** | {truncated_count} | Flagged by date-boundary assertions |
| **Partial Snapshots** | {partial_count} | Incomplete metric components |
| **Error Snapshots** | {error_count} | Upstream API failure / unmapped key |

---

## 2. Truncation & Anomaly Audit

{truncation_section}

---

## 3. Entity Coverage Sample (Top 50 Spans)

| Entity ID | Source | Metric | Days Count | Start Date | End Date | Truncated Days |
|---|---|---|---|---|---|---|
{table_rows}

---

*Report automatically generated by `footfall.backfill.generate_quality_report`.*
"""

    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(report_md, encoding="utf-8")
    return report_md
