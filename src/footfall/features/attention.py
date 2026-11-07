"""Attention feature extraction (GitHub stars and Hacker News buzz).

Implements Sections 9.3 and 9.4 of docs/BUILD.md.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence


def compute_star_metrics(
    stars_t: float,
    stars_prev: float,
    stars_adj: float | None = None,
) -> dict[str, float]:
    """Compute 28-day absolute and relative star gains.

    Section 9.3:
    - s28 = stars(t) - stars(t-28d)
    - s28_rel = s28 / (stars(t-28d) + 50)
    - s28_adj and s28_adj_rel after anomaly adjustment
    """
    s28 = max(0.0, stars_t - stars_prev)
    s28_rel = s28 / (max(0.0, stars_prev) + 50.0)

    if stars_adj is not None:
        s28_adj = max(0.0, stars_adj - stars_prev)
        s28_adj_rel = s28_adj / (max(0.0, stars_prev) + 50.0)
    else:
        s28_adj = s28
        s28_adj_rel = s28_rel

    return {
        "s28": s28,
        "s28_rel": s28_rel,
        "s28_adj": s28_adj,
        "s28_adj_rel": s28_adj_rel,
    }


def compute_hn_attention(stories: Sequence[dict[str, Any]]) -> float:
    """Compute Hacker News exponential attention index.

    Section 9.4:
    - Only Hacker News stories linking to the entity's repo.
    - Day offsets d_k (0 to 27) and points p_k:
      A(t) = sum_k 0.5^(d_k / 14) * (1 + ln(1 + p_k))
    - Half-life 14 days. Zero if no stories.
    """
    total_a = 0.0
    for story in stories:
        offset_days = float(story.get("offset_days", 0))
        if 0.0 <= offset_days <= 27.0:
            points = max(0.0, float(story.get("points", 0)))
            weight = math.pow(0.5, offset_days / 14.0)
            score = 1.0 + math.log(1.0 + points)
            total_a += weight * score

    return total_a
