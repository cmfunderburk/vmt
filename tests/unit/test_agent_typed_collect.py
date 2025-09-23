from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.grid import Grid
from econsim.simulation.agent import Agent

def test_agent_collects_typed_resources():
    g = Grid(4, 4, resources=[(1,1,'A'), (2,2,'B')])
    a = Agent(id=5, x=1, y=1, preference=CobbDouglasPreference(alpha=0.6))
    # collect A -> good1
    assert a.collect(g) is True
    assert a.inventory['good1'] == 1
    assert a.inventory['good2'] == 0
    # move to B location
    a.x, a.y = 2, 2
    assert a.collect(g) is True
    assert a.inventory['good1'] == 1
    assert a.inventory['good2'] == 1
    # cell now empty
    assert g.take_resource(2,2) is False
