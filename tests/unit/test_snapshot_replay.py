from __future__ import annotations

import random

from econsim.simulation.grid import Grid
from econsim.simulation.world import Simulation
from econsim.simulation.agent import Agent
from econsim.simulation.metrics import MetricsCollector
from econsim.simulation.respawn import RespawnScheduler
from econsim.simulation.snapshot import Snapshot
from econsim.preferences.cobb_douglas import CobbDouglasPreference


def build_sim(seed: int = 123) -> Simulation:
    grid = Grid(10, 10, [])
    pref = CobbDouglasPreference(alpha=0.5)
    agents = [Agent(id=i, x=i, y=i, preference=pref) for i in range(3)]
    sim = Simulation(grid=grid, agents=agents, config=None)
    sim.metrics_collector = MetricsCollector()
    sim._rng = random.Random(seed)  # type: ignore[attr-defined]
    sim.respawn_scheduler = RespawnScheduler(target_density=0.2, max_spawn_per_tick=20, respawn_rate=0.5)
    return sim


def advance(sim: Simulation, steps: int, *, decision: bool = False) -> None:
    rng = random.Random(999)
    for _ in range(steps):
        sim.step(rng, use_decision=decision)


def test_snapshot_replay_hash_prefix_preserved():
    # Take snapshot at initial state, then run N steps and capture per-step hash stream.
    # Replaying from the snapshot with same seeds should reproduce identical hash progression.
    seed = 77
    steps = 35
    sim = build_sim(seed=seed)
    initial_snapshot = Snapshot.from_sim(sim)
    rng = random.Random(999)
    forward_hashes: list[str] = []
    for _ in range(steps):
        sim.step(rng, use_decision=False)
        forward_hashes.append(sim.metrics_collector.determinism_hash())  # type: ignore[assignment]

    # Restore and replay
    sim2 = Snapshot.restore(initial_snapshot.serialize())
    sim2.metrics_collector = MetricsCollector()
    sim2._rng = random.Random(seed)  # type: ignore[attr-defined]
    sim2.respawn_scheduler = RespawnScheduler(target_density=0.2, max_spawn_per_tick=20, respawn_rate=0.5)
    rng2 = random.Random(999)
    replay_hashes: list[str] = []
    for _ in range(steps):
        sim2.step(rng2, use_decision=False)
        replay_hashes.append(sim2.metrics_collector.determinism_hash())  # type: ignore[assignment]
    assert replay_hashes == forward_hashes
