"""Outcome Resolver and Backtest Evaluation Engine.

Implements Sections 11.3 and 11.4 of docs/BUILD.md.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

import numpy as np
from scipy.stats import spearmanr

if TYPE_CHECKING:
    from collections.abc import Sequence

    from footfall.ledger.chain import LedgerCall


@dataclass(frozen=True)
class ResolvedCall:
    """Represents a ledger call evaluated against realized forward outcomes."""

    call_id: str
    entity_id: str
    category: str
    as_of: str
    phase: str
    p_breakout_30d: float | None
    method_version: str
    realized_g_fwd_4: float | None = None
    realized_breakout: bool | None = None
    is_resolved: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert resolved call to dictionary."""
        return asdict(self)


class BacktestResolver:
    """Evaluates historical calls against realized 4-week and 8-week outcomes."""

    def __init__(
        self,
        download_lookup: dict[tuple[str, str], float] | None = None,
    ) -> None:
        self.download_lookup = download_lookup or {}

    def resolve_calls(
        self,
        calls: Sequence[LedgerCall],
        target_weeks: int = 4,
        growth_threshold: float = 0.22314355,  # ln(1.25)
        volume_min: float = 500.0,
    ) -> list[ResolvedCall]:
        """Resolve forward outcomes for each call after target_weeks (default 4 weeks = 28 days)."""
        resolved: list[ResolvedCall] = []
        delta_days = target_weeks * 7

        for call in calls:
            t0_date = date.fromisoformat(call.as_of)
            tfwd_date = t0_date + timedelta(days=delta_days)
            tfwd_str = tfwd_date.isoformat()

            key_t0 = (call.entity_id, call.as_of)
            key_tfwd = (call.entity_id, tfwd_str)

            if key_t0 in self.download_lookup and key_tfwd in self.download_lookup:
                w_t0 = self.download_lookup[key_t0]
                w_tfwd = self.download_lookup[key_tfwd]

                g_fwd = math.log((w_tfwd + 1.0) / (w_t0 + 1.0))
                is_breakout = bool(g_fwd >= growth_threshold and w_tfwd >= volume_min)

                resolved.append(
                    ResolvedCall(
                        call_id=call.call_id,
                        entity_id=call.entity_id,
                        category=call.category,
                        as_of=call.as_of,
                        phase=call.phase,
                        p_breakout_30d=call.p_breakout_30d,
                        method_version=call.method_version,
                        realized_g_fwd_4=round(g_fwd, 4),
                        realized_breakout=is_breakout,
                        is_resolved=True,
                    )
                )
            else:
                resolved.append(
                    ResolvedCall(
                        call_id=call.call_id,
                        entity_id=call.entity_id,
                        category=call.category,
                        as_of=call.as_of,
                        phase=call.phase,
                        p_breakout_30d=call.p_breakout_30d,
                        method_version=call.method_version,
                        realized_g_fwd_4=None,
                        realized_breakout=None,
                        is_resolved=False,
                    )
                )

        return resolved

    @staticmethod
    def generate_report(resolved_calls: Sequence[ResolvedCall]) -> dict[str, Any]:
        """Generate comprehensive backtest report complying with honesty rules (Section 11.4)."""
        total = len(resolved_calls)
        resolved = [c for c in resolved_calls if c.is_resolved]
        n_resolved = len(resolved)

        cov_val = round(n_resolved / total, 4) if total > 0 else 0.0
        cov_str = f"{n_resolved}/{total} ({cov_val:.1%})"

        if n_resolved == 0:
            return {
                "total_calls": total,
                "resolved_calls": 0,
                "coverage": 0.0,
                "coverage_ratio": cov_str,
                "breakout_precision": 0.0,
                "breakout_precision_ratio": "0/0 (0.0%)",
                "base_rate": 0.0,
                "base_rate_ratio": "0/0 (0.0%)",
                "spearman_correlation": None,
                "by_category": {},
                "worst_misses": [],
            }

        # 1. Breakout precision
        breakout_calls = [c for c in resolved if c.phase == "breakout"]
        n_breakout_calls = len(breakout_calls)
        tp_count = sum(1 for c in breakout_calls if c.realized_breakout is True)

        prec_val = round(tp_count / n_breakout_calls, 4) if n_breakout_calls > 0 else 0.0
        prec_str = f"{tp_count}/{n_breakout_calls} ({prec_val:.1%})"

        # 2. Base rate across all resolved calls
        total_breakouts = sum(1 for c in resolved if c.realized_breakout is True)
        base_val = round(total_breakouts / n_resolved, 4)
        base_str = f"{total_breakouts}/{n_resolved} ({base_val:.1%})"

        # 3. Spearman correlation between predictions and realized growth
        preds = []
        actuals = []
        for c in resolved:
            if c.p_breakout_30d is not None and c.realized_g_fwd_4 is not None:
                preds.append(c.p_breakout_30d)
                actuals.append(c.realized_g_fwd_4)

        spearman_corr: float | None = None
        if len(preds) >= 3:
            corr_val, _ = spearmanr(preds, actuals)
            spearman_corr = round(float(corr_val), 4) if not np.isnan(corr_val) else 0.0

        # 4. Results by category with explicit sample sizes
        by_category: dict[str, dict[str, Any]] = {}
        for c in resolved:
            cat = c.category
            if cat not in by_category:
                by_category[cat] = {
                    "sample_size": 0,
                    "breakouts": 0,
                    "breakout_calls": 0,
                    "true_positives": 0,
                }
            by_category[cat]["sample_size"] += 1
            if c.realized_breakout:
                by_category[cat]["breakouts"] += 1
            if c.phase == "breakout":
                by_category[cat]["breakout_calls"] += 1
                if c.realized_breakout:
                    by_category[cat]["true_positives"] += 1

        for _cat, stats in by_category.items():
            n_cat = stats["sample_size"]
            stats["base_rate"] = f"{stats['breakouts']}/{n_cat} ({stats['breakouts'] / n_cat:.1%})"
            b_calls = stats["breakout_calls"]
            tp = stats["true_positives"]
            stats["precision"] = (
                f"{tp}/{b_calls} ({tp / b_calls:.1%})" if b_calls > 0 else "0/0 (N/A)"
            )

        # 5. Worst misses: largest difference between predicted prob and realized outcome
        misses: list[dict[str, Any]] = []
        for c in resolved:
            if c.p_breakout_30d is not None and c.realized_breakout is not None:
                actual_binary = 1.0 if c.realized_breakout else 0.0
                error = abs(c.p_breakout_30d - actual_binary)
                misses.append(
                    {
                        "call_id": c.call_id,
                        "entity_id": c.entity_id,
                        "category": c.category,
                        "as_of": c.as_of,
                        "phase": c.phase,
                        "predicted_p": c.p_breakout_30d,
                        "realized_growth": c.realized_g_fwd_4,
                        "realized_breakout": c.realized_breakout,
                        "error": round(error, 4),
                    }
                )

        misses.sort(key=lambda x: float(x["error"]), reverse=True)
        worst_misses = misses[:5]

        return {
            "total_calls": total,
            "resolved_calls": n_resolved,
            "coverage": cov_val,
            "coverage_ratio": cov_str,
            "breakout_precision": prec_val,
            "breakout_precision_ratio": prec_str,
            "base_rate": base_val,
            "base_rate_ratio": base_str,
            "spearman_correlation": spearman_corr,
            "by_category": by_category,
            "worst_misses": worst_misses,
        }
