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
from typing import Any, Optional
import random as _random

try:  # Local import guard (optional config not always present yet)
    from .config import SimConfig  # type: ignore
except Exception:  # pragma: no cover
    SimConfig = Any  # fallback for type checkers

from .agent import Agent
from .grid import Grid
from .respawn import RespawnScheduler  # type: ignore
from .metrics import MetricsCollector  # type: ignore


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
        if use_decision:
            for agent in self.agents:
                agent.step_decision(self.grid)
        else:  # legacy randomness path
            for agent in self.agents:
                agent.move_random(self.grid, rng)
            for agent in self.agents:
                agent.collect(self.grid)
    # Respawn hook (inert if scheduler not attached)
        if self.respawn_scheduler is not None and self._rng is not None:
            # Only invoke respawn when interval condition satisfied.
            if self._respawn_interval and self._respawn_interval > 0:
                if (self._steps % self._respawn_interval) == 0:
                    try:
                        self.respawn_scheduler.step(self.grid, self._rng, step_index=self._steps)
                    except Exception as exc:  # pragma: no cover - defensive placeholder
                        print(f"[RespawnWarning] scheduler error: {exc}")
        # Metrics hook (placeholder logic handled inside collector)
        if self.metrics_collector is not None:
            try:
                self.metrics_collector.record(self._steps, self)
            except Exception as exc:  # pragma: no cover - defensive
                print(f"[MetricsWarning] record error: {exc}")
        self._steps += 1

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
