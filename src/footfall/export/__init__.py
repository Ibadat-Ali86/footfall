"""Static export bundle and badge generation.

Implements Section 12.1 of docs/BUILD.md.
"""

from __future__ import annotations

from footfall.export.builder import (
    PHASE_BADGE_COLORS,
    generate_shields_badge,
    generate_static_export_bundle,
)
from footfall.export.claims import (
    verify_all_claims,
    verify_document_claims,
)

__all__ = [
    "PHASE_BADGE_COLORS",
    "generate_shields_badge",
    "generate_static_export_bundle",
    "verify_all_claims",
    "verify_document_claims",
]
