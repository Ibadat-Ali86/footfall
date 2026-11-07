"""Footfall feature extraction, normalization, and divergence metrics."""

from __future__ import annotations

from footfall.features.adoption import aggregate_weekly_downloads, compute_adoption_metrics
from footfall.features.attention import compute_hn_attention, compute_star_metrics
from footfall.features.engine import FeatureEngine
from footfall.features.normalize import compute_divergence_index, rank_normalize_features

__all__ = [
    "FeatureEngine",
    "aggregate_weekly_downloads",
    "compute_adoption_metrics",
    "compute_divergence_index",
    "compute_hn_attention",
    "compute_star_metrics",
    "rank_normalize_features",
]
