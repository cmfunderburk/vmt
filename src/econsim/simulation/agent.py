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
    sprite_type: str = "agent_explorer"  # default fallback
    # Mode & target
    mode: AgentMode = AgentMode.FORAGE
    target: Position | None = None
    # Carrying inventory (in-hand goods not yet deposited)
    carrying: dict[str, int] = field(default_factory=lambda: {"good1": 0, "good2": 0})
    # Stored goods at home
    home_inventory: dict[str, int] = field(default_factory=lambda: {"good1": 0, "good2": 0})
    # Backward compatibility alias (legacy code/tests may still read 'inventory')
    inventory: dict[str, int] = field(init=False, repr=False)
    # Trade partner tracking for bilateral exchange
    trade_partner_id: int | None = field(default=None, init=False, repr=False)
    meeting_point: Position | None = field(default=None, init=False, repr=False)
    is_trading: bool = field(default=False, init=False, repr=False)
    trade_cooldown: int = field(default=0, init=False, repr=False)  # Steps to wait before re-pairing
    partner_cooldowns: dict[int, int] = field(default_factory=dict, init=False, repr=False)  # Per-partner cooldown tracking
    # Bilateral exchange stagnation tracking: utility at last improvement and steps since
    last_trade_mode_utility: float = field(default=0.0, init=False, repr=False)
    trade_stagnation_steps: int = field(default=0, init=False, repr=False)
    force_deposit_once: bool = field(default=False, init=False, repr=False)
    # Unified target selection metadata (resource vs partner) for GUI/testing
    current_unified_task: tuple[str, object] | None = field(default=None, init=False, repr=False)

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
        import os  # Import here to avoid circular import issues
        
        # Respect foraging flag - don't collect if foraging is disabled
        forage_enabled = os.environ.get("ECONSIM_FORAGE_ENABLED", "1") == "1"
        if not forage_enabled:
            return False
            
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

    def withdraw_all(self) -> bool:
        """Move all home inventory goods into carrying. Returns True if withdrawn."""
        moved = False
        for k, v in list(self.home_inventory.items()):
            if v > 0:
                self.carrying[k] += v
                self.home_inventory[k] = 0
                moved = True
        return moved

    def maybe_deposit(self) -> None:
        """Deposit goods when returning home.

        Legacy rule: when bilateral exchange is active we retain goods (no deposit) so
        agents keep inventory to trade; they idle instead. We extend this with a one-time
        forced deposit override (`force_deposit_once`) used when an agent returns home
        after prolonged utility stagnation in bilateral exchange mode.
        """
        if self.mode == AgentMode.RETURN_HOME and self.at_home():
            import os
            exchange_enabled = (
                os.environ.get("ECONSIM_TRADE_DRAFT") == "1" or os.environ.get("ECONSIM_TRADE_EXEC") == "1"
            )

            if not exchange_enabled or self.force_deposit_once:
                any_dep = self.deposit()
                if any_dep:
                    if self.force_deposit_once:
                        # Clear override and go idle post-reset
                        self.force_deposit_once = False
                        self.mode = AgentMode.IDLE
                    else:
                        self.mode = AgentMode.FORAGE
                self.target = None
            else:
                self.mode = AgentMode.IDLE
                self.target = None

    def maybe_withdraw_for_trading(self) -> None:
        """Withdraw home inventory when at home for bilateral exchange mode.""" 
        if self.mode == AgentMode.RETURN_HOME and self.at_home():
            any_withdrawn = self.withdraw_all()
            if any_withdrawn:
                # Transition to IDLE mode - will move randomly to find trading partners
                self.mode = AgentMode.IDLE
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
        - If mode is IDLE: remain idle if foraging disabled; else attempt to find positive ΔU.
        - If mode is FORAGE: scan resources within PERCEPTION_RADIUS.
        - Compute ΔU = U(bundle+δ) - U(bundle). Score = ΔU / (dist + 1e-9).
        - Tie-break: higher ΔU, then shorter dist, then lexicographic (x,y).
        - If no positive ΔU and carrying goods: switch to RETURN_HOME.
          If no carrying goods: switch to IDLE.
        """
        import os  # Import here to avoid circular import issues
        
        if self.mode == AgentMode.RETURN_HOME:
            self.target = (int(self.home_x), int(self.home_y))  # type: ignore[arg-type]
            return
        
        # If currently IDLE and foraging is disabled, stay idle and don't seek targets
        if self.mode == AgentMode.IDLE:
            forage_enabled = os.environ.get("ECONSIM_FORAGE_ENABLED", "1") == "1"
            if not forage_enabled:
                self.target = None
                return

        # Gather candidate resources
        # Evaluate best resource candidate (position, delta, key)
        best_meta, _delta_u, _key = self.compute_best_resource_candidate(grid)
        # Need raw_bundle for prospecting fallback logic
        raw_bundle = self._current_bundle()

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

    # --- Unified / Shared Candidate Computation -----------------
    def compute_best_resource_candidate(self, grid: Grid) -> tuple[Position | None, float, tuple[float,int,int,int] | None]:
        """Return best resource target (position, delta_u, tie_key) without mutating state.

        tie_key matches deterministic ordering: (-ΔU, distance, x, y). Returns (None,0,None)
        if no strictly positive ΔU resource is found within perception radius.
        """
        raw_bundle = self._current_bundle()
        # Epsilon augmentation for baseline utility evaluation
        if raw_bundle[0] == 0.0 or raw_bundle[1] == 0.0:
            bundle = (raw_bundle[0] + EPSILON_UTILITY, raw_bundle[1] + EPSILON_UTILITY)
        else:
            bundle = raw_bundle
        base_u = self.preference.utility(bundle)
        max_dist = default_PERCEPTION_RADIUS
        iterator = getattr(grid, "iter_resources_sorted", grid.iter_resources)()
        best_key: tuple[float,int,int,int] | None = None
        best_pos: Position | None = None
        best_delta = 0.0
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
            if raw_bundle[0] == 0.0 or raw_bundle[1] == 0.0:
                tb0 = test_bundle[0] if test_bundle[0] > 0 else EPSILON_UTILITY
                tb1 = test_bundle[1] if test_bundle[1] > 0 else EPSILON_UTILITY
                test_bundle = (tb0, tb1)
            new_u = self.preference.utility(test_bundle)
            delta_u = new_u - base_u
            if delta_u <= 0.0:
                continue
            key = (-delta_u, dist, rx, ry)
            if best_key is None or key < best_key:
                best_key = key
                best_pos = (rx, ry)
                best_delta = delta_u
        return best_pos, best_delta, best_key

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

    def find_nearby_agents(self, all_agents: list["Agent"]) -> list[tuple["Agent", int]]:
        """Find other agents within perception radius for potential trading.
        
        Returns list of (agent, distance) tuples sorted by distance, then by agent position
        for deterministic tiebreaking. Excludes self from the results.
        """
        from .constants import default_PERCEPTION_RADIUS
        
        candidates = []
        for other_agent in all_agents:
            if other_agent is self:  # Skip self
                continue
                
            distance = self._manhattan(self.x, self.y, other_agent.x, other_agent.y)
            if distance <= default_PERCEPTION_RADIUS:
                candidates.append((other_agent, distance))
        
        # Sort by distance first, then by position for deterministic tiebreaking
        candidates.sort(key=lambda x: (x[1], x[0].x, x[0].y))
        return candidates

    def calculate_meeting_point(self, other_agent: "Agent") -> Position:
        """Calculate the midpoint between this agent and another agent for meeting.
        
        Returns the midpoint coordinates, with ties broken deterministically.
        """
        mid_x = (self.x + other_agent.x) // 2
        mid_y = (self.y + other_agent.y) // 2
        return (mid_x, mid_y)

    def pair_with_agent(self, other_agent: "Agent") -> None:
        """Establish mutual pairing with another agent for trading.
        
        Sets up meeting point and partner tracking for both agents.
        """
        meeting_point = self.calculate_meeting_point(other_agent)
        
        # Set up mutual pairing
        self.trade_partner_id = other_agent.id
        self.meeting_point = meeting_point
        
        other_agent.trade_partner_id = self.id
        other_agent.meeting_point = meeting_point

    def clear_trade_partner(self) -> None:
        """Clear trade partner state without setting cooldowns."""
        self.trade_partner_id = None
        self.meeting_point = None
        self.is_trading = False
        self.trade_cooldown = 3  # Keep general cooldown for immediate re-pairing

    def end_trading_session(self, partner: "Agent") -> None:
        """End trading session with partner and set per-partner cooldowns."""
        # Set per-partner cooldown to prevent immediate re-pairing with same agent
        self.partner_cooldowns[partner.id] = 20
        partner.partner_cooldowns[self.id] = 20
        
        # Clear trade partner state for both agents
        self.clear_trade_partner()
        partner.clear_trade_partner()

    def update_partner_cooldowns(self) -> None:
        """Decrement all partner-specific cooldowns by 1."""
        # Decrement all cooldowns
        for partner_id in list(self.partner_cooldowns.keys()):
            self.partner_cooldowns[partner_id] -= 1
            # Remove expired cooldowns
            if self.partner_cooldowns[partner_id] <= 0:
                del self.partner_cooldowns[partner_id]

    def can_trade_with_partner(self, partner_id: int) -> bool:
        """Check if this agent can trade with a specific partner (no active cooldown)."""
        return partner_id not in self.partner_cooldowns

    def move_toward_meeting_point(self, grid: "Grid") -> None:
        """Move one step toward the established meeting point."""
        if self.meeting_point is None:
            return
            
        target_x, target_y = self.meeting_point
        if (self.x, self.y) == (target_x, target_y):
            return  # Already at meeting point
            
        # Simple greedy movement toward meeting point
        dx = target_x - self.x
        dy = target_y - self.y
        
        # Prioritize horizontal movement if distance is greater
        if abs(dx) > abs(dy):
            self.x += 1 if dx > 0 else -1
        elif dy != 0:
            self.y += 1 if dy > 0 else -1

    def attempt_trade_with_partner(self, other_agent: "Agent", metrics_collector: Any = None, current_step: int = 0) -> bool:
        """(Deprecated execution path) Movement pairing no longer executes trades.

        The unified trade execution pipeline now lives exclusively in intent enumeration
        + `execute_single_intent`. This method is retained only to maintain pairing flow
        and returns False (no trade executed) so movement code can continue without
        performing a swap here.
        """
        return False

    def is_colocated_with(self, other_agent: "Agent") -> bool:
        """Check if this agent is on the same tile as another agent."""
        return self.x == other_agent.x and self.y == other_agent.y


__all__ = ["Agent", "Position", "AgentMode"]
