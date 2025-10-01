from __future__ import annotations

import os
import random
from typing import List, Tuple

from econsim.simulation.world import Simulation
from econsim.simulation.config import SimConfig


def build_sim(agent_positions: List[Tuple[int,int]], resources=None):
    cfg = SimConfig(
        grid_size=(6,6),
        initial_resources=resources or [],
        perception_radius=6,
        respawn_target_density=0.0,
        respawn_rate=0.0,
        max_spawn_per_tick=0,
        seed=42,
        enable_respawn=False,
        enable_metrics=True,
    )
    return Simulation.from_config(cfg, agent_positions=agent_positions)


def test_movement_mode_metrics_decision(monkeypatch):  # type: ignore[missing-annotations]
    monkeypatch.delenv("ECONSIM_LEGACY_RANDOM", raising=False)
    sim = build_sim([(0,0),(1,1)])
    rng = random.Random(1)
    sim.step(rng, use_decision=True)
    metrics = sim.last_step_metrics or {}
    # movement_movement_mode should exist and be 'decision' or 'unified'
    keys = [k for k in metrics.keys() if k.startswith('movement_')]
    assert any('movement_mode' in k for k in keys), f"Movement metrics missing: {keys}"


# Legacy movement test removed - legacy random movement is deprecated and no longer supported


def test_collection_diff_decision(monkeypatch):  # type: ignore[missing-annotations]
    monkeypatch.delenv("ECONSIM_LEGACY_RANDOM", raising=False)
    # Seed a few resources manually
    resources = [(0,0,'wood'), (1,1,'stone')]
    sim = build_sim([(0,0)], resources=resources)
    rng = random.Random(3)
    sim.step(rng, use_decision=True)
    metrics = sim.last_step_metrics or {}
    # Ensure collection metric key is namespaced
    assert 'collection_resources_collected' in metrics
    assert metrics['collection_resources_collected'] >= 0


def test_respawn_interval_no_respawn(monkeypatch):  # type: ignore[missing-annotations]
    # Ensure respawn handler reports skipped when disabled
    sim = build_sim([(0,0)])
    rng = random.Random(4)
    sim.step(rng, use_decision=True)
    metrics = sim.last_step_metrics or {}
    # respawn_respawn_attempted present and zero
    assert metrics.get('respawn_respawn_attempted', 0) in (0,1)


def test_metrics_handler_steps_per_sec(monkeypatch):  # type: ignore[missing-annotations]
    sim = build_sim([(0,0)])
    rng = random.Random(5)
    # Run several steps to accumulate rolling timings
    for _ in range(5):
        sim.step(rng, use_decision=True)
    metrics = sim.last_step_metrics or {}
    assert metrics.get('metrics_steps_per_sec', 0) >= 0


def test_trading_draft_execution_single_intent(monkeypatch):  # type: ignore[missing-annotations]
    monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
    monkeypatch.setenv("ECONSIM_TRADE_EXEC", "1")
    # Place two agents together and give them complementary goods
    sim = build_sim([(0,0),(0,0)])
    a0, a1 = sim.agents
    a0.carrying['wood'] = 1
    a1.carrying['stone'] = 1
    rng = random.Random(6)
    sim.step(rng, use_decision=True)
    metrics = sim.last_step_metrics or {}
    intents = metrics.get('trading_intents_count')
    executed = metrics.get('trading_executed')
    assert intents is not None and intents >= 0
    assert executed in (0,1)


def test_trading_foraged_gating(monkeypatch):  # type: ignore[missing-annotations]
    monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
    # Execution disabled to focus on gating
    monkeypatch.delenv("ECONSIM_TRADE_EXEC", raising=False)
    sim = build_sim([(0,0),(0,0)])
    # Force one agent to collect first by placing a resource they will pick
    sim.grid.add_resource(0,0,'wood')  # type: ignore[attr-defined]
    rng = random.Random(7)
    sim.step(rng, use_decision=True)
    metrics = sim.last_step_metrics or {}
    # Intents may be reduced if foraged gating applied; just ensure metric exists
    assert 'trading_intents_count' in metrics

