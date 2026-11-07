"""Adoption feature extraction and weekly download aggregations.

Implements Sections 9.1 and 9.2 of docs/BUILD.md.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from footfall.collectors.base import SnapshotQuality

if TYPE_CHECKING:
    from collections.abc import Sequence

    from footfall.collectors.base import Snapshot


def aggregate_weekly_downloads(snapshots: Sequence[Snapshot]) -> float | None:
    """Aggregate 7 daily values into weekly download sum.

    Section 9.1:
    - Weekly downloads W(e,t) is the sum of 7 daily values.
    - Require at least 6 of 7 days with quality = ok, otherwise week is missing.
    """
    if len(snapshots) < 6:
        return None

    ok_snapshots = [s for s in snapshots if s.quality == SnapshotQuality.OK]
    if len(ok_snapshots) < 6:
        return None

    return sum(s.value for s in ok_snapshots)


def compute_adoption_metrics(
    weekly_downloads: Sequence[float],
    current_idx: int,
) -> dict[str, float] | None:
    """Compute adoption growth features from weekly download series.

    Section 9.2:
    - L = ln(W + 1)
    - g4 = L(t) - L(t-4w)
    - g12 = L(t) - L(t-12w)
    - acc = g4(t) - g4(t-4w)
    """
    if current_idx < 0 or current_idx >= len(weekly_downloads):
        return None

    w_t = max(0.0, weekly_downloads[current_idx])
    l_t = math.log(w_t + 1.0)

    # g4: growth over prior 4 weeks
    if current_idx >= 4:
        w_t_4 = max(0.0, weekly_downloads[current_idx - 4])
        l_t_4 = math.log(w_t_4 + 1.0)
        g4 = l_t - l_t_4
    else:
        g4 = 0.0

    # g12: growth over prior 12 weeks
    if current_idx >= 12:
        w_t_12 = max(0.0, weekly_downloads[current_idx - 12])
        l_t_12 = math.log(w_t_12 + 1.0)
        g12 = l_t - l_t_12
    else:
        g12 = g4  # Fallback to g4 when history < 12 weeks

    # acc: acceleration g4(t) - g4(t-4w)
    if current_idx >= 8:
        w_t_8 = max(0.0, weekly_downloads[current_idx - 8])
        l_t_8 = math.log(w_t_8 + 1.0)
        g4_prev = l_t_4 - l_t_8
        acc = g4 - g4_prev
    else:
        acc = 0.0

    return {
        "W": w_t,
        "L": l_t,
        "g4": g4,
        "g12": g12,
        "acc": acc,
    }
