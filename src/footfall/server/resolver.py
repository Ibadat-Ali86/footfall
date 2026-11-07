"""Entity Identifier Allow-List Validation and In-Memory Resolution.

Implements Section 12.2 of docs/BUILD.md.
FLAGGED FOR HUMAN REVIEW per AGENTS.md rules on editing src/footfall/server/.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from footfall.registry import load_registry

# Section 12.2: Validate against ^[A-Za-z0-9@._/\-]{1,100}$ before any lookup
ENTITY_REGEX = re.compile(r"^[A-Za-z0-9@._/\-]{1,100}$")


@dataclass(frozen=True)
class EntityResolutionResult:
    """Outcome of entity lookup adhering to structured error templates."""

    status: str  # "ok" | "not_found" | "ambiguous" | "invalid_input"
    entity_id: str | None = None
    display_name: str | None = None
    candidates: tuple[str, ...] = ()
    message: str = ""


class EntityResolver:
    """In-memory resolution index from canonical IDs and package source aliases."""

    def __init__(
        self,
        canonical_map: dict[str, str],
        alias_map: dict[str, list[str]],
        display_names: dict[str, str],
    ) -> None:
        self.canonical_map = canonical_map  # normalized_id -> canonical_id
        self.alias_map = alias_map  # normalized_alias -> list[canonical_id]
        self.display_names = display_names  # canonical_id -> display_name
        self._all_keys = sorted(set(canonical_map.keys()) | set(alias_map.keys()))

    @classmethod
    def from_registry_yaml(cls, registry_path: Path | str = "registry/seed.yaml") -> EntityResolver:
        """Load resolver index directly from seed registry YAML."""
        path = Path(registry_path)
        if not path.is_file():
            return cls({}, {}, {})

        entities = load_registry(path)
        canonical_map: dict[str, str] = {}
        alias_map: dict[str, list[str]] = {}
        display_names: dict[str, str] = {}

        for e in entities:
            eid = e.entity_id
            norm_eid = eid.lower()
            canonical_map[norm_eid] = eid
            display_names[eid] = e.display_name

            for s in e.sources:
                alias = s.key.lower()
                if alias not in alias_map:
                    alias_map[alias] = []
                if eid not in alias_map[alias]:
                    alias_map[alias].append(eid)

        return cls(canonical_map, alias_map, display_names)

    @classmethod
    def from_dict_list(cls, entities_data: list[dict[str, Any]]) -> EntityResolver:
        """Create resolver from raw dictionary representations (for testing)."""
        canonical_map: dict[str, str] = {}
        alias_map: dict[str, list[str]] = {}
        display_names: dict[str, str] = {}

        for e in entities_data:
            eid = str(e["entity_id"])
            norm_eid = eid.lower()
            canonical_map[norm_eid] = eid
            display_names[eid] = str(e.get("display_name", eid))

            for s in e.get("sources", []):
                alias = str(s["key"]).lower()
                if alias not in alias_map:
                    alias_map[alias] = []
                if eid not in alias_map[alias]:
                    alias_map[alias].append(eid)

        return cls(canonical_map, alias_map, display_names)

    def resolve(self, raw_input: str) -> EntityResolutionResult:
        """Resolve arbitrary input string to canonical entity_id.

        Section 12.2 rules:
        - Validate against ^[A-Za-z0-9@._/\\-]{1,100}$ before any lookup.
        - Exact lookup in in-memory index.
        - If several match: return 'ambiguous' with at most 5 candidate ids.
        - If none match: return 'not_found' with at most 5 nearest ids by edit distance.
        - Never echo raw user input in error messages.
        """
        # 1. Allow-list validation
        if not raw_input or not ENTITY_REGEX.match(raw_input):
            return EntityResolutionResult(
                status="invalid_input",
                message="Input does not conform to allowed entity identifier pattern.",
            )

        norm_input = raw_input.strip().lower()

        # 2. Canonical exact match
        if norm_input in self.canonical_map:
            eid = self.canonical_map[norm_input]
            return EntityResolutionResult(
                status="ok",
                entity_id=eid,
                display_name=self.display_names.get(eid, eid),
                message="Resolved successfully.",
            )

        # 3. Source alias exact match
        if norm_input in self.alias_map:
            matches = self.alias_map[norm_input]
            if len(matches) == 1:
                eid = matches[0]
                return EntityResolutionResult(
                    status="ok",
                    entity_id=eid,
                    display_name=self.display_names.get(eid, eid),
                    message="Resolved successfully from package alias.",
                )
            # Multiple entities mapped to this key
            candidates = tuple(matches[:5])
            return EntityResolutionResult(
                status="ambiguous",
                candidates=candidates,
                message="Multiple candidate entities match this identifier.",
            )

        # 4. Not found: compute nearest candidate suggestions via edit distance
        nearest = difflib.get_close_matches(norm_input, self._all_keys, n=5, cutoff=0.4)
        # Map candidates back to canonical IDs
        candidate_eids: list[str] = []
        for key in nearest:
            if key in self.canonical_map:
                cid = self.canonical_map[key]
                if cid not in candidate_eids:
                    candidate_eids.append(cid)
            elif key in self.alias_map:
                for cid in self.alias_map[key]:
                    if cid not in candidate_eids:
                        candidate_eids.append(cid)

        return EntityResolutionResult(
            status="not_found",
            candidates=tuple(candidate_eids[:5]),
            message="Entity not found in registry.",
        )
