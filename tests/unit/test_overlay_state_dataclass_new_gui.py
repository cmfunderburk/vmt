from econsim.gui.overlay_state import OverlayState

def test_overlay_state_basic_mutation():
    s = OverlayState()
    # Defaults are ON by design (grid, ids, arrows, home labels)
    assert s.show_grid and s.show_agent_ids and s.show_target_arrow and s.show_home_labels
    # Toggle OFF
    s.show_grid = False
    s.show_agent_ids = False
    s.show_target_arrow = False
    s.show_home_labels = False
    assert (not s.show_grid) and (not s.show_agent_ids) and (not s.show_target_arrow) and (not s.show_home_labels)
