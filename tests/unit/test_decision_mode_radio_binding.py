"""Tests for decision mode radio wiring in MainWindow launch."""
from __future__ import annotations

import os

from PyQt6.QtWidgets import QApplication

from econsim.gui.main_window import MainWindow
from econsim.gui.start_menu import MenuSelection

app = QApplication.instance() or QApplication([])


def _launch(selection: MenuSelection) -> MainWindow:
    win = MainWindow()
    win._on_launch_requested(selection)  # type: ignore[attr-defined]
    app.processEvents()
    return win


def test_baseline_radio_disables_decision_mode():
    os.environ.pop("ECONSIM_LEGACY_RANDOM", None)
    selection = MenuSelection(
        scenario="baseline",
        mode="continuous",
        seed=11,
        grid_size=(6, 6),
        agents=2,
        density=0.2,
        enable_respawn=False,
        enable_metrics=True,
        preference_type="cobb_douglas",
        start_paused=False,
        respawn_interval=None,
        decision_mode_enabled=False,
        endowment_pattern="uniform",
        perception_radius=8,
        viewport_size=320,
    )
    win = _launch(selection)
    sess = getattr(win, "_session")
    controller = sess.controller  # type: ignore[attr-defined]
    pygame_widget = sess.pygame_widget  # type: ignore[attr-defined]
    assert not controller._use_decision_mode  # type: ignore[attr-defined]
    assert not getattr(pygame_widget, "_use_decision_default")
    win.close()


def test_legacy_scenario_forces_legacy_mode():
    os.environ.pop("ECONSIM_LEGACY_RANDOM", None)
    selection = MenuSelection(
        scenario="legacy_random",
        mode="legacy",
        seed=12,
        grid_size=(6, 6),
        agents=2,
        density=0.2,
        enable_respawn=False,
        enable_metrics=True,
        preference_type="cobb_douglas",
        start_paused=False,
        respawn_interval=None,
        decision_mode_enabled=True,  # should be ignored
        endowment_pattern="uniform",
        perception_radius=8,
        viewport_size=320,
    )
    win = _launch(selection)
    sess = getattr(win, "_session")
    controller = sess.controller  # type: ignore[attr-defined]
    pygame_widget = sess.pygame_widget  # type: ignore[attr-defined]
    assert not controller._use_decision_mode  # type: ignore[attr-defined]
    assert not getattr(pygame_widget, "_use_decision_default")
    win.close()

