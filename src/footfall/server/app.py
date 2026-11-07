"""Footfall MCP Server and Streamable HTTP Application.

Implements Section 12.2 of docs/BUILD.md.
FLAGGED FOR HUMAN REVIEW per AGENTS.md rules on editing src/footfall/server/.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Literal

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from footfall.server.service import FootfallService

if TYPE_CHECKING:
    from pathlib import Path

    from starlette.applications import Starlette
    from starlette.middleware.base import RequestResponseEndpoint
    from starlette.requests import Request
    from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces Section 12.2 and 13.1 limits and DNS rebinding protections.

    - Validates Origin header on requests to prevent DNS rebinding.
    - Rejects wildcard / unauthorized origins.
    - Sets strict security headers (no-sniff, frame-options).
    """

    def __init__(self, app: ASGIApp, allowed_origins: tuple[str, ...] | None = None) -> None:
        super().__init__(app)
        self.allowed_origins = allowed_origins or ("localhost", "127.0.0.1")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        origin = request.headers.get("origin")
        if origin:
            # Check host portion of Origin
            origin_clean = origin.split("://")[-1].split(":")[0].lower()
            if origin_clean not in self.allowed_origins:
                return JSONResponse(
                    {"error": "forbidden", "message": "Origin not permitted."},
                    status_code=403,
                )

        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'none'"
        return response


def create_mcp_server(
    exports_dir: Path | str = "exports/v1",
    registry_yaml: Path | str = "registry/seed.yaml",
) -> MCPServer:
    """Create and configure the production Footfall MCP Server (Section 12.2)."""
    server = MCPServer(
        name="footfall",
        version="v1.0.0",
        description="Footfall AI Developer Tool Adoption Index MCP Server.",
    )

    service = FootfallService.create_from_exports(
        exports_dir=exports_dir,
        registry_yaml=registry_yaml,
    )

    # Tool 1: footfall_compare
    @server.tool(
        name="footfall_compare",
        title="Compare AI Developer Tools",
        description=(
            "Compares real adoption and attention metrics for 2 to 6 AI developer tools "
            "side by side using package download volume and repository activity. "
            "Results are empirical measurements, not advice."
        ),
        annotations=ToolAnnotations(
            title="Compare AI Developer Tools",
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        ),
    )
    async def footfall_compare(
        entities: list[str],
        window_weeks: int = 12,
    ) -> str:
        """Compare 2 to 6 tools side by side."""
        if len(entities) < 2 or len(entities) > 6:
            return json.dumps(
                {
                    "code": "invalid_input",
                    "message": "Comparison requires between 2 and 6 entity identifiers.",
                    "candidates": [],
                }
            )
        result = service.compare(entities=entities, window_weeks=window_weeks)
        return json.dumps(result, indent=2)

    # Tool 2: footfall_trend
    @server.tool(
        name="footfall_trend",
        title="Weekly Trend for AI Developer Tool",
        description=(
            "Returns historical weekly adoption and attention time series for a specified "
            "AI developer tool. Results are empirical measurements, not advice."
        ),
        annotations=ToolAnnotations(
            title="Weekly Trend for AI Developer Tool",
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        ),
    )
    async def footfall_trend(
        entity: str,
        metrics: list[str] | None = None,
        window_weeks: int = 26,
    ) -> str:
        """Weekly time series for one tool."""
        result = service.trend(
            entity=entity,
            metrics=metrics,
            window_weeks=window_weeks,
        )
        return json.dumps(result, indent=2)

    # Tool 3: footfall_find_rising
    @server.tool(
        name="footfall_find_rising",
        title="Find Rising AI Developer Tools",
        description=(
            "Lists AI developer tools matching a lifecycle phase such as breakout or "
            "use_ahead, ranked by adoption acceleration. Empirical measurements, not advice."
        ),
        annotations=ToolAnnotations(
            title="Find Rising AI Developer Tools",
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        ),
    )
    async def footfall_find_rising(
        category: str = "any",
        phase: Literal[
            "insufficient_data",
            "breakout",
            "attention_ahead",
            "use_ahead",
            "fading",
            "emerging",
            "mainstream",
            "plateau",
        ] = "breakout",
        limit: int = 10,
        min_weekly_downloads: float = 500.0,
    ) -> str:
        """List tools in a lifecycle phase."""
        result = service.find_rising(
            category=category,
            phase=phase,
            limit=limit,
            min_weekly_downloads=min_weekly_downloads,
        )
        return json.dumps(result, indent=2)

    return server


def create_streamable_app(
    exports_dir: Path | str = "exports/v1",
    registry_yaml: Path | str = "registry/seed.yaml",
) -> Starlette:
    """Create hardened Starlette streamable HTTP application at /mcp."""
    server = create_mcp_server(exports_dir=exports_dir, registry_yaml=registry_yaml)
    app = server.streamable_http_app()
    app.add_middleware(SecurityHeadersMiddleware)
    return app
