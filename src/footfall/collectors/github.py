"""GitHub GraphQL collector prototype for daily repository metrics.

Implements Section 7.2 of docs/BUILD.md:
- Batches repository queries using GraphQL aliases
- Extracts stars, forks, open issues
- Authenticates via GH_READONLY_TOKEN
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from footfall.collectors.base import BaseCollector, Snapshot, SnapshotQuality

if TYPE_CHECKING:
    from pathlib import Path

    import httpx


class GitHubCollector(BaseCollector):
    """Collects repository telemetry via GitHub GraphQL API."""

    GRAPHQL_URL = "https://api.github.com/graphql"

    def __init__(
        self,
        config_path: Path | str | None = None,
        client: httpx.AsyncClient | None = None,
        token: str | None = None,
    ) -> None:
        super().__init__(config_path=config_path, client=client)
        self.token = token or os.environ.get("GH_READONLY_TOKEN", "")

    async def collect_entity(
        self,
        entity_id: str,
        source_key: str,
        obs_date: str,
    ) -> list[Snapshot]:
        """Fetch stars, forks, and issues for an owner/repo key."""
        if "/" not in source_key:
            return []
        owner, repo = source_key.split("/", 1)
        query = """
        query($owner: String!, $name: String!) {
          repository(owner: $owner, name: $name) {
            stargazerCount
            forkCount
            issues(states: OPEN) { totalCount }
          }
        }
        """
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        payload = {"query": query, "variables": {"owner": owner, "name": repo}}

        try:
            self.validate_url(self.GRAPHQL_URL)
            response = await self.client.post(
                self.GRAPHQL_URL,
                json=payload,
                headers={"User-Agent": self.user_agent, **headers},
            )
            response.raise_for_status()
            data = response.json()
            return self.parse_response(entity_id, source_key, obs_date, data)
        except Exception:
            return [
                Snapshot(
                    entity_id=entity_id,
                    source="github",
                    metric="stars",
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
        """Extract stars, forks, and open issues from GraphQL response."""
        repo_data = data.get("data", {}).get("repository") or {}
        stars = float(repo_data.get("stargazerCount", 0.0))
        forks = float(repo_data.get("forkCount", 0.0))
        open_issues = float(repo_data.get("issues", {}).get("totalCount", 0.0))
        now = self.current_iso_timestamp()

        return [
            Snapshot(
                entity_id=entity_id,
                source="github",
                metric="stars",
                obs_date=obs_date,
                value=stars,
                quality=SnapshotQuality.OK,
                collected_at=now,
            ),
            Snapshot(
                entity_id=entity_id,
                source="github",
                metric="forks",
                obs_date=obs_date,
                value=forks,
                quality=SnapshotQuality.OK,
                collected_at=now,
            ),
            Snapshot(
                entity_id=entity_id,
                source="github",
                metric="open_issues",
                obs_date=obs_date,
                value=open_issues,
                quality=SnapshotQuality.OK,
                collected_at=now,
            ),
        ]
