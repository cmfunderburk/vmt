import os, random
from econsim.simulation.world import Simulation
from econsim.simulation.agent import Agent
from econsim.simulation.grid import Grid
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.metrics import MetricsCollector
from econsim.gui.simulation_controller import SimulationController

def _build_two_agent_sim():  # helper
    a1 = Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
    a2 = Agent(id=2, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
    a1.carrying['good1'] = 4
    a2.carrying['good2'] = 4
    sim = Simulation(grid=Grid(6,6,[]), agents=[a1,a2])
    sim.metrics_collector = MetricsCollector()
    return sim

def test_runtime_toggle_enables_and_disables(monkeypatch):  # type: ignore[no-untyped-def]
    # Start with environment clean to ensure feature off
    for k in ('ECONSIM_TRADE_DRAFT','ECONSIM_TRADE_EXEC','ECONSIM_TRADE_GUI_INFO'):
        monkeypatch.delenv(k, raising=False)
    sim = _build_two_agent_sim()
    # Freeze movement to keep agents co-located across steps
    monkeypatch.setattr(Agent, 'move_random', lambda self, grid, rng: None)
    controller = SimulationController(simulation=sim)
    rng = random.Random(7)
    # Step with feature disabled → no intents
    sim.step(rng, use_decision=False)
    assert not getattr(sim, 'trade_intents', None)
    # Enable live
    controller.set_bilateral_enabled(True)
    sim.step(rng, use_decision=False)
    intents = getattr(sim, 'trade_intents', None)
    assert intents is not None and len(intents) > 0
    # Disable live
    controller.set_bilateral_enabled(False)
    sim.step(rng, use_decision=False)
    assert not getattr(sim, 'trade_intents', None)

def test_last_trade_summary_format(monkeypatch):  # type: ignore[no-untyped-def]
    for k in ('ECONSIM_TRADE_DRAFT','ECONSIM_TRADE_EXEC','ECONSIM_TRADE_GUI_INFO'):
        monkeypatch.delenv(k, raising=False)
    sim = _build_two_agent_sim()
    monkeypatch.setattr(Agent, 'move_random', lambda self, grid, rng: None)
    controller = SimulationController(simulation=sim)
    controller.set_bilateral_enabled(True)
    rng = random.Random(11)
    sim.step(rng, use_decision=False)
    summary = controller.last_trade_summary()
    # Depending on marginal utilities a trade may or may not have executed; if executed summary has required fields
    if summary is not None:
        for token in ('seller','buyer','give','take','ΔU','step'):
            assert token in summary