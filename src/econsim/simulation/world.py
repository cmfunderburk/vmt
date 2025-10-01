"""Simulation coordinator orchestrating agent and grid progression.

Manages per-tick simulation steps with support for deterministic decision-making,
bilateral trading, unified target selection, and spatial optimization. Maintains
single-threaded execution with optional resource respawn and metrics collection.

Execution Modes:
* Deterministic: Unified target selection with distance-discounted utility
* Legacy: Random walk movement for regression comparison
* Trading: Feature-flagged bilateral exchange with intent enumeration

Step Sequence:
1. Agent target selection (resource vs trading partner)
2. Movement toward targets with spatial collision handling
3. Resource collection and trade intent enumeration/execution
4. Home deposit logic and mode transitions
5. Respawn and metrics hooks
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Optional, List, Tuple, Dict
import random as _random

try:  # Local import guard (optional config not always present yet)
    from .config import SimConfig  # type: ignore
except Exception:  # pragma: no cover
    SimConfig = Any  # fallback for type checkers

import logging
from .agent import Agent, AgentMode
from .grid import Grid
from .respawn import RespawnScheduler  # type: ignore
from .metrics import MetricsCollector  # type: ignore
from .trade import (  # type: ignore
    enumerate_intents_for_cell,
    TradeEnumerationStats,
    TradeIntent,
    execute_single_intent,
)
import os

# Observer system imports (Phase 1.3: Observer Foundation)
from ..observability.registry import ObserverRegistry
from ..observability.events import AgentModeChangeEvent


def _debug_log_mode_change(agent: Agent, old_mode: AgentMode, new_mode: AgentMode, reason: str = "", 
                          observer_registry: Optional[ObserverRegistry] = None, step: int = 0) -> None:
    """Log agent mode transitions using observer system (Phase 1.3: Breaking circular dependency)."""
    if observer_registry and observer_registry.has_observers():
        # Use new observer-based event system
        event = AgentModeChangeEvent.create(
            step=step,
            agent_id=agent.id,
            old_mode=old_mode.value,
            new_mode=new_mode.value,
            reason=reason
        )
        observer_registry.notify(event)
    else:
        # Fallback to legacy logging system for backward compatibility
        try:
            from ..gui.debug_logger import log_agent_mode
            log_agent_mode(agent.id, old_mode.value, new_mode.value, reason)
        except ImportError:
            # Graceful degradation if GUI logging not available
            pass


@dataclass(slots=True)
class Simulation:
    """Core simulation engine coordinating agents, grid, and economic interactions.
    
    Manages deterministic stepping with configurable behavioral systems including
    resource foraging, bilateral trading, and spatial agent interactions.
    Provides factory construction and runtime configuration capabilities.
    """
    grid: Grid
    agents: list[Agent]
    _steps: int = 0
    config: Optional[Any] = None  # SimConfig when available
    _rng: _random.Random | None = None      # Internal RNG (hooks, future stochastic systems)
    respawn_scheduler: Any | None = None    # Optional RespawnScheduler (factory attaches if enabled)
    metrics_collector: Any | None = None    # Optional MetricsCollector (factory attaches if enabled)
    _respawn_interval: int | None = 1       # How frequently to invoke respawn (1 => every step default; None/<=0 => disabled)
    # Draft trade intents (feature-flagged). Populated when ECONSIM_TRADE_DRAFT=1; cleared each step.
    # Populated only when ECONSIM_TRADE_DRAFT=1; otherwise kept as empty list for simpler typing.
    trade_intents: list[TradeIntent] | None = None
    # Last executed trade cell highlight bookkeeping (GUI render hint; purely observational)
    _last_trade_highlight: tuple[int,int,int] | None = None  # (x,y,expire_step)
    # Performance tracking for debug logging
    _step_times: list[float] = field(default_factory=list)
    # Observer system integration (Phase 1.3: Observer Foundation)  
    _observer_registry: ObserverRegistry = field(default_factory=ObserverRegistry)
    # Step execution system (Phase 2: Step Decomposition)
    _step_executor: Any = field(default=None)
    # Pre-step resource snapshot for collection metrics (not part of determinism hash)
    pre_step_resource_count: int | None = None
    # Captured aggregated step metrics (non-deterministic hash; for testing/diagnostics)
    last_step_metrics: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Initialize internal RNG from config seed if available."""
        if self.config is not None and self._rng is None:
            seed = getattr(self.config, "seed", 0)
            self._rng = _random.Random(int(seed))

    def step(self, rng: random.Random, *, use_decision: bool = False) -> None:
        """Advance simulation by one step using decomposed handler system.

        Orchestrates step execution through focused handlers while maintaining
        deterministic behavior and performance characteristics.

        Args:
            rng: External RNG for legacy random movement mode
            use_decision: Enable deterministic decision-making and trading
        """
        # Initialize step executor on first use
        if self._step_executor is None:
            self._initialize_step_executor()
        
        # Snapshot pre-step resource count for collection metrics (decision/unified modes)
        try:
            self.pre_step_resource_count = self.grid.resource_count()
        except Exception:
            self.pre_step_resource_count = None

        # Create step context for handlers
        from .features import SimulationFeatures
        from .execution import StepContext
        
        step_num = self._steps + 1
        feature_flags = SimulationFeatures.from_environment()
        
        context = StepContext(
            simulation=self,
            step_number=step_num,
            ext_rng=rng,
            feature_flags=feature_flags,
            observer_registry=self._observer_registry
        )
        
        # Execute step through handler system
        step_metrics = self._step_executor.execute_step(context)
        self.last_step_metrics = step_metrics  # store for tests/analytics (excluded from hash logic)

        # Update determinism metrics/hash (must occur before step counter increment to preserve historical ordering semantics)
        try:
            if self.metrics_collector is not None:
                # Use step_num (current logical step about to be committed)
                self.metrics_collector.record(step_num, self)
        except Exception:  # pragma: no cover - defensive; avoid breaking simulation loop on metrics failure
            pass

        # Update step counter (handlers assume previous self._steps during execution)
        self._steps += 1

        # Optional lightweight FPS debug (will migrate to MetricsHandler once implemented)
        # (FPS debug moved to MetricsHandler metrics; print removed to avoid duplication)

        # Expire highlight if past lifetime
        if self._last_trade_highlight is not None:
            _, _, expire = self._last_trade_highlight
            if self._steps >= expire:
                self._last_trade_highlight = None

        # Flush observers at end-of-step (after all handlers)
        self._observer_registry.flush_step(step_num)

        # Clear transient cross-handler scratch data
        if hasattr(self, '_transient_foraged_ids'):
            try:
                delattr(self, '_transient_foraged_ids')
            except Exception:
                pass
        # Reset snapshot for next step
        self.pre_step_resource_count = None
    
    def _initialize_step_executor(self) -> None:
        """Initialize the step executor with ordered handlers.
        
        Handler order is critical for deterministic behavior.
        Do not reorder without updating validation tests.
        """
        from .execution import StepExecutor
        from .execution.handlers.movement_handler import MovementHandler
        from .execution.handlers.collection_handler import CollectionHandler
        from .execution.handlers.trading_handler import TradingHandler
        from .execution.handlers.metrics_handler import MetricsHandler
        from .execution.handlers.respawn_handler import RespawnHandler
        
        handlers = [
            MovementHandler(),      # Agent movement and mode transitions
            CollectionHandler(),    # Resource collection events
            TradingHandler(),      # Bilateral trading system
            MetricsHandler(),      # Performance and behavioral metrics
            RespawnHandler(),      # Resource respawn cycles
        ]
        
        self._step_executor = StepExecutor(handlers)

    @property
    def steps(self) -> int:
        return self._steps

    def serialize(self) -> dict[str, Any]:
        """Export simulation state to JSON-serializable dict."""
        return {
            "grid": self.grid.serialize(),
            "agents": [a.serialize() for a in self.agents],
            "steps": self._steps,
        }

    # --- Factory Constructor -----------------------------------------------
    @classmethod
    def from_config(
        cls,
        config: Any,  # SimConfig (forward reference; kept Any to avoid circular import issues for type checkers)
        preference_factory: Any | None = None,
        *,
        agent_positions: list[tuple[int, int]] | None = None,
    ) -> "Simulation":
        """Create simulation from configuration with optional agent positions.
        
        Args:
            config: SimConfig instance with validated parameters
            preference_factory: Optional callable returning Preference per agent
            agent_positions: Optional explicit spawn coordinates
            
        Returns:
            Configured simulation with attached hooks based on config flags
        """
        config.validate()

        # Build grid with initial resources
        grid = Grid(config.grid_size[0], config.grid_size[1], config.initial_resources)

        agents: list[Agent] = []
        if agent_positions:
            # Resolve preference factory (lazy import default)
            _pref_factory = preference_factory
            if _pref_factory is None:
                try:
                    from econsim.preferences.cobb_douglas import CobbDouglasPreference  # type: ignore
                except Exception as exc:  # pragma: no cover
                    raise RuntimeError(
                        "Default preference factory unavailable; provide preference_factory explicitly"
                    ) from exc
                _pref_factory = lambda i: CobbDouglasPreference(alpha=0.5)  # type: ignore

            # Available agent sprite types for random assignment
            agent_sprite_types = [
                "agent_explorer",
                "agent_farmer", 
                "agent_green",
                "agent_miner",
                "agent_purple",
                "agent_trader"
            ]
            
            for idx, (x, y) in enumerate(agent_positions):
                pref = _pref_factory(idx)  # type: ignore[misc]
                # Randomly assign sprite type using config seed + agent index for determinism
                sprite_rng = _random.Random(int(config.seed) + idx + 1000)  # offset to avoid conflicts
                sprite_type = sprite_rng.choice(agent_sprite_types)
                agents.append(Agent(id=idx, x=int(x), y=int(y), preference=pref, sprite_type=sprite_type))

        sim = cls(grid=grid, agents=agents, config=config)

        # Internal RNG (deterministic) always seeded for future systems
        sim._rng = _random.Random(int(config.seed))

        # Conditional hook attachment
        if getattr(config, "enable_respawn", False):
            sim.respawn_scheduler = RespawnScheduler(
                target_density=float(config.respawn_target_density),
                max_spawn_per_tick=int(config.max_spawn_per_tick),
                respawn_rate=float(config.respawn_rate),
            )
        if getattr(config, "enable_metrics", False):
            sim.metrics_collector = MetricsCollector()

        return sim

    # --- Runtime Configuration -------------------------------------------
    def set_respawn_interval(self, interval: int | None) -> None:
        """Adjust how often the respawn scheduler is invoked.

        interval = 1  => every step (default)
        interval = N>1 => every Nth step
        interval None or <=0 => disable respawn without detaching scheduler
        Deterministic: purely arithmetic on step counter.
        """
        if interval is None or interval <= 0:
            self._respawn_interval = None
        else:
            self._respawn_interval = int(interval)

    def _handle_bilateral_exchange_movement(self, agent: "Agent", rng: random.Random, step: int = 0) -> None:
        """Handle agent movement and pairing logic for bilateral trading mode.
        
        REFACTOR REQUIRED: This method is 140+ lines and handles multiple concerns
        (stagnation tracking, partner search, movement, trading). Should be decomposed
        into focused helper methods for better maintainability.
        
        Args:
            agent: Agent to handle movement for
            rng: Random number generator
            step: Current simulation step number (for observer events)
        """
        # Utility stagnation tracking: compare current utility to last improvement baseline.
        # We use carrying bundle only; if first time (baseline 0) set immediately.
        from econsim.simulation.agent import AgentMode  # local import to avoid cycle at module load
        try:
            # Only track stagnation while seeking/engaging in trade (IDLE random search or active pairing)
            if agent.mode in (AgentMode.IDLE,) or agent.trade_partner_id is not None:
                current_bundle = (
                    float(agent.carrying.get("good1", 0)),
                    float(agent.carrying.get("good2", 0)),
                )
                from .constants import EPSILON_UTILITY
                from .trade import MIN_TRADE_DELTA  # local import to avoid load cycle issues
                if current_bundle[0] == 0.0 or current_bundle[1] == 0.0:
                    eval_bundle = (
                        current_bundle[0] + EPSILON_UTILITY,
                        current_bundle[1] + EPSILON_UTILITY,
                    )
                else:
                    eval_bundle = current_bundle
                current_u = agent.preference.utility(eval_bundle)
                if agent.last_trade_mode_utility == 0.0:
                    agent.last_trade_mode_utility = current_u
                elif current_u - agent.last_trade_mode_utility > max(1e-12, MIN_TRADE_DELTA * 0.5):
                    agent.last_trade_mode_utility = current_u
                    agent.trade_stagnation_steps = 0
                else:
                    agent.trade_stagnation_steps += 1
        except Exception:  # pragma: no cover - defensive guard
            pass

        # If stagnated for 100 consecutive steps, send agent home once to deposit then idle.
        if (
            agent.trade_stagnation_steps >= 100
            and agent.mode not in (AgentMode.RETURN_HOME,)
        ):
            # Emit stagnation trigger event
            try:
                from ..gui.debug_logger import get_gui_logger
                logger = get_gui_logger()
                
                # Calculate last improvement step (approximate)
                last_improve_step = self._steps - agent.trade_stagnation_steps
                
                builder_result = logger.build_stagnation_trigger(
                    agent_id=agent.id,
                    threshold=100,
                    last_improve_step=last_improve_step,
                    action="return_home",
                    deposit=True
                )
                logger.emit_built_event(self._steps, builder_result)
            except Exception:
                pass  # Don't break simulation if logging fails
                
            if agent.trade_partner_id is not None:
                partner = self._find_agent_by_id(agent.trade_partner_id)
                if partner is not None:
                    agent.end_trading_session(partner)
                else:
                    agent.clear_trade_partner()
            agent.force_deposit_once = True
            from .agent_mode_utils import set_agent_mode
            set_agent_mode(agent, AgentMode.RETURN_HOME, "stagnation", step, self._observer_registry)
            agent.target = (int(agent.home_x), int(agent.home_y))  # type: ignore[arg-type]
            # Reset counters so we don't repeatedly trigger before deposit occurs
            agent.trade_stagnation_steps = 0
            agent.last_trade_mode_utility = 0.0
            return

        # If already paired and trading, handle trading logic
        if agent.trade_partner_id is not None:
            partner = self._find_agent_by_id(agent.trade_partner_id)
            if partner is None:
                # Partner no longer exists, clear pairing
                agent.clear_trade_partner()
                agent.move_random(self.grid, rng)
                return
                
            # If co-located with partner, attempt trading
            if agent.is_colocated_with(partner):
                agent.is_trading = True
                partner.is_trading = True
                
                # Attempt a trade - if no beneficial trade, clear partnership and search again
                trade_occurred = agent.attempt_trade_with_partner(partner, self.metrics_collector, self._steps)
                if not trade_occurred:
                    # No more beneficial trades possible, end trading session with cooldowns
                    agent.end_trading_session(partner)
                    # Start searching again next step
                return
            else:
                # Move toward meeting point
                agent.move_toward_meeting_point(self.grid)
                return
        
        # Decrement cooldowns
        if agent.trade_cooldown > 0:
            agent.trade_cooldown -= 1
        agent.update_partner_cooldowns()

        # If agent is on cooldown, just move randomly
        if agent.trade_cooldown > 0:
            agent.move_random(self.grid, rng)
            return

        # Not currently paired - search for trading partners
        nearby_agents = agent.find_nearby_agents(self.agents)
        
        if not nearby_agents:
            # No agents in perception radius - move randomly
            agent.move_random(self.grid, rng)
        elif len(nearby_agents) == 1:
            # Exactly one agent found - pair up if they're also available
            partner, _ = nearby_agents[0]
            if self._is_agent_available_for_pairing(agent, partner):
                # Both agents are available - establish pairing
                agent.pair_with_agent(partner)
                # Start moving toward meeting point
                agent.move_toward_meeting_point(self.grid)
            else:
                # Partner is busy, on cooldown, or recently traded - move randomly to find others
                agent.move_random(self.grid, rng)
        else:
            # Multiple agents found - select closest available one
            for partner, _ in nearby_agents:
                if self._is_agent_available_for_pairing(agent, partner):
                    # Found an available partner - pair up
                    agent.pair_with_agent(partner)
                    agent.move_toward_meeting_point(self.grid)
                    return
            
            # No available partners found - move randomly
            agent.move_random(self.grid, rng)

    def _find_agent_by_id(self, agent_id: int) -> "Agent | None":
        """Find an agent by ID, returning None if not found."""
        for agent in self.agents:
            if agent.id == agent_id:
                return agent
        return None

    def _is_agent_available_for_pairing(self, agent: "Agent", potential_partner: "Agent") -> bool:
        """Check if an agent is available for new trading partnerships.
        
        An agent is unavailable if they are:
        1. Already paired with someone (trade_partner_id is not None)
        2. Currently in a trading session (is_trading is True)  
        3. On general cooldown (trade_cooldown > 0)
        4. On cooldown with this specific partner
        """
        # Check if partner is already busy
        if potential_partner.trade_partner_id is not None:
            return False
            
        # Check if partner is currently trading
        if potential_partner.is_trading:
            return False
            
        # Check general cooldown
        if potential_partner.trade_cooldown > 0:
            return False
            
        # Check mutual partner-specific cooldowns
        if not agent.can_trade_with_partner(potential_partner.id):
            return False
            
        if not potential_partner.can_trade_with_partner(agent.id):
            return False
            
        return True

    # --- Unified Selection Internal Helpers --------------------
    def _unified_selection_pass(self, rng: random.Random, foraged_ids: set[int], step: int) -> None:
        """Execute unified target selection with spatial indexing and distance scaling.
        
        REFACTOR REQUIRED: This method is 280+ lines and handles spatial indexing,
        target selection, reservation tracking, and instrumentation. Should be
        decomposed into focused helper methods for better testability.
        """
        from .constants import default_PERCEPTION_RADIUS
        from .agent import AgentMode
        from .spatial import AgentSpatialGrid
        # Flags
        import os
        forage_enabled = os.environ.get("ECONSIM_FORAGE_ENABLED", "1") == "1"
        draft_enabled = os.environ.get("ECONSIM_TRADE_DRAFT") == "1"
        exec_enabled = os.environ.get("ECONSIM_TRADE_EXEC") == "1"
        trade_enabled = draft_enabled or exec_enabled
        perception = default_PERCEPTION_RADIUS
        # Distance scaling factor from config (append-only field) fallback 0.0
        k = 0.0
        try:
            if self.config is not None:
                k = float(getattr(self.config, "distance_scaling_factor", 0.0))
        except Exception:
            k = 0.0
        # Build spatial index
        index = AgentSpatialGrid(self.grid.width, self.grid.height)
        for ag in self.agents:
            index.add_agent(ag.x, ag.y, ag)
        # Reservation sets (avoid duplicate resource claims / partner races)
        claimed_resources: set[tuple[int,int]] = set()
        claimed_partners: set[int] = set()
        agents_by_id = {a.id: a for a in self.agents}
        for a in self.agents:
            if a.force_deposit_once:
                from .agent_mode_utils import set_agent_mode
                set_agent_mode(a, AgentMode.RETURN_HOME, "force_deposit_stagnation", step, self._observer_registry)
                a.target = (int(a.home_x), int(a.home_y))  # type: ignore[arg-type]
                a.maybe_deposit(self._observer_registry, step)
                continue
            if getattr(a, 'trade_partner_id', None) is not None:
                # Already paired; movement handled in post-pass
                continue
            nearby = index.get_agents_in_radius(a.x, a.y, perception) if trade_enabled else []
            # Remove self if present (defensive)
            nearby = [nb for nb in nearby if nb.id != a.id]
            choice = a.select_unified_target(
                self.grid,
                nearby,
                enable_foraging=forage_enabled,
                enable_trade=trade_enabled,
                distance_scaling_factor=k,
                step=step,
            )
            if choice is None:
                # No unified target found - try Leontief prospecting 
                if forage_enabled and getattr(a.preference, 'TYPE_NAME', '') == 'leontief':
                    try:
                        raw_bundle = (float(a.carrying.get('good1',0)), float(a.carrying.get('good2',0)))
                        prospect = a._try_leontief_prospecting(self.grid, raw_bundle)  # type: ignore[attr-defined]
                        
                        # Check if prospect is available (not claimed)
                        if prospect is not None and prospect not in claimed_resources:
                            claimed_resources.add(prospect)
                            a.target = prospect
                            a._set_mode(AgentMode.FORAGE, "resource_selection", self._observer_registry, step)
                            # Move one step toward prospect immediately
                            if (a.x, a.y) != prospect:
                                tx, ty = prospect
                                dx = tx - a.x; dy = ty - a.y
                                if abs(dx) > abs(dy):
                                    a.x += 1 if dx > 0 else -1
                                elif dy != 0:
                                    a.y += 1 if dy > 0 else -1
                            continue
                        elif prospect is not None:
                            # Primary prospect is claimed - try any available resource as fallback
                            fallback_target = None
                            for rx, ry, _ in self.grid.iter_resources():
                                if (rx, ry) not in claimed_resources:
                                    fallback_target = (rx, ry)
                                    break
                            
                            if fallback_target is not None:
                                claimed_resources.add(fallback_target)
                                a.target = fallback_target
                                a._set_mode(AgentMode.FORAGE, "resource_selection_fallback", self._observer_registry, step)
                                # Move one step toward fallback immediately
                                tx, ty = fallback_target
                                dx = tx - a.x; dy = ty - a.y
                                if abs(dx) > abs(dy):
                                    a.x += 1 if dx > 0 else -1
                                elif dy != 0:
                                    a.y += 1 if dy > 0 else -1
                                continue
                    except Exception:
                        pass
                # No target found - fall back to deposit/idle logic
                if a.carrying_total() > 0:
                    a._set_mode(AgentMode.RETURN_HOME, "carrying_capacity_full", self._observer_registry, step)
                    new_target = (int(a.home_x), int(a.home_y))  # type: ignore[arg-type]
                    a._track_target_change(new_target, step)
                    a.target = new_target
                else:
                    a._set_mode(AgentMode.IDLE, "no_target_available", self._observer_registry, step)
                    a._track_target_change(None, step)
                    a.target = None
                continue
            kind, payload = choice
            if kind == "resource":
                pos = payload["pos"]  # type: ignore[index]
                if pos in claimed_resources:
                    # Already claimed; idle fallback
                    if a.carrying_total() > 0:
                        a._set_mode(AgentMode.RETURN_HOME, "resource_claimed_fallback", self._observer_registry, step)
                        new_target = (int(a.home_x), int(a.home_y))  # type: ignore[arg-type]
                        a._track_target_change(new_target, step)
                        a.target = new_target
                    else:
                        a._set_mode(AgentMode.IDLE, "resource_claimed_fallback", self._observer_registry, step)
                        a._track_target_change(None, step)
                        a.target = None
                    continue
                claimed_resources.add(pos)
                a._track_target_change(pos, step)
                a.target = pos
                a._set_mode(AgentMode.FORAGE, "resource_selection", self._observer_registry, step)
                # Immediate attempt collect if already on cell
                collected = a.collect(self.grid, step)
                if collected:
                    foraged_ids.add(a.id)
                    a._track_target_change(None, step)
                    a.target = None
                    # After collecting, check if should return home
                    if a.carrying_total() > 0:
                        a._set_mode(AgentMode.RETURN_HOME, "collected_resource", self._observer_registry, step)
                        new_target = (int(a.home_x), int(a.home_y))  # type: ignore[arg-type]
                        a._track_target_change(new_target, step)
                        a.target = new_target
                else:
                    # Move one step toward
                    if a.target is not None and (a.x, a.y) != a.target:
                        tx, ty = a.target
                        dx = tx - a.x; dy = ty - a.y
                        if abs(dx) > abs(dy):
                            a.x += 1 if dx > 0 else -1
                        elif dy != 0:
                            a.y += 1 if dy > 0 else -1
                        # Collect if arrived
                        if a.target is not None and (a.x, a.y) == a.target and self.grid.has_resource(a.x, a.y):
                            if a.collect(self.grid, step, self._observer_registry):
                                foraged_ids.add(a.id)
                                a.target = None
                                # After collecting, check if should return home
                                if a.carrying_total() > 0:
                                    a._set_mode(AgentMode.RETURN_HOME, "collected_resource", self._observer_registry, step)
                                    a.target = (int(a.home_x), int(a.home_y))  # type: ignore[arg-type]
                a.maybe_deposit()
            elif kind == "partner":
                pid = payload["partner_id"]  # type: ignore[index]
                if pid in claimed_partners:
                    # Partner already claimed; fallback
                    if a.carrying_total() > 0:
                        a._set_mode(AgentMode.RETURN_HOME, "partner_claimed_fallback", self._observer_registry, step)
                        new_target = (int(a.home_x), int(a.home_y))  # type: ignore[arg-type]
                        a._track_target_change(new_target, step)
                        a.target = new_target
                    else:
                        a._set_mode(AgentMode.IDLE, "partner_claimed_fallback", self._observer_registry, step)
                        a._track_target_change(None, step)
                        a.target = None
                    continue
                partner = agents_by_id.get(pid)
                if partner is None or getattr(partner, 'trade_partner_id', None) is not None:
                    continue
                claimed_partners.add(pid)
                a.pair_with_agent(partner)
                # Set both agents to MOVE_TO_PARTNER mode and set targets to meeting point
                from .agent import AgentMode
                from .agent_mode_utils import set_agent_mode
                set_agent_mode(a, AgentMode.MOVE_TO_PARTNER, "paired_for_trade", step, self._observer_registry)
                a._track_target_change(a.meeting_point, step)
                a.target = a.meeting_point
                set_agent_mode(partner, AgentMode.MOVE_TO_PARTNER, "paired_for_trade", step, self._observer_registry)
                partner._track_target_change(partner.meeting_point, step)
                partner.target = partner.meeting_point
                # Initial convergence step
                a.move_toward_meeting_point(self.grid)
                partner.move_toward_meeting_point(self.grid)
                # Deposit logic not triggered for partner pursuit
            else:
                # Unknown kind (future extension)
                pass
        # Normalize FORAGE agents with missing target if grid empty
        try:
            any_resources = any(True for _ in self.grid.iter_resources())
        except Exception:
            any_resources = True
        if not any_resources:
            from .agent import AgentMode as _AM
            for a in self.agents:
                if a.mode == _AM.FORAGE and a.target is None:
                    # Safety check: agents with cargo should return home first
                    if a.carrying_total() > 0 and not a.at_home():
                        a._set_mode(_AM.RETURN_HOME, "no_target_available", self._observer_registry, step)
                        a.target = (int(a.home_x), int(a.home_y))  # type: ignore[arg-type]
                    elif a.at_home():
                        a._set_mode(_AM.IDLE, "idle_at_home", self._observer_registry, step)  # Only idle at home
                    # If no cargo and not at home, let them continue seeking or return home
        # Emit selection sample instrumentation (periodic)
        import os
        sample_period = int(os.environ.get("ECONSIM_SELECTION_SAMPLE_PERIOD", "200"))
        if step % sample_period == 0:
            try:
                from ..gui.debug_logger import get_gui_logger
                logger = get_gui_logger()
                
                # Collect top candidates for analysis
                resource_candidates = []
                partner_candidates = []
                
                for a in self.agents:
                    if a.current_unified_task is not None:
                        kind, payload = a.current_unified_task
                        if kind == "resource":
                            resource_candidates.append({
                                "agent_id": a.id,
                                "pos": payload.get("pos"),
                                "score": payload.get("score", 0.0),
                                "delta_u": payload.get("delta_u", 0.0)
                            })
                        elif kind == "partner":
                            partner_candidates.append({
                                "agent_id": a.id,
                                "partner_id": payload.get("partner_id"),
                                "score": payload.get("score", 0.0),
                                "delta_u": payload.get("delta_u", 0.0)
                            })
                
                # Sort by score (descending) and take top N
                resource_candidates.sort(key=lambda x: x["score"], reverse=True)
                partner_candidates.sort(key=lambda x: x["score"], reverse=True)
                
                builder_result = logger.build_selection_sample(
                    step=step,
                    resource_candidates=resource_candidates[:5],  # Top 5 resources
                    partner_candidates=partner_candidates[:5],   # Top 5 partners
                    total_agents=len(self.agents),
                    active_agents=len([a for a in self.agents if a.current_unified_task is not None])
                )
                logger.emit_built_event(step, builder_result)
            except Exception:
                pass  # Don't break simulation if logging fails

        # Emit target churn instrumentation (periodic)
        churn_period = int(os.environ.get("ECONSIM_CHURN_EMIT_PERIOD", "500"))
        if step % churn_period == 0:
            try:
                from ..gui.debug_logger import get_gui_logger
                logger = get_gui_logger()
                
                # Collect retarget data from all agents
                retarget_data = []
                total_retargets = 0
                
                for a in self.agents:
                    if a._recent_retargets:
                        # Count retargets in the last window
                        window_start = max(0, step - int(os.environ.get("ECONSIM_CHURN_WINDOW", "100")))
                        recent_count = len([s for s in a._recent_retargets if s >= window_start])
                        if recent_count > 0:
                            retarget_data.append({
                                "agent_id": a.id,
                                "retarget_count": recent_count,
                                "last_retarget": max(a._recent_retargets) if a._recent_retargets else step
                            })
                            total_retargets += recent_count
                
                # Debug: Always emit target churn event (even if no retargets) to see if it's working
                builder_result = logger.build_target_churn(
                    step=step,
                    total_retargets=total_retargets,
                    active_agents=len(retarget_data),
                    retarget_data=retarget_data[:10],  # Top 10 most active agents
                    window_size=int(os.environ.get("ECONSIM_CHURN_WINDOW", "100"))
                )
                logger.emit_built_event(step, builder_result)
            except Exception:
                pass  # Don't break simulation if logging fails

        # Post-pass movement for existing pairings (finish convergence)
        for a in self.agents:
            if getattr(a, 'trade_partner_id', None) is not None:
                partner_id = getattr(a, 'trade_partner_id')
                partner = self._find_agent_by_id(int(partner_id)) if partner_id is not None else None
                if partner is None:
                    a.clear_trade_partner()
                    continue
                if not a.is_colocated_with(partner):
                    a.move_toward_meeting_point(self.grid)


__all__ = ["Simulation"]
