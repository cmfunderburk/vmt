"""Test initial pause button label reflects controller paused state with start_paused flag.

If start_paused=True, ControlsPanel should show 'Resume'. Otherwise 'Pause'.
Former 'turn_mode' scenario replaced by baseline_decision + start_paused flag.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QApplication

from econsim.gui.main_window import MainWindow
from econsim.gui.start_menu import MenuSelection

app = QApplication.instance() or QApplication([])


def _launch(start_paused: bool, legacy: bool = False) -> MainWindow:
    win = MainWindow()
    selection = MenuSelection(
        scenario='legacy_random' if legacy else 'baseline_decision',
        mode='legacy' if legacy else 'continuous',
        seed=77,
        grid_size=(8,8),
        agents=2,
        density=0.2,
        enable_respawn=False,
        enable_metrics=True,
        preference_type='cobb_douglas',
        start_paused=start_paused,
    )
    win._on_launch_requested(selection)  # type: ignore[attr-defined]
    app.processEvents()
    return win


def _get_pause_text(win: MainWindow) -> str:
    sess = getattr(win, '_session')
    controls = sess.controls  # type: ignore[attr-defined]
    btn = getattr(controls, '_pause_btn')
    return btn.text()


def test_start_paused_initial_label_resume():
    win = _launch(start_paused=True)
    txt = _get_pause_text(win)
    assert txt == 'Resume', f"Start paused should show 'Resume' label, got {txt}"
    win.close()


def test_not_start_paused_initial_label_pause():
    win = _launch(start_paused=False)
    txt = _get_pause_text(win)
    assert txt == 'Pause', f"Not start paused should show 'Pause' label, got {txt}"
    win.close()
