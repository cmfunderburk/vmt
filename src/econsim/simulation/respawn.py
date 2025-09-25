"""Resource respawn scheduler (introduced Gate 5, factory-attached in Gate 6).

Maintains a target *density* of resources using a deterministic RNG. The
scheduler replenishes consumed resources to maintain the target count at
configurable intervals (controlled by simulation stepping logic).

Algorithm Summary:
1. Compute ``target_count = floor(target_density * total_cells)``.
2. If current count < target, compute deficit.
3. Spawn enough new resources in empty cells to restore target count.
4. Randomly assign resource types (A or B) with equal probability.

Capabilities:
* Deterministic replenishment using seeded RNG
* Maintains exact target density after consumption
* Random distribution of both position and resource type
* Interval-based respawn controlled by simulation step logic

Example: 10x10 grid (100 cells), density 0.25 (25 resources target)
- Turn 1: 25 resources, agents collect 4 → 21 remain
- Turn 2: 21 resources, agents collect 4 → 17 remain  
- Turn 3: 17 resources, agents collect 4 → 13 remain, then respawn adds 12 → 25 total
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import List, Tuple

from .grid import Grid


@dataclass(slots=True)
class RespawnScheduler:
    """Maintain a target density of resources by replenishing consumed resources.

    Parameters
    ----------
    target_density : float
        Desired fraction (0..1] of cells containing a resource.
    max_spawn_per_tick : int
        Hard cap for how many resources can be spawned in a single tick.
    respawn_rate : float
        Fraction (0..1] of the current deficit we attempt to fill each tick.
    """

    target_density: float
    max_spawn_per_tick: int
    respawn_rate: float  # fraction of deficit addressed each tick (0..1]

    def __post_init__(self) -> None:  # pragma: no cover (simple validation)
        if self.max_spawn_per_tick < 0:
            raise ValueError("max_spawn_per_tick must be >=0")
        if not (self.target_density >= 0.0):
            raise ValueError("target_density must be >=0")
        if not (self.respawn_rate >= 0.0):
            raise ValueError("respawn_rate must be >=0")

    def step(self, grid: Grid, rng: random.Random, *, step_index: int) -> int:  # noqa: ARG002
        """Spawn resources, moving the grid toward the target density.

        Deterministic with respect to the provided RNG and the existing grid
        state. Returns the number of newly spawned resources for this tick.
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

        # Enumerate ALL empty cells (row-major) then shuffle for a uniform selection over the entire grid.
        # Previous prefix+shuffle approach biased toward top-left when deficit small (early break).
        # Complexity: O(#empties). With typical grids (<= 64x64) and modest densities this is acceptable and
        # remains linear in grid cells (still within performance guardrails). If future scalability requires
        # optimization we can re‑introduce a stratified sampling method behind a feature flag.
        occupied = getattr(grid, "_resources", {})
        if current >= total_cells:  # grid full
            return 0
        empties: List[Tuple[int, int]] = []
        for y in range(grid.height):
            for x in range(grid.width):
                if (x, y) not in occupied:
                    empties.append((x, y))
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
