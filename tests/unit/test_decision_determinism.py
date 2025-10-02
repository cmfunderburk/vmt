import random

from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.agent import Agent, AgentMode
from econsim.simulation.world import Simulation
from econsim.simulation.config import SimConfig


def build_agents(n: int):
    pref = CobbDouglasPreference(alpha=0.5)
    return [Agent(id=i, x=0, y=0, preference=pref) for i in range(n)]


def snapshot(sim: Simulation):
    return [(a.mode.value, a.pos, a.target, dict(a.carrying)) for a in sim.agents]


def test_decision_determinism_basic():
    resources = [(2,2,"A"),(4,4,"B"),(6,1,"A")]
    cfg = SimConfig(
        grid_size=(10,10),
        initial_resources=resources,
        perception_radius=8,
        respawn_target_density=0.0,
        respawn_rate=0.0,
        max_spawn_per_tick=0,
        seed=123,
        enable_respawn=False,
        enable_metrics=False,
    )
    sim1 = Simulation.from_config(cfg, agent_positions=[(0,0),(0,0)])
    sim2 = Simulation.from_config(cfg, agent_positions=[(0,0),(0,0)])
    rng1 = random.Random(42)
    rng2 = random.Random(42)
    for _ in range(15):
        sim1.step(rng1)
        sim2.step(rng2)
        assert snapshot(sim1) == snapshot(sim2)
    # Ensure non-idle if resources exist
    assert any(a.mode != AgentMode.IDLE for a in sim1.agents)
