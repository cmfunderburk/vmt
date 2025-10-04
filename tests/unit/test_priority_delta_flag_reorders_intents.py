import os, random
from econsim.simulation.world import Simulation
from econsim.simulation.grid import Grid
from econsim.simulation.agent import Agent
from econsim.preferences.cobb_douglas import CobbDouglasPreference


def build_two(sim_seed=0):  # type: ignore[no-untyped-def]
    a1 = Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.4))
    a2 = Agent(id=2, x=0, y=0, preference=CobbDouglasPreference(alpha=0.6))
    # Force complementary marginal utilities by asymmetric bundles
    a1.carrying['good1'] = 5
    a2.carrying['good2'] = 5
    sim = Simulation(grid=Grid(4,4,[]), agents=[a1,a2])
    return sim


def test_priority_delta_flag_reorders_intents(monkeypatch):  # type: ignore[no-untyped-def]
    rng = random.Random(3)
    # Baseline (flag off)
    for k in ('ECONSIM_TRADE_DRAFT','ECONSIM_TRADE_EXEC','ECONSIM_TRADE_PRIORITY_DELTA'):
        monkeypatch.delenv(k, raising=False)
    os.environ['ECONSIM_TRADE_DRAFT'] = '1'
    sim1 = build_two()
    monkeypatch.setattr(Agent, 'move_random', lambda self, grid, rng: None)
    sim1.step(rng)
    intents_off = sim1.trade_intents
    assert intents_off is not None and len(intents_off) > 0

    # With delta priority flag
    os.environ['ECONSIM_TRADE_PRIORITY_DELTA'] = '1'
    sim2 = build_two()
    monkeypatch.setattr(Agent, 'move_random', lambda self, grid, rng: None)
    sim2.step(rng)
    intents_on = sim2.trade_intents
    assert intents_on is not None and len(intents_on) > 0

    # Each intent has priority tuple; when flag off first element is 0.0; when on should be negative delta
    off_first = intents_off[0].priority[0]
    on_first = intents_on[0].priority[0]
    assert off_first == 0.0
    assert on_first <= 0.0 and on_first != 0.0

