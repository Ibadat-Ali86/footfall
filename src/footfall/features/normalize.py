"""Cross-sectional normalization and divergence index calculation.

Implements Sections 9.5 and 9.6 of docs/BUILD.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scipy.special import ndtri

if TYPE_CHECKING:
    from collections.abc import Sequence


def rank_normalize_features(values: Sequence[float]) -> list[float]:
    """Map arbitrary feature values to standard normal z(.) scores via empirical CDF probit.

    Section 9.5:
    - Rank-normalize each feature and map to standard normal score z(.).
    - Preserves monotonic ranking without being distorted by outlier tails.
    """
    n = len(values)
    if n == 0:
        return []
    if n == 1:
        return [0.0]

    # Assign average ranks for ties
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * n

    i = 0
    while i < n:
        j = i
        while j < n - 1 and indexed[j + 1][1] == indexed[j][1]:
            j += 1
        avg_rank = (i + j + 2) / 2.0  # 1-based rank average
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg_rank
        i = j + 1

    # Map rank to percentile in (0, 1), then probit / ndtri
    z_scores: list[float] = []
    for r in ranks:
        p = (r - 0.5) / n
        # Bound p away from exact 0 or 1 to prevent +/- inf
        p = min(max(p, 1e-4), 1.0 - 1e-4)
        z = float(ndtri(p))
        z_scores.append(round(z, 5))

    return z_scores


def compute_divergence_index(
    attention_z: float,
    adoption_z: float,
) -> dict[str, Any]:
    """Compute the Divergence Index between attention and actual adoption.

    Section 9.6:
    - D = attention_z - adoption_z
    - D >= +1.0: attention is ahead of use
    - D <= -1.0: use is ahead of attention
    """
    d = round(attention_z - adoption_z, 4)
    return {
        "D": d,
        "attention_z": attention_z,
        "adoption_z": adoption_z,
        "is_attention_ahead": d >= 1.0,
        "is_use_ahead": d <= -1.0,
    }
