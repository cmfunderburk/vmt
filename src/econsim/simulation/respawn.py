"""Deterministic resource density maintenance system.

Maintains target resource density by replenishing consumed resources using
deterministic RNG. Integrates with simulation factory pattern for configurable
resource regeneration across economic scenarios.

Algorithm:
1. Calculate target count from density × total cells
2. Determine deficit between target and current resources  
3. Spawn resources in randomly selected empty cells
4. Assign resource types (A/B) with equal probability

Capabilities:
* Deterministic replenishment preserving simulation reproducibility
* Configurable density targets and spawn rate limiting
* Uniform spatial distribution across grid
* Integration with simulation stepping intervals

Example: 10×10 grid, 0.25 density targets 25 resources. After consumption
drops count to 13, respawn adds 12 to restore target density.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import List, Tuple

from .grid import Grid


@dataclass(slots=True)
class RespawnScheduler:
    """Deterministic resource density scheduler with configurable spawn limits.
    
    Maintains target resource density through deficit-based replenishment,
    ensuring reproducible behavior via seeded RNG integration.
    
    Args:
        target_density: Desired fraction (0..1] of cells containing a resource
        max_spawn_per_tick: Maximum resources spawned per step (rate limiting)
        respawn_rate: Fraction (0..1] of deficit addressed each step
    """

    target_density: float
    max_spawn_per_tick: int
    respawn_rate: float  # fraction of deficit addressed each tick (0..1]

    def __post_init__(self) -> None:
        """Validate configuration parameters for scheduler initialization."""
        if self.max_spawn_per_tick < 0:
            raise ValueError("max_spawn_per_tick must be >=0")
        if not (self.target_density >= 0.0):
            raise ValueError("target_density must be >=0")
        if not (self.respawn_rate >= 0.0):
            raise ValueError("respawn_rate must be >=0")

    def step(self, grid: Grid, rng: random.Random, *, step_index: int) -> int:  # noqa: ARG002
        """Execute one respawn cycle, spawning resources toward target density.
        
        Args:
            grid: Grid to spawn resources on
            rng: Deterministic RNG for reproducible placement
            step_index: Current simulation step (unused but kept for interface)
            
        Returns:
            Number of resources spawned this step
        """
        # Fast exits on disabled / degenerate configurations
        if self.max_spawn_per_tick == 0:
            return 0

        total_cells = grid.width * grid.height
        if total_cells <= 0:
            return 0

        # Clamp densities/rates defensively (avoid >1 runaway)
        td = 1.0 if self.target_density > 1.0 else float(self.target_density)
        rr = 1.0 if self.respawn_rate > 1.0 else float(self.respawn_rate)
        if td <= 0.0 or rr <= 0.0:
            return 0

        # Target resource count (floor for density <=1.0)
        target_count = math.floor(td * total_cells)
        if target_count <= 0:
            return 0

        current = grid.resource_count()
        deficit = target_count - current
        if deficit <= 0:
            return 0  # already at or above target (no overshoot allowed)

        desired_spawn = math.ceil(deficit * rr)
        to_spawn = min(desired_spawn, self.max_spawn_per_tick, deficit)
        if to_spawn <= 0:
            return 0

        # Get empty cells using optimized cache (O(empty_count) instead of O(width*height))
        if current >= total_cells:  # grid full
            return 0
        empties = grid.get_empty_cells_list()
        if not empties:
            return 0
        rng.shuffle(empties)
        spawn_list = empties[:to_spawn]

        spawned = 0
        for (x, y) in spawn_list:
            # Randomly assign resource type (A or B) with equal probability
            rtype = "A" if rng.random() < 0.5 else "B"
            grid.add_resource(x, y, rtype)
            spawned += 1

        # Ensure we never overshoot target (defensive assertion)
        assert grid.resource_count() <= target_count, "Respawn overshoot target density"
        return spawned


__all__ = ["RespawnScheduler"]
