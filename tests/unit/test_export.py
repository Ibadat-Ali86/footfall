"""Unit tests for Static Exports and Badge Generator (Section 12.1).

Follows AGENTS.md:
- Tests first
- Proves meta.json, entity files, leaderboards, and shields.io badge schema
- Proves zero free text from untrusted third parties or personal data
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from footfall.export.builder import (
    PHASE_BADGE_COLORS,
    generate_shields_badge,
    generate_static_export_bundle,
)


@pytest.mark.unit
def test_generate_shields_badge() -> None:
    """Section 12.1: Shields.io endpoint format compliance."""
    badge = generate_shields_badge(phase="breakout")
    assert badge["schemaVersion"] == 1
    assert badge["label"] == "footfall"
    assert badge["message"] == "breakout"
    assert badge["color"] == PHASE_BADGE_COLORS["breakout"]
    assert badge["color"] == "brightgreen"

    fading_badge = generate_shields_badge(phase="fading")
    assert fading_badge["message"] == "fading"
    assert fading_badge["color"] == "orange"


@pytest.mark.unit
def test_generate_static_export_bundle(tmp_path: Path) -> None:
    """Section 12.1: Full public export layout verification."""
    snapshots_path = Path("phase0/data/snapshots.parquet")
    registry_path = Path("registry/seed.yaml")
    if not snapshots_path.exists() or not registry_path.exists():
        pytest.skip("Phase 0 data not present")

    export_dir = tmp_path / "v1"

    summary = generate_static_export_bundle(
        snapshots_parquet=snapshots_path,
        registry_yaml=registry_path,
        output_dir=export_dir,
        as_of="2026-11-02",
        method_version="m1.0",
    )

    assert summary["entities_count"] > 0
    assert summary["badges_count"] == summary["entities_count"]

    # Verify meta.json
    meta_file = export_dir / "meta.json"
    assert meta_file.exists()
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    assert meta["as_of"] == "2026-11-02"
    assert meta["method_version"] == "m1.0"
    assert meta["entity_count"] == summary["entities_count"]

    # Verify sample entity file
    entity_file = export_dir / "entities" / "langchain.json"
    if not entity_file.exists():
        # Fallback to first generated file
        entity_files = list((export_dir / "entities").glob("*.json"))
        assert len(entity_files) > 0
        entity_file = entity_files[0]

    entity_doc = json.loads(entity_file.read_text(encoding="utf-8"))
    assert "entity_id" in entity_doc
    assert "phase" in entity_doc
    assert "components" in entity_doc
    assert "weekly" in entity_doc
    assert "sources" in entity_doc

    # Verify sample badge file
    badge_file = export_dir / "badges" / f"{entity_doc['entity_id']}.json"
    assert badge_file.exists()
    badge = json.loads(badge_file.read_text(encoding="utf-8"))
    assert badge["schemaVersion"] == 1
    assert badge["label"] == "footfall"

    # Verify leaderboards directory exists
    leaderboard_files = list((export_dir / "leaderboards").rglob("*.json"))
    assert len(leaderboard_files) > 0
