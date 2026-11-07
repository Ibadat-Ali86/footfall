"""Adoption Depth mathematical formulation and tier classification."""

from __future__ import annotations

import math


class AdoptionDepthCalculator:
    """Calculates Adoption Depth Ratio and evaluates architectural commitment."""

    def __init__(
        self,
        deep_threshold: float = 0.35,
        shallow_threshold: float = 0.15,
    ) -> None:
        """Initialize calculator with tier boundary thresholds."""
        self.deep_threshold = deep_threshold
        self.shallow_threshold = shallow_threshold

    def compute_depth_ratio(self, dependents: int, downloads: int) -> float:
        """Calculate the logarithmic ratio of downstream dependents to download volume.

        Formula:
            Depth Ratio = log10(1 + dependents) / max(1.0, log10(1 + downloads))

        Edge Cases:
            - dependents = 0: returns 0.0 (indicates unverified or zero downstream packages)
            - downloads = 0: denominator clamps to 1.0, preventing division by zero
        """
        dep_val = max(0, dependents)
        dl_val = max(0, downloads)

        num = math.log10(1.0 + dep_val)
        denom = max(1.0, math.log10(1.0 + dl_val))

        return round(num / denom, 4)

    def classify_tier(self, depth_ratio: float) -> str:
        """Classify ratio into deep, balanced, or shallow adoption tiers."""
        if depth_ratio >= self.deep_threshold:
            return "deep"
        if depth_ratio >= self.shallow_threshold:
            return "balanced"
        return "shallow"
