"""Data models for Footfall Dependents and Adoption Depth analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DependentsRecord:
    """Represents downstream architectural commitment and adoption depth."""

    entity_id: str
    source: str
    package_name: str
    dependent_packages_count: int
    dependent_repos_count: int
    monthly_downloads: int
    depth_ratio: float
    depth_tier: str
    docker_dependents_count: int | None = None
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert record to a JSON-serializable dictionary."""
        return asdict(self)
