"""Simulation configuration (Gate 5 scaffold).

Provides a single authoritative source for deterministic simulation
parameters. Logic will be added in Gate 5; current file is a planning
scaffold only.

Fields intentionally mirror Gate 5 scope:
- grid_size: (width, height) tuple
- initial_resources: sequence of (x,y,type) or (x,y) entries used to seed Grid
- perception_radius: agent decision scan radius (mirrors existing constant)
- respawn_target_density: desired proportion of cells occupied by resources
- respawn_rate: scalar controlling how aggressively deficit is reduced each tick
- max_spawn_per_tick: hard upper bound on resources spawned in a single step
- seed: base integer seed for RNG (drives respawn + any stochastic processes)

Validation & integration will be implemented when Gate 5 work begins.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Union

ResourceEntry = Union[tuple[int, int], tuple[int, int, str]]


@dataclass(slots=True)
class SimConfig:
    grid_size: tuple[int, int]
    initial_resources: Sequence[ResourceEntry]
    perception_radius: int
    respawn_target_density: float
    respawn_rate: float
    max_spawn_per_tick: int
    seed: int

    def validate(self) -> None:
        """Perform lightweight invariant checks.

        Strict enforcement deferred until full Gate 5 implementation.
        """
        gw, gh = self.grid_size
        if gw <= 0 or gh <= 0:
            raise ValueError("grid_size dimensions must be positive")
        if not (0.0 <= self.respawn_target_density <= 1.0):
            raise ValueError("respawn_target_density must be within [0,1]")
        if self.respawn_rate < 0:
            raise ValueError("respawn_rate must be non-negative")
        if self.max_spawn_per_tick < 0:
            raise ValueError("max_spawn_per_tick must be non-negative")


__all__ = ["SimConfig", "ResourceEntry"]
