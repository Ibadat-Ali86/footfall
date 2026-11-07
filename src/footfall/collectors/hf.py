"""Hugging Face collector prototype for model metrics.

Implements Section 7.2 of docs/BUILD.md.
"""

from __future__ import annotations

from typing import Any

from footfall.collectors.base import BaseCollector, Snapshot, SnapshotQuality


class HuggingFaceCollector(BaseCollector):
    """Collects model downloads and like counts from Hugging Face API."""

    BASE_URL = "https://huggingface.co/api/models"

    async def collect_entity(
        self,
        entity_id: str,
        source_key: str,
        obs_date: str,
    ) -> list[Snapshot]:
        """Fetch model metadata from Hugging Face Hub."""
        url = f"{self.BASE_URL}/{source_key}"
        try:
            data = await self.fetch_json(url)
            return self.parse_response(entity_id, source_key, obs_date, data)
        except Exception:
            return [
                Snapshot(
                    entity_id=entity_id,
                    source="huggingface",
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
        """Extract downloads and likes from Hugging Face model metadata."""
        downloads = float(data.get("downloads", 0.0))
        likes = float(data.get("likes", 0.0))
        now = self.current_iso_timestamp()

        return [
            Snapshot(
                entity_id=entity_id,
                source="huggingface",
                metric="downloads",
                obs_date=obs_date,
                value=downloads,
                quality=SnapshotQuality.OK,
                collected_at=now,
            ),
            Snapshot(
                entity_id=entity_id,
                source="huggingface",
                metric="likes",
                obs_date=obs_date,
                value=likes,
                quality=SnapshotQuality.OK,
                collected_at=now,
            ),
        ]
