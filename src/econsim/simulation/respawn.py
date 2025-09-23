"""Resource respawn scheduler (Gate 5 scaffold).

Purpose: Maintain target resource density over time in a deterministic
manner given a seeded RNG. This scaffold defines the public surface;
implementation will be added in Gate 5 proper.

Planned algorithm (later):
- Compute target_count = floor(target_density * (grid.width * grid.height)).
- If current < target_count, compute deficit and spawn up to
  min(deficit, max_spawn_per_tick, respawn_rate_scaled_amount).
- Candidate empty cells enumerated deterministically (sorted), then
  sampled using RNG for reproducibility.

Non-goals (Gate 5): spatial clustering heuristics, weighting by distance,
denial zones around agents.
"""
from __future__ import annotations

from dataclasses import dataclass
import random

from .grid import Grid


@dataclass(slots=True)
class RespawnScheduler:
    target_density: float
    max_spawn_per_tick: int
    respawn_rate: float  # conceptual: fraction of deficit addressed each tick (0..1]

  def step(self, grid: Grid, rng: random.Random, *, step_index: int) -> int:  # pragma: no cover (placeholder)
        """Attempt to spawn resources; returns number spawned.

        Placeholder implementation: returns 0 (no spawning). Real logic
        added in Gate 5 once tests are in place.
        """
        return 0


__all__ = ["RespawnScheduler"]
