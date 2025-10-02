import os, random
from econsim.simulation.world import Simulation
from econsim.simulation.grid import Grid
from econsim.simulation.agent import Agent
from econsim.preferences.cobb_douglas import CobbDouglasPreference

def build_sim():
    g = Grid(20,20, [])
    a0 = Agent(id=0,x=5,y=5,preference=CobbDouglasPreference(alpha=0.5))
    a1 = Agent(id=1,x=11,y=5,preference=CobbDouglasPreference(alpha=0.5))
    # Give inventories to enable potential trade intent once co-located
    a0.carrying['good1']=1
    a1.carrying['good2']=1
    return Simulation(grid=g, agents=[a0,a1], config=None)

def test_paired_agents_converge_and_intents_after_meeting(monkeypatch):
    monkeypatch.setenv('ECONSIM_FORAGE_ENABLED','1')
    monkeypatch.setenv('ECONSIM_TRADE_DRAFT','1')
    monkeypatch.setenv('ECONSIM_TRADE_EXEC','0')
    monkeypatch.setenv('ECONSIM_UNIFIED_SELECTION_ENABLE','1')
    sim = build_sim()
    rng = random.Random(0)
    # Step until they pair and then meet
    met = False
    for _ in range(30):
        sim.step(rng)
        a0, a1 = sim.agents
        if a0.trade_partner_id is not None and a1.trade_partner_id is not None:
            if (a0.x, a0.y) == (a1.x, a1.y):
                met = True
                break
    assert met, 'Agents failed to converge to meeting point'
    # After meeting, intents should be generated next step (since both carrying complementary goods)
    sim.step(rng)
    assert (sim.trade_intents is not None) and len(sim.trade_intents) > 0
