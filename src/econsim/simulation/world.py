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
from typing import Any

from .agent import Agent
from .grid import Grid


@dataclass(slots=True)
class Simulation:
    grid: Grid
    agents: list[Agent]
    _steps: int = 0

    def step(self, rng: random.Random, *, use_decision: bool = False) -> None:
        """Advance simulation by one tick.

        If use_decision is True (default), invokes agent decision logic (Gate 4).
        Else fall back to legacy random movement + collection (for comparative tests, if needed).
        Deterministic under provided RNG for random branch and deterministic logic branch given fixed state.
        """
        if use_decision:
            for agent in self.agents:
                agent.step_decision(self.grid)
        else:  # legacy behavior
            for agent in self.agents:
                agent.move_random(self.grid, rng)
            for agent in self.agents:
                agent.collect(self.grid)
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
