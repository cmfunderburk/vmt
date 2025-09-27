"""Simulation coordinator (Gates 3–6 implemented).

Orchestrates per-tick progression across agents & grid. Supports two
paths: legacy random walk (for baseline / regression comparison) and
deterministic decision mode (greedy 1-step target pursuit using
preference-driven ΔU scoring). Optional hooks enable resource respawn
and metrics collection when attached.

Decision Mode Sequence:
1. For each agent (list order confers contest priority): target selection
2. Single-cell movement toward target
3. Resource collection & potential retarget if race lost
4. Deposit at home if returning
5. Respawn hook → Metrics hook → step counter increment

Deferred:
* Multi-phase (pipeline) ordering strategies
* Agent interaction (trading, negotiation)
* Parallel / batched stepping (single-thread invariant maintained)
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
from .trade import enumerate_intents_for_cell, TradeIntent, execute_single_intent  # type: ignore
import os


def _debug_log_mode_change(agent: Agent, old_mode: AgentMode, new_mode: AgentMode, reason: str = "") -> None:
    """Log agent mode transitions for debugging."""
    from ..gui.debug_logger import log_agent_mode
    log_agent_mode(agent.id, old_mode.value, new_mode.value, reason)


@dataclass(slots=True)
class Simulation:
    grid: Grid
    agents: list[Agent]
    _steps: int = 0
    config: Optional[Any] = None  # SimConfig when available
    _rng: _random.Random | None = None      # Internal RNG (hooks, future stochastic systems)
    respawn_scheduler: Any | None = None    # Optional RespawnScheduler (factory attaches if enabled)
    metrics_collector: Any | None = None    # Optional MetricsCollector (factory attaches if enabled)
    _respawn_interval: int | None = 5       # New: how frequently to invoke respawn (5 => every 5 steps, None/<=0 => disabled)
    # Draft trade intents (Phase 2 feature-flagged). Populated when ECONSIM_TRADE_DRAFT=1; cleared each step.
    # Populated only when ECONSIM_TRADE_DRAFT=1; otherwise kept as empty list for simpler typing.
    trade_intents: list[TradeIntent] | None = None
    # Last executed trade cell highlight bookkeeping (GUI render hint; purely observational)
    _last_trade_highlight: tuple[int,int,int] | None = None  # (x,y,expire_step)
    # Performance tracking for debug logging
    _step_times: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:  # pragma: no cover (simple init)
        if self.config is not None and self._rng is None:
            seed = getattr(self.config, "seed", 0)
            self._rng = _random.Random(int(seed))

    def step(self, rng: random.Random, *, use_decision: bool = False) -> None:
        """Advance simulation by one tick.

        Parameters:
            rng: external RNG for legacy random movement path (retained for regression comparability).
            use_decision: deterministic decision logic toggle.

        Internal `_rng` powers respawn / metrics hooks (if present) and remains distinct to keep
        external API stable for existing test scaffolds.
        """
        # Performance tracking
        import time
        from ..gui.debug_logger import log_comprehensive, log_simulation, log_performance
        
        step_start = time.perf_counter()
        step_num = self._steps + 1
        
        # Comprehensive debug logging for simulation steps
        log_comprehensive(f"=== SIMULATION STEP {step_num} START ===", step_num)
        
        # Log step summary (filtered by log level in debug_logger)
        log_comprehensive(f"Agents: {len(self.agents)}, Resources: {self.grid.resource_count()}, Decision Mode: {use_decision}", step_num)
        
        forage_enabled = os.environ.get("ECONSIM_FORAGE_ENABLED", "1") == "1"
        hash_neutral = os.environ.get("ECONSIM_TRADE_HASH_NEUTRAL") == "1"  # default early to avoid unbound
        parity_restore_snapshot: list[tuple[int, dict[str,int]]] | None = None
        # Track which agents foraged (collected) this tick for trade gating when both systems on
        foraged_ids: set[int] = set()
        unified_mode_active = False
        draft_enabled = os.environ.get("ECONSIM_TRADE_DRAFT") == "1"
        exec_enabled = os.environ.get("ECONSIM_TRADE_EXEC") == "1"
        unified_disabled = os.environ.get("ECONSIM_UNIFIED_SELECTION_DISABLE") == "1"
        explicit_unified = os.environ.get("ECONSIM_UNIFIED_SELECTION_ENABLE") == "1"
        if use_decision and forage_enabled and (not unified_disabled) and (exec_enabled or explicit_unified):
            # Unified selection (Option 1): evaluate resource vs partner for all agents before movement.
            unified_mode_active = True
            self._unified_selection_pass(rng, foraged_ids)
        elif use_decision and forage_enabled:
            for agent in self.agents:
                try:
                    collected = agent.step_decision(self.grid)  # type: ignore[assignment]
                except TypeError:
                    agent.step_decision(self.grid)  # legacy fallback
                    collected = False
                if collected:
                    foraged_ids.add(agent.id)
        elif use_decision and not forage_enabled:
            # Decision mode but foraging disabled: optional behaviors depend on exchange flags.
            # If exchange also disabled, agents should return home then idle.
            exchange_any = os.environ.get("ECONSIM_TRADE_DRAFT") == "1" or os.environ.get("ECONSIM_TRADE_EXEC") == "1"
            if not exchange_any:
                # Neither foraging nor exchange: agents return home then idle
                for agent in self.agents:
                    # Clear any existing target first (they shouldn't be pursuing resources)
                    agent.target = None
                    
                    # If agent is not at home, set to return home (regardless of carrying inventory)
                    if not agent.at_home():
                        agent.mode = AgentMode.RETURN_HOME
                    else:
                        # Already at home, can idle immediately (deposit any carrying goods first)
                        agent.maybe_deposit()
                        agent.mode = AgentMode.IDLE
                    
                    # Execute the step to actually move toward home / deposit
                    agent.step_decision(self.grid)
            else:
                # Exchange enabled but foraging disabled: agents immediately start bilateral exchange
                for agent in self.agents:
                    # CRITICAL FIX: If agent is still in FORAGE mode but foraging is disabled, transition them
                    if agent.mode == AgentMode.FORAGE and not forage_enabled:
                        # Immediately transition to IDLE for bilateral exchange (skip return home)
                        agent.mode = AgentMode.IDLE
                        agent.target = None
                    
                    # If agent is at home, withdraw available inventory for trading
                    if agent.at_home() and sum(agent.home_inventory.values()) > 0:
                        agent.withdraw_all()
                        agent.mode = AgentMode.IDLE
                        agent.target = None
                    
                    # All agents should be in IDLE mode for bilateral exchange
                    # (No return home step when bilateral exchange is enabled)
                    if agent.mode == AgentMode.RETURN_HOME:
                        # Preserve RETURN_HOME only if a forced deposit is pending (stagnation recovery)
                        if getattr(agent, "force_deposit_once", False):
                            # Let normal decision step move toward home & eventually deposit
                            try:
                                agent.step_decision(self.grid)
                            except Exception:
                                pass
                            continue  # Do not enter bilateral movement this tick
                        else:
                            # Legacy behavior: convert to IDLE for exchange search
                            agent.mode = AgentMode.IDLE
                            agent.target = None

                    # In bilateral exchange mode (IDLE), use tiered movement logic
                    if agent.mode == AgentMode.IDLE:
                        self._handle_bilateral_exchange_movement(agent, rng)
                    # Any other mode (should be rare here) just perform decision step for safety
        else:  # legacy randomness path (foraging always implicit here if enabled)
            for agent in self.agents:
                agent.move_random(self.grid, rng)
            for agent in self.agents:
                agent.collect(self.grid)
        # Draft trade intent enumeration (feature flag; no state mutation)
        if draft_enabled or exec_enabled:  # enumeration only when a trade feature flag is active
            intents: List[TradeIntent] = []
            # Build co-location index (O(n))
            cell_map: Dict[Tuple[int, int], List[Agent]] = {}
            for a in self.agents:
                cell_map.setdefault((a.x, a.y), []).append(a)
            for coloc_agents in cell_map.values():
                if len(coloc_agents) > 1:
                    # If both forage and exchange enabled, restrict trade consideration to agents
                    # that did NOT actively forage (collected) this tick, honoring "forage first then trade".
                    if use_decision and forage_enabled and len(foraged_ids) > 0:
                        filtered = [ag for ag in coloc_agents if ag.id not in foraged_ids]
                        if len(filtered) > 1:
                            intents.extend(enumerate_intents_for_cell(filtered))
                    else:
                        intents.extend(enumerate_intents_for_cell(coloc_agents))
            self.trade_intents = intents
            executed: TradeIntent | None = None
            if exec_enabled and intents:
                # Optional hash parity mode: if ECONSIM_TRADE_HASH_NEUTRAL=1 we restore inventories after metrics.
                if hash_neutral:
                    parity_restore_snapshot = [(a.id, dict(a.carrying)) for a in self.agents]
                # Build id map once
                agents_by_id: Dict[int, Agent] = {a.id: a for a in self.agents}
                executed = execute_single_intent(intents, agents_by_id, step_num)
                # Capture highlight immediately if executed; metrics hook will not need agents_by_id
                if executed is not None:
                    try:
                        seller_agent = agents_by_id.get(executed.seller_id)
                        if seller_agent is not None:
                            self._last_trade_highlight = (
                                int(getattr(seller_agent, 'x', 0)),
                                int(getattr(seller_agent, 'y', 0)),
                                self._steps + 12,
                            )
                    except Exception:
                        pass
                # Parity debug (hash redesign deferred). Enable only when explicitly requested.
                if os.environ.get("ECONSIM_DEBUG_TRADE_PARITY") == "1":  # pragma: no cover - debug aid
                    try:
                        import json as _json
                        snap = [  # type: ignore[var-annotated]
                            {
                                "id": a.id,
                                "x": a.x,
                                "y": a.y,
                                "c": dict(a.carrying),
                                "h": dict(a.home_inventory),
                            }
                            for a in sorted(self.agents, key=lambda ag: ag.id)
                        ]
                        print("[PARITY_EXEC_SNAP]" + _json.dumps(snap))
                    except Exception:
                        pass
            if self.metrics_collector is not None:
                try:
                    mc = self.metrics_collector  # type: ignore[attr-defined]
                    mc.trade_intents_generated += len(intents)  # type: ignore[attr-defined]
                    if exec_enabled:
                        if executed is not None:
                            seller_delta_u = getattr(executed, "delta_utility", 0.0)
                            buyer_delta_u = seller_delta_u  # Approximation placeholder
                            hash_neutral_mode = os.environ.get("ECONSIM_TRADE_HASH_NEUTRAL") == "1"
                            # Unified metrics registration (counters + histories)
                            mc.register_executed_trade(
                                step=self._steps,
                                agent1_id=executed.seller_id,
                                agent2_id=executed.buyer_id,
                                agent1_give=executed.give_type,
                                agent1_take=executed.take_type,
                                agent1_delta_u=seller_delta_u,
                                agent2_delta_u=buyer_delta_u,
                                realized_utility_gain=seller_delta_u,
                                hash_neutral=hash_neutral_mode,
                            )
                        else:
                            mc.no_trade_ticks += 1  # type: ignore[attr-defined]
                except Exception:  # pragma: no cover
                    pass
            # Pairing cleanup: clear persistent pairings that are co-located but have no remaining intents
            try:
                active_pairs: set[tuple[int,int]] = set()
                for it in self.trade_intents or []:
                    pair = (min(it.seller_id, it.buyer_id), max(it.seller_id, it.buyer_id))
                    active_pairs.add(pair)
                executed_pair: tuple[int,int] | None = None
                if 'executed' in locals() and executed is not None:
                    executed_pair = (min(executed.seller_id, executed.buyer_id), max(executed.seller_id, executed.buyer_id))
                seen: set[int] = set()
                for agent in sorted(self.agents, key=lambda a: a.id):
                    pid = getattr(agent, 'trade_partner_id', None)
                    if pid is None or agent.id in seen:
                        continue
                    partner = self._find_agent_by_id(pid)
                    if partner is None:
                        agent.clear_trade_partner()
                        continue
                    pair_key = (min(agent.id, pid), max(agent.id, pid))
                    if executed_pair is not None and pair_key == executed_pair:
                        agent.end_trading_session(partner)
                    else:
                        if (agent.x, agent.y) == (partner.x, partner.y) and pair_key not in active_pairs:
                            agent.end_trading_session(partner)
                    seen.add(agent.id); seen.add(pid)
            except Exception:  # pragma: no cover
                pass
        else:
            self.trade_intents = None
            # Trade disabled: clear lingering pairings & meeting points
            for a in self.agents:
                if getattr(a, 'trade_partner_id', None) is not None:
                    try:
                        a.clear_trade_partner()
                    except Exception:
                        pass
        # Respawn hook (inert if scheduler not attached)
        if self.respawn_scheduler is not None and self._rng is not None:
            # Only invoke respawn when interval condition satisfied.
            if self._respawn_interval and self._respawn_interval > 0:
                if (self._steps % self._respawn_interval) == 0:
                    try:
                        self.respawn_scheduler.step(self.grid, self._rng, step_index=self._steps)
                    except Exception as exc:  # pragma: no cover - defensive placeholder
                        logging.getLogger(__name__).warning("Respawn scheduler error: %s", exc)
        # Metrics hook (placeholder logic handled inside collector)
        if self.metrics_collector is not None:
            try:
                if os.environ.get("ECONSIM_DEBUG_TRADE_PARITY") == "1":  # pragma: no cover - debug aid
                    try:
                        import json as _json
                        snap = [  # type: ignore[var-annotated]
                            {
                                "id": a.id,
                                "x": a.x,
                                "y": a.y,
                                "c": dict(a.carrying),
                                "h": dict(a.home_inventory),
                            }
                            for a in sorted(self.agents, key=lambda ag: ag.id)
                        ]
                        print("[PARITY_HASH_SNAP]" + _json.dumps(snap))
                    except Exception:
                        pass
                self.metrics_collector.record(self._steps, self)
            except Exception as exc:  # pragma: no cover - defensive
                logging.getLogger(__name__).warning("Metrics record error: %s", exc)
        # Restore inventories post-hash if hash-neutral parity mode active
        if hash_neutral and parity_restore_snapshot is not None:
            id_map = {a.id: a for a in self.agents}
            for aid, carry in parity_restore_snapshot:
                a = id_map.get(aid)
                if a is not None:
                    a.carrying.clear()
                    a.carrying.update(carry)
        
        # End-of-step logging and performance metrics
        step_num = self._steps + 1
        log_comprehensive(f"=== SIMULATION STEP {step_num} END ===", step_num)
        
        # Performance metrics
        step_end = time.perf_counter()
        step_duration = (step_end - step_start) * 1000  # Convert to milliseconds
        
        # Track steps per second over recent window
        if not hasattr(self, '_step_times'):
            self._step_times = []
        self._step_times.append(step_end)
        
        # Keep only last 30 steps for rolling average
        if len(self._step_times) > 30:
            self._step_times.pop(0)
        
        # Calculate steps per second if we have enough data
        if len(self._step_times) >= 2:
            time_window = self._step_times[-1] - self._step_times[0]
            if time_window > 0:
                steps_per_sec = (len(self._step_times) - 1) / time_window
                # Use legacy performance logging - unified periodic logging is handled by higher-level code
                log_performance(f"{steps_per_sec:.1f} steps/sec | Frame: {step_duration:.1f}ms | Agents: {len(self.agents)} | Resources: {self.grid.resource_count()}", step_num)
        
        self._steps += 1
        # Expire highlight if past its lifetime
        if self._last_trade_highlight is not None:
            # Only need expiry for maintenance; coordinates consumed by renderer.
            _, _, expire = self._last_trade_highlight
            if self._steps >= expire:
                self._last_trade_highlight = None
        # Clear transient unified task markers post-step (retain only for one frame visibility if needed)
        if unified_mode_active:
            for a in self.agents:
                # Keep a.current_unified_task for possible overlay; comment out clearing if persistent desired
                pass

    @property
    def steps(self) -> int:
        return self._steps

    def serialize(self) -> dict[str, Any]:  # pragma: no cover (future use)
        return {
            "grid": self.grid.serialize(),
            "agents": [a.serialize() for a in self.agents],
            "steps": self._steps,
        }

    # --- Factory (Gate 6) -------------------------------------------------
    @classmethod
    def from_config(
        cls,
        config: Any,  # SimConfig (forward reference; kept Any to avoid circular import issues for type checkers)
        preference_factory: Any | None = None,
        *,
        agent_positions: list[tuple[int, int]] | None = None,
    ) -> "Simulation":
        """Construct a Simulation from a SimConfig.

        Parameters
        ----------
        config : SimConfig
            Configuration instance (validated here).
        preference_factory : callable | None
            Callable returning a Preference instance per agent (signature: (agent_index) -> Preference).
            If None, uses a default Cobb-Douglas (alpha=0.5) if available, else raises.
        agent_positions : list[(x,y)] | None
            Explicit spawn coordinates; if None, agents list derived implicitly from distinct
            home positions of size len(...) not yet specified (Gate 6 keeps existing manual agent creation
            outside; this factory currently focuses on hooks + grid construction). For now, if None, creates
            zero agents (callers may extend in later gate revisions). This keeps scope minimal and avoids
            assumptions about desired agent count at factory call sites during incremental adoption.

        Notes
        -----
        * Keeps deterministic seeding via config.seed.
        * Attaches respawn & metrics hooks only if enable flags True.
        * Leaves perception radius un-applied (agents still reference existing constant) — unification deferred.
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

    def _handle_bilateral_exchange_movement(self, agent: "Agent", rng: random.Random) -> None:
        """Handle sophisticated movement logic for bilateral exchange mode.
        
        Implements tiered decision process:
        1. Check for nearby agents within perception radius
        2. If multiple agents found, select closest with tiebreak rules
        3. If exactly one agent found, pair up and path to meeting point
        4. If no agents found, move randomly
        5. Handle trading when co-located
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
            if agent.trade_partner_id is not None:
                partner = self._find_agent_by_id(agent.trade_partner_id)
                if partner is not None:
                    agent.end_trading_session(partner)
                else:
                    agent.clear_trade_partner()
            agent.force_deposit_once = True
            _debug_log_mode_change(agent, agent.mode, AgentMode.RETURN_HOME, "stagnation")
            agent.mode = AgentMode.RETURN_HOME
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
    def _unified_selection_pass(self, rng: random.Random, foraged_ids: set[int]) -> None:
        """Unified selection pass using spatial index + distance-discounted utility.

        Replaces earlier heuristic dual-path chooser. Maintains O(n) build +
        O(candidates) query via AgentSpatialGrid. Still honors forced deposit
        cycles and existing pairing states.
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
                a.mode = AgentMode.RETURN_HOME
                a.target = (int(a.home_x), int(a.home_y))  # type: ignore[arg-type]
                a.maybe_deposit()
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
                            a.mode = AgentMode.FORAGE
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
                                a.mode = AgentMode.FORAGE
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
                    a.mode = AgentMode.RETURN_HOME
                    a.target = (int(a.home_x), int(a.home_y))  # type: ignore[arg-type]
                else:
                    a.mode = AgentMode.IDLE
                    a.target = None
                continue
            kind, payload = choice
            if kind == "resource":
                pos = payload["pos"]  # type: ignore[index]
                if pos in claimed_resources:
                    # Already claimed; idle fallback
                    if a.carrying_total() > 0:
                        a.mode = AgentMode.RETURN_HOME
                        a.target = (int(a.home_x), int(a.home_y))  # type: ignore[arg-type]
                    else:
                        a.mode = AgentMode.IDLE
                        a.target = None
                    continue
                claimed_resources.add(pos)
                a.target = pos
                a.mode = AgentMode.FORAGE
                # Immediate attempt collect if already on cell
                collected = a.collect(self.grid)
                if collected:
                    foraged_ids.add(a.id)
                    a.target = None
                    # After collecting, check if should return home
                    if a.carrying_total() > 0:
                        a.mode = AgentMode.RETURN_HOME
                        a.target = (int(a.home_x), int(a.home_y))  # type: ignore[arg-type]
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
                            if a.collect(self.grid):
                                foraged_ids.add(a.id)
                                a.target = None
                                # After collecting, check if should return home
                                if a.carrying_total() > 0:
                                    a.mode = AgentMode.RETURN_HOME
                                    a.target = (int(a.home_x), int(a.home_y))  # type: ignore[arg-type]
                a.maybe_deposit()
            elif kind == "partner":
                pid = payload["partner_id"]  # type: ignore[index]
                if pid in claimed_partners:
                    # Partner already claimed; fallback
                    if a.carrying_total() > 0:
                        a.mode = AgentMode.RETURN_HOME
                        a.target = (int(a.home_x), int(a.home_y))  # type: ignore[arg-type]
                    else:
                        a.mode = AgentMode.IDLE
                        a.target = None
                    continue
                partner = agents_by_id.get(pid)
                if partner is None or getattr(partner, 'trade_partner_id', None) is not None:
                    continue
                claimed_partners.add(pid)
                a.pair_with_agent(partner)
                # Set both agents to MOVE_TO_PARTNER mode and set targets to meeting point
                from .agent import AgentMode
                _debug_log_mode_change(a, a.mode, AgentMode.MOVE_TO_PARTNER, "paired_for_trade")
                a.mode = AgentMode.MOVE_TO_PARTNER
                a.target = a.meeting_point
                _debug_log_mode_change(partner, partner.mode, AgentMode.MOVE_TO_PARTNER, "paired_for_trade")
                partner.mode = AgentMode.MOVE_TO_PARTNER
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
                        a.mode = _AM.RETURN_HOME
                        a.target = (int(a.home_x), int(a.home_y))  # type: ignore[arg-type]
                    elif a.at_home():
                        a.mode = _AM.IDLE  # Only idle at home
                    # If no cargo and not at home, let them continue seeking or return home
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
