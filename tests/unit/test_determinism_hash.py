from __future__ import annotations

import random

from econsim.simulation.grid import Grid
from econsim.simulation.world import Simulation
from econsim.simulation.config import SimConfig


def build_sim(seed: int, with_respawn: bool = True) -> Simulation:
	# Empty grid initially; resources may spawn via respawn when enabled
	grid_tmp = Grid(12,8, [])
	cfg = SimConfig(
		grid_size=(grid_tmp.width, grid_tmp.height),
		initial_resources=[],
		perception_radius=8,
		respawn_target_density=0.15 if with_respawn else 0.0,
		respawn_rate=0.5 if with_respawn else 0.0,
		max_spawn_per_tick=10 if with_respawn else 0,
		seed=seed,
		enable_respawn=with_respawn,
		enable_metrics=True,
	)
	# Agent positions deterministic pattern replicating prior logic
	agent_positions = [(i % 6, (i * 3) % 8) for i in range(5)]
	sim = Simulation.from_config(cfg, agent_positions=agent_positions)
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

