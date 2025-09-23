from __future__ import annotations

import random

from econsim.simulation.grid import Grid
from econsim.simulation.world import Simulation
from econsim.simulation.agent import Agent
from econsim.simulation.metrics import MetricsCollector
from econsim.simulation.respawn import RespawnScheduler
from econsim.preferences.cobb_douglas import CobbDouglasPreference


def build_sim(seed: int, with_respawn: bool = True) -> Simulation:
	grid = Grid(12, 8, [])
	pref = CobbDouglasPreference(alpha=0.5)
	agents = [Agent(id=i, x=i % 6, y=(i * 3) % 8, preference=pref) for i in range(5)]
	sim = Simulation(grid=grid, agents=agents, config=None)
	sim.metrics_collector = MetricsCollector()
	if with_respawn:
		sim._rng = random.Random(seed)  # type: ignore[attr-defined]
		sim.respawn_scheduler = RespawnScheduler(target_density=0.15, max_spawn_per_tick=10, respawn_rate=0.5)
	return sim


def advance(sim: Simulation, steps: int) -> None:
	rng = random.Random(999)
	for _ in range(steps):
		sim.step(rng, use_decision=False)


def test_determinism_same_seed_same_hash():
	sim1 = build_sim(seed=42)
	sim2 = build_sim(seed=42)
	advance(sim1, 40)
	advance(sim2, 40)
	assert sim1.metrics_collector.determinism_hash() == sim2.metrics_collector.determinism_hash()  # type: ignore[assignment]


def test_determinism_position_change_changes_hash():
	sim1 = build_sim(seed=43)
	advance(sim1, 30)
	h_before = sim1.metrics_collector.determinism_hash()  # type: ignore[assignment]
	# Perturb state (agent 0 position)
	sim1.agents[0].x += 1
	advance(sim1, 1)
	h_after = sim1.metrics_collector.determinism_hash()  # type: ignore[assignment]
	assert h_after != h_before

