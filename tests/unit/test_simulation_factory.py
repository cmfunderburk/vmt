from __future__ import annotations

import random
import pytest

from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
from econsim.simulation.metrics import MetricsCollector
from econsim.simulation.respawn import RespawnScheduler

# Helper preference (reuse default via factory when not provided)


def build_config(enable_respawn: bool = True, enable_metrics: bool = True, seed: int = 123) -> SimConfig:
    return SimConfig(
        grid_size=(8, 6),
        initial_resources=[(1, 1, "A"), (2, 2, "B"), (3, 4, "A")],
        perception_radius=8,
        respawn_target_density=0.2,
        respawn_rate=0.5,
        max_spawn_per_tick=5,
        seed=seed,
        enable_respawn=enable_respawn,
        enable_metrics=enable_metrics,
    )


def step_n(sim: Simulation, n: int, decision: bool = False) -> None:
    ext_rng = random.Random(999)
    for _ in range(n):
        sim.step(ext_rng, use_decision=decision)


def test_factory_attaches_hooks_when_enabled():
    cfg = build_config(True, True, seed=42)
    sim = Simulation.from_config(cfg, agent_positions=[(0, 0), (2, 1)])
    assert isinstance(sim.respawn_scheduler, RespawnScheduler)
    assert isinstance(sim.metrics_collector, MetricsCollector)
    # Behavior-based check: run a few steps and ensure respawn can act (resources grow toward density)
    before = sim.grid.resource_count()
    step_n(sim, 5)
    after = sim.grid.resource_count()
    assert after >= before  # non-decreasing with active respawn


def test_factory_skips_hooks_when_disabled():
    cfg = build_config(False, False, seed=1)
    sim = Simulation.from_config(cfg, agent_positions=[(0, 0)])
    assert sim.respawn_scheduler is None
    assert sim.metrics_collector is None


def test_initial_resources_loaded():
    cfg = build_config(seed=5)
    sim = Simulation.from_config(cfg, agent_positions=[])
    ser = sim.grid.serialize()["resources"]
    assert (1, 1, "A") in ser and (2, 2, "B") in ser and (3, 4, "A") in ser


def test_determinism_same_seed():
    cfg1 = build_config(seed=77)
    cfg2 = build_config(seed=77)
    sim1 = Simulation.from_config(cfg1, agent_positions=[(0, 0)])
    sim2 = Simulation.from_config(cfg2, agent_positions=[(0, 0)])
    step_n(sim1, 10, decision=False)
    step_n(sim2, 10, decision=False)
    # Compare serialized resource layout (sorted)
    assert sim1.grid.serialize()["resources"] == sim2.grid.serialize()["resources"]


def test_different_seed_diverges():
    cfg1 = build_config(seed=101)
    cfg2 = build_config(seed=202)
    sim1 = Simulation.from_config(cfg1, agent_positions=[(0, 0)])
    sim2 = Simulation.from_config(cfg2, agent_positions=[(0, 0)])
    step_n(sim1, 12, decision=False)
    step_n(sim2, 12, decision=False)
    if sim1.grid.serialize()["resources"] == sim2.grid.serialize()["resources"]:  # extremely unlikely
        step_n(sim1, 5)
        step_n(sim2, 5)
    assert sim1.grid.serialize()["resources"] != sim2.grid.serialize()["resources"]


def test_metrics_hash_parity_manual_vs_factory():
    # Build factory sim
    cfg = build_config(seed=55)
    f_sim = Simulation.from_config(cfg, agent_positions=[(0, 0), (1, 0)])
    # Manual wiring equivalent
    m_cfg = build_config(seed=55)
    # Reproduce manual wiring (without using factory) for parity
    from econsim.preferences.cobb_douglas import CobbDouglasPreference
    from econsim.simulation.grid import Grid
    from econsim.simulation.agent import Agent

    grid = Grid(m_cfg.grid_size[0], m_cfg.grid_size[1], m_cfg.initial_resources)
    pref = CobbDouglasPreference(alpha=0.5)
    agents = [
        Agent(id=0, x=0, y=0, preference=pref),
        Agent(id=1, x=1, y=0, preference=pref),
    ]
    manual = Simulation(grid=grid, agents=agents, config=m_cfg)
    manual._rng = random.Random(m_cfg.seed)  # type: ignore[attr-defined]
    if m_cfg.enable_respawn:
        manual.respawn_scheduler = RespawnScheduler(
            target_density=m_cfg.respawn_target_density,
            max_spawn_per_tick=m_cfg.max_spawn_per_tick,
            respawn_rate=m_cfg.respawn_rate,
        )
    if m_cfg.enable_metrics:
        manual.metrics_collector = MetricsCollector()

    step_n(f_sim, 15)
    step_n(manual, 15)

    if f_sim.metrics_collector and manual.metrics_collector:
        assert (
            f_sim.metrics_collector.determinism_hash()
            == manual.metrics_collector.determinism_hash()
        )


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__])
