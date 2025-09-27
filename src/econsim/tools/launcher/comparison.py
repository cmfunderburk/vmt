"""Comparison selection state management (Step 7 / Gate G6).

Pure selection logic independent of registry, operating only on string labels.
Maintains a bounded, ordered, duplicate‑free list of labels representing tests
chosen for side‑by‑side comparison.

Key Behaviors:
* Deterministic insertion ordering (list preserves order of acceptance).
* Capacity enforcement with informative result codes.
* Duplicate additions are idempotent rejections (explicit reason provided).
* Validation: comparison launch is valid with >= 2 selections.

All methods are O(n) with small n (max default 4). The simplicity and
predictability outweigh any micro-optimizations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class AddResult:
    """Result of an add attempt.

    added: True if label appended.
    reason: Failure category when added is False (duplicate | capacity | invalid).
    """

    added: bool
    reason: str | None = None

    def ok(self) -> bool:  # pragma: no cover - trivial
        return self.added


class ComparisonController:
    __slots__ = ("_max", "_labels")

    def __init__(self, max_selections: int = 4) -> None:
        if max_selections < 2:
            raise ValueError("max_selections must be >= 2 (baseline + candidate)")
        self._max = int(max_selections)
        self._labels: list[str] = []

    # Mutation ---------------------------------------------------------
    def add(self, label: str) -> AddResult:
        if not label.strip():
            return AddResult(False, "invalid")
        if label in self._labels:
            return AddResult(False, "duplicate")
        if len(self._labels) >= self._max:
            return AddResult(False, "capacity")
        self._labels.append(label)
        return AddResult(True, None)

    def remove(self, label: str) -> bool:
        try:
            self._labels.remove(label)
            return True
        except ValueError:
            return False

    def clear(self) -> None:  # pragma: no cover - trivial
        if self._labels:
            self._labels.clear()

    # Introspection ----------------------------------------------------
    def selected(self) -> List[str]:
        return list(self._labels)

    def can_launch(self) -> bool:
        return len(self._labels) >= 2

    def count(self) -> int:
        return len(self._labels)

    def capacity(self) -> int:
        return self._max

    def remaining(self) -> int:
        return self._max - len(self._labels)

    def contains(self, label: str) -> bool:
        return label in self._labels

    def snapshot(self) -> dict[str, object]:
        return {
            "labels": list(self._labels),
            "capacity": self._max,
            "count": len(self._labels),
            "remaining": self.remaining(),
            "can_launch": self.can_launch(),
        }

    # Dunder -----------------------------------------------------------
    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._labels)

    def __iter__(self):  # pragma: no cover - trivial
        return iter(self._labels)

    def __repr__(self) -> str:  # pragma: no cover - deterministic simple repr
        return f"ComparisonController(max={self._max}, labels={self._labels!r})"


__all__ = ["ComparisonController", "AddResult"]
