"""Unit tests for Star Burst anomaly detection and privacy preservation.

Follows AGENTS.md:
- Tests first
- Flag for human review when editing src/footfall/anomaly/
- Proves identities and usernames are never stored
- Proves wording rules (Section 10.5: 'unusual star activity', never 'fake' or 'fraud')
"""

from __future__ import annotations

import pytest

from footfall.anomaly.bursts import (
    BurstWindow,
    detect_star_bursts,
    evaluate_privacy_preserving_sample,
)


@pytest.mark.unit
def test_detect_star_bursts_merges_consecutive_days() -> None:
    """Section 10.2: delta_d >= max(N_min, b + k * m), merge consecutive burst days."""
    # 28 days of baseline (gain = 2 stars per day)
    daily_gains = [2.0] * 28

    # 3 consecutive burst days: +150, +200, +120
    daily_gains += [150.0, 200.0, 120.0]

    # Followed by 10 normal days
    daily_gains += [2.0] * 10

    from datetime import date, timedelta

    start_d = date(2026, 6, 1)
    dates = [(start_d + timedelta(days=i)).isoformat() for i in range(len(daily_gains))]

    windows = detect_star_bursts(
        entity_id="test_repo",
        dates=dates,
        daily_gains=daily_gains,
        n_min=30.0,
        k=8.0,
    )

    assert len(windows) == 1
    w = windows[0]
    assert w.start_date == "2026-06-29"
    assert w.end_date == "2026-07-01"
    assert w.burst_days == 3
    assert w.total_stars == 470.0
    assert w.baseline_median == 2.0


@pytest.mark.unit
def test_privacy_preserving_sampling_discards_identities() -> None:
    """Section 10.3: Stargazer features in memory only, identities discarded immediately."""
    # Raw account sample with usernames in memory
    raw_stargazers = [
        {"username": "user1", "account_age_days": 10, "public_repos": 0, "followers": 0},
        {"username": "user2", "account_age_days": 5, "public_repos": 1, "followers": 0},
        {"username": "user3", "account_age_days": 500, "public_repos": 12, "followers": 45},
        {"username": "user4", "account_age_days": 200, "public_repos": 0, "followers": 0},  # low
    ]

    aggregate = evaluate_privacy_preserving_sample(raw_stargazers)

    # Must contain only aggregates and sample_size
    assert aggregate["sample_size"] == 4
    # 3 of 4 are low quality (<30 days old OR (0 repos and 0 followers))
    assert aggregate["low_quality_share"] == 0.75

    # Strictly verify NO usernames or per-account keys leaked into aggregate
    assert "username" not in aggregate
    assert "users" not in aggregate
    assert "raw" not in aggregate


@pytest.mark.unit
def test_burst_adjustment_and_hn_explanation() -> None:
    """Section 10.4 & 10.5: Flag wording and HN explanation."""
    window = BurstWindow(
        entity_id="fast-llm",
        start_date="2026-08-01",
        end_date="2026-08-03",
        burst_days=3,
        total_stars=600.0,
        baseline_median=5.0,
        burst_excess=585.0,
        low_quality_share=0.65,
        sample_size=50,
        has_hn_story=True,
    )

    summary = window.to_summary()

    # Rule: Wording must say 'unusual star activity', never 'fake', 'fraud', or 'bought'
    assert "unusual star activity" in summary["public_flag"]
    assert "fake" not in summary["public_flag"].lower()
    assert "fraud" not in summary["public_flag"].lower()
    assert "bought" not in summary["public_flag"].lower()

    # Explained by HN story lowers confidence
    assert summary["explained_by"] == "hn_story"
    assert summary["confidence"] == "medium"
