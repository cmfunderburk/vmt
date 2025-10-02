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
    from .components.mode_state_machine import AgentModeStateMachine

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
        
        # Initialize target selection component
        from .components.target_selection import ResourceTargetStrategy
        self._target_selection = ResourceTargetStrategy()
        
        # Initialize mode state machine component
        from .components.mode_state_machine import AgentModeStateMachine
        self._mode_state_machine = AgentModeStateMachine(self.id)
        self._mode_state_machine.set_event_emitter(self._event_emitter)
    
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
        Centralized mode setter with state machine validation and event emission.
        
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
        
        # Validate transition using state machine
        if not self._mode_state_machine.validate_and_emit_transition(
            old_mode.value, new_mode.value, reason, step_number, observer_registry, event_buffer
        ):
            # Invalid transition - log and reject
            self._debug_log_mode_change(old_mode, new_mode, f"REJECTED: {reason}")
            return
            
        self._debug_log_mode_change(old_mode, new_mode, reason)
        self.mode = new_mode

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
        
        Uses target selection component for resource selection.
        Transitions to RETURN_HOME when carrying goods but no targets available.
        """
        import os  # Import here to avoid circular import issues
        
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

        # Use target selection component
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

    # --- Unified / Shared Candidate Computation -----------------
    def compute_best_resource_candidate(self, grid: Grid) -> tuple[Position | None, float, tuple[float,int,int,int] | None]:
        """Return best resource target using target selection component.
        
        Maintains backward compatibility for select_unified_target and other methods
        that depend on this interface. Delegates to the target selection component.
        
        Returns:
            (position, delta_u, tie_key) where tie_key = (-delta_u, distance, x, y)
        """
        current_bundle = self._current_bundle()
        candidate = self._target_selection.select_target(
            (self.x, self.y), current_bundle, self.preference, grid
        )
        
        if candidate is None:
            return None, 0.0, None
        
        # Convert to expected format for backward compatibility
        key = (-candidate.delta_u_raw, candidate.distance, candidate.position[0], candidate.position[1])
        return candidate.position, candidate.delta_u_raw, key

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
