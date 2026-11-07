"""Footfall phase evaluation and hypothesis validation package."""

from __future__ import annotations

from footfall.phase.classifier import (
    LifecyclePhase,
    PhaseClassifier,
    PhaseInput,
    PhaseResult,
)
from footfall.phase.h1_evaluation import (
    BaselinesEvaluator,
    CandidateModel,
    block_bootstrap_origins,
    compute_cross_sectional_spearman,
    evaluate_top_decile_precision,
    generate_walk_forward_splits,
)

__all__ = [
    "BaselinesEvaluator",
    "CandidateModel",
    "LifecyclePhase",
    "PhaseClassifier",
    "PhaseInput",
    "PhaseResult",
    "block_bootstrap_origins",
    "compute_cross_sectional_spearman",
    "evaluate_top_decile_precision",
    "generate_walk_forward_splits",
]
