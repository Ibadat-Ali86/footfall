"""PyPI collector prototype (pypistats.org) with PEP 503 normalization.

Implements Section 7.2 of docs/BUILD.md.
"""

from __future__ import annotations

import re
from typing import Any

from footfall.collectors.base import BaseCollector, Snapshot, SnapshotQuality


class PyPICollector(BaseCollector):
    """Collects daily download telemetry from pypistats.org."""

    BASE_URL = "https://pypistats.org/api/packages"

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize package name according to PEP 503."""
        return re.sub(r"[-_.]+", "-", name).lower()

    async def collect_entity(
        self,
        entity_id: str,
        source_key: str,
        obs_date: str,
    ) -> list[Snapshot]:
        """Fetch daily downloads for a normalized PyPI package."""
        normalized = self.normalize_name(source_key)
        url = f"{self.BASE_URL}/{normalized}/overall"
        try:
            data = await self.fetch_json(url)
            return self.parse_response(entity_id, source_key, obs_date, data)
        except Exception:
            return [
                Snapshot(
                    entity_id=entity_id,
                    source="pypi",
                    metric="downloads",
                    obs_date=obs_date,
                    value=0.0,
                    quality=SnapshotQuality.ERROR,
                    collected_at=self.current_iso_timestamp(),
                )
            ]

    def parse_response(
        self,
        entity_id: str,
        source_key: str,
        obs_date: str,
        data: dict[str, Any],
    ) -> list[Snapshot]:
        """Parse pypistats JSON payload and filter for obs_date."""
        rows = data.get("data", [])
        daily_downloads = 0.0
        found_date = False

        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict) and row.get("date") == obs_date:
                    # Filter for category "without_mirrors" if present, else aggregate
                    if row.get("category") == "without_mirrors":
                        daily_downloads = float(row.get("downloads", 0.0))
                        found_date = True
                        break
                    elif row.get("category") == "overall" and not found_date:
                        daily_downloads = float(row.get("downloads", 0.0))
                        found_date = True

        quality = SnapshotQuality.OK if found_date else SnapshotQuality.PARTIAL

        return [
            Snapshot(
                entity_id=entity_id,
                source="pypi",
                metric="downloads",
                obs_date=obs_date,
                value=daily_downloads,
                quality=quality,
                collected_at=self.current_iso_timestamp(),
            )
        ]
