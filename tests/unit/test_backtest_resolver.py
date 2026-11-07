"""Unit tests for the Backtest Resolver and Report Generator (Section 11.3 & 11.4).

Follows AGENTS.md:
- Tests first
- Proves outcome resolution against realized 4-week growth
- Proves breakout precision and base rate computation with explicit denominators
- Proves Spearman rank correlation against baselines
- Proves category breakdowns and worst misses table
"""

from __future__ import annotations

import pytest

from footfall.ledger.chain import LedgerCall
from footfall.ledger.resolver import (
    BacktestResolver,
    ResolvedCall,
)


@pytest.mark.unit
def test_resolve_calls_computes_forward_growth() -> None:
    """Section 11.3: Compute realized g_fwd_4 = ln((W_t+28 + 1)/(W_t + 1)) and breakout label."""
    # Synthetic weekly downloads table:
    # entity-1: W(2026-06-01) = 1,000, W(2026-06-29) = 1,500
    # g_fwd = ln(1501/1001) ~ 0.405 >= ln(1.25) ~ 0.223 -> True Breakout!
    # entity-2: W(2026-06-01) = 2,000, W(2026-06-29) = 1,800 (g_fwd < 0) -> Not Breakout
    weekly_downloads_map: dict[tuple[str, str], float] = {
        ("entity-1", "2026-06-01"): 1000.0,
        ("entity-1", "2026-06-29"): 1500.0,
        ("entity-2", "2026-06-01"): 2000.0,
        ("entity-2", "2026-06-29"): 1800.0,
        ("entity-3", "2026-06-01"): 500.0,  # missing 4-week outcome
    }

    call1 = LedgerCall(
        call_id="c1",
        entity_id="entity-1",
        category="agent-framework",
        as_of="2026-06-01",
        phase="breakout",
        p_breakout_30d=0.85,
        method_version="m1.0",
        features_hash="h1",
        prev_hash="0" * 64,
        record_hash="r1",
    )

    call2 = LedgerCall(
        call_id="c2",
        entity_id="entity-2",
        category="llm-sdk",
        as_of="2026-06-01",
        phase="breakout",
        p_breakout_30d=0.75,
        method_version="m1.0",
        features_hash="h2",
        prev_hash="r1",
        record_hash="r2",
    )

    call3 = LedgerCall(
        call_id="c3",
        entity_id="entity-3",
        category="vector-store",
        as_of="2026-06-01",
        phase="emerging",
        p_breakout_30d=0.30,
        method_version="m1.0",
        features_hash="h3",
        prev_hash="r2",
        record_hash="r3",
    )

    resolver = BacktestResolver(download_lookup=weekly_downloads_map)
    resolved = resolver.resolve_calls([call1, call2, call3])

    assert len(resolved) == 3
    # Call 1: resolved as true positive
    r1 = resolved[0]
    assert r1.is_resolved is True
    assert r1.realized_g_fwd_4 is not None
    assert r1.realized_g_fwd_4 > 0.4
    assert r1.realized_breakout is True

    # Call 2: resolved as false positive
    r2 = resolved[1]
    assert r2.is_resolved is True
    assert r2.realized_g_fwd_4 is not None
    assert r2.realized_g_fwd_4 < 0.0
    assert r2.realized_breakout is False

    # Call 3: unresolved due to missing 4-week window
    r3 = resolved[2]
    assert r3.is_resolved is False


@pytest.mark.unit
def test_backtest_report_metrics_and_honesty_rules() -> None:
    """Section 11.3 & 11.4: Precision, base rate, Spearman correlation, denominators."""
    resolved_calls = [
        ResolvedCall(
            call_id="c1",
            entity_id="pkg1",
            category="agent-framework",
            as_of="2026-06-01",
            phase="breakout",
            p_breakout_30d=0.9,
            method_version="m1.0",
            realized_g_fwd_4=0.45,
            realized_breakout=True,
            is_resolved=True,
        ),
        ResolvedCall(
            call_id="c2",
            entity_id="pkg2",
            category="agent-framework",
            as_of="2026-06-01",
            phase="breakout",
            p_breakout_30d=0.8,
            method_version="m1.0",
            realized_g_fwd_4=0.05,
            realized_breakout=False,
            is_resolved=True,
        ),
        ResolvedCall(
            call_id="c3",
            entity_id="pkg3",
            category="llm-sdk",
            as_of="2026-06-01",
            phase="plateau",
            p_breakout_30d=0.1,
            method_version="m1.0",
            realized_g_fwd_4=-0.10,
            realized_breakout=False,
            is_resolved=True,
        ),
        ResolvedCall(
            call_id="c4",
            entity_id="pkg4",
            category="llm-sdk",
            as_of="2026-06-01",
            phase="mainstream",
            p_breakout_30d=0.2,
            method_version="m1.0",
            realized_g_fwd_4=0.02,
            realized_breakout=False,
            is_resolved=True,
        ),
        ResolvedCall(
            call_id="c5",
            entity_id="pkg5",
            category="agent-framework",
            as_of="2026-06-01",
            phase="emerging",
            p_breakout_30d=0.4,
            method_version="m1.0",
            realized_g_fwd_4=None,
            realized_breakout=None,
            is_resolved=False,
        ),
    ]

    report = BacktestResolver.generate_report(resolved_calls)

    # 4 resolved out of 5
    assert report["total_calls"] == 5
    assert report["resolved_calls"] == 4
    assert report["coverage"] == 0.8
    assert report["coverage_ratio"] == "4/5 (80.0%)"

    # Breakout calls: 2 calls (pkg1, pkg2). True positive: 1 (pkg1).
    # Precision: 1/2 = 50.0%
    assert report["breakout_precision"] == 0.5
    assert report["breakout_precision_ratio"] == "1/2 (50.0%)"

    # Base rate: 1 breakout among 4 resolved entities = 1/4 = 25.0%
    assert report["base_rate"] == 0.25
    assert report["base_rate_ratio"] == "1/4 (25.0%)"

    # Spearman rank correlation should be positive between p_breakout_30d and realized_g_fwd_4
    assert report["spearman_correlation"] is not None
    assert report["spearman_correlation"] > 0.8

    # Category breakdown must include sample sizes
    assert "agent-framework" in report["by_category"]
    assert report["by_category"]["agent-framework"]["sample_size"] == 2
    assert "llm-sdk" in report["by_category"]
    assert report["by_category"]["llm-sdk"]["sample_size"] == 2

    # Worst misses table
    assert len(report["worst_misses"]) > 0
