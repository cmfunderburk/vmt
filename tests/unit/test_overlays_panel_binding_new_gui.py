import os

from econsim.gui.panels.overlays_panel import OverlaysPanel
from econsim.gui.overlay_state import OverlayState


def test_overlays_panel_toggles():
    os.environ["ECONSIM_NEW_GUI"] = "1"
    state = OverlayState()
    panel = OverlaysPanel(state)
    # Initial all False
    assert not state.show_grid
    assert not state.show_agent_ids
    assert not state.show_target_arrow
    # Directly invoke slots (bypass checkbox signals to avoid needing full Qt test harness)
    panel._on_grid(True)
    panel._on_ids(True)
    panel._on_arrow(True)
    assert state.show_grid
    assert state.show_agent_ids
    assert state.show_target_arrow
