"""Comprehensive Feature Engine for Footfall.

Orchestrates adoption, attention, and normalization features.
Strictly guarantees point-in-time calculation to prevent temporal leakage.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from footfall.features.adoption import compute_adoption_metrics
from footfall.features.attention import compute_hn_attention, compute_star_metrics

if TYPE_CHECKING:
    from collections.abc import Sequence


class FeatureEngine:
    """Computes point-in-time features for all tracked entities."""

    def compute_entity_week_features(
        self,
        entity_id: str,
        weekly_downloads: Sequence[float],
        weekly_stars: Sequence[float],
        current_week_idx: int,
        stories: Sequence[dict[str, Any]] | None = None,
    ) -> dict[str, float]:
        """Compute point-in-time features for an entity at current_week_idx.

        Strict leakage prevention:
        - Only data at or before current_week_idx is accessible.
        - Future series points are deliberately truncated.
        """
        if current_week_idx < 0:
            raise ValueError("current_week_idx must be >= 0")

        # Slice strictly up to current week
        dl_history = list(weekly_downloads[: current_week_idx + 1])
        stars_history = list(weekly_stars[: current_week_idx + 1])

        # 1. Adoption metrics
        adoption = compute_adoption_metrics(dl_history, current_idx=len(dl_history) - 1)
        if adoption is None:
            w_val, l_val, g4_val, g12_val, acc_val = 0.0, 0.0, 0.0, 0.0, 0.0
        else:
            w_val = adoption["W"]
            l_val = adoption["L"]
            g4_val = adoption["g4"]
            g12_val = adoption["g12"]
            acc_val = adoption["acc"]

        # 2. Star metrics (4 weeks / 28 days = 4 weekly buckets prior)
        if stars_history:
            stars_t = stars_history[-1]
            stars_prev = stars_history[-5] if len(stars_history) >= 5 else stars_history[0]
            star_metrics = compute_star_metrics(stars_t, stars_prev)
            s28_val = star_metrics["s28"]
            s28_rel_val = star_metrics["s28_rel"]
        else:
            s28_val = 0.0
            s28_rel_val = 0.0

        # 3. Attention metrics
        a_val = compute_hn_attention(stories or [])

        return {
            "W": w_val,
            "L": l_val,
            "g4": g4_val,
            "g12": g12_val,
            "acc": acc_val,
            "s28": s28_val,
            "s28_rel": s28_rel_val,
            "attention_A": a_val,
        }
