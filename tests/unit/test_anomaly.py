"""Unit tests for the Anomaly module (Section 10 & 9.9).

Follows AGENTS.md:
- Tests first
- Flag for human review when editing src/footfall/anomaly/
- Proves identities, usernames, and PII are never written to disk or logs
- Proves wording rules (Section 10.5: 'unusual star activity', never 'fake' or 'fraud')
- Proves download anomaly detection (Section 9.9: 'download_step',
  caveat 'possible CI, mirror or bot traffic')
"""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from typing import Any

import pytest

from footfall.anomaly.bursts import (
    BurstWindow,
    compute_adjusted_star_gain,
    evaluate_privacy_preserving_sample,
)
from footfall.anomaly.downloads import (
    detect_download_anomalies,
)


@pytest.mark.unit
def test_privacy_audit_zero_identities_persisted(
    tmp_path: Any,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """T1.6 Mandate: Strictly proves identities/usernames are NEVER written to disk or logs."""
    # 1. Setup logging capture
    caplog.set_level(logging.DEBUG)

    # 2. Raw input containing PII / usernames / identity metadata
    sensitive_usernames = ["alice_smith_99", "bob_suspicious_bot", "charlie_farm_user"]
    raw_stargazers = [
        {
            "username": sensitive_usernames[0],
            "account_age_days": 10,
            "public_repos": 0,
            "followers": 0,
        },
        {
            "username": sensitive_usernames[1],
            "account_age_days": 5,
            "public_repos": 0,
            "followers": 0,
        },
        {
            "username": sensitive_usernames[2],
            "account_age_days": 20,
            "public_repos": 0,
            "followers": 0,
        },
    ]

    # 3. Execute privacy-preserving sampling
    sample_metrics = evaluate_privacy_preserving_sample(raw_stargazers)

    # 4. Create a BurstWindow and persist its summary output to disk
    window = BurstWindow(
        entity_id="test-agent",
        start_date="2026-05-01",
        end_date="2026-05-03",
        burst_days=3,
        total_stars=300.0,
        baseline_median=5.0,
        burst_excess=285.0,
        low_quality_share=sample_metrics["low_quality_share"],
        sample_size=sample_metrics["sample_size"],
    )

    summary = window.to_summary()

    # Write summary to disk
    out_file = tmp_path / "anomaly_output.json"
    out_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # 5. Read entire disk content and verify NO sensitive identifiers exist
    disk_content = out_file.read_text(encoding="utf-8")
    for name in sensitive_usernames:
        assert name not in disk_content, f"PII leak detected on disk: {name}"

    # 6. Verify NO sensitive identifiers exist in any log records
    for name in sensitive_usernames:
        assert name not in caplog.text, f"PII leak detected in logs: {name}"

    # 7. Check output contains only aggregate statistics
    assert summary["sample_size"] == 3
    assert summary["low_quality_share"] == 1.0
    assert "alice" not in str(summary)


@pytest.mark.unit
def test_download_anomaly_detection_flags_download_step() -> None:
    """Section 9.9: Robust z-score of weekly L differences >= 4 without matching star/HN."""
    # 30 weeks of stable downloads: 10,000/week (L = ln(10001) ~ 9.21)
    weeks: list[str] = []
    downloads: list[float] = []
    start_d = date(2026, 1, 5)  # Monday

    for i in range(30):
        weeks.append((start_d + timedelta(weeks=i)).isoformat())
        downloads.append(10000.0)

    # Week 30: massive sudden 10x spike to 100,000/week without star or HN activity
    weeks.append((start_d + timedelta(weeks=30)).isoformat())
    downloads.append(100000.0)

    # Detect anomalies
    anomalies = detect_download_anomalies(
        entity_id="sample-lib",
        week_dates=weeks,
        weekly_downloads=downloads,
        star_activity_dates=[],
        hn_story_dates=[],
        z_threshold=4.0,
    )

    assert len(anomalies) == 1
    anom = anomalies[0]
    assert anom.entity_id == "sample-lib"
    assert anom.week_date == weeks[30]
    assert anom.flag_type == "download_step"
    assert anom.robust_z >= 4.0
    assert "possible CI, mirror or bot traffic" in anom.caveat
    # Section 9.9: Never call it fraud
    assert "fraud" not in anom.caveat.lower()
    assert "fake" not in anom.caveat.lower()


@pytest.mark.unit
def test_download_anomaly_suppressed_when_matching_star_or_hn_activity() -> None:
    """Section 9.9: If matching star or HN activity within 2 weeks, do not flag download_step."""
    weeks: list[str] = []
    downloads: list[float] = []
    start_d = date(2026, 1, 5)

    for i in range(30):
        weeks.append((start_d + timedelta(weeks=i)).isoformat())
        downloads.append(10000.0)

    spike_week = (start_d + timedelta(weeks=30)).isoformat()
    weeks.append(spike_week)
    downloads.append(100000.0)

    # Matching HN story 3 days before the spike week
    hn_story_date = (start_d + timedelta(weeks=30) - timedelta(days=3)).isoformat()

    anomalies = detect_download_anomalies(
        entity_id="sample-lib",
        week_dates=weeks,
        weekly_downloads=downloads,
        star_activity_dates=[],
        hn_story_dates=[hn_story_date],
        z_threshold=4.0,
    )

    # Should be empty because HN activity explains the download increase
    assert len(anomalies) == 0


@pytest.mark.unit
def test_dispute_status_hides_public_flag() -> None:
    """Section 10.5: Maintainers can dispute; flag is hidden while status is 'disputed'."""
    window = BurstWindow(
        entity_id="disputed-pkg",
        start_date="2026-07-01",
        end_date="2026-07-03",
        burst_days=3,
        total_stars=500.0,
        baseline_median=2.0,
        burst_excess=494.0,
        low_quality_share=0.8,
        sample_size=40,
        dispute_status="disputed",
    )

    summary = window.to_summary()
    assert summary["dispute_status"] == "disputed"
    assert summary["is_hidden"] is True
    assert summary["public_flag"] == ""  # Hidden during review


@pytest.mark.unit
def test_compute_adjusted_star_gain() -> None:
    """Section 10.4: s28_adj = s28 - burst_excess * low_quality_share."""
    window1 = BurstWindow(
        entity_id="foo",
        start_date="2026-07-01",
        end_date="2026-07-02",
        burst_days=2,
        total_stars=200.0,
        baseline_median=5.0,
        burst_excess=190.0,
        low_quality_share=0.5,
        sample_size=35,
    )

    raw_s28 = 500.0
    adjusted_s28 = compute_adjusted_star_gain(s28=raw_s28, burst_windows=[window1])

    # 500 - (190 * 0.5) = 500 - 95 = 405.0
    assert adjusted_s28 == 405.0
