from __future__ import annotations

import random

from econsim.simulation.grid import Grid
from econsim.simulation.world import Simulation
from econsim.simulation.agent import Agent
from econsim.simulation.metrics import MetricsCollector
from econsim.preferences.cobb_douglas import CobbDouglasPreference


def make_sim(n_agents: int = 4) -> Simulation:
	grid = Grid(15, 10, [])
	pref = CobbDouglasPreference(alpha=0.5)
	agents = [Agent(id=i, x=i % 5, y=(i * 2) % 10, preference=pref) for i in range(n_agents)]
	sim = Simulation(grid=grid, agents=agents, config=None)
	sim.metrics_collector = MetricsCollector()
	# Provide internal rng for respawn if later needed (not configured here)
	return sim


def advance(sim: Simulation, steps: int) -> None:
	rng = random.Random(77)
	for _ in range(steps):
		sim.step(rng)


def test_metrics_basic_integrity():
	sim = make_sim()
	steps = 30
	advance(sim, steps)
	recs = list(sim.metrics_collector.records())  # type: ignore[arg-type]
	assert len(recs) == steps
	# Field coverage
	required = {"step", "agents", "resources", "carry_g1", "carry_g2", "home_g1", "home_g2"}
	for r in recs:
		assert required.issubset(r), r
		# Non-negative numeric values
		for k in required - {"step"}:
			assert isinstance(r[k], int)
			assert r[k] >= 0
	# Agent count constant
	agent_counts = {r["agents"] for r in recs}
	assert len(agent_counts) == 1 and next(iter(agent_counts)) == 4


def test_determinism_hash_changes_with_state():
	# Two sims identical seeds & trajectories => identical hash
	sim1 = make_sim()
	sim2 = make_sim()
	advance(sim1, 25)
	advance(sim2, 25)
	h1 = sim1.metrics_collector.determinism_hash()  # type: ignore[assignment]
	h2 = sim2.metrics_collector.determinism_hash()  # type: ignore[assignment]
	assert h1 == h2
	# Modify one agent position then advance one more step -> different hash
	sim2.agents[0].x += 1
	advance(sim2, 1)
	h3 = sim2.metrics_collector.determinism_hash()  # type: ignore[assignment]
	assert h3 != h2

