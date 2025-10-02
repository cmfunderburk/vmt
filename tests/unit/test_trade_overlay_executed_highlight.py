import os

from econsim.simulation.world import Simulation
from econsim.simulation.agent import Agent
from econsim.simulation.grid import Grid
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.metrics import MetricsCollector
from econsim.gui._trade_debug_overlay import render_trade_debug
import pygame


def test_trade_overlay_executed_highlight(monkeypatch):  # type: ignore[no-untyped-def]
    os.environ['ECONSIM_TRADE_DRAFT'] = '1'
    os.environ['ECONSIM_TRADE_EXEC'] = '1'
    os.environ['ECONSIM_TRADE_GUI_INFO'] = '1'

    # Minimal pygame surface init (headless)
    pygame.display.init()
    pygame.font.init()
    surface = pygame.Surface((200, 120))
    font = pygame.font.SysFont(None, 14)

    a1 = Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
    a2 = Agent(id=2, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
    a1.carrying['good1'] = 8
    a1.carrying['good2'] = 1
    a2.carrying['good1'] = 1
    a2.carrying['good2'] = 6

    sim = Simulation(grid=Grid(5,5,[]), agents=[a1,a2])
    sim.metrics_collector = MetricsCollector()

    def noop_step_decision(self, grid):  # type: ignore[no-untyped-def]
        return None
    monkeypatch.setattr(Agent, 'step_decision', noop_step_decision)  # type: ignore[attr-defined]
    import random
    dummy_rng = random.Random(0)
    sim.step(rng=dummy_rng)

    # Render overlay (should include executed trade highlight and summary line)
    render_trade_debug(surface, font, sim)
    # Basic assertions on metrics used for highlight
    mc = sim.metrics_collector
    assert mc.last_executed_trade is not None
    assert mc.trade_ticks == 1

    # Clean up pygame
    pygame.display.quit()
