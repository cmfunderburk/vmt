"""Test registry abstraction (Phase 1 scaffold)."""
from __future__ import annotations

from typing import Callable, List, Dict

from .types import TestConfiguration, RegistryValidationResult


class TestRegistry:
    def __init__(
        self,
        builtin_source: Callable[[], List[TestConfiguration]],
        custom_source: Callable[[], List[TestConfiguration]] | None = None,
    ) -> None:
        self._builtin_source = builtin_source
        self._custom_source = custom_source
        self._cache: Dict[int, TestConfiguration] = {}

    def _load(self) -> None:
        if self._cache:
            return
        all_items: List[TestConfiguration] = list(self._builtin_source())
        if self._custom_source:
            all_items.extend(self._custom_source())
        self._cache = {c.id: c for c in all_items}

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
        # Placeholder duplication check by label
        labels = {}
        duplicates: List[str] = []
        for cfg in self._cache.values():
            if cfg.label in labels:
                duplicates.append(cfg.label)
            else:
                labels[cfg.label] = 1
        return RegistryValidationResult(ok=not duplicates, duplicates=duplicates, missing=[])
