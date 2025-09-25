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
from .agent import Agent
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
    _respawn_interval: int | None = 1       # New: how frequently to invoke respawn (1 => every step, None/<=0 => disabled)
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
        if use_decision and forage_enabled:
            for agent in self.agents:
                try:
                    collected = agent.step_decision(self.grid)  # type: ignore[assignment]
                except TypeError:
                    # Older signature fallback (if any test constructs legacy Agent w/out updated method)
                    agent.step_decision(self.grid)  # type: ignore[misc]
                    collected = False
                if collected:
                    foraged_ids.add(agent.id)
        elif use_decision and not forage_enabled:
            # Decision mode but foraging disabled: optional behaviors depend on exchange flags.
            # If exchange also disabled, deterministically return home then idle.
            exchange_any = os.environ.get("ECONSIM_TRADE_DRAFT") == "1" or os.environ.get("ECONSIM_TRADE_EXEC") == "1"
            if not exchange_any:
                # Foraging disabled and no exchange features: remain idle (no carrying mutation).
                for agent in self.agents:
                    agent.mode = agent.mode.IDLE  # type: ignore[assignment]
                    agent.target = None
            else:
                # Exchange only: freeze position (no movement/collection) to allow observation of trade intents.
                pass
        else:  # legacy randomness path (foraging always implicit here if enabled)
            for agent in self.agents:
                agent.move_random(self.grid, rng)
            for agent in self.agents:
                agent.collect(self.grid)
        # Draft trade intent enumeration (feature flag; no state mutation)
        draft_enabled = os.environ.get("ECONSIM_TRADE_DRAFT") == "1"
        exec_enabled = os.environ.get("ECONSIM_TRADE_EXEC") == "1"
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
                            mc.trades_executed += 1  # type: ignore[attr-defined]
                            # Update realized utility gain (approx) using stored delta_utility
                            try:
                                mc.realized_utility_gain_total += float(getattr(executed, "delta_utility", 0.0))  # type: ignore[attr-defined]
                            except Exception:  # pragma: no cover
                                pass
                            # Fairness round increment (Phase 3 advisory metric)
                            try:
                                mc.fairness_round += 1  # type: ignore[attr-defined]
                            except Exception:
                                pass
                            # Record last executed trade summary
                            mc.last_executed_trade = {
                                "step": self._steps,
                                "seller": executed.seller_id,
                                "buyer": executed.buyer_id,
                                "give_type": executed.give_type,
                                "take_type": executed.take_type,
                                "delta_utility": getattr(executed, "delta_utility", 0.0),
                            }
                            mc.trade_ticks += 1  # type: ignore[attr-defined]
                        else:
                            mc.no_trade_ticks += 1  # type: ignore[attr-defined]
                except Exception:  # pragma: no cover
                    pass
        else:
            self.trade_intents = None
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

            for idx, (x, y) in enumerate(agent_positions):
                pref = _pref_factory(idx)  # type: ignore[misc]
                agents.append(Agent(id=idx, x=int(x), y=int(y), preference=pref))

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


__all__ = ["Simulation"]
