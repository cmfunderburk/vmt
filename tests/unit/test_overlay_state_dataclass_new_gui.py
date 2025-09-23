from econsim.gui.overlay_state import OverlayState

def test_overlay_state_basic_mutation():
    s = OverlayState()
    assert not s.show_grid and not s.show_agent_ids and not s.show_target_arrow
    s.show_grid = True
    s.show_agent_ids = True
    s.show_target_arrow = True
    assert s.show_grid and s.show_agent_ids and s.show_target_arrow
