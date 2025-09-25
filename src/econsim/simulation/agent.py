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
    # Sprite identifier for visual rendering (randomly assigned at creation)
    sprite_type: str = "agent_emoji_builder"  # default fallback
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
            # No single resource gives positive ΔU - try prospecting for Leontief agents
            prospect_target = self._try_leontief_prospecting(grid, raw_bundle)
            if prospect_target is not None:
                self.target = prospect_target
                self.mode = AgentMode.FORAGE
            elif self.carrying_total() > 0:
                self.mode = AgentMode.RETURN_HOME
                self.target = (int(self.home_x), int(self.home_y))  # type: ignore[arg-type]
            else:
                self.mode = AgentMode.IDLE
                self.target = None
        else:
            self.target = best_meta
            self.mode = AgentMode.FORAGE

    def _try_leontief_prospecting(self, grid: Grid, raw_bundle: tuple[float, float]) -> Position | None:
        """Attempt prospecting behavior for Leontief agents when no single resource gives positive ΔU.
        
        Returns the best first resource to collect when building a complementary bundle,
        or None if no viable prospects exist.
        """
        # Only apply prospecting to Leontief preference agents
        if getattr(self.preference, 'TYPE_NAME', '') != 'leontief':
            return None
        
        best_prospect: tuple[float, int, int, int] | None = None  # key = (-score, dist, x, y)
        best_prospect_pos: Position | None = None
        max_dist = default_PERCEPTION_RADIUS
        
        # Use sorted iteration for deterministic ordering
        iterator = getattr(grid, "iter_resources_sorted", grid.iter_resources)()
        
        for rx, ry, rtype in iterator:
            dist_to_resource = self._manhattan(self.x, self.y, rx, ry)
            if dist_to_resource > max_dist:
                continue
            
            good = RESOURCE_TYPE_TO_GOOD.get(rtype)
            if not good:
                continue
                
            # Find the best complementary resource for this starting resource
            prospect_score = self._calculate_prospect_score(
                (rx, ry), rtype, grid, raw_bundle, max_dist
            )
            
            if prospect_score > 0.0:
                key = (-prospect_score, dist_to_resource, rx, ry)
                if best_prospect is None or key < best_prospect:
                    best_prospect = key
                    best_prospect_pos = (rx, ry)
        
        return best_prospect_pos

    def _calculate_prospect_score(
        self, 
        resource_pos: Position, 
        resource_type: str, 
        grid: Grid, 
        current_bundle: tuple[float, float],
        max_dist: int
    ) -> float:
        """Calculate prospect score for a resource when building complementary bundles.
        
        Score = expected utility gain from collecting both complementary resources / total effort
        """
        rx, ry = resource_pos
        dist_to_first = self._manhattan(self.x, self.y, rx, ry)
        
        # Find nearest complementary resource
        complement_pos, complement_dist = self._find_nearest_complement_resource(
            resource_pos, resource_type, grid, max_dist
        )
        
        if complement_pos is None:
            return 0.0  # No complement available
        
        # Calculate total effort: home -> resource1 -> resource2 -> home
        cx, cy = complement_pos
        dist_between = self._manhattan(rx, ry, cx, cy)
        dist_home = self._manhattan(cx, cy, int(self.home_x), int(self.home_y))  # type: ignore[arg-type]
        total_effort = dist_to_first + dist_between + dist_home
        
        # Calculate expected utility gain from collecting both resources
        first_good = RESOURCE_TYPE_TO_GOOD[resource_type]
        complement_type = self._peek_resource_type_at(grid, cx, cy)
        if complement_type is None:
            return 0.0
            
        second_good = RESOURCE_TYPE_TO_GOOD.get(complement_type)
        if second_good is None:
            return 0.0
        
        # Simulate final bundle after collecting both resources
        final_bundle = [current_bundle[0], current_bundle[1]]
        if first_good == "good1":
            final_bundle[0] += 1.0
        else:
            final_bundle[1] += 1.0
            
        if second_good == "good1":
            final_bundle[0] += 1.0
        else:
            final_bundle[1] += 1.0
        
        # Calculate utility gain (use epsilon lift for consistent evaluation)
        base_bundle = current_bundle
        if base_bundle[0] == 0.0 or base_bundle[1] == 0.0:
            base_bundle = (base_bundle[0] + EPSILON_UTILITY, base_bundle[1] + EPSILON_UTILITY)
            
        final_bundle_tuple = (final_bundle[0], final_bundle[1])
        if final_bundle[0] == 0.0 or final_bundle[1] == 0.0:
            final_bundle_tuple = (final_bundle[0] + EPSILON_UTILITY, final_bundle[1] + EPSILON_UTILITY)
        
        base_utility = self.preference.utility(base_bundle)
        final_utility = self.preference.utility(final_bundle_tuple)
        utility_gain = final_utility - base_utility
        
        # Score = utility gain per unit effort
        return utility_gain / (total_effort + 1e-9)

    def _find_nearest_complement_resource(
        self, 
        resource_pos: Position, 
        resource_type: str, 
        grid: Grid, 
        max_dist: int
    ) -> tuple[Position | None, int]:
        """Find the nearest resource that complements the given resource type.
        
        Returns (position, distance) or (None, 0) if no complement found.
        """
        rx, ry = resource_pos
        current_good = RESOURCE_TYPE_TO_GOOD.get(resource_type)
        if current_good is None:
            return None, 0
        
        # Determine what complementary good we need
        complement_good = "good2" if current_good == "good1" else "good1"
        complement_resource_type = None
        for rtype, good in RESOURCE_TYPE_TO_GOOD.items():
            if good == complement_good:
                complement_resource_type = rtype
                break
        
        if complement_resource_type is None:
            return None, 0
        
        best_complement: tuple[int, int, int] | None = None  # (dist, x, y)
        iterator = getattr(grid, "iter_resources_sorted", grid.iter_resources)()
        
        for cx, cy, ctype in iterator:
            if ctype != complement_resource_type:
                continue
            if (cx, cy) == resource_pos:  # Skip the same resource
                continue
                
            dist = self._manhattan(rx, ry, cx, cy)
            if dist > max_dist * 2:  # Allow longer distances for complements
                continue
                
            key = (dist, cx, cy)
            if best_complement is None or key < best_complement:
                best_complement = key
        
        if best_complement is None:
            return None, 0
        
        return (best_complement[1], best_complement[2]), best_complement[0]

    def _peek_resource_type_at(self, grid: Grid, x: int, y: int) -> str | None:
        """Non-destructively peek at the resource type at a given position."""
        for rx, ry, rtype in grid.iter_resources():
            if rx == x and ry == y:
                return rtype
        return None

    def step_decision(self, grid: Grid) -> bool:
        """Perform one decision+movement+interaction step (without RNG).

        Returns True if the agent actively foraged (collected a resource this tick),
        False otherwise. This return value is advisory and ignored by existing
        callers that do not capture it (backward compatible).
        """
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
        return bool(collected)

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
