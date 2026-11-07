"""Unit tests for Footfall feature engine and leakage prevention.

Follows AGENTS.md:
- Tests first
- No live API calls
- Mathematical verification of Section 9 specifications
- Explicit leakage test: future data must not alter historical features
"""

from __future__ import annotations

import math
from datetime import UTC, date, datetime, timedelta

import pytest

from footfall.collectors.base import Snapshot, SnapshotQuality
from footfall.features.adoption import (
    aggregate_weekly_downloads,
    compute_adoption_metrics,
)
from footfall.features.attention import (
    compute_hn_attention,
    compute_star_metrics,
)
from footfall.features.normalize import (
    compute_divergence_index,
    rank_normalize_features,
)


@pytest.mark.unit
def test_weekly_downloads_aggregation_rules() -> None:
    """Section 9.1: Sum of 7 daily values. Require at least 6 of 7 days quality=ok."""
    week_start = date(2026, 10, 5)  # Monday
    now_iso = datetime.now(UTC).isoformat()

    # 1. Complete week: all 7 days ok
    snaps_ok = [
        Snapshot(
            entity_id="pkg1",
            source="pypi",
            metric="downloads",
            obs_date=(week_start + timedelta(days=i)).isoformat(),
            value=100.0,
            quality=SnapshotQuality.OK,
            collected_at=now_iso,
        )
        for i in range(7)
    ]
    w_val = aggregate_weekly_downloads(snaps_ok)
    assert w_val == 700.0

    # 2. 6 days ok, 1 truncated: valid under 6-of-7 rule
    snaps_6_ok = snaps_ok[:6] + [
        Snapshot(
            entity_id="pkg1",
            source="pypi",
            metric="downloads",
            obs_date=(week_start + timedelta(days=6)).isoformat(),
            value=100.0,
            quality=SnapshotQuality.TRUNCATED,
            collected_at=now_iso,
        )
    ]
    w_val_6 = aggregate_weekly_downloads(snaps_6_ok)
    assert w_val_6 == 600.0

    # 3. Only 5 days ok: week is missing (returns None)
    snaps_5_ok = snaps_ok[:5]
    w_val_5 = aggregate_weekly_downloads(snaps_5_ok)
    assert w_val_5 is None


@pytest.mark.unit
def test_adoption_growth_metrics() -> None:
    """Section 9.2: L = ln(W + 1), g4, g12, acc."""
    # Setup 16 weekly download values
    weekly_w = [100.0] * 16  # Constant 100
    metrics = compute_adoption_metrics(weekly_w, current_idx=15)
    assert metrics is not None
    assert math.isclose(metrics["L"], math.log(101.0))
    assert math.isclose(metrics["g4"], 0.0, abs_tol=1e-6)
    assert math.isclose(metrics["g12"], 0.0, abs_tol=1e-6)
    assert math.isclose(metrics["acc"], 0.0, abs_tol=1e-6)

    # Accelerating series: W doubles every 4 weeks
    # W: 100, ..., 200, ..., 400, ..., 800
    weekly_acc = [100.0] * 4 + [200.0] * 4 + [400.0] * 4 + [800.0] * 4
    metrics_acc = compute_adoption_metrics(weekly_acc, current_idx=15)
    assert metrics_acc is not None
    # g4 = ln(801) - ln(401) ~= ln(2) ~= 0.6931
    assert math.isclose(metrics_acc["g4"], math.log(801.0 / 401.0), rel_tol=1e-4)


@pytest.mark.unit
def test_star_metrics() -> None:
    """Section 9.3: s28 = stars(t) - stars(t-28d), s28_rel = s28 / (stars(t-28d) + 50)."""
    stars_t = 1200.0
    stars_t_minus_28 = 1000.0

    res = compute_star_metrics(stars_t=stars_t, stars_prev=stars_t_minus_28)
    assert res["s28"] == 200.0
    expected_rel = 200.0 / (1000.0 + 50.0)
    assert math.isclose(res["s28_rel"], expected_rel)


@pytest.mark.unit
def test_hn_attention_decay() -> None:
    """Section 9.4: A(t) = sum_k 0.5^(d_k / 14) * (1 + ln(1 + p_k))."""
    # Story today (d=0) with 99 points: 0.5^0 * (1 + ln(100)) = 1 + ln(100)
    stories = [{"offset_days": 0, "points": 99}]
    a_val = compute_hn_attention(stories)
    expected = 1.0 + math.log(100.0)
    assert math.isclose(a_val, expected, rel_tol=1e-5)

    # Story 14 days ago (d=14) with 99 points: 0.5^1 * (1 + ln(100))
    stories_14 = [{"offset_days": 14, "points": 99}]
    a_val_14 = compute_hn_attention(stories_14)
    assert math.isclose(a_val_14, expected * 0.5, rel_tol=1e-5)

    # No stories returns 0.0
    assert compute_hn_attention([]) == 0.0


@pytest.mark.unit
def test_cross_sectional_normalization_and_divergence() -> None:
    """Section 9.5 & 9.6: Rank-normalize within group to standard normal z(.), compute D."""
    values = [10.0, 50.0, 100.0, 200.0, 500.0]
    z_scores = rank_normalize_features(values)
    assert len(z_scores) == len(values)
    # Monotonicity: higher values get strictly higher z-scores
    for i in range(len(z_scores) - 1):
        assert z_scores[i] < z_scores[i + 1]

    # Mean should be close to 0.0
    assert math.isclose(sum(z_scores) / len(z_scores), 0.0, abs_tol=1e-5)

    # Divergence calculation
    div = compute_divergence_index(
        attention_z=1.5,
        adoption_z=0.2,
    )
    assert div["D"] == 1.3
    assert div["is_attention_ahead"] is True
    assert div["is_use_ahead"] is False


@pytest.mark.unit
def test_leakage_invariance() -> None:
    """Strict leakage test: modifying or adding data after time t must not change features at t."""
    from footfall.features.engine import FeatureEngine

    engine = FeatureEngine()

    # Generate historical sequence of 10 weeks
    base_data = {
        "pkg_test": [1000.0 + i * 50.0 for i in range(10)],
    }

    features_t = engine.compute_entity_week_features(
        entity_id="pkg_test",
        weekly_downloads=base_data["pkg_test"],
        weekly_stars=[500.0 + i * 20.0 for i in range(10)],
        current_week_idx=9,
    )

    # Simulate future: 5 weeks of massive breakout added at weeks 10..14
    future_data = {
        "pkg_test": base_data["pkg_test"] + [50000.0, 100000.0, 200000.0, 500000.0, 1000000.0],
    }

    features_t_with_future = engine.compute_entity_week_features(
        entity_id="pkg_test",
        weekly_downloads=future_data["pkg_test"],
        weekly_stars=[500.0 + i * 20.0 for i in range(10)] + [10000.0] * 5,
        current_week_idx=9,
    )

    # Features at week 9 MUST be bit-for-bit identical
    for k in ["L", "g4", "s28", "s28_rel"]:
        assert math.isclose(features_t[k], features_t_with_future[k]), (
            f"Leakage detected on feature {k}!"
        )
