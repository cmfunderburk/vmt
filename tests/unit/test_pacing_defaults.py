"""Tests for pacing defaults and presence of Unlimited option.

Turn mode removed; simulate former behavior via start_paused baseline + initial 1.0 tps selection if applicable.
Focus: ControlsPanel state (speed combo contents, labels) across legacy and continuous modes.
"""
from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication

from econsim.gui.main_window import MainWindow
from econsim.gui.start_menu import MenuSelection

app = QApplication.instance() or QApplication([])


def _launch_mode(win: MainWindow, mode: str, start_paused: bool = False) -> None:
    scenario = 'legacy_random' if mode == 'legacy' else 'baseline_decision'
    selection = MenuSelection(
        scenario=scenario,
        mode=('legacy' if mode == 'legacy' else 'continuous'),
        seed=123,
        grid_size=(8,8),
        agents=3,
        density=0.2,
        enable_respawn=False,
        enable_metrics=True,
        preference_type='cobb_douglas',
        start_paused=start_paused,
    )
    # Invoke protected launch handler directly for test speed.
    win._on_launch_requested(selection)  # type: ignore[attr-defined]
    app.processEvents()


def _extract_controls(window: MainWindow):
    sess = getattr(window, '_session', None)
    assert sess is not None, 'Session not established after launch'
    return sess.controls


def test_start_paused_baseline_has_five_tps_default():
    win = MainWindow()
    _launch_mode(win, 'continuous', start_paused=True)
    controls = _extract_controls(win)
    combo = getattr(controls, '_speed_box')
    # Baseline now defaults to 5.0 tps even if started paused.
    assert combo.currentText().lower().startswith('5.0'), f"Expected 5.0 tps default, got {combo.currentText()}"
    win.close()


def test_legacy_mode_defaults_five_tps():
    win = MainWindow()
    _launch_mode(win, 'legacy')
    controls = _extract_controls(win)
    combo = getattr(controls, '_speed_box')
    label = getattr(controls, '_pacing_label', None)
    assert combo.currentText().lower().startswith('5.0'), f"Legacy mode should default to 5.0 tps, got {combo.currentText()}"
    # Label should be absent or hidden (unchanged expectation)
    if label is not None:
        assert label.text() == '', "Pacing label text should be empty in legacy (unlimited) mode"
    win.close()


def test_continuous_mode_defaults_five_tps():
    win = MainWindow()
    _launch_mode(win, 'continuous')
    controls = _extract_controls(win)
    combo = getattr(controls, '_speed_box')
    label = getattr(controls, '_pacing_label', None)
    assert combo.currentText().lower().startswith('5.0'), f"Continuous mode should default to 5.0 tps, got {combo.currentText()}"
    if label is not None:
        assert label.text() == '', "Pacing label text should be empty in continuous (throttled) mode"
    win.close()
