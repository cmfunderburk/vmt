"""Simulation coordinator (Gate 4 evolving).

Gate 3 behavior: random movement + collection.
Gate 4 Phase P3: introduce preference-driven decision loop (greedy 1-step toward selected target)
while maintaining deterministic progression under a seeded RNG.

Step phases (decision mode):
 1. Each agent runs decision step (target select if needed, move one cell, collect, maybe deposit).

Remaining deferrals:
- Multi-phase update ordering strategies.
- Concurrency / parallel stepping.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Optional
import random as _random

try:  # Local import guard (Gate 5 scaffold)
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
        # Gate 5 placeholder: respawn & metrics hooks will be inserted here using self._rng
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
