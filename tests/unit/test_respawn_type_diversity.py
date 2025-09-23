"""Test that respawn scheduler now produces both resource types deterministically.

We run a small simulation with respawn enabled and ensure that after several
steps both 'A' and 'B' types appear on the grid for a fixed seed.
"""
from __future__ import annotations

import random

from econsim.simulation.world import Simulation
from econsim.simulation.config import SimConfig


def build_sim() -> Simulation:
    cfg = SimConfig(
        grid_size=(10,6),
        initial_resources=[],
        perception_radius=8,
        respawn_target_density=0.2,
        respawn_rate=0.6,
        max_spawn_per_tick=8,
        seed=1234,
        enable_respawn=True,
        enable_metrics=True,
    )
    return Simulation.from_config(cfg, agent_positions=[(0,0)])


def test_respawn_includes_both_types():
    sim = build_sim()
    rng = random.Random(777)
    for _ in range(25):
        sim.step(rng, use_decision=False)
    types = {t for (_,_,t) in sim.grid.iter_resources()}
    assert 'A' in types, 'Type A missing after respawn steps'
    assert 'B' in types, 'Type B missing after respawn steps'
