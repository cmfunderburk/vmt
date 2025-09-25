"""Agent abstraction (Gate 4+ decision capable).

Represents a mobile economic actor collecting typed resources under a
preference function. Maintains distinct *carrying* vs *home* inventories
and mode-driven behavior (FORAGE, RETURN_HOME, IDLE). Decision mode uses
greedy 1-step movement toward the highest scored resource target within
a perception radius, applying epsilon bootstrap to avoid zero-product
stalls for multiplicative utilities.

Capabilities:
* Deterministic target selection (tie-break: −ΔU, distance, x, y)
* Inventory deposit on home arrival
* Mode transitions (forage ↔ return_home ↔ idle)

Deferred:
* Multi-agent trading / interaction rules
* Production / consumption cycles
* Path planning beyond greedy 1-step heuristic
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from econsim.preferences.base import Preference

from .constants import EPSILON_UTILITY, default_PERCEPTION_RADIUS
from .grid import Grid

Position = tuple[int, int]


class AgentMode(str, Enum):  # str for readable serialization/debug
    FORAGE = "forage"
    RETURN_HOME = "return_home"
    IDLE = "idle"


# Perception radius (Manhattan) for decision logic (Gate 4 constant)
PERCEPTION_RADIUS = 8

# Resource type -> inventory good mapping (centralized constant)
RESOURCE_TYPE_TO_GOOD = {
    "A": "good1",
    "B": "good2",
}


@dataclass(slots=True)
class Agent:
    id: int
    x: int
    y: int
    preference: Preference
    # Home position (could differ from spawn later; for now equals initial x,y unless provided)
    home_x: int | None = None  # set non-None in __post_init__
    home_y: int | None = None
    # Mode & target
    mode: AgentMode = AgentMode.FORAGE
    target: Position | None = None
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
    def move_random(
        self, grid: Grid, rng: random.Random
    ) -> None:  # placeholder until decision logic (Phase P3)
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
        if rtype == "A":
            self.carrying["good1"] += 1
            return True
        if rtype == "B":
            self.carrying["good2"] += 1
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

    # --- Decision Logic (Phase P3) -------------------------------
    def _manhattan(self, x1: int, y1: int, x2: int, y2: int) -> int:
        return abs(x1 - x2) + abs(y1 - y2)

    def _current_bundle(self) -> tuple[float, float]:
        # Use carrying goods to reflect marginal decision while foraging
        return float(self.carrying["good1"]), float(self.carrying["good2"])

    def select_target(self, grid: Grid) -> None:
        """Select a resource target or update mode per decision rules.

        Logic (simplified for initial implementation):
        - If mode is RETURN_HOME: keep target at home (unless already there).
        - If mode is IDLE: attempt to find positive ΔU; else remain idle.
        - If mode is FORAGE: scan resources within PERCEPTION_RADIUS.
        - Compute ΔU = U(bundle+δ) - U(bundle). Score = ΔU / (dist + 1e-9).
        - Tie-break: higher ΔU, then shorter dist, then lexicographic (x,y).
        - If no positive ΔU and carrying goods: switch to RETURN_HOME.
          If no carrying goods: switch to IDLE.
        """
        if self.mode == AgentMode.RETURN_HOME:
            self.target = (int(self.home_x), int(self.home_y))  # type: ignore[arg-type]
            return

        # Gather candidate resources
        raw_bundle = self._current_bundle()
        # Epsilon augmentation: if any component zero, lift both by epsilon for utility baseline
        if raw_bundle[0] == 0.0 or raw_bundle[1] == 0.0:
            bundle = (raw_bundle[0] + EPSILON_UTILITY, raw_bundle[1] + EPSILON_UTILITY)
        else:
            bundle = raw_bundle
        base_u = self.preference.utility(bundle)
        best: tuple[float, int, int, int] | None = None  # key = (-delta_u, dist, x, y)
        best_meta: tuple[int, int] | None = None
        max_dist = default_PERCEPTION_RADIUS
    # Use sorted iteration (deterministic ordering helper)
        iterator = getattr(grid, "iter_resources_sorted", grid.iter_resources)()
        for rx, ry, rtype in iterator:
            dist = self._manhattan(self.x, self.y, rx, ry)
            if dist > max_dist:
                continue
            good = RESOURCE_TYPE_TO_GOOD.get(rtype)
            if not good:
                continue
            if good == "good1":
                test_bundle = (bundle[0] + 1.0, bundle[1])
            else:
                test_bundle = (bundle[0], bundle[1] + 1.0)
            # Apply epsilon lifting if the other dimension still effectively zero
            # (Using original raw_bundle to detect zero pre-acquisition state)
            if raw_bundle[0] == 0.0 or raw_bundle[1] == 0.0:
                # ensure both components at least epsilon for consistent marginal evaluation
                tb0 = test_bundle[0] if test_bundle[0] > 0 else EPSILON_UTILITY
                tb1 = test_bundle[1] if test_bundle[1] > 0 else EPSILON_UTILITY
                test_bundle = (tb0, tb1)
            new_u = self.preference.utility(test_bundle)
            delta_u = new_u - base_u
            if delta_u <= 0.0:
                continue
            key = (-delta_u, dist, rx, ry)
            if best is None or key < best:
                best = key
                best_meta = (rx, ry)

        if best_meta is None:
            if self.carrying_total() > 0:
                self.mode = AgentMode.RETURN_HOME
                self.target = (int(self.home_x), int(self.home_y))  # type: ignore[arg-type]
            else:
                self.mode = AgentMode.IDLE
                self.target = None
        else:
            self.target = best_meta
            self.mode = AgentMode.FORAGE

    def step_decision(self, grid: Grid) -> None:
        """Perform one decision+movement+interaction step (without RNG)."""
        # Select/refresh target if none or mode requires it
        if self.target is None or self.mode not in (AgentMode.FORAGE):
            self.select_target(grid)
        # Movement toward target
        if self.target is not None and (self.x, self.y) != self.target:
            tx, ty = self.target
            dx = tx - self.x
            dy = ty - self.y
            # Greedy: horizontal priority if abs(dx) > abs(dy) else vertical
            if abs(dx) > abs(dy):
                self.x += 1 if dx > 0 else -1
            elif dy != 0:
                self.y += 1 if dy > 0 else -1
            else:  # same cell already (shouldn't happen due to earlier check)
                pass
        # Interactions
        collected = self.collect(grid)
        if collected:
            # Clear target so reselection occurs next tick
            self.target = None
        else:
            # If we reached target but resource already gone (collected earlier this tick), retarget immediately.
            if (
                self.target is not None
                and (self.x, self.y) == self.target
                and not grid.has_resource(self.x, self.y)
            ):
                self.target = None
                self.select_target(grid)
        # Deposit if arriving home
        self.maybe_deposit()

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

    # Aggregated inventory (carrying + home) without mutation (future trade / analytics helper)
    def total_inventory(self) -> dict[str, int]:
        if not self.carrying and not self.home_inventory:
            return {}
        # Copy home first, then overlay carrying counts
        combined: dict[str, int] = dict(self.home_inventory)
        for k, v in self.carrying.items():
            if v:
                combined[k] = combined.get(k, 0) + v
        return combined


__all__ = ["Agent", "Position", "AgentMode"]
