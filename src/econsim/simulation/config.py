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
    respawn_rate: float = 0.1
    max_spawn_per_tick: int = 3
    seed: int = 0
    enable_respawn: bool = True
    enable_metrics: bool = True
    # Gate 7 (trading primitive) feature flag: when False trading subsystem is inert and
    # determinism hash matches prior gates. Append-only to preserve config ordering contract.
    enable_trading: bool = False

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
        if self.max_spawn_per_tick < 0:
            raise ValueError("max_spawn_per_tick must be non-negative")
        # Boolean flags implicitly validated; could add type checks if untrusted sources used.


__all__ = ["SimConfig", "ResourceEntry"]
