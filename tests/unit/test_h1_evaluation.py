"""Unit tests for Hypothesis H1 evaluation engine and baselines.

Follows AGENTS.md:
- Tests first
- Offline mathematical validation
- Validates Baselines B0..B3, Walk-forward splits with embargo, and Block Bootstrap
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from footfall.phase.h1_evaluation import (
    BaselinesEvaluator,
    block_bootstrap_origins,
    compute_cross_sectional_spearman,
    generate_walk_forward_splits,
)


@pytest.mark.unit
def test_baselines_evaluator_predictions() -> None:
    """Verify B0..B3 baselines per Section 4.3."""
    evaluator = BaselinesEvaluator()

    # Features: [g4, g12, acc, s28_rel, attention_A, adoption_z, attention_z, D]
    features = np.array(
        [
            [0.25, 0.50, 0.10, 0.15, 2.0, 0.8, 0.5, -0.3],
            [-0.10, -0.05, -0.02, 0.05, 0.0, -0.4, 0.1, 0.5],
        ]
    )

    # B0: No change -> all 0.0
    preds_b0 = evaluator.predict_b0(features)
    assert np.allclose(preds_b0, [0.0, 0.0])

    # B1: Trailing 4-week download growth -> g4 (column 0)
    preds_b1 = evaluator.predict_b1(features)
    assert np.allclose(preds_b1, [0.25, -0.10])

    # B2: Trailing 28-day star growth -> s28_rel (column 3)
    preds_b2 = evaluator.predict_b2(features)
    assert np.allclose(preds_b2, [0.15, 0.05])

    # B3: Fitted linear model on B1 and B2
    evaluator.fit_b3(features, np.array([0.20, -0.08]))
    preds_b3 = evaluator.predict_b3(features)
    assert len(preds_b3) == 2


@pytest.mark.unit
def test_compute_cross_sectional_spearman() -> None:
    """Test Spearman rank correlation between predictions and realized targets."""
    # Perfect rank correlation
    preds = np.array([0.1, 0.2, 0.5, 0.8])
    targets = np.array([1.0, 2.0, 5.0, 8.0])
    rho = compute_cross_sectional_spearman(preds, targets)
    assert math.isclose(rho, 1.0, abs_tol=1e-5)

    # Inverted rank correlation
    inv_targets = np.array([8.0, 5.0, 2.0, 1.0])
    rho_inv = compute_cross_sectional_spearman(preds, inv_targets)
    assert math.isclose(rho_inv, -1.0, abs_tol=1e-5)


@pytest.mark.unit
def test_walk_forward_splits_with_embargo() -> None:
    """Walk-forward splits must strictly respect embargo weeks."""
    total_weeks = 50
    min_train_weeks = 20
    embargo_weeks = 4

    splits = generate_walk_forward_splits(
        total_weeks=total_weeks,
        min_train_weeks=min_train_weeks,
        embargo_weeks=embargo_weeks,
    )

    assert len(splits) > 0
    for train_indices, test_origin in splits:
        # Every train week must be <= test_origin - embargo_weeks
        max_train = max(train_indices)
        assert max_train <= test_origin - embargo_weeks, (
            f"Embargo violation: max_train={max_train}, "
            f"test_origin={test_origin}, embargo={embargo_weeks}"
        )


@pytest.mark.unit
def test_block_bootstrap_origins() -> None:
    """Block bootstrap resamples blocks of origins and computes confidence interval."""
    # Synthetic origin differences: candidate beats baseline by ~0.10
    rng = np.random.default_rng(20261101)
    diffs = rng.normal(loc=0.10, scale=0.03, size=40)

    ci_lower, ci_upper, p_val = block_bootstrap_origins(
        differences=diffs,
        block_size=4,
        n_resamples=500,
        seed=20261101,
    )

    # 95% CI should exclude zero
    assert ci_lower > 0.0
    assert ci_upper > ci_lower
    assert p_val < 0.05
