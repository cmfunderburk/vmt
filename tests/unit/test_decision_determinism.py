import random

from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.agent import Agent, AgentMode
from econsim.simulation.grid import Grid
from econsim.simulation.world import Simulation


def build_agents(n: int):
    pref = CobbDouglasPreference(alpha=0.5)
    return [Agent(id=i, x=0, y=0, preference=pref) for i in range(n)]


def snapshot(sim: Simulation):
    return [(a.mode.value, a.pos, a.target, dict(a.carrying)) for a in sim.agents]


def test_decision_determinism_basic():
    grid1 = Grid(10, 10, resources=[(2, 2, "A"), (4, 4, "B"), (6, 1, "A")])
    grid2 = Grid(10, 10, resources=[(2, 2, "A"), (4, 4, "B"), (6, 1, "A")])
    sim1 = Simulation(grid1, build_agents(2))
    sim2 = Simulation(grid2, build_agents(2))
    rng1 = random.Random(42)
    rng2 = random.Random(42)
    for _ in range(15):
        sim1.step(rng1, use_decision=True)
        sim2.step(rng2, use_decision=True)
        assert snapshot(sim1) == snapshot(sim2)
    # Ensure non-idle if resources exist
    assert any(a.mode != AgentMode.IDLE for a in sim1.agents)
