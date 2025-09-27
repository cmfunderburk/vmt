"""Test registry abstraction (Step 6 implementation).

Provides aggregation of builtin + custom test configurations with:
* Lazy loading & caching
* Duplicate detection (ID and label uniqueness)
* Lookup helpers by id / label
* Validation summary via `RegistryValidationResult`

The registry does not (yet) auto‑refresh on filesystem changes; callers may
explicitly invoke `reload()` if sources are dynamic.
"""
from __future__ import annotations

from typing import Callable, List, Dict

from .types import TestConfiguration, RegistryValidationResult


class TestRegistry:
    """In‑memory index of available test configurations."""

    def __init__(
        self,
        builtin_source: Callable[[], List[TestConfiguration]],
        custom_source: Callable[[], List[TestConfiguration]] | None = None,
    ) -> None:
        self._builtin_source = builtin_source
        self._custom_source = custom_source
        self._cache: Dict[int, TestConfiguration] = {}

    # ------------------------------------------------------------------
    # Loading & Cache Management
    # ------------------------------------------------------------------
    def reload(self) -> None:
        """Force cache rebuild from sources."""
        self._cache.clear()
        self._load(force=True)

    def _load(self, force: bool = False) -> None:
        if self._cache and not force:
            return
        all_items: List[TestConfiguration] = list(self._builtin_source())
        if self._custom_source:
            all_items.extend(self._custom_source())
        # Build cache; later duplicates will be flagged in validate()
        ordered: Dict[int, TestConfiguration] = {}
        for cfg in all_items:
            # Keep first occurrence of an ID to preserve deterministic ordering
            if cfg.id not in ordered:
                ordered[cfg.id] = cfg
        self._cache = ordered

    def all(self) -> Dict[int, TestConfiguration]:  # pragma: no cover - trivial
        self._load()
        return dict(self._cache)

    def by_id(self, test_id: int) -> TestConfiguration | None:  # pragma: no cover - trivial
        self._load()
        return self._cache.get(test_id)

    def by_label(self, label: str) -> TestConfiguration | None:  # pragma: no cover - placeholder
        self._load()
        for cfg in self._cache.values():
            if cfg.label == label:
                return cfg
        return None

    def validate(self) -> RegistryValidationResult:
        self._load()
        label_seen: Dict[str, int] = {}
        id_seen: Dict[int, int] = {}
        duplicates: List[str] = []
        # ID collisions are theoretically guarded by dict insertion, but we still
        # inspect original combined list by re-calling sources (non-cached) to
        # detect qualitative duplication for diagnostics.
        combined: List[TestConfiguration] = list(self._builtin_source())
        if self._custom_source:
            combined.extend(self._custom_source())
        for cfg in combined:
            if cfg.id in id_seen and cfg.label not in duplicates:
                duplicates.append(cfg.label)
            id_seen[cfg.id] = 1
            if cfg.label in label_seen and cfg.label not in duplicates:
                duplicates.append(cfg.label)
            label_seen[cfg.label] = 1
        return RegistryValidationResult(ok=not duplicates, duplicates=sorted(duplicates), missing=[])
