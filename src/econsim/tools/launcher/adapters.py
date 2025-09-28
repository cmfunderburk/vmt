"""Transitional adapter layer (Step 9 / Gate G8).

Bridges existing monolith framework test definitions (`framework.test_configs`)
into the new launcher module ecosystem without modifying their source. Once the
monolith delegates all test configuration access through `TestRegistry`, the UI
and future CLI will share a single authoritative configuration index.

This file is intentionally light-weight and will be removed / reduced after the
full UI refactor (Phase 3 / Part 2) when a consolidated configuration loading
pipeline is established.
"""
from __future__ import annotations

from typing import List

from .types import TestConfiguration
from .registry import TestRegistry


def load_registry_from_monolith() -> TestRegistry:
    """Construct a registry from legacy sources (placeholder)."""
    """Create a `TestRegistry` from the legacy framework test configs.

    Imports `framework.test_configs` lazily to avoid import side effects during
    unit tests that do not require the full monolith. This function should be
    the *only* bridge the monolith uses to obtain a registry in transitional
    Phase 2.4.
    """

    # Import framework test configs. Try new location first, fallback to legacy.
    try:  # New location (Phase 1.3 migration)
        from .framework import test_configs as legacy  # type: ignore
    except ModuleNotFoundError:
        # Fallback to legacy location for compatibility
        try:  # pragma: no cover - import branch
            from MANUAL_TESTS.framework import test_configs as legacy  # type: ignore
        except ModuleNotFoundError:  # Fallback: attempt relative path injection
            import sys
            from pathlib import Path
            root = Path(__file__).resolve().parents[4]  # src/econsim/tools/launcher -> repo root
            manual_dir = root / "MANUAL_TESTS" / "framework"
            if manual_dir.exists():
                sys.path.insert(0, str(manual_dir.parent.parent))  # add repo root
                from MANUAL_TESTS.framework import test_configs as legacy  # type: ignore
            else:  # If still unavailable, propagate original error
                raise

    def builtin_source() -> List[TestConfiguration]:
        out: List[TestConfiguration] = []
        for cfg in legacy.ALL_TEST_CONFIGS.values():
            # Map legacy TestConfiguration to launcher TestConfiguration (reduced schema)
            out.append(
                TestConfiguration(
                    id=cfg.id,
                    label=cfg.name,  # Using human-readable name as label
                    mode="framework",  # We'll treat all as framework-capable; original mode still accessible
                    file=None,  # Path not currently tracked at this layer; UI/executor may supply
                    meta={
                        "description": cfg.description,
                        "grid_size": cfg.grid_size,
                        "agent_count": cfg.agent_count,
                        "resource_density": cfg.resource_density,
                        "perception_radius": cfg.perception_radius,
                        "preference_mix": cfg.preference_mix,
                        "seed": cfg.seed,
                    },
                )
            )
        return out

    # Custom source placeholder (custom tests will be integrated later by using discovery module)
    def custom_source() -> List[TestConfiguration]:  # pragma: no cover - trivial placeholder
        return []

    return TestRegistry(builtin_source=builtin_source, custom_source=custom_source)


__all__ = ["load_registry_from_monolith"]
