"""Simulation configuration (Gate 5 defined; Gate 6 integration target).

Acts as the authoritative parameter bundle for constructing a
deterministic simulation. Gate 6 will introduce a factory method
(`Simulation.from_config`) that consumes this dataclass to attach
respawn and metrics hooks and seed internal RNG state.

Fields:
* ``grid_size``: (width, height)
* ``initial_resources``: iterable of (x,y[,type]) tuples
* ``perception_radius``: decision scan radius (mirrors constant; may be unified later)
* ``respawn_target_density``: desired occupancy fraction (0..1]
* ``respawn_rate``: fraction of deficit addressed per tick
* ``max_spawn_per_tick``: cap on newly spawned resources each tick
* ``seed``: base RNG seed (drives deterministic respawn & future stochastic systems)

Upcoming (Gate 6 extensions): enable flags for respawn / metrics and overlay default.
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
