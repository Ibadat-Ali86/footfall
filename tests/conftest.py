"""conftest.py — shared pytest fixtures."""
from __future__ import annotations

import pytest


@pytest.fixture()
def sample_entity_id() -> str:
    """A canonical entity_id used across unit tests."""
    return "langgraph"
