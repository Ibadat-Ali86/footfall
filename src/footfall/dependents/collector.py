"""Collector for package dependents counts from open ecosystem registries."""

from __future__ import annotations

import logging
import time
import urllib.parse
from datetime import UTC, datetime

import httpx

from footfall.dependents.depth import AdoptionDepthCalculator
from footfall.dependents.models import DependentsRecord

logger = logging.getLogger(__name__)

REGISTRY_MAP: dict[str, str] = {
    "pypi": "pypi.org",
    "npm": "npmjs.org",
}


class DependentsCollector:
    """Collects downstream package and repository dependents counts via ecosyste.ms API."""

    def __init__(
        self,
        base_url: str = "https://packages.ecosyste.ms/api/v1",
        timeout: float = 10.0,
        max_retries: int = 3,
        calculator: AdoptionDepthCalculator | None = None,
    ) -> None:
        """Initialize collector with API settings and depth calculator."""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.calculator = calculator or AdoptionDepthCalculator()

    def fetch_dependents(
        self,
        entity_id: str,
        source: str,
        package_name: str,
    ) -> DependentsRecord | None:
        """Fetch downstream dependency counts for a given package and source."""
        registry = REGISTRY_MAP.get(source.lower())
        if not registry:
            logger.warning("Unsupported registry source for dependents: %s", source)
            return None

        quoted_name = urllib.parse.quote(package_name, safe="")
        url = f"{self.base_url}/registries/{registry}/packages/{quoted_name}"
        headers = {
            "User-Agent": "Footfall-Dependents-Engine/1.0",
            "Accept": "application/json",
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(url, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        dep_pkgs = int(data.get("dependent_packages_count") or 0)
                        dep_repos = int(data.get("dependent_repos_count") or 0)
                        downloads = int(data.get("downloads") or 0)
                        docker_deps = data.get("docker_dependents_count")
                        docker_count = int(docker_deps) if docker_deps is not None else None

                        ratio = self.calculator.compute_depth_ratio(
                            dependents=dep_pkgs, downloads=downloads
                        )
                        tier = self.calculator.classify_tier(ratio)
                        now_str = datetime.now(UTC).isoformat()

                        return DependentsRecord(
                            entity_id=entity_id,
                            source=source.lower(),
                            package_name=package_name,
                            dependent_packages_count=dep_pkgs,
                            dependent_repos_count=dep_repos,
                            monthly_downloads=downloads,
                            depth_ratio=ratio,
                            depth_tier=tier,
                            docker_dependents_count=docker_count,
                            timestamp=now_str,
                        )
                    if resp.status_code == 404:
                        logger.info("Package %s not found in registry %s", package_name, registry)
                        return None
                    if resp.status_code < 500 and resp.status_code != 429:
                        logger.warning(
                            "Unexpected HTTP error %d querying %s", resp.status_code, url
                        )
                        return None
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                logger.warning(
                    "Attempt %d failed querying dependents for %s: %s",
                    attempt,
                    package_name,
                    str(exc),
                )

            if attempt < self.max_retries:
                time.sleep(0.5 * (2 ** (attempt - 1)))

        return None
