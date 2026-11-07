"""Anomaly detection and trust layer.

Implements Sections 9.9 and 10 of docs/BUILD.md.
FLAGGED FOR HUMAN REVIEW per AGENTS.md rules on editing src/footfall/anomaly/.
"""

from __future__ import annotations

from footfall.anomaly.bursts import (
    BurstWindow,
    compute_adjusted_star_gain,
    detect_star_bursts,
    evaluate_privacy_preserving_sample,
)
from footfall.anomaly.downloads import (
    DownloadAnomaly,
    detect_download_anomalies,
)

__all__ = [
    "BurstWindow",
    "DownloadAnomaly",
    "compute_adjusted_star_gain",
    "detect_download_anomalies",
    "detect_star_bursts",
    "evaluate_privacy_preserving_sample",
]
