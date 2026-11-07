"""Learned Phase Classifier and Benchmark Evaluator.

Implements Section 5.2 and Section 20 Phase 4 Backlog:
- Machine learning alternative to rule-based heuristic classification
- Trains L2-regularized logistic model over standardized feature inputs
- Benchmarks out-of-sample accuracy directly against the heuristic PhaseClassifier
- Strictly enforces parsimony gate: learned model earns its place ONLY if it
  beats the heuristic baseline by a pre-registered margin.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from footfall.phase.classifier import LifecyclePhase, PhaseInput

if TYPE_CHECKING:
    from footfall.phase.classifier import PhaseClassifier


@dataclass(frozen=True)
class LearnedPhaseReport:
    """Consolidated performance evaluation and parsimony decision report."""

    learned_accuracy: float
    heuristic_accuracy: float
    margin: float
    earns_place_in_backtest: bool
    decision_rationale: str


class LearnedPhaseClassifier:
    """Trained statistical model for lifecycle phase classification."""

    FEATURE_NAMES: list[str] = [
        "adoption_z",
        "attention_z",
        "divergence",
        "g4",
        "g12",
        "age_months",
        "weekly_volume",
        "history_weeks",
    ]

    def __init__(self, c_reg: float = 1.0, random_state: int = 42) -> None:
        """Initialize classifier with regularization parameter and random seed."""
        self.c_reg = c_reg
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.model = LogisticRegression(
            C=self.c_reg,
            max_iter=1000,
            random_state=self.random_state,
        )
        self.classes_: list[LifecyclePhase] = []
        self._is_fitted: bool = False

    def _extract_features(self, inp: PhaseInput) -> list[float]:
        """Convert a PhaseInput instance into a numerical feature vector."""
        return [
            float(inp.adoption_z),
            float(inp.attention_z),
            float(inp.divergence),
            float(inp.g4),
            float(inp.g12),
            float(inp.age_months),
            float(inp.weekly_volume),
            float(inp.history_weeks),
        ]

    def fit(self, inputs: list[PhaseInput], targets: list[LifecyclePhase]) -> None:
        """Standardize feature matrix and fit logistic regression model."""
        if not inputs or not targets:
            raise ValueError("Training inputs and targets cannot be empty.")

        X = np.array([self._extract_features(inp) for inp in inputs])
        y = np.array([t.value for t in targets])

        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.classes_ = [LifecyclePhase(c) for c in self.model.classes_]
        self._is_fitted = True

    def predict(self, inp: PhaseInput) -> LifecyclePhase:
        """Predict the most likely lifecycle phase for a single tool input."""
        if not self._is_fitted:
            raise RuntimeError("Classifier must be fitted before calling predict.")

        X = np.array([self._extract_features(inp)])
        X_scaled = self.scaler.transform(X)
        pred_val = self.model.predict(X_scaled)[0]
        return LifecyclePhase(pred_val)

    def predict_proba(self, inp: PhaseInput) -> dict[LifecyclePhase, float]:
        """Return probability distribution over all known lifecycle phases."""
        if not self._is_fitted:
            raise RuntimeError("Classifier must be fitted before calling predict_proba.")

        X = np.array([self._extract_features(inp)])
        X_scaled = self.scaler.transform(X)
        probs = self.model.predict_proba(X_scaled)[0]

        return {cls: round(float(prob), 4) for cls, prob in zip(self.classes_, probs, strict=False)}

    def benchmark_vs_heuristic(
        self,
        heuristic: PhaseClassifier,
        test_inputs: list[PhaseInput],
        test_targets: list[LifecyclePhase],
        required_accuracy_margin: float = 0.05,
    ) -> LearnedPhaseReport:
        """Directly benchmark out-of-sample accuracy against the heuristic rule classifier."""
        if not test_inputs or not test_targets:
            raise ValueError("Test set cannot be empty.")

        learned_correct = 0
        heuristic_correct = 0
        total = len(test_inputs)

        for inp, target in zip(test_inputs, test_targets, strict=True):
            learned_pred = self.predict(inp)
            heuristic_result = heuristic.classify(inp)

            if learned_pred == target:
                learned_correct += 1
            if heuristic_result.phase == target:
                heuristic_correct += 1

        learned_acc = round(learned_correct / total, 4)
        heuristic_acc = round(heuristic_correct / total, 4)
        margin = round(learned_acc - heuristic_acc, 4)

        earns_place = margin >= required_accuracy_margin

        if earns_place:
            rationale = (
                f"Learned model achieved {learned_acc:.1%} accuracy vs {heuristic_acc:.1%} "
                f"for heuristic rules (+{margin:.1%}), exceeding required margin of "
                f"+{required_accuracy_margin:.1%}. Earns place in methods v2.0."
            )
        else:
            rationale = (
                f"Learned model margin (+{margin:.1%}) failed to exceed the required "
                f"+{required_accuracy_margin:.1%} threshold over heuristic rules "
                f"({heuristic_acc:.1%}). "
                "Parsimony principle mandates retaining the transparent rule-based model."
            )

        return LearnedPhaseReport(
            learned_accuracy=learned_acc,
            heuristic_accuracy=heuristic_acc,
            margin=margin,
            earns_place_in_backtest=earns_place,
            decision_rationale=rationale,
        )
