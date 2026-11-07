"""Footfall trust and anomaly detection layer.

FLAGGED FOR HUMAN REVIEW per AGENTS.md rules on editing src/footfall/anomaly/.
"""

from __future__ import annotations

from footfall.anomaly.bursts import (
    BurstWindow,
    detect_star_bursts,
    evaluate_privacy_preserving_sample,
)

__all__ = [
    "BurstWindow",
    "detect_star_bursts",
    "evaluate_privacy_preserving_sample",
]
