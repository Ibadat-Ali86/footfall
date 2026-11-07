"""Unit tests for entity registry models and offline validation.

Follows AGENTS.md rules:
- Write tests first.
- Pure unit tests with mocked/fixture data.
- Never call a live upstream API from a test.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from footfall.registry import (
    Entity,
    EntitySource,
    MappingConfidence,
    RegistryCategory,
    RegistryStatus,
    load_registry,
)


@pytest.fixture
def valid_entity_dict() -> dict[str, object]:
    """Sample valid entity dictionary."""
    return {
        "entity_id": "langgraph",
        "display_name": "LangGraph",
        "category": "agent-framework",
        "status": "active",
        "sources": [
            {
                "source": "github",
                "key": "langchain-ai/langgraph",
                "mapping_confidence": "verified",
                "verified_at": "2026-11-01T00:00:00Z",
            },
            {
                "source": "pypi",
                "key": "langgraph",
                "mapping_confidence": "verified",
                "verified_at": "2026-11-01T00:00:00Z",
            },
            {
                "source": "npm",
                "key": "@langchain/langgraph",
                "mapping_confidence": "verified",
                "verified_at": "2026-11-01T00:00:00Z",
            },
        ],
    }


@pytest.mark.unit
def test_entity_model_validation(valid_entity_dict: dict[str, object]) -> None:
    """Entity model parses valid data correctly."""
    entity = Entity.model_validate(valid_entity_dict)
    assert entity.entity_id == "langgraph"
    assert entity.category == RegistryCategory.AGENT_FRAMEWORK
    assert entity.status == RegistryStatus.ACTIVE
    assert len(entity.sources) == 3
    assert entity.sources[0].mapping_confidence == MappingConfidence.VERIFIED


@pytest.mark.unit
def test_invalid_entity_id_rejected() -> None:
    """Entity IDs must match ^[a-z0-9-]{3,64}$."""
    with pytest.raises(ValueError, match="String should match pattern"):
        Entity(
            entity_id="Invalid_ID_With_Caps!",
            display_name="Invalid",
            category=RegistryCategory.LLM_SDK,
            status=RegistryStatus.ACTIVE,
            sources=[
                EntitySource(
                    source="github",
                    key="owner/repo",
                    mapping_confidence=MappingConfidence.DECLARED,
                )
            ],
        )


@pytest.mark.unit
def test_empty_sources_rejected() -> None:
    """An entity must have at least one source."""
    with pytest.raises(ValueError, match="List should have at least 1 item"):
        Entity(
            entity_id="no-sources-tool",
            display_name="No Sources",
            category=RegistryCategory.VECTOR_STORE,
            status=RegistryStatus.ACTIVE,
            sources=[],
        )


@pytest.mark.unit
def test_schema_json_matches_pydantic() -> None:
    """Ensure registry/schema.json exists and is valid JSON Schema."""
    schema_path = Path(__file__).parents[2] / "registry" / "schema.json"
    assert schema_path.exists()
    schema_data = json.loads(schema_path.read_text())
    assert schema_data["title"] == "FootfallEntityRegistry"
    assert "properties" in schema_data["items"]


@pytest.mark.unit
def test_load_seed_registry() -> None:
    """Verify loading the repository's registry/seed.yaml."""
    seed_path = Path(__file__).parents[2] / "registry" / "seed.yaml"
    assert seed_path.exists()
    entities = load_registry(seed_path)
    assert len(entities) > 0
    # Every entity must have unique entity_id
    ids = [e.entity_id for e in entities]
    assert len(ids) == len(set(ids)), "Duplicate entity_ids found in registry"
