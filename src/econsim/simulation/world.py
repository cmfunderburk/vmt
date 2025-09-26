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
from dataclasses import dataclass
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
                executed = execute_single_intent(intents, agents_by_id)
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
        """Perform unified resource/partner candidate evaluation and movement.

        Process:
        1. Precompute best resource candidate per agent (no mutation besides storing helper data)
        2. Determine partner scores via localized search (bounded by perception radius constant)
        3. Decide per agent (stable order) with reservation sets to avoid duplicate claims
        4. Execute one-step movement + interactions analogous to existing decision path
        """
        from .constants import default_PERCEPTION_RADIUS
        from .agent import AgentMode
        # Precompute resource candidates
        resource_choices: dict[int, tuple[tuple[int,int] | None, float, tuple[float,int,int,int] | None]] = {}
        for a in self.agents:
            resource_choices[a.id] = a.compute_best_resource_candidate(self.grid)
        # Reservation sets
        claimed_resources: set[tuple[int,int]] = set()
        claimed_partners: set[int] = set()
        # Partner availability baseline
        agents_by_id = {a.id: a for a in self.agents}
        # Iterate in stable agent order
        for a in self.agents:
            if a.force_deposit_once:
                # Forced deposit cycle: ensure RETURN_HOME path
                a.mode = AgentMode.RETURN_HOME
                a.target = (int(a.home_x), int(a.home_y))  # type: ignore[arg-type]
                a.step_decision(self.grid)  # Reuse deposit/move logic
                continue
            # Skip dead or currently paired/trading agents (let exchange movement manage them)
            if getattr(a, 'trade_partner_id', None) is not None:
                # Paired agents will be moved in a post-pass
                continue
            best_resource_pos, best_delta_u, best_key = resource_choices[a.id]
            # Partner candidate search (radius-limited) - simple divergence heuristic
            perception = default_PERCEPTION_RADIUS
            partner_choice: tuple[float, tuple[float,int,int,int], int] | None = None  # (score, tie_key, partner_id)
            for other in self.agents:
                if other.id == a.id:
                    continue
                if other.id in claimed_partners:
                    continue
                if getattr(other, 'trade_partner_id', None) is not None:
                    continue
                dist = abs(other.x - a.x) + abs(other.y - a.y)
                if dist > perception:
                    continue
                inv_div = abs(sum(a.carrying.values()) - sum(other.carrying.values()))
                partner_score = (inv_div + 1.0) / (1 + dist)
                tie = (-partner_score, dist, min(a.id, other.id), max(a.id, other.id))
                if partner_choice is None or tie < partner_choice[1]:
                    partner_choice = (partner_score, tie, other.id)
            # Decide between resource and partner
            chosen_kind = None
            chosen_target = None
            if partner_choice is not None and best_key is not None:
                # Compare tie-keys directly with optional slight resource preference (no multiplier now)
                if partner_choice[1] < best_key:  # partner strictly better
                    chosen_kind = 'partner'
                    chosen_target = partner_choice[2]
                else:
                    chosen_kind = 'resource'
                    chosen_target = best_resource_pos
            elif partner_choice is not None and best_key is None:
                chosen_kind = 'partner'
                chosen_target = partner_choice[2]
            elif best_key is not None:
                chosen_kind = 'resource'
                chosen_target = best_resource_pos
            # Apply decision
            if chosen_kind == 'resource' and isinstance(chosen_target, tuple):
                if chosen_target not in claimed_resources:
                    claimed_resources.add(chosen_target)
                    a.target = chosen_target
                    a.mode = AgentMode.FORAGE
                    collected = a.collect(self.grid)
                    if collected:
                        foraged_ids.add(a.id)
                        a.target = None
                    else:
                        # Move one step toward target greedily (duplicate of movement logic) if not already there
                        if a.target is not None and (a.x, a.y) != a.target:
                            tx, ty = a.target
                            dx = tx - a.x
                            dy = ty - a.y
                            if abs(dx) > abs(dy):
                                a.x += 1 if dx > 0 else -1
                            elif dy != 0:
                                a.y += 1 if dy > 0 else -1
                        # Try collect again if moved onto resource
                        if a.target is not None and (a.x, a.y) == a.target:
                            if self.grid.has_resource(a.x, a.y):
                                if a.collect(self.grid):
                                    foraged_ids.add(a.id)
                                    a.target = None
                    a.maybe_deposit()
                    a.current_unified_task = ('resource', chosen_target)
                else:
                    a.current_unified_task = None
            elif chosen_kind == 'partner' and isinstance(chosen_target, int):
                partner = agents_by_id.get(chosen_target)
                if partner is not None and partner.id not in claimed_partners and partner.trade_partner_id is None:
                    claimed_partners.add(partner.id)
                    # Establish pairing (mutual) and move toward meeting point
                    a.pair_with_agent(partner)
                    a.current_unified_task = ('partner', partner.id)
                    a.move_toward_meeting_point(self.grid)
                else:
                    # Fallback: no valid partner, attempt resource movement if available
                    if best_key is not None and best_resource_pos not in claimed_resources:
                        claimed_resources.add(best_resource_pos)  # type: ignore[arg-type]
                        a.target = best_resource_pos
                        a.mode = AgentMode.FORAGE
                        a.current_unified_task = ('resource', best_resource_pos)
                a.maybe_deposit()
            else:
                # No choice => idle fallback / deposit if carrying
                if a.carrying and a.carrying_total() > 0:
                    a.mode = AgentMode.RETURN_HOME
                    a.target = (int(a.home_x), int(a.home_y))  # type: ignore[arg-type]
                else:
                    # Explicit idle when no resources or partner choice (empty grid path)
                    a.mode = AgentMode.IDLE
                    a.target = None
                a.current_unified_task = None
        # Final idle normalization: if grid has zero resources and agent still marked FORAGE with no target, set IDLE
        try:
            any_resources = any(True for _ in self.grid.iter_resources())
        except Exception:
            any_resources = True  # conservative
        if not any_resources:
            from .agent import AgentMode as _AM
            for a in self.agents:
                if a.mode == _AM.FORAGE and (a.target is None):
                    a.mode = _AM.IDLE
        # Post-pass: advance movement for paired agents toward meeting point (both sides) so they converge.
        from .agent import AgentMode as _AM2
        for a in self.agents:
            if a.trade_partner_id is not None:
                partner = self._find_agent_by_id(a.trade_partner_id)
                if partner is None:
                    a.clear_trade_partner()
                    continue
                # Only move if not yet co-located
                if not a.is_colocated_with(partner):
                    a.move_toward_meeting_point(self.grid)
                # After movement, if co-located leave pairing for intents to trigger trade via enumeration.
                # (Optional future: clear pairing if no intents after N steps.)


__all__ = ["Simulation"]
