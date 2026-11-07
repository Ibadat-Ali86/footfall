"""npm downloads collector prototype with silent truncation detection.

Implements Section 7.2 of docs/BUILD.md.
"""

from __future__ import annotations

from typing import Any

from footfall.collectors.base import BaseCollector, Snapshot, SnapshotQuality


class NpmCollector(BaseCollector):
    """Collects daily download telemetry from api.npmjs.org."""

    BASE_URL = "https://api.npmjs.org/downloads/range"

    async def collect_entity(
        self,
        entity_id: str,
        source_key: str,
        obs_date: str,
    ) -> list[Snapshot]:
        """Fetch daily downloads for a specific package on obs_date."""
        url = f"{self.BASE_URL}/{obs_date}:{obs_date}/{source_key}"
        try:
            data = await self.fetch_json(url)
            return self.parse_response(entity_id, source_key, obs_date, data)
        except Exception:
            return [
                Snapshot(
                    entity_id=entity_id,
                    source="npm",
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
        """Parse npm download response and flag silent truncation."""
        returned_start = data.get("start", "")
        # Silent truncation check (Section 7.2):
        # npm silently resets start to ~18 months ago if earlier date requested
        is_truncated = returned_start != obs_date
        quality = SnapshotQuality.TRUNCATED if is_truncated else SnapshotQuality.OK

        downloads_list = data.get("downloads", [])
        total_downloads = 0.0

        if isinstance(downloads_list, list) and downloads_list:
            # First item in downloads array corresponds to requested single day
            first_entry = downloads_list[0]
            if isinstance(first_entry, dict):
                total_downloads = float(first_entry.get("downloads", 0.0))

        return [
            Snapshot(
                entity_id=entity_id,
                source="npm",
                metric="downloads",
                obs_date=obs_date,
                value=total_downloads,
                quality=quality,
                collected_at=self.current_iso_timestamp(),
            )
        ]
