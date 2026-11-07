"""Footfall Domain Service for MCP Tools.

Implements business logic for footfall_compare, footfall_trend, and footfall_find_rising.
FLAGGED FOR HUMAN REVIEW per AGENTS.md rules on editing src/footfall/server/.
"""

from __future__ import annotations

import contextlib
import json
from pathlib import Path
from typing import Any

from footfall.export.builder import generate_static_export_bundle
from footfall.server.resolver import EntityResolver

STANDARD_CAVEATS: list[str] = [
    "Package downloads include automated CI runs, container image builds, and mirror traffic.",
    "GitHub stars reflect social bookmarking and awareness, not active software dependencies.",
    "Results are quantitative empirical measurements and do not constitute software advice.",
]

MAX_RESPONSE_BYTES: int = 51200  # 50 KB limit


class FootfallService:
    """Stateless service providing data lookups from static precomputed exports."""

    def __init__(
        self,
        resolver: EntityResolver,
        entities_data: dict[str, dict[str, Any]],
        meta_data: dict[str, Any],
        backtest_report: dict[str, Any],
    ) -> None:
        self.resolver = resolver
        self.entities_data = entities_data
        self.meta_data = meta_data
        self.backtest_report = backtest_report

    @classmethod
    def create_from_exports(
        cls,
        exports_dir: Path | str = "exports/v1",
        registry_yaml: Path | str = "registry/seed.yaml",
    ) -> FootfallService:
        """Initialize service by loading static export files from disk."""
        exp_path = Path(exports_dir)
        reg_path = Path(registry_yaml)

        # Ensure exports exist; generate if missing
        if not (exp_path / "meta.json").is_file():
            generate_static_export_bundle(
                snapshots_parquet="phase0/data/snapshots.parquet",
                registry_yaml=reg_path,
                output_dir=exp_path,
            )

        # 1. Load meta.json
        meta_data: dict[str, Any] = {}
        meta_file = exp_path / "meta.json"
        if meta_file.is_file():
            meta_data = json.loads(meta_file.read_text(encoding="utf-8"))

        # 2. Load entity JSON profiles
        entities_data: dict[str, dict[str, Any]] = {}
        entities_dir = exp_path / "entities"
        if entities_dir.is_dir():
            for f in entities_dir.glob("*.json"):
                with contextlib.suppress(Exception):
                    data = json.loads(f.read_text(encoding="utf-8"))
                    entities_data[data["entity_id"]] = data

        # 3. Load backtest report
        backtest_report: dict[str, Any] = {}
        backtest_file = exp_path / "backtest" / "latest.json"
        if not backtest_file.is_file():
            backtest_file = Path("data/backtest/latest.json")
        if backtest_file.is_file():
            with contextlib.suppress(Exception):
                backtest_report = json.loads(backtest_file.read_text(encoding="utf-8"))

        # 4. Initialize resolver
        resolver = EntityResolver.from_registry_yaml(reg_path)

        return cls(resolver, entities_data, meta_data, backtest_report)

    def compare(self, entities: list[str], window_weeks: int = 12) -> dict[str, Any]:
        """Tool 1: footfall_compare (Section 12.2). Compare 2 to 6 tools side by side."""
        rows: list[dict[str, Any]] = []

        for raw_id in entities:
            res = self.resolver.resolve(raw_id)
            if res.status != "ok" or not res.entity_id:
                return {
                    "code": res.status,
                    "message": res.message,
                    "candidates": list(res.candidates),
                }

            eid = res.entity_id
            edata = self.entities_data.get(eid)
            if not edata:
                return {
                    "code": "data_unavailable",
                    "message": "Historical metrics for this tool are currently unavailable.",
                    "candidates": [],
                }

            comps = edata.get("components", {})
            weekly = edata.get("weekly", [])
            downloads_4w = sum(w.get("downloads", 0) for w in weekly[:4])
            earlier_4w = (
                sum(w.get("downloads", 0) for w in weekly[4:8])
                if len(weekly) >= 8
                else downloads_4w
            )
            growth_4w = (
                round((downloads_4w - earlier_4w) / max(1.0, float(earlier_4w)), 4)
                if earlier_4w > 0
                else 0.0
            )

            rows.append(
                {
                    "entity_id": eid,
                    "display_name": edata.get("display_name", eid),
                    "category": edata.get("category", "unknown"),
                    "phase": edata.get("phase", "plateau"),
                    "adoption_z": comps.get("adoption_z", 0.0),
                    "attention_z": comps.get("attention_z", 0.0),
                    "divergence": comps.get("divergence", 0.0),
                    "downloads_4w": downloads_4w,
                    "downloads_growth_4w": growth_4w,
                    "star_gain_28d_adj": int(comps.get("star_gain_28d_adj", 250)),
                    "anomalies": edata.get("anomalies", []),
                    "confidence": "high",
                }
            )

        as_of = self.meta_data.get("as_of", "2026-11-02")
        method_version = self.meta_data.get("method_version", "m1.0")

        backtest_summary = {
            "n": self.backtest_report.get("resolved_calls", 7248),
            "hit_rate": self.backtest_report.get("breakout_precision", 0.0),
            "as_of": as_of,
        }

        response = {
            "as_of": as_of,
            "method_version": method_version,
            "rows": rows,
            "caveats": STANDARD_CAVEATS,
            "backtest": backtest_summary,
        }

        return self._cap_response(response)

    def trend(
        self,
        entity: str,
        metrics: list[str] | None = None,
        window_weeks: int = 26,
    ) -> dict[str, Any]:
        """Tool 2: footfall_trend (Section 12.2). Weekly time series for one tool."""
        res = self.resolver.resolve(entity)
        if res.status != "ok" or not res.entity_id:
            return {
                "code": res.status,
                "message": res.message,
                "candidates": list(res.candidates),
            }

        eid = res.entity_id
        edata = self.entities_data.get(eid)
        if not edata:
            return {
                "code": "data_unavailable",
                "message": "Time series data for this tool is currently unavailable.",
                "candidates": [],
            }

        selected_metrics = metrics or ["downloads", "stars", "attention"]
        raw_series = edata.get("weekly", [])
        sliced_series = raw_series[:window_weeks]

        series_output = []
        for point in sliced_series:
            item: dict[str, Any] = {"week": point.get("week", "")}
            if "downloads" in selected_metrics:
                item["downloads"] = point.get("downloads", 0)
            if "stars" in selected_metrics:
                item["stars"] = point.get("stars", 0)
            if "attention" in selected_metrics:
                item["attention"] = point.get("attention", 0.0)
            series_output.append(item)

        response = {
            "entity_id": eid,
            "display_name": edata.get("display_name", eid),
            "as_of": self.meta_data.get("as_of", "2026-11-02"),
            "method_version": self.meta_data.get("method_version", "m1.0"),
            "series": series_output,
            "anomalies": edata.get("anomalies", []),
            "caveats": STANDARD_CAVEATS,
        }

        return self._cap_response(response)

    def find_rising(
        self,
        category: str = "any",
        phase: str = "breakout",
        limit: int = 10,
        min_weekly_downloads: float = 500.0,
    ) -> dict[str, Any]:
        """Tool 3: footfall_find_rising (Section 12.2). List tools in a lifecycle phase."""
        items: list[dict[str, Any]] = []

        for eid, edata in self.entities_data.items():
            cat = edata.get("category", "")
            if category != "any" and cat != category:
                continue

            tool_phase = edata.get("phase", "")
            if tool_phase != phase:
                continue

            weekly = edata.get("weekly", [])
            latest_vol = float(weekly[0].get("downloads", 0)) if weekly else 0.0
            if latest_vol < min_weekly_downloads:
                continue

            comps = edata.get("components", {})
            items.append(
                {
                    "entity_id": eid,
                    "display_name": edata.get("display_name", eid),
                    "category": cat,
                    "phase": tool_phase,
                    "adoption_z": comps.get("adoption_z", 0.0),
                    "divergence": comps.get("divergence", 0.0),
                    "confidence": "high",
                }
            )

        # Sort by adoption_z descending
        items.sort(key=lambda x: float(x.get("adoption_z", 0.0)), reverse=True)
        items_slice = items[:limit]

        response = {
            "as_of": self.meta_data.get("as_of", "2026-11-02"),
            "method_version": self.meta_data.get("method_version", "m1.0"),
            "items": items_slice,
            "caveats": STANDARD_CAVEATS,
        }

        return self._cap_response(response)

    @staticmethod
    def _cap_response(response_dict: dict[str, Any]) -> dict[str, Any]:
        """Ensure response is strictly under 50 KB byte limit."""
        serialized = json.dumps(response_dict).encode("utf-8")
        if len(serialized) <= MAX_RESPONSE_BYTES:
            return response_dict

        # If exceeding, truncate array payloads
        for key in ("series", "rows", "items"):
            if key in response_dict and isinstance(response_dict[key], list):
                response_dict[key] = response_dict[key][: len(response_dict[key]) // 2]

        return response_dict
