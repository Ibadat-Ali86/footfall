"""Star Burst anomaly detection and privacy-preserving audit.

Implements Section 10 of docs/BUILD.md.
FLAGGED FOR HUMAN REVIEW per AGENTS.md rules on editing src/footfall/anomaly/.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True)
class BurstWindow:
    """Represents a merged window of consecutive anomalous star burst days."""

    entity_id: str
    start_date: str
    end_date: str
    burst_days: int
    total_stars: float
    baseline_median: float
    burst_excess: float
    low_quality_share: float = 0.0
    sample_size: int = 0
    has_hn_story: bool = False

    dispute_status: str = "normal"

    def to_summary(self) -> dict[str, Any]:
        """Convert burst window to public trust layer output.

        Enforces Section 10.5 wording rules:
        - Must say 'unusual star activity', never 'fake', 'fraud', or 'bought'.
        - Explanations are templated strings with computed values.
        - Dispute process: maintainers can dispute; flag is hidden while status is 'disputed'.
        """
        is_unusual = self.low_quality_share >= 0.5 and self.sample_size >= 30
        is_hidden = self.dispute_status == "disputed"

        if is_hidden:
            flag_text = ""
        elif is_unusual:
            flag_text = (
                f"unusual star activity: {self.burst_excess:.0f} stars above baseline "
                f"across {self.burst_days} days "
                f"({self.low_quality_share:.1%} low-activity accounts)"
            )
        else:
            flag_text = (
                f"star burst: {self.burst_excess:.0f} stars above baseline "
                f"across {self.burst_days} days"
            )

        explained_by = "hn_story" if self.has_hn_story else None
        confidence = "medium" if self.has_hn_story else ("high" if is_unusual else "low")

        return {
            "entity_id": self.entity_id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "burst_days": self.burst_days,
            "total_stars": self.total_stars,
            "baseline_median": self.baseline_median,
            "burst_excess": self.burst_excess,
            "low_quality_share": self.low_quality_share,
            "sample_size": self.sample_size,
            "is_unusual": is_unusual,
            "explained_by": explained_by,
            "confidence": confidence,
            "dispute_status": self.dispute_status,
            "is_hidden": is_hidden,
            "public_flag": flag_text,
        }


def compute_adjusted_star_gain(s28: float, burst_windows: Sequence[BurstWindow]) -> float:
    """Compute adjusted star gain down-weighting low-quality bursts (Section 10.4).

    Formula: s28_adj = s28 - sum(burst_excess * low_quality_share)
    """
    excess_deduction = sum(w.burst_excess * w.low_quality_share for w in burst_windows)
    return max(0.0, float(s28 - excess_deduction))


def detect_star_bursts(
    entity_id: str,
    dates: Sequence[str],
    daily_gains: Sequence[float],
    n_min: float = 30.0,
    k: float = 8.0,
) -> list[BurstWindow]:
    """Detect anomalous star gain spikes and merge consecutive days into windows.

    Section 10.2:
    - Baseline b is the median of the prior 28 days.
    - m is the MAD scaled to standard deviation (1.4826 * MAD).
    - Day d is a burst day if delta_d >= max(N_min, b + k * m).
    """
    n = len(daily_gains)
    if n < 29:
        return []

    burst_indices: list[int] = []
    gains_arr = np.asarray(daily_gains, dtype=np.float64)

    for i in range(28, n):
        prior_28 = gains_arr[i - 28 : i]
        median_b = float(np.median(prior_28))
        abs_dev = np.abs(prior_28 - median_b)
        mad_m = 1.4826 * float(np.median(abs_dev))

        threshold = max(n_min, median_b + k * mad_m)
        if gains_arr[i] >= threshold:
            burst_indices.append(i)

    if not burst_indices:
        return []

    # Merge consecutive burst days
    windows: list[BurstWindow] = []
    group_start = burst_indices[0]
    prev_idx = burst_indices[0]

    for curr_idx in burst_indices[1:] + [-1]:
        if curr_idx == prev_idx + 1:
            prev_idx = curr_idx
        else:
            # End of consecutive window
            w_indices = list(range(group_start, prev_idx + 1))
            total_s = float(np.sum(gains_arr[w_indices]))
            base_median = float(np.median(gains_arr[group_start - 28 : group_start]))
            excess = max(0.0, total_s - (base_median * len(w_indices)))

            windows.append(
                BurstWindow(
                    entity_id=entity_id,
                    start_date=dates[group_start],
                    end_date=dates[prev_idx],
                    burst_days=len(w_indices),
                    total_stars=total_s,
                    baseline_median=base_median,
                    burst_excess=excess,
                )
            )

            if curr_idx != -1:
                group_start = curr_idx
                prev_idx = curr_idx

    return windows


def evaluate_privacy_preserving_sample(
    raw_stargazers: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Compute low_quality_share in memory and strictly discard all identities.

    Section 10.3:
    - low_quality_share is share with account age < 30 days OR (0 repos and 0 followers).
    - Discard every identity and per-user value immediately.
    """
    if not raw_stargazers:
        return {"low_quality_share": 0.0, "sample_size": 0}

    low_quality_count = 0
    total_count = len(raw_stargazers)

    for acct in raw_stargazers:
        age_days = float(acct.get("account_age_days", 999.0))
        repos = int(acct.get("public_repos", 1))
        followers = int(acct.get("followers", 1))

        if age_days < 30.0 or (repos == 0 and followers == 0):
            low_quality_count += 1

    low_quality_share = round(low_quality_count / total_count, 4)

    # Return ONLY aggregates and sample size
    return {
        "low_quality_share": low_quality_share,
        "sample_size": total_count,
    }
