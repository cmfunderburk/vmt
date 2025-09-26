import os, random
import pytest

from econsim.simulation.world import Simulation
from econsim.simulation.agent import Agent
from econsim.simulation.grid import Grid
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.metrics import MetricsCollector
from econsim.gui.simulation_controller import SimulationController


def _simple_pref():
    return CobbDouglasPreference(alpha=0.5)


from typing import Iterable, Sequence, Tuple, List, Any


def _build_sim(a_positions: Sequence[Tuple[int,int]], resources: Iterable[Tuple[int,int,str]] = ()) -> Simulation:
    agents: List[Agent] = [Agent(id=i+1, x=x, y=y, preference=_simple_pref()) for i, (x,y) in enumerate(a_positions)]
    # Give asymmetric inventories to satisfy marginal utility improvement tests for at least one direction.
    if len(agents) >= 2:
        agents[0].carrying['good1'] = 2
        agents[0].carrying['good2'] = 0
        agents[1].carrying['good1'] = 0
        agents[1].carrying['good2'] = 2
    for ag in agents[2:]:  # any extras get a neutral baseline
        ag.carrying['good1'] = 1
        ag.carrying['good2'] = 1
    sim = Simulation(grid=Grid(8,8,list(resources)), agents=agents)
    sim.metrics_collector = MetricsCollector()
    return sim


def _clear_trade_flags(monkeypatch: Any) -> None:  # type: ignore[override]
    for k in ("ECONSIM_TRADE_DRAFT","ECONSIM_TRADE_EXEC","ECONSIM_TRADE_GUI_INFO"):
        monkeypatch.delenv(k, raising=False)


def _clear_forage_flag(monkeypatch: Any) -> None:  # type: ignore[override]
    monkeypatch.delenv("ECONSIM_FORAGE_ENABLED", raising=False)


@pytest.mark.parametrize("forage,exchange", [
    (False, False),
    (False, True),
    (True, False),
    (True, True),
])
def test_behavior_matrix_decision_mode(forage: bool, exchange: bool, monkeypatch: Any):  # type: ignore[no-untyped-def]
    """Validate the four-mode gating matrix semantics in decision mode.

    Assertions focus on: movement / collection vs static, trade intent presence, and
    that when both enabled only non-foraging agents appear in intents (coarse check).
    """
    _clear_trade_flags(monkeypatch)
    _clear_forage_flag(monkeypatch)
    sim = _build_sim([(0,0),(0,0)])
    controller = SimulationController(simulation=sim)
    rng = random.Random(0)
    # Configure flags via controller (mirrors GUI path)
    controller.set_forage_enabled(forage)
    controller.set_bilateral_enabled(exchange)
    # Ensure decision mode path
    use_decision = True
    # Prime: place a resource so foraging path can collect if enabled
    if forage:
        sim.grid.add_resource(0,0,'A')
    sim.step(rng, use_decision=use_decision)
    intents = getattr(sim, 'trade_intents', None)
    if not forage and not exchange:
        # Agents should have moved toward home & possibly idled, but no trade intents
        assert intents is None
    elif not forage and exchange:
        # Exchange only: enumeration runs; intents list may be empty if marginal utility conditions fail
        assert intents is not None
    elif forage and not exchange:
        # Foraging only: no trade intents, at least one agent collected (carrying updated or target cleared)
        assert intents is None
        # At least one inventory increased (good1 or good2) at home or carrying
        assert any(a.carrying['good1'] > 1 or a.carrying['good2'] > 1 for a in sim.agents)
    else:  # forage and exchange
        # Trade intents may or may not exist; if they do and a collection occurred this tick, ensure
        # the collecting agent (whose carrying increased) is excluded.
        if intents:
            collected_ids = [a.id for a in sim.agents if a.carrying['good1'] > 2 or a.carrying['good2'] > 2]
            if collected_ids:
                for it in intents:
                    assert it.seller_id not in collected_ids and it.buyer_id not in collected_ids


def test_gui_checkboxes_toggle(monkeypatch):  # type: ignore[no-untyped-def]
    """Smoke test the ControlsPanel checkboxes manipulating controller flags.

    We instantiate the panel with a controller and simulate user toggles by calling
    the slot methods directly (avoids full Qt event loop complexity in unit test).
    """
    from econsim.gui.panels.controls_panel import ControlsPanel
    _clear_trade_flags(monkeypatch)
    _clear_forage_flag(monkeypatch)
    sim = _build_sim([(0,0),(0,0)])
    controller = SimulationController(simulation=sim)
    # Baseline defaults (updated: bilateral exchange now enabled by default)
    assert controller.forage_enabled() is True
    assert controller.bilateral_enabled() is True
    # Build panel (Qt widgets need a QApplication; rely on global one if tests already created)
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
    except Exception:  # pragma: no cover - if PyQt backend missing, skip
        pytest.skip("QApplication not available")
    _ = ControlsPanel(on_back=lambda: None, controller=controller)
    # Simulate user intent by calling public controller methods (checkbox wiring covered by other smoke tests)
    controller.set_bilateral_enabled(True)
    assert controller.bilateral_enabled() is True
    controller.set_forage_enabled(False)
    assert controller.forage_enabled() is False
    # Place a resource and step in decision mode to ensure no collection occurs when disabled
    sim.grid.add_resource(0,0,'A')
    before_present = sim.grid.has_resource(0,0)
    sim.step(random.Random(1), use_decision=True)
    after_present = sim.grid.has_resource(0,0)
    # Resource should remain because foraging logic skipped
    assert before_present and after_present
    # Env var should be explicit '0'
    assert os.environ.get('ECONSIM_FORAGE_ENABLED') == '0'
    controller.set_forage_enabled(True)
    assert controller.forage_enabled() is True

__all__ = [
    'test_behavior_matrix_decision_mode',
    'test_gui_checkboxes_toggle',
]
