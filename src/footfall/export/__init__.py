"""Static export bundle and badge generation.

Implements Section 12.1 of docs/BUILD.md.
"""

from __future__ import annotations

from footfall.export.builder import (
    PHASE_BADGE_COLORS,
    generate_shields_badge,
    generate_static_export_bundle,
)

__all__ = [
    "PHASE_BADGE_COLORS",
    "generate_shields_badge",
    "generate_static_export_bundle",
]
