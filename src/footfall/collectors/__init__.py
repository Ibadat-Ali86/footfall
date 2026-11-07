"""Footfall data collectors package.

Provides collectors for GitHub, npm, PyPI, Hugging Face, and Hacker News.
"""

from __future__ import annotations

from footfall.collectors.base import (
    BaseCollector,
    HostSecurityError,
    ResponseSizeExceededError,
    Snapshot,
    SnapshotQuality,
)
from footfall.collectors.github import GitHubCollector
from footfall.collectors.hf import HuggingFaceCollector
from footfall.collectors.hn import HackerNewsCollector
from footfall.collectors.npm import NpmCollector
from footfall.collectors.pypi import PyPICollector

__all__ = [
    "BaseCollector",
    "GitHubCollector",
    "HackerNewsCollector",
    "HostSecurityError",
    "HuggingFaceCollector",
    "NpmCollector",
    "PyPICollector",
    "ResponseSizeExceededError",
    "Snapshot",
    "SnapshotQuality",
]
