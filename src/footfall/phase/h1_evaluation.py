"""Hypothesis H1 Evaluation Engine.

Implements Sections 4.3 and 9 of docs/BUILD.md:
- Baselines B0..B3
- Candidate Ridge / Gradient Boosting models
- Walk-forward expanding window evaluation with 4-week embargo
- Cross-sectional Spearman rank correlation
- Top-decile breakout precision
- Block bootstrap confidence intervals over weekly origins
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression, Ridge

if TYPE_CHECKING:
    from collections.abc import Sequence


class BaselinesEvaluator:
    """Implements pre-registered reference baselines B0, B1, B2, B3."""

    def __init__(self) -> None:
        self.b3_model: LinearRegression | None = None

    def predict_b0(self, features: np.ndarray) -> np.ndarray:
        """B0: No change baseline (g_fwd = 0.0)."""
        return np.zeros(len(features), dtype=np.float64)

    def predict_b1(self, features: np.ndarray) -> np.ndarray:
        """B1: Trailing 4-week download growth (column 0: g4)."""
        return features[:, 0].astype(np.float64)

    def predict_b2(self, features: np.ndarray) -> np.ndarray:
        """B2: Trailing 28-day relative star growth (column 3: s28_rel)."""
        return features[:, 3].astype(np.float64)

    def fit_b3(self, features: np.ndarray, targets: np.ndarray) -> None:
        """B3: Linear combination of B1 (g4) and B2 (s28_rel)."""
        x_b3 = features[:, [0, 3]]
        self.b3_model = LinearRegression().fit(x_b3, targets)

    def predict_b3(self, features: np.ndarray) -> np.ndarray:
        """Predict using fitted B3 linear regression."""
        if self.b3_model is None:
            # Fallback to simple mean of B1 and B2 if not yet fitted
            res_fb: np.ndarray = 0.5 * (self.predict_b1(features) + self.predict_b2(features))
            return res_fb
        x_b3 = features[:, [0, 3]]
        raw_pred = self.b3_model.predict(x_b3)
        res_arr: np.ndarray = np.asarray(raw_pred, dtype=np.float64)
        return res_arr


def compute_cross_sectional_spearman(
    preds: np.ndarray,
    targets: np.ndarray,
) -> float:
    """Compute Spearman rank correlation across entities for a single time origin.

    Robust to zero-variance edge cases.
    """
    if len(preds) < 3 or len(targets) < 3:
        return 0.0

    # If all predictions or targets are constant, correlation is undefined -> 0.0
    if np.all(preds == preds[0]) or np.all(targets == targets[0]):
        return 0.0

    res = stats.spearmanr(preds, targets)
    corr = float(getattr(res, "statistic", res[0]))
    if math.isnan(corr):
        return 0.0
    return corr


def generate_walk_forward_splits(
    total_weeks: int,
    min_train_weeks: int = 26,
    embargo_weeks: int = 4,
) -> list[tuple[list[int], int]]:
    """Generate walk-forward expanding window splits with strict temporal embargo.

    Section 4.3:
    - Weekly origins.
    - Features may use data up to and including t only.
    - 4-week embargo between train and test.
    """
    splits: list[tuple[list[int], int]] = []
    first_test_origin = min_train_weeks + embargo_weeks

    for test_origin in range(first_test_origin, total_weeks):
        train_max = test_origin - embargo_weeks
        train_indices = list(range(0, train_max + 1))
        splits.append((train_indices, test_origin))

    return splits


def block_bootstrap_origins(
    differences: np.ndarray | Sequence[float],
    block_size: int = 4,
    n_resamples: int = 1000,
    seed: int = 20261101,
) -> tuple[float, float, float]:
    """Moving block bootstrap over weekly origins to evaluate hypothesis confidence intervals.

    Returns:
        tuple[float, float, float]: (ci_lower_2_5, ci_upper_97_5, p_value)
    """
    diff_arr = np.asarray(differences, dtype=np.float64)
    n = len(diff_arr)
    if n == 0:
        return (0.0, 0.0, 1.0)
    if n < block_size:
        block_size = max(1, n)

    rng = np.random.default_rng(seed)
    num_blocks = math.ceil(n / block_size)

    # Valid block starting indices
    max_start = n - block_size + 1
    bootstrap_means: list[float] = []

    for _ in range(n_resamples):
        starts = rng.integers(0, max_start, size=num_blocks)
        sample = np.concatenate([diff_arr[s : s + block_size] for s in starts])[:n]
        bootstrap_means.append(float(np.mean(sample)))

    boot_arr = np.array(bootstrap_means)
    ci_lower = float(np.percentile(boot_arr, 2.5))
    ci_upper = float(np.percentile(boot_arr, 97.5))

    # Empirical two-sided p-value against null hypothesis mean <= 0
    p_value = float(np.mean(boot_arr <= 0.0))

    return (round(ci_lower, 4), round(ci_upper, 4), round(p_value, 4))


class CandidateModel:
    """Pre-registered regularized candidate model (Ridge / Gradient Boosting)."""

    def __init__(self, alpha: float = 1.0) -> None:
        self.model = Ridge(alpha=alpha)

    def fit(self, features: np.ndarray, targets: np.ndarray) -> None:
        """Fit candidate model on training origin features."""
        self.model.fit(features, targets)

    def predict(self, features: np.ndarray) -> np.ndarray:
        """Generate predictions for target origin."""
        raw_pred = self.model.predict(features)
        res_arr: np.ndarray = np.asarray(raw_pred, dtype=np.float64)
        return res_arr


def evaluate_top_decile_precision(
    preds: np.ndarray,
    actual_growth: np.ndarray,
    weekly_volumes: np.ndarray,
    growth_threshold: float = 0.2231,  # ln(1.25)
    volume_floor: float = 500.0,
) -> float:
    """Compute top-decile breakout precision.

    Section 4.3:
    Breakout defined as: realized growth >= threshold and volume >= floor.
    """
    n = len(preds)
    if n < 10:
        return 0.0

    k = max(1, int(round(0.10 * n)))
    top_indices = np.argsort(preds)[-k:]

    is_breakout = (actual_growth >= growth_threshold) & (weekly_volumes >= volume_floor)
    true_positives = np.sum(is_breakout[top_indices])
    return float(true_positives / k)
