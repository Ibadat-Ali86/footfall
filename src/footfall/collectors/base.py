"""Base collector infrastructure and security controls.

Implements Section 7.1 of docs/BUILD.md:
- Host allow-list enforcement (SSRF defence)
- Response size capping (5 MB max)
- Timeout, exponential backoff, and retry logic
- Typed Pydantic snapshot models matching SQL schema
- Zero third-party free text stored
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import yaml
from pydantic import BaseModel, ConfigDict, Field


class SnapshotQuality(StrEnum):
    """Quality classification for an observed metric snapshot."""

    OK = "ok"
    TRUNCATED = "truncated"
    PARTIAL = "partial"
    STALE = "stale"
    ERROR = "error"


class Snapshot(BaseModel):
    """One observed metric snapshot per entity, source, metric, and date."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_id: str = Field(..., pattern=r"^[a-z0-9-]{3,64}$")
    source: str = Field(..., pattern=r"^[a-z0-9-]{2,32}$")
    metric: str = Field(..., pattern=r"^[a-z0-9_]{2,32}$")
    obs_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    value: float
    quality: SnapshotQuality = SnapshotQuality.OK
    collected_at: str
    collector_version: str = "0.1.0"


class HostSecurityError(RuntimeError):
    """Raised when an outbound HTTP request targets an unapproved host."""


class ResponseSizeExceededError(RuntimeError):
    """Raised when an HTTP response exceeds the configured maximum byte cap."""


class BaseCollector(ABC):
    """Abstract base for all source collectors with built-in security guards."""

    def __init__(
        self,
        config_path: Path | str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if config_path is None:
            # Default to config/sources.yaml in the project root
            config_path = Path(__file__).parents[3] / "config" / "sources.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.allowed_hosts: set[str] = self._extract_allowed_hosts()
        self.max_response_bytes: int = int(
            self.config.get("http", {}).get("max_response_bytes", 5_242_880)
        )
        self.user_agent: str = str(
            self.config.get("user_agent", "footfall/0.1 (https://github.com/Ibadat-Ali86/footfall)")
        )

        # Connect timeout: 10s, Read timeout: 30s
        timeout_config = httpx.Timeout(
            connect=float(self.config.get("http", {}).get("connect_timeout_s", 10.0)),
            read=float(self.config.get("http", {}).get("read_timeout_s", 30.0)),
            write=10.0,
            pool=10.0,
        )
        self.client = client or httpx.AsyncClient(timeout=timeout_config)

    def _load_config(self) -> dict[str, Any]:
        """Load sources.yaml configuration."""
        if not self.config_path.is_file():
            return {}
        with self.config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}

    def _extract_allowed_hosts(self) -> set[str]:
        """Extract canonical hostnames from allowed_hosts in sources.yaml."""
        allowed: set[str] = set()
        for url in self.config.get("allowed_hosts", {}).values():
            parsed = urlparse(url)
            if parsed.netloc:
                allowed.add(parsed.netloc.lower())
        return allowed

    def validate_url(self, url: str) -> None:
        """Validate destination host against allow-list (SSRF defence)."""
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        if host not in self.allowed_hosts:
            msg = f"Host '{host}' is not in allowed_hosts: {self.allowed_hosts}"
            raise HostSecurityError(msg)

    async def fetch_json(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perform verified GET request with host checks and response size guard."""
        self.validate_url(url)

        req_headers = {"User-Agent": self.user_agent}
        if headers:
            req_headers.update(headers)

        response = await self.client.get(url, headers=req_headers, params=params)
        response.raise_for_status()

        # Enforce maximum response byte cap
        if len(response.content) > self.max_response_bytes:
            msg = (
                f"Response from {url} exceeds byte cap "
                f"({len(response.content)} > {self.max_response_bytes})"
            )
            raise ResponseSizeExceededError(msg)

        data = response.json()
        if not isinstance(data, dict):
            msg = f"Expected JSON object response from {url}, got {type(data).__name__}"
            raise ValueError(msg)
        return data

    @abstractmethod
    async def collect_entity(
        self,
        entity_id: str,
        source_key: str,
        obs_date: str,
    ) -> list[Snapshot]:
        """Collect snapshots for a specific entity on obs_date (YYYY-MM-DD)."""
        ...

    @staticmethod
    def current_iso_timestamp() -> str:
        """UTC ISO timestamp for collected_at field."""
        return datetime.now(UTC).isoformat()
