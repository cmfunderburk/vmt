"""Simulation coordinator (Gates 3–5 implemented).

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


@dataclass(slots=True)
class Simulation:
    grid: Grid
    agents: list[Agent]
    _steps: int = 0
    config: Optional[Any] = None  # SimConfig when available (Gate 5)
    _rng: _random.Random | None = None      # Internal RNG (respawn/metrics later)
    respawn_scheduler: Any | None = None    # Gate 5: optional RespawnScheduler
    metrics_collector: Any | None = None    # Gate 5: optional MetricsCollector

    def __post_init__(self) -> None:  # pragma: no cover (simple init)
        if self.config is not None and self._rng is None:
            seed = getattr(self.config, "seed", 0)
            self._rng = _random.Random(int(seed))

    def step(self, rng: random.Random, *, use_decision: bool = False) -> None:
        """Advance simulation by one tick.

        Parameters:
            rng: external RNG (legacy random movement path); retained until Gate 5 removes need.
            use_decision: when True, run deterministic decision logic; when False, use legacy random walk.

        Gate 5 Note: internal self._rng will drive new dynamic systems (respawn, metrics) while
        preserving current signature to avoid test churn in intermediate commits.
        """
        if use_decision:
            for agent in self.agents:
                agent.step_decision(self.grid)
        else:  # legacy randomness path
            for agent in self.agents:
                agent.move_random(self.grid, rng)
            for agent in self.agents:
                agent.collect(self.grid)
        # Respawn hook (Gate 5 - inert until scheduler provided)
        if self.respawn_scheduler is not None and self._rng is not None:
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


__all__ = ["Simulation"]
