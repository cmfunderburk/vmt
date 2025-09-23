from typing import List, Tuple
import pytest
from PyQt6.QtWidgets import QApplication

from econsim.simulation.world import Simulation
from econsim.simulation.grid import Grid
from econsim.simulation.agent import Agent
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.gui.embedded_pygame import EmbeddedPygameWidget

# Reuse a single QApplication across tests (pytest -s safe) if not already created
app = QApplication.instance() or QApplication([])


def _build_sim_single_resource(decision: bool):
    # Grid 5x5 with one resource at (4,4); agent starts at (0,0). In decision mode agent should move diagonally (greedy path toward target).
    grid = Grid(5, 5, resources=[(4, 4, 'A')])
    pref = CobbDouglasPreference(alpha=0.5)
    agent = Agent(id=0, x=0, y=0, preference=pref)
    sim = Simulation(grid=grid, agents=[agent])
    return sim


def _tick(widget: EmbeddedPygameWidget, steps: int) -> None:
    for _ in range(steps):
        widget._on_tick()  # type: ignore[attr-defined] direct call for test speed
        app.processEvents()


def test_widget_defaults_to_decision_mode(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv('ECONSIM_LEGACY_RANDOM', raising=False)
    sim = _build_sim_single_resource(decision=True)
    widget = EmbeddedPygameWidget(simulation=sim)
    _tick(widget, 5)
    agent = sim.agents[0]
    # Decision path should have moved both x and y positively (toward 4,4).
    assert agent.x > 0 and agent.y > 0, "Agent did not exhibit directed movement toward resource in decision mode default"


def test_widget_legacy_env_flag_forces_random(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('ECONSIM_LEGACY_RANDOM', '1')
    sim = _build_sim_single_resource(decision=False)
    widget = EmbeddedPygameWidget(simulation=sim)
    # Run a few ticks; random walk may move only along one axis or oscillate; ensure NOT strictly moving both axes each tick toward (4,4).
    positions: List[Tuple[int, int]] = []
    for _ in range(5):
        widget._on_tick()  # type: ignore[attr-defined]
        app.processEvents()
        positions.append((sim.agents[0].x, sim.agents[0].y))
    # Heuristic: if all first 3 moves advanced both x and y (monotonic toward target) it's likely decision, fail.
    advances = 0
    last = (0, 0)
    for x, y in positions[1:4]:
        if x > last[0] and y > last[1]:
            advances += 1
        last = (x, y)
    assert advances < 3, "Legacy random flag did not appear to switch off decision mode (movement looked deterministic)"


def test_widget_constructor_param_overrides_env(monkeypatch: pytest.MonkeyPatch):
    # Force env legacy but pass decision_mode=True to override
    monkeypatch.setenv('ECONSIM_LEGACY_RANDOM', '1')
    sim = _build_sim_single_resource(decision=True)
    widget = EmbeddedPygameWidget(simulation=sim, decision_mode=True)
    _tick(widget, 4)
    a = sim.agents[0]
    assert a.x > 0 and a.y > 0, "Constructor override decision_mode=True did not take effect over env flag"
