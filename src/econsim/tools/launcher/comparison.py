"""Comparison selection logic (Phase 1 scaffold)."""
from __future__ import annotations

from typing import List


class ComparisonController:
    def __init__(self, max_selections: int = 4) -> None:
        self._max = max_selections
        self._selected: list[str] = []

    def add(self, label: str) -> bool:
        if label in self._selected:
            return True  # idempotent add
        if len(self._selected) >= self._max:
            return False
        self._selected.append(label)
        return True

    def remove(self, label: str) -> bool:
        if label not in self._selected:
            return False
        self._selected.remove(label)
        return True

    def clear(self) -> None:  # pragma: no cover - trivial
        self._selected.clear()

    def selected(self) -> List[str]:  # pragma: no cover - trivial
        return list(self._selected)

    def can_launch(self) -> bool:
        return len(self._selected) >= 2
