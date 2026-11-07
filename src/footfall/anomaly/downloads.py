"""Download anomaly detection and trust layer.

Implements Section 9.9 of docs/BUILD.md.
FLAGGED FOR HUMAN REVIEW per AGENTS.md rules on editing src/footfall/anomaly/.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True)
class DownloadAnomaly:
    """Represents an anomalous step or jump in weekly download volumes."""

    entity_id: str
    week_date: str
    weekly_downloads: float
    delta_L: float
    robust_z: float
    flag_type: str = "download_step"
    caveat: str = "possible CI, mirror or bot traffic"
    dispute_status: str = "normal"

    def to_summary(self) -> dict[str, Any]:
        """Convert download anomaly to public output."""
        is_hidden = self.dispute_status == "disputed"
        flag_text = (
            f"download step: weekly jump delta_L={self.delta_L:.2f} "
            f"(z={self.robust_z:.1f}) - {self.caveat}"
            if not is_hidden
            else ""
        )
        return {
            "entity_id": self.entity_id,
            "week_date": self.week_date,
            "weekly_downloads": self.weekly_downloads,
            "delta_L": self.delta_L,
            "robust_z": self.robust_z,
            "flag_type": self.flag_type,
            "caveat": self.caveat,
            "dispute_status": self.dispute_status,
            "is_hidden": is_hidden,
            "public_flag": flag_text,
        }


def detect_download_anomalies(
    entity_id: str,
    week_dates: Sequence[str],
    weekly_downloads: Sequence[float],
    star_activity_dates: Sequence[str] = (),
    hn_story_dates: Sequence[str] = (),
    z_threshold: float = 4.0,
    rolling_weeks: int = 26,
) -> list[DownloadAnomaly]:
    """Detect anomalous download jumps using robust z-scores over rolling window (Section 9.9).

    Specification:
    - Compute robust z-score of weekly L differences using median and MAD over 26 weeks.
    - L = ln(W + 1).
    - If abs(z) >= 4 with no matching star or Hacker News activity within 2 weeks (+/- 14 days),
      record 'download_step' and add caveat 'possible CI, mirror or bot traffic'.
    - Never call it fraud.
    """
    n = len(weekly_downloads)
    if n < rolling_weeks + 1 or len(week_dates) != n:
        return []

    # Compute L = ln(W + 1)
    downloads_arr = np.asarray(weekly_downloads, dtype=np.float64)
    L = np.log(np.maximum(0.0, downloads_arr) + 1.0)
    delta_L = np.diff(L)  # length n - 1

    # Parse external dates for matching
    star_dates = [date.fromisoformat(d) for d in star_activity_dates]
    hn_dates = [date.fromisoformat(d) for d in hn_story_dates]

    anomalies: list[DownloadAnomaly] = []

    # Rolling evaluation: index i in delta_L corresponds to week_dates[i + 1]
    for i in range(rolling_weeks, len(delta_L)):
        prior_window = delta_L[i - rolling_weeks : i]
        median_m = float(np.median(prior_window))
        mad = float(np.median(np.abs(prior_window - median_m)))
        scaled_mad = 1.4826 * mad

        current_delta = float(delta_L[i])
        diff = current_delta - median_m

        robust_z = (10.0 if abs(diff) > 0.5 else 0.0) if scaled_mad < 1e-6 else diff / scaled_mad

        if abs(robust_z) >= z_threshold:
            curr_week_date = date.fromisoformat(week_dates[i + 1])

            # Check if matching star activity within 14 days
            has_star = any(abs((curr_week_date - d).days) <= 14 for d in star_dates)
            has_hn = any(abs((curr_week_date - d).days) <= 14 for d in hn_dates)

            if not (has_star or has_hn):
                anomalies.append(
                    DownloadAnomaly(
                        entity_id=entity_id,
                        week_date=week_dates[i + 1],
                        weekly_downloads=float(downloads_arr[i + 1]),
                        delta_L=round(current_delta, 4),
                        robust_z=round(robust_z, 4),
                    )
                )

    return anomalies
