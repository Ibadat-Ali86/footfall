"""Pydantic Input Models and JSON Schemas for MCP Tools.

Implements Section 12.2 of docs/BUILD.md.
FLAGGED FOR HUMAN REVIEW per AGENTS.md rules on editing src/footfall/server/.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

ENTITY_STRING_PATTERN: str = r"^[A-Za-z0-9@._/\-]{1,100}$"

EntityIdentifier = Annotated[
    str,
    StringConstraints(
        pattern=ENTITY_STRING_PATTERN,
        min_length=1,
        max_length=100,
    ),
]


class CompareInput(BaseModel):
    """Input parameters for tool 1: footfall_compare."""

    model_config = ConfigDict(extra="forbid")

    entities: list[EntityIdentifier] = Field(
        ...,
        min_length=2,
        max_length=6,
        description="List of 2 to 6 entity identifiers (canonical ID, GitHub repo, package).",
    )
    window_weeks: int = Field(
        default=12,
        ge=4,
        le=52,
        description="Historical comparison window in weeks (4 to 52, default 12).",
    )


class TrendInput(BaseModel):
    """Input parameters for tool 2: footfall_trend."""

    model_config = ConfigDict(extra="forbid")

    entity: EntityIdentifier = Field(
        ...,
        description="Target tool identifier (canonical ID, GitHub repo, or package name).",
    )
    metrics: list[Literal["downloads", "stars", "attention"]] | None = Field(
        default=None,
        description="Metrics to include ('downloads', 'stars', 'attention'). Defaults to all.",
    )
    window_weeks: int = Field(
        default=26,
        ge=4,
        le=104,
        description="Time series lookback window in weeks (4 to 104, default 26).",
    )


class FindRisingInput(BaseModel):
    """Input parameters for tool 3: footfall_find_rising."""

    model_config = ConfigDict(extra="forbid")

    category: str = Field(
        default="any",
        description="Category filter (e.g. 'agent-framework', 'llm-sdk', 'mcp-server', or 'any').",
    )
    phase: Literal[
        "insufficient_data",
        "breakout",
        "attention_ahead",
        "use_ahead",
        "fading",
        "emerging",
        "mainstream",
        "plateau",
    ] = Field(
        default="breakout",
        description="Target lifecycle phase to search for (default 'breakout').",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of tools to return (1 to 20, default 10).",
    )
    min_weekly_downloads: float = Field(
        default=500.0,
        ge=0.0,
        description="Minimum weekly volume floor to filter out inactive packages (default 500).",
    )
