"""Economic agent with decision-making, resource collection, and bilateral trading.

Mobile economic actor that collects typed resources based on preference functions.
Maintains separate carrying and home inventories with mode-driven behavior 
(FORAGE, RETURN_HOME, IDLE, MOVE_TO_PARTNER). Uses unified target selection 
with distance-discounted utility for both resources and trading partners.

Core Features:
* Deterministic target selection with configurable distance scaling
* Bilateral exchange with partner pairing and meeting points
* Epsilon-bootstrapped utility for zero-bundle edge cases
* Mode transitions with structured debug logging

Architecture:
* Factory construction via SimConfig
* Deterministic tie-breaking: (-ΔU, distance, x, y)
* O(n) per-step complexity with spatial indexing
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING

from econsim.preferences.base import Preference

from .constants import EPSILON_UTILITY, default_PERCEPTION_RADIUS
from .grid import Grid

if TYPE_CHECKING:
    from ..observability.registry import ObserverRegistry
    from ..observability.event_buffer import StepEventBuffer
    from .components.event_emitter import AgentEventEmitter
    from .components.inventory import AgentInventory
    from .components.trading_partner import TradingPartner
    from .components.target_selection import ResourceTargetStrategy

Position = tuple[int, int]


class AgentMode(str, Enum):  # str for readable serialization/debug
    """Agent behavioral modes determining movement and interaction patterns.
    
    FORAGE: Actively seek and collect resources based on utility maximization
    RETURN_HOME: Move toward home position to deposit carried goods
    IDLE: Stationary or random movement, available for partner pairing
    MOVE_TO_PARTNER: Move toward established meeting point for trading
    """
    FORAGE = "forage"
    RETURN_HOME = "return_home"
    IDLE = "idle"
    MOVE_TO_PARTNER = "move_to_partner"


# Manhattan distance perception radius for resource detection
PERCEPTION_RADIUS = 8

# A→good1, B→good2
RESOURCE_TYPE_TO_GOOD = {
    "A": "good1",
    "B": "good2",
}


@dataclass(slots=True)
class Agent:
    """Economic agent with resource collection and bilateral trading capabilities.
    
    Maintains dual inventory system (carrying + home) and supports multiple
    behavioral modes including resource foraging and partner-based trading.
    Uses unified target selection with distance-discounted utility scoring.
    """
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
    
    # Trade partner tracking for bilateral exchange (now handled by properties)
    # Bilateral exchange stagnation tracking: utility at last improvement and steps since
    last_trade_mode_utility: float = field(default=0.0, init=False, repr=False)
    trade_stagnation_steps: int = field(default=0, init=False, repr=False)
    
    # Refactored components (initialized in __post_init__)
    _event_emitter: 'AgentEventEmitter | None' = field(default=None, init=False, repr=False)
    _inventory: 'AgentInventory | None' = field(default=None, init=False, repr=False)
    _trading_partner: 'TradingPartner | None' = field(default=None, init=False, repr=False)
    _target_selection: 'ResourceTargetStrategy | None' = field(default=None, init=False, repr=False)
    force_deposit_once: bool = field(default=False, init=False, repr=False)
    # Target churn tracking for instrumentation
    _recent_retargets: list[int] = field(default_factory=list, init=False, repr=False)  # Steps when target changed
    
    def _track_target_change(self, new_target: Position | None, step: int) -> None:
        """Track target changes for behavioral churn analysis.
        
        Maintains history of recent target changes for behavioral instrumentation
        and emits retargeting events via observer pattern.
        """
        if new_target != self.target:
            self._recent_retargets.append(step)
            # Keep only recent retargets (last 100 steps)
            if len(self._recent_retargets) > 100:
                self._recent_retargets = self._recent_retargets[-100:]
            
            # Track retargeting for behavioral analysis using observer pattern
            try:
                from ..observability.observer_logger import get_global_observer_logger
                logger = get_global_observer_logger()
                if logger:
                    logger.track_agent_retargeting(step, self.id)
            except Exception:
                pass  # Don't break simulation if logging fails
    # Unified target selection metadata (resource vs partner) for GUI/testing
    current_unified_task: tuple[str, object] | None = field(default=None, init=False, repr=False)
    # Unified selection commitment tracking:
    unified_commitment: dict[str, object] = field(default_factory=dict, init=False, repr=False)
    unified_commitment_started: int = field(default=0, init=False, repr=False)
    
    # Refactored components (feature flagged)
    _movement: Any = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize derived fields and backward compatibility aliases."""
        # If home not explicitly set, default to spawn coords
        if self.home_x is None:
            self.home_x = self.x
        if self.home_y is None:
            self.home_y = self.y
        # Backward compatibility: expose carrying as 'inventory'
        object.__setattr__(self, "inventory", self.carrying)
        
        # Initialize refactored components
        from .components.movement import AgentMovement
        self._movement = AgentMovement(self.id)
        
        from .components.event_emitter import AgentEventEmitter
        object.__setattr__(self, "_event_emitter", AgentEventEmitter(self.id))
        
        from .components.inventory import AgentInventory
        self._inventory = AgentInventory(self.preference)
        # CRITICAL: Set up aliases (not copies!)
        object.__setattr__(self, "carrying", self._inventory.carrying)
        object.__setattr__(self, "home_inventory", self._inventory.home_inventory)
        object.__setattr__(self, "inventory", self._inventory.inventory)
        
        # Initialize trading partner component
        from .components.trading_partner import TradingPartner
        self._trading_partner = TradingPartner(self.id)
        
        # Initialize target selection component (feature flagged)
        from .agent_flags import is_refactor_enabled
        if is_refactor_enabled("target_selection"):
            from .components.target_selection import ResourceTargetStrategy
            self._target_selection = ResourceTargetStrategy()
    
    # Trading partner properties that delegate to component
    @property
    def trade_partner_id(self) -> int | None:
        """Get trade partner ID from component."""
        return self._trading_partner.trade_partner_id
    
    @trade_partner_id.setter
    def trade_partner_id(self, value: int | None) -> None:
        """Set trade partner ID in component."""
        self._trading_partner.trade_partner_id = value
    
    @property
    def meeting_point(self) -> Position | None:
        """Get meeting point from component."""
        return self._trading_partner.meeting_point
    
    @meeting_point.setter
    def meeting_point(self, value: Position | None) -> None:
        """Set meeting point in component."""
        self._trading_partner.meeting_point = value
    
    @property
    def is_trading(self) -> bool:
        """Get trading status from component."""
        return self._trading_partner.is_trading
    
    @is_trading.setter
    def is_trading(self, value: bool) -> None:
        """Set trading status in component."""
        self._trading_partner.is_trading = value
    
    @property
    def trade_cooldown(self) -> int:
        """Get trade cooldown from component."""
        return self._trading_partner.trade_cooldown
    
    @trade_cooldown.setter
    def trade_cooldown(self, value: int) -> None:
        """Set trade cooldown in component."""
        self._trading_partner.trade_cooldown = value
    
    @property
    def partner_cooldowns(self) -> dict[int, int]:
        """Get partner cooldowns from component."""
        return self._trading_partner.partner_cooldowns
    
    @partner_cooldowns.setter
    def partner_cooldowns(self, value: dict[int, int]) -> None:
        """Set partner cooldowns in component."""
        self._trading_partner.partner_cooldowns = value

    def _debug_log_mode_change(self, old_mode: AgentMode, new_mode: AgentMode, reason: str = "") -> None:
        """Log agent mode transitions for debugging via observer events."""
        try:
            from ..observability.observer_logger import get_global_observer_logger
            from ..observability.events import DebugLogEvent
            
            logger = get_global_observer_logger()
            if logger is not None:
                # Add context about agent state
                carrying_count = sum(self.carrying.values()) 
                capacity_info = f"carrying: {carrying_count}"  # VMT agents have unlimited carrying capacity
                if self.target:
                    target_info = f", target: {self.target}"
                else:
                    target_info = ""
                context = f"{capacity_info}{target_info}"
                if reason:
                    context = f"({reason}), {context}"
                
                # Emit debug event for mode switch
                debug_msg = f"MODE_SWITCH agent={self.id} {old_mode.value}->{new_mode.value} {context}"
                debug_event = DebugLogEvent.create(step=0, category="agent_mode", message=debug_msg)
                logger.observer_registry.notify(debug_event)
        except Exception:  # pragma: no cover
            pass  # Graceful degradation when observer system not available

    def _set_mode(self, new_mode: AgentMode, reason: str = "", observer_registry: Optional['ObserverRegistry'] = None, step_number: int = 0, event_buffer: Optional['StepEventBuffer'] = None) -> None:
        """
        Centralized mode setter that emits AgentModeChangeEvent.
        
        Args:
            new_mode: Target AgentMode
            reason: Brief description for analytics (e.g., "resource_found", "returned_home")
            observer_registry: Event registry (optional, for testing - immediate mode)
            step_number: Current step for event context
            event_buffer: Event buffer for batched processing (preferred for performance)
        """
        if self.mode == new_mode:
            return  # No-op if mode unchanged
            
        old_mode = self.mode
        self._debug_log_mode_change(old_mode, new_mode, reason)
        self.mode = new_mode
        
        # Emit mode change event
        self._event_emitter.emit_mode_change(
            old_mode.value, new_mode.value, reason, step_number, observer_registry, event_buffer
        )

    # --- Movement --------------------------------------------------
    def move_random(
        self, grid: Grid, rng: random.Random
    ) -> None:
        """Move one step randomly in 4-neighborhood or stay put."""
        new_pos = self._movement.move_random((self.x, self.y), grid, rng)
        self.x, self.y = new_pos

    # --- Resource Interaction -------------------------------------
    def collect(self, grid: Grid, step: int = -1, observer_registry: Optional['ObserverRegistry'] = None) -> bool:
        """Collect resource at current position if foraging enabled.
        
        Maps resource types: A→good1, B→good2. Tracks acquisition for 
        behavioral logging when step >= 0.
        
        Args:
            grid: Grid for resource access
            step: Current step number for logging and events
            observer_registry: Event registry for resource collection events
        
        Returns:
            True if resource collected, False otherwise.
        """
        import os  # Import here to avoid circular import issues
        
        # Respect foraging flag - don't collect if foraging is disabled
        forage_enabled = os.environ.get("ECONSIM_FORAGE_ENABLED", "1") == "1"
        if not forage_enabled:
            return False
            
        rtype = grid.take_resource_type(self.x, self.y)
        if rtype is None:
            return False
        # Collect resource using inventory component
        self._inventory.collect_resource(rtype)
        
        # Track acquisition for behavioral analysis using observer pattern
        if step >= 0:
            try:
                from ..observability.observer_logger import get_global_observer_logger
                logger = get_global_observer_logger()
                if logger:
                    # Use log_resource_event for resource acquisition tracking
                    logger.log_resource_event(
                        event_type="pickup",
                        position=(self.x, self.y),
                        resource_type=rtype,
                        agent_id=self.id,
                        step=step
                    )
            except Exception:
                pass  # Don't break simulation if logging fails
        
        # Emit resource collection event
        self._event_emitter.emit_resource_collection(
            self.x, self.y, rtype, step if step >= 0 else 0, observer_registry
        )
        return True
        # Unknown resource type ignored
        return False

    # --- Home / Deposit Logic ------------------------------------
    def at_home(self) -> bool:
        """Check if agent is currently at their home position."""
        return self.x == self.home_x and self.y == self.home_y

    def carrying_total(self) -> int:
        """Return total number of goods currently being carried."""
        return self._inventory.carrying_total()
    
    def current_utility(self) -> float:
        """Calculate current utility from total wealth (carrying + home inventory)."""
        return self._inventory.current_utility()

    def deposit(self) -> bool:
        """Move all carried goods into home inventory. Returns True if any deposited."""
        return self._inventory.deposit_all()

    def withdraw_all(self) -> bool:
        """Move all home inventory goods into carrying. Returns True if withdrawn."""
        return self._inventory.withdraw_all()

    def maybe_deposit(self, observer_registry: Optional['ObserverRegistry'] = None, step_number: int = 0) -> None:
        """Deposit carried goods at home and transition to appropriate mode.
        
        Behavioral transitions after deposit:
        - Both forage + exchange enabled: withdraw goods and continue foraging
        - Only forage enabled: continue foraging (keep goods at home)
        - Only exchange enabled: withdraw goods for trading
        - Neither enabled: idle at home
        - force_deposit_once override: deposit and idle (stagnation recovery)
        
        Args:
            observer_registry: Event registry for mode change notifications
            step_number: Current step for event context
        """
        if self.mode == AgentMode.RETURN_HOME and self.at_home():
            import os
            forage_enabled = os.environ.get("ECONSIM_FORAGE_ENABLED", "1") == "1"
            exchange_enabled = (
                os.environ.get("ECONSIM_TRADE_DRAFT") == "1" or 
                os.environ.get("ECONSIM_TRADE_EXEC") == "1"
            )
            
            # Handle forced deposit override (from stagnation)
            if self.force_deposit_once:
                any_deposited = self.deposit()
                if any_deposited:
                    self.force_deposit_once = False
                self._set_mode(AgentMode.IDLE, "force_deposit", observer_registry, step_number)
            else:
                # Normal deposit logic based on enabled behaviors
                any_deposited = self.deposit()
                if any_deposited:
                    if forage_enabled and exchange_enabled:
                        self.withdraw_all()
                        self._set_mode(AgentMode.FORAGE, "deposited_goods", observer_registry, step_number)
                    elif forage_enabled and not exchange_enabled:
                        self._set_mode(AgentMode.FORAGE, "deposited_goods", observer_registry, step_number)
                    elif not forage_enabled and exchange_enabled:
                        self.withdraw_all()
                        self._set_mode(AgentMode.IDLE, "deposited_goods", observer_registry, step_number)
                    else:
                        self._set_mode(AgentMode.IDLE, "deposited_goods", observer_registry, step_number)
                else:
                    # No goods to deposit - transition to appropriate mode
                    if forage_enabled:
                        self._set_mode(AgentMode.FORAGE, "phase_change", observer_registry, step_number)
                    elif exchange_enabled:
                        self.withdraw_all()
                        self._set_mode(AgentMode.IDLE, "phase_change", observer_registry, step_number)
                    else:
                        self._set_mode(AgentMode.IDLE, "phase_change", observer_registry, step_number)
                self.target = None
            return

    def maybe_withdraw_for_trading(self, observer_registry: Optional['ObserverRegistry'] = None, step_number: int = 0) -> None:
        """Withdraw home inventory when at home for bilateral exchange mode.
        
        Args:
            observer_registry: Event registry for mode change notifications
            step_number: Current step for event context
        """ 
        if self.mode == AgentMode.RETURN_HOME and self.at_home():
            any_withdrawn = self.withdraw_all()
            if any_withdrawn:
                # Transition to IDLE mode - will move randomly to find trading partners
                self._set_mode(AgentMode.IDLE, "trade_ready", observer_registry, step_number)
                self.target = None

    # --- Decision Logic -------------------------------------------
    def _manhattan(self, x1: int, y1: int, x2: int, y2: int) -> int:
        """Calculate Manhattan distance between two points."""
        return abs(x1 - x2) + abs(y1 - y2)

    def _current_bundle(self) -> tuple[float, float]:
        """Get current bundle (good1, good2) from total wealth (carrying + home inventory).
        
        Uses total wealth for consistent utility calculations, ensuring trade predictions
        match actual execution utility calculations.
        """
        return self._inventory.current_bundle()

    def select_target(self, grid: Grid, observer_registry: Optional['ObserverRegistry'] = None, step_number: int = 0) -> None:
        """Select movement target based on current mode and available resources.
        
        RETURN_HOME: Target home position
        MOVE_TO_PARTNER: Target meeting point  
        IDLE: Stay idle if foraging disabled
        FORAGE: Find highest utility resource within perception radius
        
        Args:
            grid: Grid for resource access and spatial queries
            observer_registry: Event registry for mode change notifications
            step_number: Current step for event context
        
        Uses refactored target selection component when flag is enabled.
        Transitions to RETURN_HOME when carrying goods but no targets available.
        """
        import os  # Import here to avoid circular import issues
        from .agent_flags import is_refactor_enabled
        
        if self.mode == AgentMode.RETURN_HOME:
            self.target = (int(self.home_x), int(self.home_y))  # type: ignore[arg-type]
            return
        
        # If moving to partner, maintain target as meeting point
        if self.mode == AgentMode.MOVE_TO_PARTNER:
            if self.meeting_point is not None:
                self.target = self.meeting_point
            return
        
        # If currently IDLE and foraging is disabled, stay idle and don't seek targets
        if self.mode == AgentMode.IDLE:
            forage_enabled = os.environ.get("ECONSIM_FORAGE_ENABLED", "1") == "1"
            if not forage_enabled:
                self.target = None
                return

        # Use refactored target selection component if enabled
        if is_refactor_enabled("target_selection") and self._target_selection is not None:
            current_bundle = self._current_bundle()
            candidate = self._target_selection.select_target(
                (self.x, self.y), current_bundle, self.preference, grid
            )
            
            if candidate is not None:
                self.target = candidate.position
                self._set_mode(AgentMode.FORAGE, "resource_found", observer_registry, step_number)
            elif self.carrying_total() > 0:
                self._set_mode(AgentMode.RETURN_HOME, "no_targets", observer_registry, step_number)
                self.target = (int(self.home_x), int(self.home_y))  # type: ignore[arg-type]
            else:
                self._set_mode(AgentMode.IDLE, "no_targets", observer_registry, step_number)
                self.target = None
        else:
            # LEGACY: Existing implementation
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
                    self._set_mode(AgentMode.FORAGE, "prospecting", observer_registry, step_number)
                elif self.carrying_total() > 0:
                    self._set_mode(AgentMode.RETURN_HOME, "no_targets", observer_registry, step_number)
                    self.target = (int(self.home_x), int(self.home_y))  # type: ignore[arg-type]
                else:
                    self._set_mode(AgentMode.IDLE, "no_targets", observer_registry, step_number)
                    self.target = None
            else:
                self.target = best_meta
                self._set_mode(AgentMode.FORAGE, "resource_found", observer_registry, step_number)

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
        
        ⚠️ PERFORMANCE CRITICAL: This function was causing O(R²) complexity leading to 96.6% 
        performance loss in Pure Leontief scenarios. Optimized with resource caching to O(R).
        
        🔍 BEHAVIOR REVIEW NEEDED: The prospecting algorithm makes forward-looking decisions
        about complementary resource collection. This may need behavioral validation in 
        future review passes to ensure economic coherence and educational value.
        """
        # Only apply prospecting to Leontief preference agents
        if getattr(self.preference, 'TYPE_NAME', '') != 'leontief':
            return None
        
        best_prospect: tuple[float, int, int, int] | None = None  # key = (-score, dist, x, y)
        best_prospect_pos: Position | None = None
        max_dist = default_PERCEPTION_RADIUS
        
        # 🚀 PERFORMANCE OPTIMIZATION: Cache resources by type to avoid O(R²) complexity
        # Build resource cache ONLY for resources within perception range to avoid O(A×R) bottleneck
        resource_cache: dict[str, list[tuple[int, int]]] = {}
        position_to_type_cache: dict[tuple[int, int], str] = {}
        iterator = getattr(grid, "iter_resources_sorted", grid.iter_resources)()
        
        # Pre-filter resources by distance before caching (critical optimization!)
        for rx, ry, rtype in iterator:
            dist_to_resource = self._manhattan(self.x, self.y, rx, ry)
            if dist_to_resource > max_dist:
                continue  # Skip distant resources entirely
                
            if rtype not in resource_cache:
                resource_cache[rtype] = []
            resource_cache[rtype].append((rx, ry))
            position_to_type_cache[(rx, ry)] = rtype

        # Process each nearby resource position to find prospects
        for rtype, positions in resource_cache.items():
            for rx, ry in positions:
                # Distance already checked above - all cached resources are within range
                dist_to_resource = self._manhattan(self.x, self.y, rx, ry)
                
                good = RESOURCE_TYPE_TO_GOOD.get(rtype)
                if not good:
                    continue
                    
                # Find the best complementary resource for this starting resource
                prospect_score = self._calculate_prospect_score_cached(
                    (rx, ry), rtype, resource_cache, position_to_type_cache, raw_bundle, max_dist
                )
                
                if prospect_score > 0.0:
                    key = (-prospect_score, dist_to_resource, rx, ry)
                    if best_prospect is None or key < best_prospect:
                        best_prospect = key
                        best_prospect_pos = (rx, ry)
        
        return best_prospect_pos

    def _calculate_prospect_score_cached(
        self,
        resource_pos: Position, 
        resource_type: str,
        resource_cache: dict[str, list[tuple[int, int]]],
        position_to_type_cache: dict[tuple[int, int], str],
        current_bundle: tuple[float, float],
        max_dist: int
    ) -> float:
        """🚀 OPTIMIZED: Calculate prospect score using cached resource positions.
        
        Performance improvement: O(R) instead of O(R²) by using pre-built resource cache
        instead of iterating through grid for each complement search.
        """
        rx, ry = resource_pos
        dist_to_first = self._manhattan(self.x, self.y, rx, ry)
        
        # Find nearest complementary resource using cached positions
        complement_pos, complement_dist = self._find_nearest_complement_cached(
            resource_pos, resource_type, resource_cache, max_dist
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
        # Get complement type from O(1) position lookup instead of grid iteration
        complement_type = position_to_type_cache.get((cx, cy))
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

    def _find_nearest_complement_cached(
        self,
        resource_pos: Position, 
        resource_type: str, 
        resource_cache: dict[str, list[tuple[int, int]]],
        max_dist: int
    ) -> tuple[Position | None, int]:
        """🚀 OPTIMIZED: Find nearest complement using cached resource positions.
        
        Performance improvement: O(C) instead of O(R) where C is complement count.
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
        
        # Get cached positions for complement resource type
        complement_positions = resource_cache.get(complement_resource_type, [])
        if not complement_positions:
            return None, 0
        
        best_complement: tuple[int, int, int] | None = None  # (dist, x, y)
        
        for cx, cy in complement_positions:
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

    def _get_resource_type_from_cache(
        self, 
        resource_cache: dict[str, list[tuple[int, int]]],
        x: int, 
        y: int
    ) -> str | None:
        """🚀 OPTIMIZED: Get resource type at position using cached data.
        
        Performance improvement: O(T) instead of O(R) where T is resource type count.
        """
        for resource_type, positions in resource_cache.items():
            if (x, y) in positions:
                return resource_type
        return None

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

    def step_decision(self, grid: Grid, observer_registry: Optional['ObserverRegistry'] = None, step_number: int = 0) -> bool:
        """Perform one decision+movement+interaction step (without RNG).

        Returns True if the agent actively foraged (collected a resource this tick),
        False otherwise. This return value is advisory and ignored by existing
        callers that do not capture it (backward compatible).
        
        Args:
            grid: Grid for resource access and spatial queries
            observer_registry: Event registry for mode change notifications
            step_number: Current step for event context
        """
        # Select/refresh target if none or mode requires it
        if self.target is None or self.mode not in (AgentMode.FORAGE, AgentMode.MOVE_TO_PARTNER):
            self.select_target(grid, observer_registry, step_number)
        # Movement toward target
        if self.target is not None and (self.x, self.y) != self.target:
            old_pos = (self.x, self.y)
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
            
            # Track movement for behavioral analysis using observer pattern
            new_pos = (self.x, self.y)
            if new_pos != old_pos:
                try:
                    from ..observability.observer_logger import get_global_observer_logger
                    logger = get_global_observer_logger()
                    if logger:
                        # Log movement as spatial event
                        message = f"Agent {self.id} moved from {old_pos} to {new_pos}"
                        logger.log_spatial(message, step_number)
                except Exception:
                    pass  # Don't break simulation if logging fails
        # Interactions
        collected = self.collect(grid, step_number, observer_registry)
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
                self.select_target(grid, observer_registry, step_number)
        # Deposit if arriving home
        self.maybe_deposit(observer_registry, step_number)
        return bool(collected)

    # --- Unified Target Selection --------------------------------
    def select_unified_target(
        self,
        grid: Grid,
        nearby_agents: list["Agent"],
        *,
        enable_foraging: bool,
        enable_trade: bool,
        distance_scaling_factor: float,
        step: int,
    ) -> tuple[str, object] | None:
        """Unified target selection with distance-discounted utility scoring.
        
        Evaluates both resource and trading partner candidates, applying
        distance scaling factor k where score = ΔU / (1 + k*d²).
        Uses deterministic tie-breaking for reproducible behavior.
        
        Returns:
            ("resource", metadata) or ("partner", metadata) or None
        """
        # Skip if forced deposit cycle active
        if self.force_deposit_once:
            return None
        best_choice: tuple[str, object] | None = None
        best_score: float = -1.0

        # Initialize partner search tracking (for instrumentation)
        scanned_count = 0
        eligible_count = 0
        rejected_partners = []
        chosen_partner_id = None

        # Helper: consider candidate with deterministic tie-break
        def _maybe_commit(kind: str, payload: dict) -> None:
            nonlocal best_choice, best_score
            score = payload.get("discounted", -1.0)
            if score < 0:
                return
            if best_choice is None:
                best_choice = (kind, payload)
                best_score = score
                return
            if score > best_score + 1e-15:  # strictly better
                best_choice = (kind, payload)
                best_score = score
            elif abs(score - best_score) <= 1e-15:
                # Deterministic tie-break: resources by (x,y); partners by partner_id
                if kind == "resource" and best_choice[0] == "resource":
                    cx, cy = payload["pos"]
                    bx, by = best_choice[1]["pos"]  # type: ignore[index]
                    if (cx, cy) < (bx, by):
                        best_choice = (kind, payload)
                elif kind == "partner" and best_choice[0] == "partner":
                    if payload["partner_id"] < best_choice[1]["partner_id"]:  # type: ignore[index]
                        best_choice = (kind, payload)
                else:
                    # Mixed types: prefer higher raw (undiscounted) ΔU; if still tie, choose lexicographically by kind
                    raw_new = payload.get("delta_u", 0.0)
                    raw_old = best_choice[1].get("delta_u", 0.0)  # type: ignore[index]
                    if raw_new > raw_old + 1e-15:
                        best_choice = (kind, payload)
                    elif abs(raw_new - raw_old) <= 1e-15 and kind < best_choice[0]:
                        best_choice = (kind, payload)

        # Resource candidates
        if enable_foraging:
            pos, delta_u, key = self.compute_best_resource_candidate(grid)
            if pos is not None and delta_u > 0.0:
                dist = abs(pos[0] - self.x) + abs(pos[1] - self.y)
                discounted = delta_u / (1.0 + distance_scaling_factor * (dist * dist))
                _maybe_commit("resource", {"pos": pos, "delta_u": delta_u, "discounted": discounted, "dist": dist})

        # Partner candidates (conservative estimate): scan nearby_agents list (already radius filtered by caller ideally)
        if enable_trade and nearby_agents:
            # Conservative heuristic: potential gain = max(0, mu_gain_partner - mu_loss_self) for one swap across goods
            from econsim.preferences.helpers import marginal_utility as _mu
            # Precompute own marginal utilities once (using carrying+home aggregated implicitly by helper)
            self_mu = _mu(
                self.preference,
                self.carrying,
                self.home_inventory,
                epsilon_lift=True,
                include_missing_two_goods=True,
            )
            
            for other in nearby_agents:
                scanned_count += 1
                
                if other.id == self.id:
                    rejected_partners.append((other.id, "self"))
                    continue
                # Skip if already paired via older bilateral path (will be handled elsewhere)  
                if getattr(other, 'trade_partner_id', None) is not None or getattr(self, 'trade_partner_id', None) is not None:
                    rejected_partners.append((other.id, "already_paired"))
                    continue
                
                eligible_count += 1
                other_mu = _mu(
                    other.preference,
                    other.carrying,
                    other.home_inventory,
                    epsilon_lift=True,
                    include_missing_two_goods=True,
                )
                # Evaluate both swap directions; keep best positive conservative estimate
                best_partner_delta = 0.0
                # self gives good1, receives good2
                if self.carrying.get('good1', 0) > 0 and other.carrying.get('good2', 0) > 0:
                    gain_self = self_mu.get('good2', 0.0) - self_mu.get('good1', 0.0)
                    gain_other = other_mu.get('good1', 0.0) - other_mu.get('good2', 0.0)
                    combined = min(gain_self, gain_other)  # conservative (bottleneck)
                    if combined > best_partner_delta:
                        best_partner_delta = combined
                # self gives good2, receives good1
                if self.carrying.get('good2', 0) > 0 and other.carrying.get('good1', 0) > 0:
                    gain_self = self_mu.get('good1', 0.0) - self_mu.get('good2', 0.0)
                    gain_other = other_mu.get('good2', 0.0) - other_mu.get('good1', 0.0)
                    combined = min(gain_self, gain_other)
                    if combined > best_partner_delta:
                        best_partner_delta = combined
                if best_partner_delta <= 0.0:
                    rejected_partners.append((other.id, "negative_utility"))
                    continue
                dist = abs(other.x - self.x) + abs(other.y - self.y)
                discounted = best_partner_delta / (1.0 + distance_scaling_factor * (dist * dist))
                
                # Track if this partner gets chosen
                old_best = best_choice
                _maybe_commit("partner", {
                    "partner_id": other.id,
                    "delta_u": best_partner_delta,
                    "discounted": discounted,
                    "dist": dist,
                })
                # Check if this partner was chosen (regardless of whether choice changed)
                if best_choice is not None and best_choice[0] == "partner" and best_choice[1]["partner_id"] == other.id:
                    chosen_partner_id = other.id

        # Emit partner search instrumentation with consolidated rejections
        if enable_trade and nearby_agents and scanned_count > 0:
            import os
            sample_period = int(os.environ.get("ECONSIM_PARTNER_SEARCH_SAMPLE_PERIOD", "1"))
            
            if step % sample_period == 0:
                from ..observability.observer_logger import get_global_observer_logger
                logger = get_global_observer_logger()
                if logger:
                    # Emit consolidated partner search event with rejection data using observer pattern
                    # Sample first 3 rejections to keep log size manageable
                    rejection_sample = rejected_partners[:3] if rejected_partners else []
                    
                    # Create structured partner search analysis message
                    message = (
                        f"Partner search - Agent {self.id}: "
                        f"Scanned: {scanned_count}, "
                        f"Eligible: {eligible_count}, "
                        f"Chosen: {chosen_partner_id if chosen_partner_id is not None else 'None'}, "
                        f"Rejections: {len(rejection_sample)}"
                    )
                    logger.log_trade(message, step)
                    
        self.current_unified_task = best_choice
        return best_choice

    # --- Serialization (Optional Future Use) ----------------------
    def serialize(self) -> Mapping[str, Any]:
        """Serialize agent state to dictionary for persistence and debugging.
        
        Includes backward compatible 'inventory' field (alias for carrying).
        """
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
        """Get agent's current position as a (x, y) tuple."""
        return (self.x, self.y)

    def total_inventory(self) -> dict[str, int]:
        """Return combined carrying + home inventory without mutation."""
        return self._inventory.total_inventory()

    def find_nearby_agents(self, all_agents: list["Agent"]) -> list[tuple["Agent", int]]:
        """Find other agents within perception radius for potential trading.
        
        Returns list of (agent, distance) tuples sorted by distance, then by agent position
        for deterministic tiebreaking. Excludes self from the results.
        """
        return self._trading_partner.find_nearby_agents((self.x, self.y), all_agents)

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
        self._trading_partner.establish_pairing((self.x, self.y), other_agent)

    def clear_trade_partner(self) -> None:
        """Clear trade partner state without setting cooldowns."""
        self._trading_partner.clear_trade_partner()

    def end_trading_session(self, partner: "Agent") -> None:
        """End trading session with partner and set per-partner cooldowns."""
        self._trading_partner.end_trading_session(partner)

    def update_partner_cooldowns(self) -> None:
        """Decrement all partner-specific cooldowns by 1."""
        self._trading_partner.update_cooldowns()

    def can_trade_with_partner(self, partner_id: int) -> bool:
        """Check if this agent can trade with a specific partner (no active cooldown)."""
        return self._trading_partner.can_trade_with_partner(partner_id)

    def move_toward_meeting_point(self, grid: "Grid") -> None:
        """Move one step toward the established meeting point."""
        if self._trading_partner.meeting_point is None:
            return
            
        new_pos = self._movement.move_toward_meeting_point((self.x, self.y), self._trading_partner.meeting_point)
        self.x, self.y = new_pos

    def attempt_trade_with_partner(self, other_agent: "Agent", metrics_collector: Any = None, current_step: int = 0) -> bool:
        """Deprecated trade execution path - no longer executes trades.
        
        Trade execution now handled by unified intent enumeration pipeline.
        Returns False to maintain pairing flow compatibility.
        """
        return False

    def is_colocated_with(self, other_agent: "Agent") -> bool:
        """Check if this agent is on the same tile as another agent."""
        return self.x == other_agent.x and self.y == other_agent.y


__all__ = ["Agent", "Position", "AgentMode"]
