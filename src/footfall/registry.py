"""Entity registry models, schemas, and loader functions.

Governs Section 7.3 and Section 8 of docs/BUILD.md.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegistryCategory(StrEnum):
    """Permitted entity categories per SQL schema."""

    AGENT_FRAMEWORK = "agent-framework"
    LLM_SDK = "llm-sdk"
    MCP_SERVER = "mcp-server"
    VECTOR_STORE = "vector-store"
    EVAL_TOOL = "eval-tool"
    MODEL = "model"
    OTHER = "other"


class RegistryStatus(StrEnum):
    """Entity tracking lifecycle status."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    EXCLUDED = "excluded"


class SourceType(StrEnum):
    """Allowed upstream platforms."""

    GITHUB = "github"
    NPM = "npm"
    PYPI = "pypi"
    HUGGINGFACE = "huggingface"


class MappingConfidence(StrEnum):
    """Hypothesis H3 confidence grades.

    verified: Bidirectional proof (package references repo, repo references package)
    declared: One-directional reference
    heuristic: Name alignment without reciprocal link
    """

    VERIFIED = "verified"
    DECLARED = "declared"
    HEURISTIC = "heuristic"


class EntitySource(BaseModel):
    """Single upstream identifier mapping for an entity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source: SourceType
    key: str = Field(
        ...,
        pattern=r"^[A-Za-z0-9@._/\-]{1,100}$",
        description="owner/repo for GitHub, package name for npm/PyPI, model ID for Hugging Face",
    )
    mapping_confidence: MappingConfidence = MappingConfidence.DECLARED
    verified_at: str | None = None


class Entity(BaseModel):
    """Core entity definition tracked across ecosystems."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_id: str = Field(
        ...,
        pattern=r"^[a-z0-9-]{3,64}$",
        description="Unique URL-safe slug for the entity",
    )
    display_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Human-readable title",
    )
    category: RegistryCategory
    status: RegistryStatus = RegistryStatus.ACTIVE
    sources: list[EntitySource] = Field(
        ...,
        min_length=1,
        description="At least one source mapping is required",
    )

    @field_validator("sources")
    @classmethod
    def validate_unique_sources(cls, v: list[EntitySource]) -> list[EntitySource]:
        """Ensure an entity does not register duplicate (source, key) pairs."""
        seen: set[tuple[str, str]] = set()
        for s in v:
            pair = (s.source.value, s.key.lower())
            if pair in seen:
                raise ValueError(f"Duplicate source entry in entity: {pair}")
            seen.add(pair)
        return v


def validate_registry_data(raw_items: list[dict[str, Any]]) -> list[Entity]:
    """Parse and validate a list of raw entity dictionaries."""
    entities: list[Entity] = []
    seen_ids: set[str] = set()

    for item in raw_items:
        entity = Entity.model_validate(item)
        if entity.entity_id in seen_ids:
            raise ValueError(f"Duplicate entity_id detected in registry: {entity.entity_id}")
        seen_ids.add(entity.entity_id)
        entities.append(entity)

    return entities


def load_registry(path: Path | str) -> list[Entity]:
    """Load, parse, and validate an entity registry YAML file."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Registry file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, list):
        msg = f"Registry root must be a YAML sequence, got {type(data).__name__}"
        raise ValueError(msg)

    return validate_registry_data(data)


def compute_coverage_stats(entities: list[Entity]) -> dict[str, Any]:
    """Calculate Hypothesis H3 coverage and mapping confidence metrics."""
    total_entities = len(entities)
    total_mappings = sum(len(e.sources) for e in entities)
    by_category: dict[str, int] = {}
    by_source: dict[str, int] = {}
    by_confidence: dict[str, int] = {
        MappingConfidence.VERIFIED.value: 0,
        MappingConfidence.DECLARED.value: 0,
        MappingConfidence.HEURISTIC.value: 0,
    }

    for e in entities:
        cat_key = e.category.value
        by_category[cat_key] = by_category.get(cat_key, 0) + 1
        for s in e.sources:
            src_key = s.source.value
            by_source[src_key] = by_source.get(src_key, 0) + 1
            by_confidence[s.mapping_confidence.value] += 1

    verified_count = by_confidence[MappingConfidence.VERIFIED.value]
    verified_pct = (verified_count / total_mappings * 100.0) if total_mappings > 0 else 0.0

    return {
        "total_entities": total_entities,
        "total_mappings": total_mappings,
        "by_category": by_category,
        "by_source": by_source,
        "by_confidence": by_confidence,
        "verified_percentage": round(verified_pct, 2),
        "h3_gate_passed": verified_pct >= 95.0,
    }
