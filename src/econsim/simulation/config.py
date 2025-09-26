"""Simulation configuration (Gate 6 integrated; evolved from Gate 5 draft).

Acts as the authoritative parameter bundle for constructing a
deterministic simulation. Factory method `Simulation.from_config` consumes
this dataclass to attach respawn / metrics hooks and seed internal RNG state.

Fields:
* ``grid_size``: (width, height)
* ``initial_resources``: iterable of (x,y[,type]) tuples
* ``perception_radius``: decision scan radius (mirrors constant; may be unified later)
* ``respawn_target_density``: desired occupancy fraction (0..1]
* ``respawn_rate``: fraction of deficit addressed per tick
* ``max_spawn_per_tick``: cap on newly spawned resources each tick
* ``seed``: base RNG seed (drives deterministic respawn & future stochastic systems)

Includes enable flags for respawn / metrics; overlay toggle remains a GUI concern.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Union

ResourceEntry = Union[tuple[int, int], tuple[int, int, str]]


@dataclass(slots=True)
class SimConfig:
    grid_size: tuple[int, int]
    initial_resources: Sequence[ResourceEntry]
    perception_radius: int = 8
    respawn_target_density: float = 0.25
    respawn_rate: float = 0.25  # Default to 25% (partial replenishment) - now GUI configurable
    max_spawn_per_tick: int = 100  # High enough to handle full deficit respawn
    seed: int = 0
    enable_respawn: bool = True
    enable_metrics: bool = True
    viewport_size: int = 320
    # Unified selection distance discount scaling factor (k) used in
    # ΔU_base / (1 + k * distance^2). Range constrained in validate().
    distance_scaling_factor: float = 0.0

    def validate(self) -> None:
        """Perform lightweight invariant checks (Gate 6 integration).

        Keeps validation minimal to avoid premature rigidity; expands in later gates
        if configuration surface grows.
        """
        gw, gh = self.grid_size
        if gw <= 0 or gh <= 0:
            raise ValueError("grid_size dimensions must be positive")
        if not (0.0 <= self.respawn_target_density <= 1.0):
            raise ValueError("respawn_target_density must be within [0,1]")
        if self.respawn_rate < 0:
            raise ValueError("respawn_rate must be non-negative")
        if not (320 <= self.viewport_size <= 800):
            raise ValueError("viewport_size must be within [320, 800]")
        if self.max_spawn_per_tick < 0:
            raise ValueError("max_spawn_per_tick must be non-negative")
        if not (0.0 <= self.distance_scaling_factor <= 10.0):
            raise ValueError("distance_scaling_factor must be within [0,10]")
        # Boolean flags implicitly validated; could add type checks if untrusted sources used.


__all__ = ["SimConfig", "ResourceEntry"]
