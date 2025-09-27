"""Transitional adapters bridging monolith to new registry/executor (Phase 1 scaffold)."""
from __future__ import annotations

from typing import List

from .types import TestConfiguration
from .registry import TestRegistry


def _placeholder_builtin_source() -> List[TestConfiguration]:  # pragma: no cover - placeholder
    # This will be replaced with real extraction of builtin test config logic.
    return []


def load_registry_from_monolith() -> TestRegistry:
    """Construct a registry from legacy sources (placeholder)."""
    return TestRegistry(builtin_source=_placeholder_builtin_source)
