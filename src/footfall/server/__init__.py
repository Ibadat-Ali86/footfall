"""Footfall MCP Server and Serving Layer.

Implements Section 12.2 of docs/BUILD.md.
FLAGGED FOR HUMAN REVIEW per AGENTS.md rules on editing src/footfall/server/.
"""

from __future__ import annotations

from footfall.server.app import (
    SecurityHeadersMiddleware,
    create_mcp_server,
    create_streamable_app,
)
from footfall.server.resolver import (
    EntityResolutionResult,
    EntityResolver,
)
from footfall.server.schemas import (
    CompareInput,
    FindRisingInput,
    TrendInput,
)
from footfall.server.service import (
    FootfallService,
)

__all__ = [
    "CompareInput",
    "EntityResolutionResult",
    "EntityResolver",
    "FindRisingInput",
    "FootfallService",
    "SecurityHeadersMiddleware",
    "TrendInput",
    "create_mcp_server",
    "create_streamable_app",
]
