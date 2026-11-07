"""Footfall Dependents & Ecosystem Adoption Depth Engine (Phase 4 Backlog).

Measures architectural integration depth via downstream package and repository
dependents across PyPI and npm registries.
"""

from __future__ import annotations

from footfall.dependents.collector import DependentsCollector
from footfall.dependents.depth import AdoptionDepthCalculator
from footfall.dependents.models import DependentsRecord

__all__ = [
    "AdoptionDepthCalculator",
    "DependentsCollector",
    "DependentsRecord",
]
