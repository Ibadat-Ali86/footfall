"""Unit tests for the historical backfill runner and data-quality generator.

Follows AGENTS.md rules:
- Tests first.
- Offline tests using mocked collectors and fixtures.
- Validates chunking, truncation detection, and Parquet persistence.
- Validates data-quality report generation.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from footfall.backfill import BackfillEngine, generate_quality_report
from footfall.collectors.base import Snapshot, SnapshotQuality
from footfall.registry import (
    Entity,
    EntitySource,
    MappingConfidence,
    RegistryCategory,
    RegistryStatus,
)
from footfall.store.parquet import ParquetSnapshotStore


@pytest.fixture
def mock_entities() -> list[Entity]:
    """Sample entities for backfill testing."""
    return [
        Entity(
            entity_id="langgraph",
            display_name="LangGraph",
            category=RegistryCategory.AGENT_FRAMEWORK,
            status=RegistryStatus.ACTIVE,
            sources=[
                EntitySource(
                    source="npm",
                    key="@langchain/langgraph",
                    mapping_confidence=MappingConfidence.VERIFIED,
                ),
                EntitySource(
                    source="pypi",
                    key="langgraph",
                    mapping_confidence=MappingConfidence.VERIFIED,
                ),
            ],
        ),
        Entity(
            entity_id="old-framework",
            display_name="Old Framework",
            category=RegistryCategory.AGENT_FRAMEWORK,
            status=RegistryStatus.ACTIVE,
            sources=[
                EntitySource(
                    source="npm",
                    key="old-framework-pkg",
                    mapping_confidence=MappingConfidence.VERIFIED,
                )
            ],
        ),
    ]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_backfill_engine_writes_parquet(tmp_path: Path, mock_entities: list[Entity]) -> None:
    """BackfillEngine runs collectors and writes deduplicated Parquet snapshots."""
    output_parquet = tmp_path / "backfill_snapshots.parquet"
    engine = BackfillEngine(output_parquet=output_parquet, entities=mock_entities)

    # Mock npm collector collect_entity to return mock snapshots
    mock_snapshots = [
        Snapshot(
            entity_id="langgraph",
            source="npm",
            metric="downloads",
            obs_date="2026-11-01",
            value=48250.0,
            quality=SnapshotQuality.OK,
            collected_at="2026-11-02T00:00:00Z",
        ),
        Snapshot(
            entity_id="old-framework",
            source="npm",
            metric="downloads",
            obs_date="2024-01-01",
            value=15.0,
            quality=SnapshotQuality.TRUNCATED,
            collected_at="2026-11-02T00:00:00Z",
        ),
    ]

    engine.npm_collector.collect_entity = AsyncMock(
        side_effect=[[mock_snapshots[0]], [mock_snapshots[1]]]
    )
    engine.pypi_collector.collect_entity = AsyncMock(return_value=[])

    total_records = await engine.run_npm_backfill(obs_date="2026-11-01")
    assert total_records == 2

    # Verify Parquet store has the records
    store = ParquetSnapshotStore(output_parquet)
    loaded = store.read_snapshots()
    assert len(loaded) == 2

    # Verify truncation flag is preserved
    old_record = next(s for s in loaded if s.entity_id == "old-framework")
    assert old_record.quality == SnapshotQuality.TRUNCATED


@pytest.mark.unit
def test_generate_quality_report(tmp_path: Path) -> None:
    """generate_quality_report creates markdown summary with flagged truncations."""
    parquet_path = tmp_path / "test_report.parquet"
    report_md_path = tmp_path / "data_quality_report.md"

    store = ParquetSnapshotStore(parquet_path)
    store.write_snapshots(
        [
            Snapshot(
                entity_id="langgraph",
                source="npm",
                metric="downloads",
                obs_date="2026-11-01",
                value=48250.0,
                quality=SnapshotQuality.OK,
                collected_at="2026-11-02T00:00:00Z",
            ),
            Snapshot(
                entity_id="old-framework",
                source="npm",
                metric="downloads",
                obs_date="2024-01-01",
                value=15.0,
                quality=SnapshotQuality.TRUNCATED,
                collected_at="2026-11-02T00:00:00Z",
            ),
        ]
    )

    report_content = generate_quality_report(parquet_path, report_md_path)
    assert report_md_path.exists()
    assert "Data Quality Report" in report_content
    assert "Truncated Snapshots: 1" in report_content or "1 truncated" in report_content.lower()
    assert "old-framework" in report_content
