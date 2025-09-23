"""Agent abstraction (Gate 4 Phase P2 upgrade).

Enhancements over Gate 3:
- Distinct carrying vs home (stored) inventories.
- Agent modes: forage, return_home, idle.
- Optional target coordinate (future decision logic will set/clear).
- Deposit logic when returning home.

Still deferred (Phase P3+):
- Utility-driven target selection & greedy movement.
- Multi-agent interactions / trade.
"""
from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from econsim.preferences.base import Preference

from .grid import Grid

Position = tuple[int, int]


class AgentMode(str, Enum):  # str for readable serialization/debug
    FORAGE = "forage"
    RETURN_HOME = "return_home"
    IDLE = "idle"


@dataclass(slots=True)
class Agent:
    id: int
    x: int
    y: int
    preference: Preference
    # Home position (could differ from spawn later; for now equals initial x,y unless provided)
    home_x: int | None = None
    home_y: int | None = None
    # Mode & target
    mode: AgentMode = AgentMode.FORAGE
    target: Optional[Position] = None
    # Carrying inventory (in-hand goods not yet deposited)
    carrying: dict[str, int] = field(default_factory=lambda: {"good1": 0, "good2": 0})
    # Stored goods at home
    home_inventory: dict[str, int] = field(default_factory=lambda: {"good1": 0, "good2": 0})
    # Backward compatibility alias (legacy code/tests may still read 'inventory')
    inventory: dict[str, int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # If home not explicitly set, default to spawn coords
        if self.home_x is None:
            self.home_x = self.x
        if self.home_y is None:
            self.home_y = self.y
        # Backward compatibility: expose carrying as 'inventory'
        object.__setattr__(self, "inventory", self.carrying)

    # --- Movement --------------------------------------------------
    def move_random(self, grid: Grid, rng: random.Random) -> None:  # placeholder until decision logic (Phase P3)
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
            self.carrying['good1'] += 1
            return True
        if rtype == 'B':
            self.carrying['good2'] += 1
            return True
        # Unknown type: silently ignore (placeholder policy)
        return False

    # --- Home / Deposit Logic ------------------------------------
    def at_home(self) -> bool:
        return self.x == self.home_x and self.y == self.home_y

    def carrying_total(self) -> int:
        return sum(self.carrying.values())

    def deposit(self) -> bool:
        """Move all carried goods into home inventory. Returns True if any deposited."""
        moved = False
        for k, v in list(self.carrying.items()):
            if v > 0:
                self.home_inventory[k] += v
                self.carrying[k] = 0
                moved = True
        return moved

    def maybe_deposit(self) -> None:
        if self.mode == AgentMode.RETURN_HOME and self.at_home():
            any_dep = self.deposit()
            # Transition after deposit: if we still expect to forage (carrying now zero)
            if any_dep:
                # Decision logic will set mode appropriately later; default to FORAGE for now
                self.mode = AgentMode.FORAGE
                self.target = None

    # --- Serialization (Optional Future Use) ----------------------
    def serialize(self) -> Mapping[str, Any]:
        # Provide backward compatible 'inventory' (carrying) plus new fields
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "home": (self.home_x, self.home_y),
            "mode": self.mode.value,
            "target": self.target,
            "carrying": dict(self.carrying),
            "home_inventory": dict(self.home_inventory),
            "inventory": dict(self.carrying),  # legacy alias
            "preference": self.preference.serialize(),
        }

    # Position helper
    @property
    def pos(self) -> Position:
        return (self.x, self.y)

__all__ = ["Agent", "Position", "AgentMode"]
