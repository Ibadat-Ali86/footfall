"""Developer Stack Analyzer.

Parses dependency manifests (pyproject.toml, requirements.txt, package.json),
resolves tracked AI ecosystem entities, and computes lifecycle phase breakdowns.
"""

from __future__ import annotations

import contextlib
import json
import re
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from footfall.server.resolver import EntityResolver


@dataclass(frozen=True)
class StackItem:
    """Individual tracked package within a developer stack."""

    declared_package: str
    entity_id: str
    display_name: str
    category: str
    phase: str
    adoption_z: float
    divergence: float
    confidence: str


@dataclass(frozen=True)
class StackReport:
    """Consolidated adoption and lifecycle analysis for a project stack."""

    manifest_file: str
    total_dependencies: int
    tracked_tools_count: int
    mean_adoption_z: float
    phase_distribution: dict[str, int]
    tracked_items: list[StackItem]
    caveats: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary representation."""
        return asdict(self)


class StackAnalyzer:
    """Analyzes software dependency manifests against Footfall seed registry."""

    def __init__(
        self,
        resolver: EntityResolver,
        entities_data: dict[str, dict[str, Any]],
    ) -> None:
        self.resolver = resolver
        self.entities_data = entities_data

    @classmethod
    def create_from_exports(
        cls,
        exports_dir: Path | str = "exports/v1",
        registry_yaml: Path | str = "registry/seed.yaml",
    ) -> StackAnalyzer:
        """Initialize StackAnalyzer using precomputed static exports."""
        exp_path = Path(exports_dir)
        reg_path = Path(registry_yaml)

        resolver = EntityResolver.from_registry_yaml(reg_path)

        entities_data: dict[str, dict[str, Any]] = {}
        entities_dir = exp_path / "entities"
        if entities_dir.is_dir():
            for f in entities_dir.glob("*.json"):
                with contextlib.suppress(Exception):
                    data = json.loads(f.read_text(encoding="utf-8"))
                    entities_data[data["entity_id"]] = data

        return cls(resolver=resolver, entities_data=entities_data)

    def extract_dependencies(self, manifest_path: Path | str) -> list[str]:
        """Extract declared package names from pyproject.toml, requirements.txt, or package.json."""
        path = Path(manifest_path)
        if not path.is_file():
            raise FileNotFoundError(f"Manifest file not found: {path}")

        name = path.name.lower()
        if name == "pyproject.toml":
            return self._parse_pyproject(path)
        if "requirements" in name or name.endswith(".txt"):
            return self._parse_requirements(path)
        if name == "package.json":
            return self._parse_package_json(path)

        # Fallback line-by-line parser
        return self._parse_requirements(path)

    def _parse_pyproject(self, path: Path) -> list[str]:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        deps: set[str] = set()

        # PEP 621 project.dependencies
        project = data.get("project", {})
        for req in project.get("dependencies", []):
            pkg = self._clean_package_string(req)
            if pkg:
                deps.add(pkg)

        # Optional dependencies
        for group in project.get("optional-dependencies", {}).values():
            for req in group:
                pkg = self._clean_package_string(req)
                if pkg:
                    deps.add(pkg)

        # Poetry dependencies
        poetry = data.get("tool", {}).get("poetry", {})
        for req in poetry.get("dependencies", {}):
            if req.lower() != "python":
                deps.add(req.lower())

        return sorted(deps)

    def _parse_requirements(self, path: Path) -> list[str]:
        deps: set[str] = set()
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            pkg = self._clean_package_string(line)
            if pkg:
                deps.add(pkg)
        return sorted(deps)

    def _parse_package_json(self, path: Path) -> list[str]:
        data = json.loads(path.read_text(encoding="utf-8"))
        deps: set[str] = set()
        for section in ("dependencies", "devDependencies"):
            for pkg in data.get(section, {}):
                deps.add(pkg.lower())
        return sorted(deps)

    @staticmethod
    def _clean_package_string(req: str) -> str:
        """Strip environment markers, extras, and version constraints from package string."""
        # Split on comments or environment markers
        clean = req.split(";")[0].split("#")[0].strip()
        # Remove extras [dev,etc]
        clean = re.sub(r"\[.*?\]", "", clean)
        # Split on version comparison operators
        clean = re.split(r"[><=~^!]", clean)[0].strip()
        return clean.lower()

    def analyze_manifest(self, manifest_path: Path | str) -> StackReport:
        """Analyze dependencies in a manifest file and compute ecosystem metrics."""
        path = Path(manifest_path)
        declared_pkgs = self.extract_dependencies(path)

        tracked_items: list[StackItem] = []
        phase_dist: dict[str, int] = {}
        total_adoption_z: float = 0.0

        for pkg in declared_pkgs:
            # Attempt to resolve package via EntityResolver
            match = self.resolver.resolve(pkg)
            if match.status == "ok" and match.entity_id:
                canonical_id = match.entity_id
                profile = self.entities_data.get(canonical_id)
                if profile:
                    comp = profile.get("components", {})
                    phase = profile.get("phase", "plateau")
                    item = StackItem(
                        declared_package=pkg,
                        entity_id=canonical_id,
                        display_name=profile.get("display_name", canonical_id),
                        category=profile.get("category", "unknown"),
                        phase=phase,
                        adoption_z=float(comp.get("adoption_z", 0.0)),
                        divergence=float(comp.get("divergence", 0.0)),
                        confidence="verified",
                    )
                    tracked_items.append(item)
                    phase_dist[phase] = phase_dist.get(phase, 0) + 1
                    total_adoption_z += item.adoption_z

        mean_z = round(total_adoption_z / len(tracked_items), 2) if tracked_items else 0.0

        caveats = [
            (
                "Package downloads include automated CI runs, container image builds, "
                "and mirror traffic."
            ),
            (
                "Results are quantitative empirical measurements and do not constitute "
                "financial or software advice."
            ),
        ]

        return StackReport(
            manifest_file=path.name,
            total_dependencies=len(declared_pkgs),
            tracked_tools_count=len(tracked_items),
            mean_adoption_z=mean_z,
            phase_distribution=phase_dist,
            tracked_items=tracked_items,
            caveats=caveats,
        )
