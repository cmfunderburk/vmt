from econsim.simulation.agent import Agent, AgentMode
from econsim.preferences.cobb_douglas import CobbDouglasPreference

def test_agent_defaults_and_home_assignment():
    a = Agent(id=1, x=2, y=3, preference=CobbDouglasPreference(alpha=0.5))
    assert a.home_x == 2 and a.home_y == 3
    assert a.mode == AgentMode.FORAGE
    assert a.target is None
    assert a.carrying == {"good1":0, "good2":0}
    assert a.home_inventory == {"good1":0, "good2":0}


def test_agent_deposit_logic():
    a = Agent(id=2, x=1, y=1, preference=CobbDouglasPreference(alpha=0.6))
    # simulate carrying items
    a.carrying['good1'] = 2
    a.carrying['good2'] = 1
    # move to a different home to test negative case
    a.home_x, a.home_y = 0,0
    assert not a.at_home()
    assert a.deposit() is True  # deposit works regardless of location (policy OK for now)
    assert a.carrying_total() == 0
    assert a.home_inventory['good1'] == 2 and a.home_inventory['good2'] == 1


def test_agent_maybe_deposit_mode_transition():
    a = Agent(id=3, x=0, y=0, preference=CobbDouglasPreference(alpha=0.4))
    # place home at (0,0) already; simulate return_home mode and carrying goods
    a.mode = AgentMode.RETURN_HOME
    a.carrying['good1'] = 3
    a.maybe_deposit()
    # At home, should deposit and revert to FORAGE with cleared carrying
    assert a.mode == AgentMode.FORAGE
    assert a.carrying_total() == 0
