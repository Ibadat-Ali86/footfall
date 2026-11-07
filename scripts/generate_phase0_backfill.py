"""Deterministic generator for Phase 0 backfill dataset.

Generates 18 months of daily snapshots across the 180 seed entities:
- PyPI and npm download histories with weekly seasonality
- GitHub cumulative stars and daily deltas
- Injected star burst windows for Hypothesis H2 review
- Explicit truncation markers for npm boundaries (Task T0.7 rule compliance)
- Seed: 20261101 (pre-registered in phase0/preregistration.yaml)
"""

from __future__ import annotations

import math
import random
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from footfall.collectors.base import Snapshot, SnapshotQuality
from footfall.registry import load_registry
from footfall.store.parquet import ParquetSnapshotStore


def generate_backfill_dataset(
    output_parquet: Path | str,
    registry_path: Path | str,
    start_date: str = "2025-05-01",
    end_date: str = "2026-11-01",
    seed: int = 20261101,
) -> int:
    """Generate deterministic synthetic historical backfill for Phase 0."""
    rng = random.Random(seed)  # noqa: S311
    entities = load_registry(registry_path)
    store = ParquetSnapshotStore(output_parquet)

    start_d = date.fromisoformat(start_date)
    end_d = date.fromisoformat(end_date)
    total_days = (end_d - start_d).days + 1

    snapshots: list[Snapshot] = []
    now_iso = datetime.now(UTC).isoformat()

    # Pre-select entities for breakout, mainstream, plateau, fading, and star bursts
    entity_ids = [e.entity_id for e in entities]
    rng.shuffle(entity_ids)

    # 25 breakout candidates with accelerating adoption
    breakouts = set(entity_ids[:25])
    # 50 entities with injected star bursts (for H2 evaluation)
    burst_entities = set(entity_ids[25:75])
    # 3 entities with historical npm silent truncations (for T0.7 guardrail validation)
    truncated_entities = set(entity_ids[75:78])

    for entity in entities:
        e_id = entity.entity_id
        is_breakout = e_id in breakouts
        has_burst = e_id in burst_entities
        has_truncation = e_id in truncated_entities

        # Base volume scales
        base_dl = rng.uniform(200.0, 50000.0)
        daily_growth = rng.uniform(0.0005, 0.003) if is_breakout else rng.uniform(-0.0002, 0.001)

        base_stars = rng.uniform(100.0, 40000.0)
        current_stars = base_stars

        # Random burst window timing if applicable
        burst_day_idx = rng.randint(100, total_days - 60) if has_burst else -1
        burst_duration = rng.randint(2, 5) if has_burst else 0

        # Collect sources
        has_pypi = any(s.source.value == "pypi" for s in entity.sources)
        has_npm = any(s.source.value == "npm" for s in entity.sources)
        has_github = any(s.source.value == "github" for s in entity.sources)
        has_hf = any(s.source.value == "hf" for s in entity.sources)

        for day_idx in range(total_days):
            current_date = start_d + timedelta(days=day_idx)
            date_str = current_date.isoformat()
            day_of_week = current_date.weekday()

            # Weekly seasonality: weekend dip for developer tools (~35% drop on Sat/Sun)
            seasonality = 0.65 if day_of_week in (5, 6) else 1.05

            # Growth factor
            growth_mult = math.exp(daily_growth * day_idx)

            # 1. Downloads (PyPI and/or npm)
            noise = rng.gauss(1.0, 0.08)
            daily_dl = max(5.0, base_dl * growth_mult * seasonality * noise)

            if has_pypi:
                snapshots.append(
                    Snapshot(
                        entity_id=e_id,
                        source="pypi",
                        metric="downloads",
                        obs_date=date_str,
                        value=round(daily_dl * (0.6 if has_npm else 1.0), 1),
                        quality=SnapshotQuality.OK,
                        collected_at=now_iso,
                    )
                )

            if has_npm:
                # If entity is flagged for silent truncation on early dates
                quality = SnapshotQuality.OK
                if has_truncation and day_idx < 14:
                    quality = SnapshotQuality.TRUNCATED

                snapshots.append(
                    Snapshot(
                        entity_id=e_id,
                        source="npm",
                        metric="downloads",
                        obs_date=date_str,
                        value=round(daily_dl * (0.4 if has_pypi else 1.0), 1),
                        quality=quality,
                        collected_at=now_iso,
                    )
                )

            # 2. GitHub Stars
            if has_github:
                base_daily_star_gain = max(0.5, (base_stars / 1000.0) * rng.uniform(0.5, 1.5))
                is_burst = burst_day_idx <= day_idx < (burst_day_idx + burst_duration)
                burst_bonus = rng.uniform(80.0, 300.0) if is_burst else 0.0

                daily_gain = base_daily_star_gain + burst_bonus
                current_stars += daily_gain

                snapshots.append(
                    Snapshot(
                        entity_id=e_id,
                        source="github",
                        metric="stars",
                        obs_date=date_str,
                        value=round(current_stars, 1),
                        quality=SnapshotQuality.OK,
                        collected_at=now_iso,
                    )
                )

            # 3. Hugging Face
            if has_hf and day_idx % 7 == 0:  # weekly HF snapshot
                hf_dl = max(10.0, base_dl * 0.3 * growth_mult * rng.uniform(0.9, 1.1))
                snapshots.append(
                    Snapshot(
                        entity_id=e_id,
                        source="hf",
                        metric="downloads",
                        obs_date=date_str,
                        value=round(hf_dl, 1),
                        quality=SnapshotQuality.OK,
                        collected_at=now_iso,
                    )
                )

    total_written = store.write_snapshots(snapshots)
    return total_written


if __name__ == "__main__":
    root_dir = Path(__file__).parents[1]
    registry_file = root_dir / "registry" / "seed.yaml"
    out_parquet = root_dir / "phase0" / "data" / "snapshots.parquet"

    print("Generating deterministic Phase 0 backfill dataset...")
    count = generate_backfill_dataset(
        output_parquet=out_parquet,
        registry_path=registry_file,
    )
    print(f"Dataset generated: {out_parquet} ({count} records)")
