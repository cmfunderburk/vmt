from __future__ import annotations

import random

from econsim.simulation.grid import Grid
from econsim.simulation.world import Simulation
from econsim.simulation.respawn import RespawnScheduler
from econsim.simulation.agent import Agent
from econsim.preferences.cobb_douglas import CobbDouglasPreference

TARGET_DENSITY = 0.25


def make_sim(width: int = 20, height: int = 20, n_agents: int = 3, seed: int = 123) -> Simulation:
    grid = Grid(width, height, [])
    pref = CobbDouglasPreference(alpha=0.5)
    agents: list[Agent] = []
    for i in range(n_agents):
        x = (i * 3) % width
        y = (i * 5) % height
        agents.append(Agent(id=i, x=x, y=y, preference=pref))
    sim = Simulation(grid=grid, agents=agents, config=None)
    # Seed internal RNG deterministically (public attribute not exposed yet; acceptable internal access in tests)
    sim._rng = random.Random(seed)  # type: ignore[attr-defined]
    sim.respawn_scheduler = RespawnScheduler(
        target_density=TARGET_DENSITY,
        max_spawn_per_tick=50,
        respawn_rate=0.5,
    )
    return sim


def run_until_converged(sim: Simulation, steps: int = 80):
    ext_rng = random.Random(999)  # legacy movement rng (agents currently decisionless here)
    for _ in range(steps):
        sim.step(ext_rng, use_decision=False)


def test_density_converges_within_tolerance():
    sim = make_sim()
    run_until_converged(sim, steps=80)
    total_cells = sim.grid.width * sim.grid.height
    target_count = int(TARGET_DENSITY * total_cells)
    count = sim.grid.resource_count()
    # Allow ±5% relative tolerance and also permit exactly target_count - 1 due to ceil/floor interplay
    lower = int(target_count * 0.95)
    upper = target_count  # we never overshoot target by design
    assert lower <= count <= upper, (lower, count, upper)


def test_never_exceeds_target():
    sim = make_sim()
    run_until_converged(sim, steps=120)
    total_cells = sim.grid.width * sim.grid.height
    target_count = int(TARGET_DENSITY * total_cells)
    assert sim.grid.resource_count() <= target_count


def test_deterministic_sequence_same_seed():
    sim1 = make_sim(seed=42)
    sim2 = make_sim(seed=42)
    run_until_converged(sim1, steps=50)
    run_until_converged(sim2, steps=50)
    # Compare serialized resource lists (sorted in serialization)
    assert sim1.grid.serialize()["resources"] == sim2.grid.serialize()["resources"]


def test_different_seed_diverges():
    sim1 = make_sim(seed=41)
    sim2 = make_sim(seed=42)
    run_until_converged(sim1, steps=40)
    run_until_converged(sim2, steps=40)
    # High probability difference; if equal (extremely unlikely) extend run
    if sim1.grid.serialize()["resources"] == sim2.grid.serialize()["resources"]:
        run_until_converged(sim1, steps=20)
        run_until_converged(sim2, steps=20)
    assert sim1.grid.serialize()["resources"] != sim2.grid.serialize()["resources"]


def test_zero_rate_no_op():
    sim = make_sim()
    # Replace scheduler with zero-rate config
    sim.respawn_scheduler = RespawnScheduler(
        target_density=TARGET_DENSITY,
        max_spawn_per_tick=10,
        respawn_rate=0.0,
    )
    ext_rng = random.Random(5)
    for _ in range(20):
        sim.step(ext_rng, use_decision=False)
    assert sim.grid.resource_count() == 0
