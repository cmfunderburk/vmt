import os
from econsim.simulation.world import Simulation
import random
from econsim.simulation.agent import Agent
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.grid import Grid
from econsim.simulation.metrics import MetricsCollector


def build_sim(agents):  # type: ignore[no-untyped-def]
    grid = Grid(5,5, [])
    sim = Simulation(grid=grid, agents=agents)
    sim.metrics_collector = MetricsCollector()
    return sim


def test_trade_metrics_realized_gain_and_ticks(monkeypatch):  # type: ignore[no-untyped-def]
    os.environ['ECONSIM_TRADE_DRAFT'] = '1'
    os.environ['ECONSIM_TRADE_EXEC'] = '1'
    a1 = Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
    a2 = Agent(id=2, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
    # Set bundles to produce one trade (8,1) & (1,6)
    a1.carrying['good1'] = 8
    a1.carrying['good2'] = 1
    a2.carrying['good1'] = 1
    a2.carrying['good2'] = 6

    sim = build_sim([a1,a2])  # type: ignore[arg-type]

    # Prevent movement / resource interactions
    def noop_step_decision(self, grid):  # type: ignore[no-untyped-def]
        return None
    monkeypatch.setattr(Agent, 'step_decision', noop_step_decision)  # type: ignore[attr-defined]

    dummy_rng = random.Random(0)
    sim.step(rng=dummy_rng)

    mc = sim.metrics_collector
    assert mc is not None
    # After one step exactly one trade tick
    assert mc.trade_ticks == 1
    assert mc.no_trade_ticks == 0
    assert mc.trades_executed == 1
    # Delta utility stored (approx >0)
    assert mc.realized_utility_gain_total > 0.0
    # Last executed trade structure
    assert mc.last_executed_trade is not None
    lt = mc.last_executed_trade
    for key in ['seller','buyer','give_type','take_type','delta_utility','step']:
        assert key in lt

    # Second step may still trade depending on marginal utilities (current approximation allows second swap)
    sim.step(rng=dummy_rng)
    assert mc.trade_ticks >= 1

