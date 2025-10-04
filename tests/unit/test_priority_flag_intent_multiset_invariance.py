import os, random
from econsim.simulation.world import Simulation
from econsim.simulation.grid import Grid
from econsim.simulation.agent import Agent
from econsim.preferences.cobb_douglas import CobbDouglasPreference


def build_two():  # type: ignore[no-untyped-def]
    a1 = Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.4))
    a2 = Agent(id=2, x=0, y=0, preference=CobbDouglasPreference(alpha=0.6))
    a1.carrying['good1'] = 5
    a2.carrying['good2'] = 5
    sim = Simulation(grid=Grid(4,4,[]), agents=[a1,a2])
    return sim


def intent_signature_list(intents):  # type: ignore[no-untyped-def]
    return sorted([
        (i.seller_id, i.buyer_id, i.give_type, i.take_type, i.quantity)
        for i in intents
    ])


def test_priority_flag_intent_multiset_invariance(monkeypatch):  # type: ignore[no-untyped-def]
    rng = random.Random(7)
    # Baseline
    os.environ['ECONSIM_TRADE_DRAFT'] = '1'
    sim1 = build_two()
    monkeypatch.setattr(Agent, 'move_random', lambda self, grid, rng: None)
    sim1.step(rng)
    intents_off = sim1.trade_intents
    assert intents_off

    # With flag
    os.environ['ECONSIM_TRADE_DRAFT'] = '1'
    os.environ['ECONSIM_TRADE_PRIORITY_DELTA'] = '1'
    sim2 = build_two()
    monkeypatch.setattr(Agent, 'move_random', lambda self, grid, rng: None)
    sim2.step(rng)
    intents_on = sim2.trade_intents
    assert intents_on

    assert intent_signature_list(intents_off) == intent_signature_list(intents_on), "Priority flag must not change trade intent multiset, only ordering"
    # Ordering should differ (or at least the priority tuple first element differ) if delta priorities active
    if len(intents_off) > 0 and len(intents_on) > 0:
        if intents_off[0].priority[0] == 0.0:
            assert intents_on[0].priority[0] <= 0.0 and intents_on[0].priority[0] != 0.0
