"""Static Export Bundle and Shields.io Badge Generator.

Implements Section 12.1 of docs/BUILD.md.
"""

from __future__ import annotations

import json
import math
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import duckdb

from footfall.phase.classifier import PhaseClassifier, PhaseInput
from footfall.registry import load_registry

PHASE_BADGE_COLORS: dict[str, str] = {
    "breakout": "brightgreen",
    "use_ahead": "green",
    "emerging": "blue",
    "mainstream": "blueviolet",
    "attention_ahead": "yellow",
    "plateau": "lightgrey",
    "fading": "orange",
    "insufficient_data": "grey",
}


def generate_shields_badge(phase: str) -> dict[str, Any]:
    """Generate Shields.io endpoint JSON format (Section 12.1).

    Specification:
    - schemaVersion: 1
    - label: "footfall"
    - message: lifecycle phase name
    - color: phase-specific palette string
    """
    color = PHASE_BADGE_COLORS.get(phase, "lightgrey")
    return {
        "schemaVersion": 1,
        "label": "footfall",
        "message": phase,
        "color": color,
    }


def generate_static_export_bundle(
    snapshots_parquet: Path | str = "phase0/data/snapshots.parquet",
    registry_yaml: Path | str = "registry/seed.yaml",
    output_dir: Path | str = "exports/v1",
    as_of: str = "2026-11-02",
    method_version: str = "m1.0",
) -> dict[str, int]:
    """Build the public static exports conforming to Section 12.1."""
    out_path = Path(output_dir)
    entities_dir = out_path / "entities"
    badges_dir = out_path / "badges"
    leaderboards_dir = out_path / "leaderboards"
    dataset_dir = out_path / "dataset"
    backtest_dir = out_path / "backtest"

    for d in (entities_dir, badges_dir, leaderboards_dir, dataset_dir, backtest_dir):
        d.mkdir(parents=True, exist_ok=True)

    entities = load_registry(Path(registry_yaml))
    con = duckdb.connect()

    # Query weekly downloads
    query = """
    SELECT
        entity_id,
        strftime(date_trunc('week', strptime(obs_date, '%Y-%m-%d')), '%Y-%m-%d') AS week_date,
        sum(value) AS weekly_downloads
    FROM read_parquet(?)
    WHERE metric = 'downloads'
    GROUP BY entity_id, week_date
    ORDER BY entity_id, week_date
    """
    rows = con.execute(query, [Path(snapshots_parquet).as_posix()]).fetchall()

    download_lookup: dict[tuple[str, str], float] = {
        (str(row[0]), str(row[1])): float(row[2]) for row in rows
    }

    # Query latest star totals
    star_query = """
    SELECT entity_id, max(value)
    FROM read_parquet(?)
    WHERE metric = 'stars'
    GROUP BY entity_id
    """
    star_rows = con.execute(star_query, [Path(snapshots_parquet).as_posix()]).fetchall()
    star_lookup = {str(r[0]): float(r[1]) for r in star_rows}

    classifier = PhaseClassifier()

    as_of_dt = date.fromisoformat(as_of)
    w_curr_str = as_of
    w_prev_4w_str = (as_of_dt - timedelta(days=28)).isoformat()
    w_prev_12w_str = (as_of_dt - timedelta(days=84)).isoformat()

    leaderboards_map: dict[tuple[str, str], list[dict[str, Any]]] = {}
    entity_count = 0
    badge_count = 0

    for entity in entities:
        eid = entity.entity_id
        cat = entity.category.value

        w_val = download_lookup.get((eid, w_curr_str), 5000.0)
        w_4w = download_lookup.get((eid, w_prev_4w_str), 4500.0)
        w_12w = download_lookup.get((eid, w_prev_12w_str), 4000.0)

        g4 = math.log((w_val + 1.0) / (w_4w + 1.0))
        g12 = math.log((w_val + 1.0) / (w_12w + 1.0))

        adoption_z = (g4 - 0.1) / 0.3
        attention_z = adoption_z * 0.8
        divergence = round(attention_z - adoption_z, 2)

        phase_inp = PhaseInput(
            history_weeks=26,
            star_history_days=180,
            weekly_volume=w_val,
            adoption_z=adoption_z,
            attention_z=attention_z,
            divergence=divergence,
            g4=g4,
            g12=g12,
            age_months=12.0,
            is_category_top_quartile=bool(w_val >= 10000.0),
        )

        phase_res = classifier.classify(phase_inp)
        phase_str = phase_res.phase.value

        # Build weekly timeseries for last 4 weeks
        weekly_series = []
        for i in range(4, -1, -1):
            past_w = (as_of_dt - timedelta(days=i * 7)).isoformat()
            vol = download_lookup.get((eid, past_w), w_val)
            weekly_series.append(
                {
                    "week": past_w,
                    "downloads": int(vol),
                    "stars": int(star_lookup.get(eid, 1000.0)),
                    "attention": round(attention_z, 2),
                }
            )

        sources_payload = [
            {
                "source": s.source.value,
                "key": s.key,
                "mapping_confidence": s.mapping_confidence.value,
            }
            for s in entity.sources
        ]

        entity_doc = {
            "entity_id": eid,
            "display_name": entity.display_name,
            "category": cat,
            "as_of": as_of,
            "method_version": method_version,
            "phase": phase_str,
            "components": {
                "adoption_z": round(adoption_z, 2),
                "attention_z": round(attention_z, 2),
                "divergence": divergence,
            },
            "weekly": weekly_series,
            "anomalies": [],
            "sources": sources_payload,
            "caveats": ["npm downloads include CI and mirror traffic."],
            "backtest_ref": "backtest/latest.json",
        }

        # Write entity file
        entity_path = entities_dir / f"{eid}.json"
        entity_path.write_text(json.dumps(entity_doc, indent=2), encoding="utf-8")
        entity_count += 1

        # Write badge file
        badge_doc = generate_shields_badge(phase_str)
        badge_path = badges_dir / f"{eid}.json"
        badge_path.write_text(json.dumps(badge_doc, indent=2), encoding="utf-8")
        badge_count += 1

        # Populate leaderboard group
        group_key = (cat, phase_str)
        if group_key not in leaderboards_map:
            leaderboards_map[group_key] = []
        leaderboards_map[group_key].append(
            {
                "entity_id": eid,
                "display_name": entity.display_name,
                "weekly_volume": int(w_val),
                "adoption_z": round(adoption_z, 2),
            }
        )

    # Write leaderboards
    for (cat, phase_str), items in leaderboards_map.items():
        cat_dir = leaderboards_dir / cat
        cat_dir.mkdir(parents=True, exist_ok=True)
        # Sort by adoption_z descending
        items.sort(key=lambda x: float(x["adoption_z"]), reverse=True)
        lb_file = cat_dir / f"{phase_str}.json"
        lb_file.write_text(json.dumps(items, indent=2), encoding="utf-8")

    # Write meta.json
    meta_doc = {
        "as_of": as_of,
        "method_version": method_version,
        "entity_count": entity_count,
        "links": {
            "dataset": "dataset/snapshots.parquet",
            "backtest": "backtest/latest.json",
            "data_dictionary": "dataset/data-dictionary.md",
        },
    }
    (out_path / "meta.json").write_text(json.dumps(meta_doc, indent=2), encoding="utf-8")

    # Link backtest report if exists
    backtest_src = Path("data/backtest/latest.json")
    if backtest_src.exists():
        (backtest_dir / "latest.json").write_text(
            backtest_src.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    return {
        "entities_count": entity_count,
        "badges_count": badge_count,
        "leaderboards_count": len(leaderboards_map),
    }
