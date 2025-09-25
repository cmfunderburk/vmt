from __future__ import annotations

import random
import pytest  # type: ignore

from econsim.simulation.world import Simulation
from econsim.simulation.config import SimConfig
from typing import List, Tuple
from econsim.simulation.agent import Agent


def _sim_with_agents(positions: List[Tuple[int, int]]):
    cfg = SimConfig(
        grid_size=(6,6),
        initial_resources=[],
        perception_radius=6,
        respawn_target_density=0.0,
        respawn_rate=0.0,
        max_spawn_per_tick=0,
        seed=31,
        enable_respawn=False,
        enable_metrics=True,
    )
    return Simulation.from_config(cfg, agent_positions=positions)


def test_single_execution_swap(monkeypatch) -> None:  # type: ignore[missing-annotations]
    monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
    monkeypatch.setenv("ECONSIM_TRADE_EXEC", "1")
    sim = _sim_with_agents([(0,0),(0,0)])
    monkeypatch.setattr(Agent, "move_random", lambda self, grid, rng: None)
    a0, a1 = sim.agents
    # Target example: Agent0 (8,1), Agent1 (1,6)
    a0.carrying['good1'] = 8
    a0.carrying['good2'] = 1
    a1.carrying['good1'] = 1
    a1.carrying['good2'] = 6
    rng = random.Random(5)
    sim.step(rng, use_decision=False)
    # After execution: (7,2) and (2,5)
    assert a0.carrying['good1'] == 7
    assert a0.carrying['good2'] == 2
    assert a1.carrying['good1'] == 2
    assert a1.carrying['good2'] == 5
    # Metrics increment
    assert sim.metrics_collector.trades_executed == 1  # type: ignore[attr-defined]


def test_no_double_execution(monkeypatch) -> None:  # type: ignore[missing-annotations]
    monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
    monkeypatch.setenv("ECONSIM_TRADE_EXEC", "1")
    sim = _sim_with_agents([(0,0),(0,0)])
    monkeypatch.setattr(Agent, "move_random", lambda self, grid, rng: None)
    a0, a1 = sim.agents
    a0.carrying['good1'] = 8
    a0.carrying['good2'] = 1
    a1.carrying['good1'] = 1
    a1.carrying['good2'] = 6
    rng = random.Random(7)
    sim.step(rng, use_decision=False)
    # One swap only (second intent not formed because each agent now possesses both goods)
    assert a0.carrying['good1'] == 7
    assert a0.carrying['good2'] == 2
    assert a1.carrying['good1'] == 2
    assert a1.carrying['good2'] == 5
    assert sim.metrics_collector.trades_executed == 1  # type: ignore[attr-defined]


@pytest.mark.xfail(reason="Determinism hash parity between draft and execution deferred: carrying inventories mutate during execution and are included in current hash design.")
def test_hash_parity_execution_flag(monkeypatch) -> None:  # type: ignore[missing-annotations]
    # Deferred: Hash SHOULD differ presently because execution mutates carrying inventories.
    # This test remains as documentation of the intended invariant once hash redesign occurs.
    sim_a = _sim_with_agents([(0,0),(0,0)])
    sim_b = _sim_with_agents([(0,0),(0,0)])
    a0a, a1a = sim_a.agents
    a0b, a1b = sim_b.agents
    a0a.carrying['good1'] = 1
    a1a.carrying['good2'] = 1
    a0b.carrying['good1'] = 1
    a1b.carrying['good2'] = 1
    rng_a = random.Random(9)
    rng_b = random.Random(9)
    # Draft only
    monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
    monkeypatch.setattr(Agent, "move_random", lambda self, grid, rng: None)
    sim_a.step(rng_a, use_decision=False)
    hash_draft = sim_a.metrics_collector.determinism_hash()  # type: ignore[union-attr]
    # Draft + exec
    monkeypatch.setenv("ECONSIM_TRADE_EXEC", "1")
    sim_b.step(rng_b, use_decision=False)
    hash_exec = sim_b.metrics_collector.determinism_hash()  # type: ignore[union-attr]
    assert hash_draft == hash_exec


def test_flag_gating(monkeypatch) -> None:  # type: ignore[missing-annotations]
    # No draft flag => exec flag alone should still enumerate (we allow exec implies enumeration)
    monkeypatch.delenv("ECONSIM_TRADE_DRAFT", raising=False)
    monkeypatch.setenv("ECONSIM_TRADE_EXEC", "1")
    sim = _sim_with_agents([(0,0),(0,0)])
    monkeypatch.setattr(Agent, "move_random", lambda self, grid, rng: None)
    a0, a1 = sim.agents
    a0.carrying['good1'] = 8
    a0.carrying['good2'] = 1
    a1.carrying['good1'] = 1
    a1.carrying['good2'] = 6
    rng = random.Random(11)
    sim.step(rng, use_decision=False)
    # Swap executed -> (7,2) and (2,5)
    assert (a0.carrying['good1'], a0.carrying['good2']) == (7, 2)
    assert (a1.carrying['good1'], a1.carrying['good2']) == (2, 5)


def test_execution_requires_inventory(monkeypatch) -> None:  # type: ignore[missing-annotations]
    # If buyer lacks take_type or seller lacks give_type at execution moment, skip
    monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
    monkeypatch.setenv("ECONSIM_TRADE_EXEC", "1")
    sim = _sim_with_agents([(0,0),(0,0)])
    monkeypatch.setattr(Agent, "move_random", lambda self, grid, rng: None)
    a0, a1 = sim.agents
    # Only one side has goods; no valid swap
    a0.carrying['good1'] = 8
    rng = random.Random(13)
    sim.step(rng, use_decision=False)
    # No change
    assert a0.carrying['good1'] == 8 and a0.carrying['good2'] == 0
    assert a1.carrying['good1'] == 0 and a1.carrying['good2'] == 0
    assert sim.metrics_collector.trades_executed == 0  # type: ignore[attr-defined]


def test_no_trade_when_marginals_not_reciprocal(monkeypatch) -> None:  # type: ignore[missing-annotations]
    monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
    monkeypatch.setenv("ECONSIM_TRADE_EXEC", "1")
    sim = _sim_with_agents([(0,0),(0,0)])
    monkeypatch.setattr(Agent, "move_random", lambda self, grid, rng: None)
    a0, a1 = sim.agents
    # Symmetric balanced bundles (5,5) & (5,5) => marginal utilities equal => no trade
    a0.carrying['good1'] = 5
    a0.carrying['good2'] = 5
    a1.carrying['good1'] = 5
    a1.carrying['good2'] = 5
    rng = random.Random(17)
    sim.step(rng, use_decision=False)
    assert a0.carrying['good1'] == 5 and a0.carrying['good2'] == 5
    assert a1.carrying['good1'] == 5 and a1.carrying['good2'] == 5
    assert sim.metrics_collector.trades_executed == 0  # type: ignore[attr-defined]
