"""UI test for agent metrics dropdown and labels.
Ensures that after launching a small simulation, the ControlsPanel agent box
is populated and labels update after a manual step.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QApplication

from econsim.gui.main_window import MainWindow
from econsim.gui.start_menu import MenuSelection

app = QApplication.instance() or QApplication([])

def _launch() -> MainWindow:
    win = MainWindow()
    selection = MenuSelection(
        scenario='baseline_decision',
        mode='continuous',
        seed=42,
        grid_size=(6,6),
        agents=2,
        density=0.15,
        enable_respawn=False,
        enable_metrics=True,
        preference_type='cobb_douglas',
    )
    win._on_launch_requested(selection)  # type: ignore[attr-defined]
    app.processEvents()
    return win


def test_agent_dropdown_and_labels_update():
    win = _launch()
    sess = getattr(win, '_session')
    controls = sess.controls  # type: ignore[attr-defined]
    box = getattr(controls, '_agent_box')
    assert box.count() >= 1, 'Expected at least one agent in dropdown'
    # Trigger update manually
    controls._update_agent_metrics()  # type: ignore[attr-defined]
    carry_label = getattr(controls, '_agent_carry_label')
    util_label = getattr(controls, '_agent_util_label')
    assert carry_label.text().startswith('carry:'), 'Carry label not populated'
    assert util_label.text().startswith('U:'), 'Utility label not populated'
    win.close()
