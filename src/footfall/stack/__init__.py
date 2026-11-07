"""Footfall Stack Analysis Module.

Audits developer repository manifests (pyproject.toml, requirements.txt, package.json)
for tracked AI tools, evaluating ecosystem lifecycle phases and adoption momentum.
"""

from __future__ import annotations

from footfall.stack.analyzer import StackAnalyzer, StackReport

__all__ = ["StackAnalyzer", "StackReport"]
