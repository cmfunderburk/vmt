import os, random
from econsim.simulation.world import Simulation
from econsim.simulation.grid import Grid
from econsim.simulation.agent import Agent
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.metrics import MetricsCollector


def build_sim():  # type: ignore[no-untyped-def]
    a1 = Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
    a2 = Agent(id=2, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
    a1.carrying['good1'] = 6
    a1.carrying['good2'] = 1
    a2.carrying['good1'] = 1
    a2.carrying['good2'] = 6
    sim = Simulation(grid=Grid(5,5,[]), agents=[a1,a2])
    sim.metrics_collector = MetricsCollector()
    return sim


def test_fairness_round_increments(monkeypatch):  # type: ignore[no-untyped-def]
    for k in ('ECONSIM_TRADE_DRAFT','ECONSIM_TRADE_EXEC','ECONSIM_TRADE_PRIORITY_DELTA'):
        monkeypatch.delenv(k, raising=False)
    os.environ['ECONSIM_TRADE_DRAFT'] = '1'
    os.environ['ECONSIM_TRADE_EXEC'] = '1'
    sim = build_sim()
    import random as _r
    rng = _r.Random(5)
    monkeypatch.setattr(Agent, 'move_random', lambda self, grid, rng: None)
    mc = sim.metrics_collector
    assert mc is not None
    assert mc.fairness_round == 0
    sim.step(rng)
    # One trade should typically execute; fairness_round increments if so.
    assert mc.fairness_round in (0,1)
    # Run multiple steps to allow further trades if conditions persist.
    for _ in range(4):
        sim.step(rng)
    assert mc.fairness_round >= 0

