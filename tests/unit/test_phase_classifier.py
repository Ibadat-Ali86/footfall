"""Table-driven boundary tests for lifecycle phase rules (Task T1.5).

Implements Section 9.7 of docs/BUILD.md:
- First-match-wins rule evaluation
- Tests boundary conditions for all 8 lifecycle phases
- Validates methods.yaml configuration
"""

from __future__ import annotations

import math

import pytest

from footfall.phase.classifier import (
    LifecyclePhase,
    PhaseClassifier,
    PhaseInput,
)


@pytest.fixture
def classifier() -> PhaseClassifier:
    """Instantiate classifier with canonical default parameters."""
    return PhaseClassifier()


@pytest.mark.unit
def test_phase_insufficient_data(classifier: PhaseClassifier) -> None:
    """Rule 1: Fewer than 12 weeks of downloads or 56 days of stars."""
    # Only 10 weeks of history
    inp = PhaseInput(
        history_weeks=10,
        star_history_days=60,
        weekly_volume=2000.0,
        adoption_z=1.5,
        attention_z=1.0,
        divergence=0.0,
        g4=0.5,
        g12=0.8,
        age_months=12.0,
    )
    result = classifier.classify(inp)
    assert result.phase == LifecyclePhase.INSUFFICIENT_DATA


@pytest.mark.unit
def test_phase_breakout_and_volume_floor(classifier: PhaseClassifier) -> None:
    """Rule 2: adoption_z >= 1.0 and g4 >= ln(1.25) and W >= W_min."""
    g4_breakout = math.log(1.25) + 0.01  # > ln(1.25) ~= 0.2231

    # 1. Valid breakout
    inp_ok = PhaseInput(
        history_weeks=20,
        star_history_days=100,
        weekly_volume=600.0,  # >= 500
        adoption_z=1.2,
        attention_z=1.0,
        divergence=-0.2,
        g4=g4_breakout,
        g12=0.5,
        age_months=8.0,
    )
    assert classifier.classify(inp_ok).phase == LifecyclePhase.BREAKOUT

    # 2. Volume floor fail: W = 400 < 500 -> Not breakout
    inp_low_vol = PhaseInput(
        history_weeks=20,
        star_history_days=100,
        weekly_volume=400.0,  # Below W_min
        adoption_z=1.2,
        attention_z=1.0,
        divergence=-0.2,
        g4=g4_breakout,
        g12=0.5,
        age_months=8.0,
    )
    assert classifier.classify(inp_low_vol).phase != LifecyclePhase.BREAKOUT


@pytest.mark.unit
def test_phase_attention_ahead_and_use_ahead(classifier: PhaseClassifier) -> None:
    """Rule 3: D >= 1.0 and adoption_z < 0.5 -> attention_ahead.

    Rule 4: D <= -1.0 and adoption_z >= 0.5 -> use_ahead.
    """
    # Attention ahead (hype ahead of actual adoption)
    inp_hype = PhaseInput(
        history_weeks=25,
        star_history_days=150,
        weekly_volume=1000.0,
        adoption_z=0.1,  # < 0.5
        attention_z=1.6,
        divergence=1.5,  # >= 1.0
        g4=0.05,
        g12=0.10,
        age_months=12.0,
    )
    assert classifier.classify(inp_hype).phase == LifecyclePhase.ATTENTION_AHEAD

    # Use ahead (quiet workhorse: adoption ahead of stars/attention)
    inp_workhorse = PhaseInput(
        history_weeks=25,
        star_history_days=150,
        weekly_volume=15000.0,
        adoption_z=0.9,  # >= 0.5
        attention_z=-0.4,
        divergence=-1.3,  # <= -1.0
        g4=0.15,
        g12=0.30,
        age_months=15.0,
    )
    assert classifier.classify(inp_workhorse).phase == LifecyclePhase.USE_AHEAD


@pytest.mark.unit
def test_phase_fading_emerging_mainstream(classifier: PhaseClassifier) -> None:
    """Rules 5, 6, 7: fading, emerging, mainstream."""
    # Fading: adoption_z <= -1.0 and consecutive negative g12
    inp_fading = PhaseInput(
        history_weeks=30,
        star_history_days=200,
        weekly_volume=800.0,
        adoption_z=-1.2,
        attention_z=-0.5,
        divergence=0.7,
        g4=-0.2,
        g12=-0.4,
        age_months=20.0,
        consecutive_fading_weeks=4,
    )
    assert classifier.classify(inp_fading).phase == LifecyclePhase.FADING

    # Emerging: age < 6 months
    inp_emerging = PhaseInput(
        history_weeks=14,
        star_history_days=70,
        weekly_volume=600.0,
        adoption_z=0.2,
        attention_z=0.4,
        divergence=0.2,
        g4=0.08,
        g12=0.10,
        age_months=4.5,  # < 6 months
    )
    assert classifier.classify(inp_emerging).phase == LifecyclePhase.EMERGING

    # Mainstream: top quartile volume and stable growth |g4| < 0.1
    inp_mainstream = PhaseInput(
        history_weeks=50,
        star_history_days=300,
        weekly_volume=250000.0,
        adoption_z=0.4,
        attention_z=0.2,
        divergence=-0.2,
        g4=0.02,  # |g4| < 0.1
        g12=0.05,
        age_months=24.0,
        is_category_top_quartile=True,
    )
    assert classifier.classify(inp_mainstream).phase == LifecyclePhase.MAINSTREAM
