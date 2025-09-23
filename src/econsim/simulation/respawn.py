"""Resource respawn scheduler (introduced Gate 5, factory-attached in Gate 6).

Maintains a target *density* of resources using a deterministic RNG. Each
step moves the grid toward the target by spawning at most a bounded number
of new resources in empty cells. Enumeration of candidate cells is
deterministic (row-major) and randomized only by a seeded shuffle for
reproducibility.

Algorithm Summary:
1. Compute ``target_count = floor(target_density * total_cells)``.
2. If below target, compute deficit and desired spawn (deficit * respawn_rate).
3. Enumerate a limited prefix of empty cells (early stop) → shuffle → take slice.
4. Insert new resources (currently all type 'A').

Capabilities:
* Deterministic convergence toward density without overshoot (assert enforced)
* Bounded per-tick work via ``max_spawn_per_tick`` & early enumeration stop

Deferred / Not Yet Included:
* Multi-type respawn balancing (A vs B proportion strategies)
* Spatial clustering / exclusion zones
* Adaptive spawn rate modulation based on consumption velocity
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import List, Tuple

from .grid import Grid


@dataclass(slots=True)
class RespawnScheduler:
    """Maintain a target density of resources.

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
    respawn_rate: float  # conceptual: fraction of deficit addressed each tick (0..1]

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

        # Enumerate empty cells deterministically (row-major) then shuffle
        occupied = getattr(grid, "_resources", {})  # trusted internal use
        empties: List[Tuple[int, int]] = []
        if current >= total_cells:  # grid full
            return 0
        target_collect = to_spawn * 2  # modest oversample for shuffle randomness
        for y in range(grid.height):
            for x in range(grid.width):
                if (x, y) not in occupied:
                    empties.append((x, y))
                    if len(empties) >= target_collect:
                        break
            if len(empties) >= target_collect:
                break
        if not empties:
            return 0

        rng.shuffle(empties)  # deterministic under RNG
        spawn_list = empties[:to_spawn]

        spawned = 0
        for (x, y) in spawn_list:
            grid.add_resource(x, y, "A")  # default type A for now
            spawned += 1

        # Ensure we never overshoot target (defensive assertion)
        assert grid.resource_count() <= target_count, "Respawn overshoot target density"
        return spawned


__all__ = ["RespawnScheduler"]
