"""Tests for pacing defaults (criteria 3a, 3b) and presence of Unlimited option.

We construct the MainWindow through session descriptors emulating different modes.
Focus is on ControlsPanel state: selected speed value, presence of pacing label, and
whether Unlimited is selected outside turn mode.
"""
from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication

from econsim.gui.main_window import MainWindow
from econsim.gui.start_menu import MenuSelection

app = QApplication.instance() or QApplication([])


def _launch_mode(win: MainWindow, mode: str) -> None:
    # Build a MenuSelection similar to what StartMenuPage would emit.
    scenario = 'turn_mode' if mode == 'turn' else ('legacy_random' if mode == 'legacy' else 'baseline_decision')
    selection = MenuSelection(
        scenario=scenario,
        mode=mode,
        seed=123,
        grid_size=(8,8),
        agents=3,
        density=0.2,
        enable_respawn=False,
        enable_metrics=True,
        preference_type='cobb_douglas',
    )
    # Invoke protected launch handler directly for test speed.
    win._on_launch_requested(selection)  # type: ignore[attr-defined]
    app.processEvents()


def _extract_controls(window: MainWindow):
    sess = getattr(window, '_session', None)
    assert sess is not None, 'Session not established after launch'
    return sess.controls


def test_turn_mode_defaults_to_1_tps_with_label():
    win = MainWindow()
    _launch_mode(win, 'turn')
    controls = _extract_controls(win)
    combo = getattr(controls, '_speed_box')
    label = getattr(controls, '_pacing_label', None)
    # Selected item should have text '1.0'
    assert combo.currentText().startswith('1.0'), f"Expected 1.0 tps selected, got {combo.currentText()}"
    assert label is not None and label.text() == '(pacing)', "Pacing label text missing '(pacing)' at 1.0 tps"
    # Unlimited option present
    texts = [combo.itemText(i) for i in range(combo.count())]
    assert any(t.lower().startswith('unlimited') for t in texts), "Unlimited option missing in speed combo"
    win.close()


def test_legacy_mode_defaults_unlimited():
    win = MainWindow()
    _launch_mode(win, 'legacy')
    controls = _extract_controls(win)
    combo = getattr(controls, '_speed_box')
    label = getattr(controls, '_pacing_label', None)
    assert combo.currentText().lower().startswith('unlimited'), f"Legacy mode should default to Unlimited, got {combo.currentText()}"
    # Label should be absent or hidden
    if label is not None:
        assert label.text() == '', "Pacing label text should be empty in legacy (unlimited) mode"
    win.close()


def test_continuous_mode_defaults_unlimited():
    win = MainWindow()
    _launch_mode(win, 'continuous')
    controls = _extract_controls(win)
    combo = getattr(controls, '_speed_box')
    label = getattr(controls, '_pacing_label', None)
    assert combo.currentText().lower().startswith('unlimited'), f"Continuous mode should default to Unlimited, got {combo.currentText()}"
    if label is not None:
        assert label.text() == '', "Pacing label text should be empty in continuous (unlimited) mode"
    win.close()
