"""Test that manual steps in legacy (non-decision) mode use random walk path.

We compare position after N manual steps under legacy vs decision mode.
Given deterministic seed, decision path should follow greedy movement toward
nearest beneficial resource deterministically, while legacy random path
should (with overwhelming probability) diverge from that specific path.

Acceptance: positions differ OR (if equal) the hash differs after same number of steps.
If a rare collision occurs (extremely unlikely with chosen setup), test retries with a different seed.
"""
from __future__ import annotations

import random

from econsim.simulation.world import Simulation
from econsim.simulation.config import SimConfig
from econsim.preferences.factory import PreferenceFactory

STEPS = 12


def build_sim(seed: int):
    cfg = SimConfig(
        grid_size=(10, 10),
        initial_resources=[(5, 5, "A"), (2, 8, "B"), (8, 2, "A")],
        seed=seed,
        enable_respawn=False,
        enable_metrics=True,
    )
    pref = lambda i: PreferenceFactory.create("cobb_douglas", alpha=0.5)  # type: ignore[arg-type]
    return Simulation.from_config(cfg, pref, agent_positions=[(0, 0)])


def run_decision(seed: int):
    sim = build_sim(seed)
    rng = random.Random(seed)
    for _ in range(STEPS):
        sim.step(rng, use_decision=True)
    agent = sim.agents[0]
    pos = (agent.x, agent.y)
    h = sim.metrics_collector.determinism_hash()
    return pos, h


def run_legacy(seed: int):
    sim = build_sim(seed)
    rng = random.Random(seed)
    for _ in range(STEPS):
        sim.step(rng, use_decision=False)
    agent = sim.agents[0]
    pos = (agent.x, agent.y)
    h = sim.metrics_collector.determinism_hash()
    return pos, h


def test_legacy_mode_manual_random_walk_diverges():
    # Try up to 3 seeds in vanishingly unlikely case of identical positions+hash.
    for base_seed in (101, 202, 303):
        d_pos, d_hash = run_decision(base_seed)
        l_pos, l_hash = run_legacy(base_seed)
        if d_pos != l_pos or d_hash != l_hash:
            # Success condition: at least one differs
            assert True
            return
    raise AssertionError("Legacy random walk path did not diverge from decision path across retry seeds")
