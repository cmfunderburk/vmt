import os

from econsim.simulation.trade import enumerate_intents_for_cell
from econsim.simulation.agent import Agent
from econsim.preferences.cobb_douglas import CobbDouglasPreference

def test_trade_intent_delta_utility_computed():
    os.environ['ECONSIM_TRADE_DRAFT'] = '1'
    # Explicitly disable priority delta flag for this test (verifies baseline ordering)
    if 'ECONSIM_TRADE_PRIORITY_DELTA' in os.environ:
        del os.environ['ECONSIM_TRADE_PRIORITY_DELTA']
    # Construct two agents with asymmetric bundles to trigger reciprocal trade
    a1 = Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
    a2 = Agent(id=2, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
    # Bundles: (8,1) and (1,6) to satisfy marginal cross-condition
    a1.carrying['good1'] = 8
    a1.carrying['good2'] = 1
    a2.carrying['good1'] = 1
    a2.carrying['good2'] = 6
    intents = enumerate_intents_for_cell([a1, a2])
    # There should be exactly one beneficial direction under rule producing delta_utility > 0
    assert len(intents) == 1
    intent = intents[0]
    assert intent.delta_utility > 0.0, f"Expected positive combined marginal lift, got {intent.delta_utility}"
    # Priority first element 0.0 when delta priority flag OFF
    assert os.environ.get('ECONSIM_TRADE_PRIORITY_DELTA') != '1'
    assert intent.priority[0] == 0.0, "Priority should remain 0.0 without ECONSIM_TRADE_PRIORITY_DELTA flag"

