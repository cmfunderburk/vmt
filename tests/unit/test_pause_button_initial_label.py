"""Test initial pause button label reflects controller paused state in turn mode.

Turn mode launches controller paused, so the ControlsPanel should show 'Resume'.
A non-turn mode (continuous) should show 'Pause'.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QApplication

from econsim.gui.main_window import MainWindow
from econsim.gui.start_menu import MenuSelection

app = QApplication.instance() or QApplication([])


def _launch(mode: str) -> MainWindow:
    win = MainWindow()
    selection = MenuSelection(
        scenario='turn_mode' if mode=='turn' else ('legacy_random' if mode=='legacy' else 'baseline_decision'),
        mode=mode,
        seed=77,
        grid_size=(8,8),
        agents=2,
        density=0.2,
        enable_respawn=False,
        enable_metrics=True,
        preference_type='cobb_douglas',
    )
    win._on_launch_requested(selection)  # type: ignore[attr-defined]
    app.processEvents()
    return win


def _get_pause_text(win: MainWindow) -> str:
    sess = getattr(win, '_session')
    controls = sess.controls  # type: ignore[attr-defined]
    btn = getattr(controls, '_pause_btn')
    return btn.text()


def test_turn_mode_initial_label_resume():
    win = _launch('turn')
    txt = _get_pause_text(win)
    assert txt == 'Resume', f"Turn mode should start paused with 'Resume' label, got {txt}"
    win.close()


def test_continuous_mode_initial_label_pause():
    win = _launch('continuous')
    txt = _get_pause_text(win)
    assert txt == 'Pause', f"Continuous mode should start running with 'Pause' label, got {txt}"
    win.close()
