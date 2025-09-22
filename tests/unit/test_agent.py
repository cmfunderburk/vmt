import random

from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.grid import Grid
from econsim.simulation.agent import Agent


def test_agent_movement_stays_in_bounds():
    rng = random.Random(123)
    g = Grid(5, 5)
    a = Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
    for _ in range(50):
        a.move_random(g, rng)
        assert 0 <= a.x < 5 and 0 <= a.y < 5


def test_agent_deterministic_path():
    seed = 999
    rng1 = random.Random(seed)
    rng2 = random.Random(seed)
    g = Grid(6, 4)
    a1 = Agent(id=1, x=2, y=1, preference=CobbDouglasPreference(alpha=0.5))
    a2 = Agent(id=1, x=2, y=1, preference=CobbDouglasPreference(alpha=0.5))
    for _ in range(25):
        a1.move_random(g, rng1)
        a2.move_random(g, rng2)
    assert a1.pos == a2.pos


def test_agent_collects_resource():
    g = Grid(5, 5, resources=[(1, 1)])
    a = Agent(id=2, x=1, y=1, preference=CobbDouglasPreference(alpha=0.4))
    before = a.inventory["good1"]
    collected = a.collect(g)
    assert collected is True
    assert a.inventory["good1"] == before + 1
    # resource now gone
    assert g.take_resource(1, 1) is False
