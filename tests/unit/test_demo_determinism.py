"""Determinism regression guard for demo script components.

Purpose: Ensure that running a small decision-mode simulation with a fixed
seed and preference produces an identical determinism hash across two fresh
Simulation instances.
"""
from __future__ import annotations

import random

from econsim.simulation.world import Simulation
from econsim.simulation.grid import Grid
from econsim.simulation.config import SimConfig

STEPS = 15
SEED = 4321


def _build() -> Simulation:
    # Small deterministic grid pattern
    grid_tmp = Grid(12,8)
    idx=0
    for y in range(0, grid_tmp.height, 2):
        for x in range(0, grid_tmp.width, 2):
            grid_tmp.add_resource(x,y, "A" if idx %2==0 else "B")
            idx+=1
    init_resources = grid_tmp.serialize()["resources"]
    cfg = SimConfig(
        grid_size=(grid_tmp.width, grid_tmp.height),
        initial_resources=init_resources,
        perception_radius=8,
        respawn_target_density=0.0,
        respawn_rate=0.0,
        max_spawn_per_tick=0,
        seed=SEED,
        enable_respawn=False,
        enable_metrics=True,
    )
    sim = Simulation.from_config(cfg, agent_positions=[(0,0)])
    return sim


def _run(sim: Simulation) -> str:
    rng = random.Random(SEED + 99)
    for _ in range(STEPS):
        sim.step(rng)
    return sim.metrics_collector.determinism_hash()  # type: ignore[attr-defined]


def test_demo_hash_stability():
    h1 = _run(_build())
    h2 = _run(_build())
    assert h1 == h2, f"Determinism hash diverged: {h1} vs {h2}"