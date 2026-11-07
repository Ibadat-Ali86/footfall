"""Hacker News collector prototype using Algolia search API.

Implements Section 7.2 of docs/BUILD.md:
- Queries by exact GitHub repository URL
- Aggregates story counts and points
- Zero user comments or text stored
- Mandatory attribution: "Search by Algolia"
"""

from __future__ import annotations

from typing import Any

from footfall.collectors.base import BaseCollector, Snapshot, SnapshotQuality


class HackerNewsCollector(BaseCollector):
    """Collects Hacker News attention metrics matching repository URLs."""

    SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"
    ATTRIBUTION = "Search by Algolia"

    async def collect_entity(
        self,
        entity_id: str,
        source_key: str,
        obs_date: str,
    ) -> list[Snapshot]:
        """Query Hacker News stories mentioning the repository URL."""
        # Clean owner/repo into matchable URL query
        repo_url = f"github.com/{source_key}"
        params = {
            "query": repo_url,
            "restrictSearchableAttributes": "url",
            "tags": "story",
            "hitsPerPage": 50,
        }
        try:
            data = await self.fetch_json(self.SEARCH_URL, params=params)
            return self.parse_response(entity_id, source_key, obs_date, data)
        except Exception:
            return [
                Snapshot(
                    entity_id=entity_id,
                    source="hackernews",
                    metric="stories",
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
        """Aggregate total stories and cumulative points from Algolia hits."""
        hits = data.get("hits", [])
        total_points = 0.0
        story_count = 0.0

        if isinstance(hits, list):
            story_count = float(len(hits))
            for hit in hits:
                if isinstance(hit, dict):
                    points = float(hit.get("points") or 0.0)
                    total_points += points

        now = self.current_iso_timestamp()
        return [
            Snapshot(
                entity_id=entity_id,
                source="hackernews",
                metric="stories",
                obs_date=obs_date,
                value=story_count,
                quality=SnapshotQuality.OK,
                collected_at=now,
            ),
            Snapshot(
                entity_id=entity_id,
                source="hackernews",
                metric="points",
                obs_date=obs_date,
                value=total_points,
                quality=SnapshotQuality.OK,
                collected_at=now,
            ),
        ]
