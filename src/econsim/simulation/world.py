"""Simulation coordinator (Gate 3).

Manages a collection of agents and a grid. Provides deterministic step
progression given a seeded RNG. Each step:
 1. Each agent moves (random placeholder logic).
 2. Each agent attempts to collect resource at its location.

Deferrals:
- Utility-based targeted movement.
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

    def step(self, rng: random.Random) -> None:
        """Advance simulation by one tick (deterministic with provided RNG)."""
        # Movement phase
        for agent in self.agents:
            agent.move_random(self.grid, rng)
        # Collection phase
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
