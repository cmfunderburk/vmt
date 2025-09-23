import random

from econsim.preferences.base import Preference
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.agent import Agent
from econsim.simulation.grid import Grid
from econsim.simulation.world import Simulation


def build_agents(n: int, pref: Preference):
    return [Agent(id=i, x=0, y=0, preference=pref) for i in range(n)]


def test_simulation_deterministic():
    seed = 2025
    rng1 = random.Random(seed)
    rng2 = random.Random(seed)
    grid1 = Grid(6, 6, resources=[(1, 1), (2, 2)])
    grid2 = Grid(6, 6, resources=[(1, 1), (2, 2)])
    pref = CobbDouglasPreference(alpha=0.5)
    sim1 = Simulation(grid1, build_agents(3, pref))
    sim2 = Simulation(grid2, build_agents(3, pref))
    for _ in range(15):
        sim1.step(rng1)
        sim2.step(rng2)
    assert sim1.steps == sim2.steps == 15
    # Compare agent positions and inventory
    for a1, a2 in zip(sim1.agents, sim2.agents, strict=False):
        assert a1.pos == a2.pos
        assert a1.inventory == a2.inventory
    # Remaining resources identical state
    assert grid1.serialize()["resources"] == grid2.serialize()["resources"]


def test_simulation_collection_progress():
    rng = random.Random(77)
    # Place line of resources along x-axis
    resources = [(i, 0) for i in range(1, 6)]
    grid = Grid(10, 3, resources=resources)
    pref = CobbDouglasPreference(alpha=0.6)
    sim = Simulation(grid, [Agent(id=1, x=0, y=0, preference=pref)])
    collected = 0
    for _ in range(50):
        before = sim.agents[0].inventory["good1"]
        sim.step(rng)
        after = sim.agents[0].inventory["good1"]
        if after > before:
            collected += 1
    assert collected >= 1  # eventually picks up at least one
    assert sim.steps == 50
