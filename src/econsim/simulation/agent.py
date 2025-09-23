"""Agent abstraction (Gate 3).

Minimal placeholder agent:
- Holds position within grid bounds.
- Maintains simple two-good inventory (good1, good2).
- References a Preference (not yet used for movement decisions).
- Provides random movement (4-neighborhood + stay option) and resource collection.

Deferrals:
- Utility-driven movement choices.
- Budgets/prices, optimization routines.
- Multi-agent interactions / trade.
"""
from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from econsim.preferences.base import Preference

from .grid import Grid

Position = tuple[int, int]


@dataclass(slots=True)
class Agent:
    id: int
    x: int
    y: int
    preference: Preference
    inventory: dict[str, int] = field(default_factory=lambda: {"good1": 0, "good2": 0})

    # --- Movement --------------------------------------------------
    def move_random(self, grid: Grid, rng: random.Random) -> None:
        """Move at most one step in 4-neighborhood (or stay). Deterministic under provided RNG."""
        moves = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]
        dx, dy = rng.choice(moves)
        nx, ny = self.x + dx, self.y + dy
        if 0 <= nx < grid.width and 0 <= ny < grid.height:
            self.x, self.y = nx, ny

    # --- Resource Interaction -------------------------------------
    def collect(self, grid: Grid) -> bool:
        """Collect typed resource at current cell if present.

        Mapping policy (Gate 4 Phase P2 groundwork):
        - Resource type 'A' -> inventory['good1']
        - Resource type 'B' -> inventory['good2']
        - Any other type -> ignored for now (future extension)

        Returns True if a recognized resource was collected, else False.
        """
        rtype = grid.take_resource_type(self.x, self.y)
        if rtype is None:
            return False
        if rtype == 'A':
            self.inventory['good1'] += 1
            return True
        if rtype == 'B':
            self.inventory['good2'] += 1
            return True
        # Unknown type: silently ignore (placeholder policy)
        return False

    # --- Serialization (Optional Future Use) ----------------------
    def serialize(self) -> Mapping[str, Any]:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "inventory": dict(self.inventory),
            "preference": self.preference.serialize(),
        }

    # Position helper
    @property
    def pos(self) -> Position:
        return (self.x, self.y)

__all__ = ["Agent", "Position"]
