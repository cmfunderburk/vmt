"""Overlay pixel difference test for new GUI overlay_state flags.

Skips unless ECONSIM_NEW_GUI=1.
"""
from __future__ import annotations
import os
import time
import pytest

from PyQt6.QtWidgets import QApplication

pytestmark = pytest.mark.skipif(os.environ.get("ECONSIM_NEW_GUI") != "1", reason="New GUI flag not enabled")


@pytest.fixture(scope="module")
def app():  # pragma: no cover
    return QApplication.instance() or QApplication([])


def build_minimal_sim():
    # Reuse existing simple test simulation path
    from econsim.simulation.grid import Grid
    from econsim.simulation.agent import Agent
    from econsim.simulation.world import Simulation
    from econsim.preferences.cobb_douglas import CobbDouglasPreference
    from econsim.simulation.config import SimConfig

    cfg = SimConfig(grid_size=(8, 8), initial_resources=[(1,1,"A"),(2,2,"B"),(3,3,"A")], seed=42)
    sim = Simulation.from_config(cfg, preference_factory=lambda i: CobbDouglasPreference(alpha=0.5), agent_positions=[(0,0),(1,1)])
    return sim


def test_overlay_pixel_difference(app):
    from econsim.gui.embedded_pygame import EmbeddedPygameWidget
    from econsim.gui.overlay_state import OverlayState

    sim = build_minimal_sim()
    w = EmbeddedPygameWidget(simulation=sim)
    # Let a few frames process
    for _ in range(5):
        app.processEvents()
        time.sleep(0.01)
    base_bytes = w.get_surface_bytes()
    assert len(base_bytes) > 0

    # Enable agent IDs + grid + target arrow (even if no target, other overlays should change output)
    assert w.overlay_state is not None
    w.overlay_state.show_grid = True
    w.overlay_state.show_agent_ids = True
    w.overlay_state.show_target_arrow = True

    for _ in range(5):
        app.processEvents()
        time.sleep(0.01)
    overlay_bytes = w.get_surface_bytes()

    diff = sum(b1 != b2 for b1, b2 in zip(base_bytes, overlay_bytes))
    ratio = diff / max(1, len(base_bytes))
    # Expect at least a small visible difference (>0.002 ~0.2%)
    assert ratio > 0.002, f"Overlay difference ratio too small: {ratio}"