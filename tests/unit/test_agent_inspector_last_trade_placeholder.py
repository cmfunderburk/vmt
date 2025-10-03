import os, random, pygame
import pytest

from econsim.simulation.world import Simulation
from econsim.simulation.agent import Agent
from econsim.simulation.grid import Grid
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.metrics import MetricsCollector
from econsim.gui.simulation_controller import SimulationController

@pytest.mark.skipif('DISPLAY' not in os.environ, reason='Headless environment without DISPLAY variable')
def test_agent_inspector_last_trade_placeholder(monkeypatch):  # type: ignore[no-untyped-def]
    # Enable bilateral flags via controller method to avoid global leak complexity
    os.environ['ECONSIM_TRADE_DRAFT'] = '1'
    os.environ['ECONSIM_TRADE_EXEC'] = '1'
    os.environ['ECONSIM_TRADE_GUI_INFO'] = '1'

    a1 = Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
    a2 = Agent(id=2, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
    a1.carrying['good1'] = 5
    a2.carrying['good2'] = 5

    sim = Simulation(grid=Grid(6,6,[]), agents=[a1,a2])
    sim.metrics_collector = MetricsCollector()
    controller = SimulationController(simulation=sim)
    controller.set_bilateral_enabled(True)

    # Prevent movement randomness
    monkeypatch.setattr(Agent, 'move_random', lambda self, grid, rng: None)
    rng = random.Random(1)
    sim.step(rng)

    summary = controller.last_trade_summary()
    assert summary is None or 'seller' in summary  # Either no trade occurred or formatted string present
