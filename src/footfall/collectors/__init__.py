"""Base collector interface and shared HTTP client.

Every source-specific collector inherits from BaseCollector and uses
the shared httpx client configured from config/sources.yaml.

Design decisions:
- One shared httpx.AsyncClient per collector run (not per-request) avoids
  connection exhaustion under the PyPI 1 RPS limit.
- All host validation happens at init time against the allow-list, not per-call.
- tenacity-style retry is wired in at the transport level so all subclasses
  get it for free.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseCollector(ABC):
    """Abstract base for all source collectors.

    Subclasses implement collect() and nothing else; all HTTP,
    retry, timeout, size-cap and idempotency logic lives here.
    """

    # TODO T0.6 — wire in shared httpx client with sources.yaml config
    # TODO T0.6 — implement host allow-list validation
    # TODO T0.6 — implement response size cap
    # TODO T0.6 — implement idempotent write guard

    @abstractmethod
    async def collect(self, obs_date: str) -> list[dict[str, Any]]:
        """Collect snapshots for obs_date (YYYY-MM-DD).

        Returns:
            A list of raw snapshot dicts. Empty list on total failure.
            Each dict must include entity_id, source, metric, obs_date, value, quality.

        Raises:
            Never raises. Errors are captured in the returned quality field.
        """
        ...
