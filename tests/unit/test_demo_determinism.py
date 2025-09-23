"""Determinism regression guard for demo script components.

Purpose: Ensure that running a small decision-mode simulation with a fixed
seed and preference produces an identical determinism hash across two fresh
Simulation instances.
"""
from __future__ import annotations

import random

from econsim.simulation.world import Simulation
from econsim.simulation.grid import Grid
from econsim.simulation.agent import Agent
from econsim.simulation.metrics import MetricsCollector
from econsim.preferences.cobb_douglas import CobbDouglasPreference

STEPS = 15
SEED = 4321


def _build() -> Simulation:
    # Small deterministic grid pattern
    grid = Grid(12, 8)
    idx = 0
    for y in range(0, grid.height, 2):
        for x in range(0, grid.width, 2):
            grid.add_resource(x, y, "A" if idx % 2 == 0 else "B")
            idx += 1
    pref = CobbDouglasPreference(alpha=0.5)
    agents = [Agent(id=0, x=0, y=0, preference=pref)]
    sim = Simulation(grid=grid, agents=agents, config=None)
    sim._rng = random.Random(SEED)  # type: ignore[attr-defined]
    sim.metrics_collector = MetricsCollector()
    return sim


def _run(sim: Simulation) -> str:
    rng = random.Random(SEED + 99)
    for _ in range(STEPS):
        sim.step(rng, use_decision=True)
    return sim.metrics_collector.determinism_hash()  # type: ignore[attr-defined]


def test_demo_hash_stability():
    h1 = _run(_build())
    h2 = _run(_build())
    assert h1 == h2, f"Determinism hash diverged: {h1} vs {h2}"