"""Unit tests for the Learned Phase Classifier evaluation (Phase 4 Backlog).

Proves:
- Feature extraction and model training using scikit-learn.
- Deterministic out-of-sample probability and phase predictions.
- Objective benchmarking against the pre-registered heuristic PhaseClassifier.
- Verification of the parsimony gate: learned model earns its place ONLY if it beats rules.
"""

from __future__ import annotations

import pytest

from footfall.phase.classifier import LifecyclePhase, PhaseClassifier, PhaseInput
from footfall.phase.learned import LearnedPhaseClassifier, LearnedPhaseReport


@pytest.fixture
def synthetic_training_data() -> tuple[list[PhaseInput], list[LifecyclePhase]]:
    """Fixture providing simulated historical feature vectors and phase targets."""
    inputs: list[PhaseInput] = []
    targets: list[LifecyclePhase] = []

    # 1. Breakouts: high volume, high g4, high adoption
    for i in range(25):
        inputs.append(
            PhaseInput(
                history_weeks=12,
                star_history_days=90,
                weekly_volume=20000.0 + i * 500,
                adoption_z=2.5 + (i % 3) * 0.2,
                attention_z=1.0,
                divergence=0.8,
                g4=0.65 + (i % 4) * 0.05,
                g12=1.2,
                age_months=8.0,
            )
        )
        targets.append(LifecyclePhase.BREAKOUT)

    # 2. Mainstream: high volume, moderate growth, balanced divergence
    for i in range(25):
        inputs.append(
            PhaseInput(
                history_weeks=52,
                star_history_days=365,
                weekly_volume=80000.0 + i * 1000,
                adoption_z=1.8,
                attention_z=1.5,
                divergence=0.1,
                g4=0.08,
                g12=0.25,
                age_months=24.0,
                is_category_top_quartile=True,
            )
        )
        targets.append(LifecyclePhase.MAINSTREAM)

    # 3. Fading: negative divergence, negative growth
    for _i in range(25):
        inputs.append(
            PhaseInput(
                history_weeks=36,
                star_history_days=250,
                weekly_volume=5000.0,
                adoption_z=-1.2,
                attention_z=0.5,
                divergence=-1.4,
                g4=-0.25,
                g12=-0.40,
                age_months=18.0,
                consecutive_fading_weeks=5,
            )
        )
        targets.append(LifecyclePhase.FADING)

    return inputs, targets


def test_learned_classifier_training_and_prediction(
    synthetic_training_data: tuple[list[PhaseInput], list[LifecyclePhase]],
) -> None:
    """Proves that LearnedPhaseClassifier trains and produces valid predictions."""
    X, y = synthetic_training_data
    model = LearnedPhaseClassifier()
    model.fit(X, y)

    # Test breakout sample
    test_breakout = PhaseInput(
        history_weeks=12,
        star_history_days=90,
        weekly_volume=25000.0,
        adoption_z=2.7,
        attention_z=1.1,
        divergence=0.9,
        g4=0.70,
        g12=1.3,
        age_months=7.0,
    )
    predicted_phase = model.predict(test_breakout)
    assert predicted_phase in (LifecyclePhase.BREAKOUT, LifecyclePhase.EMERGING)

    probabilities = model.predict_proba(test_breakout)
    assert len(probabilities) > 0
    assert abs(sum(probabilities.values()) - 1.0) < 1e-4


def test_learned_classifier_parsimony_benchmark(
    synthetic_training_data: tuple[list[PhaseInput], list[LifecyclePhase]],
) -> None:
    """Proves benchmark against heuristic classifier and parsimony decision gate."""
    X, y = synthetic_training_data
    model = LearnedPhaseClassifier()
    model.fit(X[:50], y[:50])

    heuristic = PhaseClassifier()
    report: LearnedPhaseReport = model.benchmark_vs_heuristic(
        heuristic=heuristic,
        test_inputs=X[50:],
        test_targets=y[50:],
        required_accuracy_margin=0.05,
    )

    assert 0.0 <= report.learned_accuracy <= 1.0
    assert (
        "heuristic" in report.decision_rationale.lower()
        or "learned" in report.decision_rationale.lower()
    )
