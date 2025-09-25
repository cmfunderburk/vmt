"""Smoke test: switching from 1.0 tps pacing to Unlimited increases step throughput.

We simulate a short run using MainWindow launch in turn mode (which sets 1.0 tps),
collect steps after a fixed wall time slice, then change speed to Unlimited and
collect steps over an equivalent slice. Expect second slice steps > first slice steps.

Test is tolerant: requires at least 2x improvement OR absolute difference >= 3 steps.
This avoids flakiness on slower CI runners while still catching regressions
(e.g., if controller playback_tps not applied or Unlimited not honored).
"""
from __future__ import annotations

import time
from PyQt6.QtWidgets import QApplication

from econsim.gui.main_window import MainWindow
from econsim.gui.start_menu import MenuSelection

app = QApplication.instance() or QApplication([])

SLICE_SEC = 0.25  # short slice (250ms)


def _launch_turn() -> MainWindow:
    win = MainWindow()
    selection = MenuSelection(
        scenario='baseline_decision',  # unified baseline replaces former turn_mode
        mode='continuous',
        seed=321,
        grid_size=(8,8),
        agents=4,
        density=0.3,
        enable_respawn=False,
        enable_metrics=True,
        preference_type='cobb_douglas',
        start_paused=False,
    )
    win._on_launch_requested(selection)  # type: ignore[attr-defined]
    app.processEvents()
    return win


def _pump(duration: float):
    end = time.perf_counter() + duration
    while time.perf_counter() < end:
        app.processEvents()
        # small sleep yields to event loop timers
        time.sleep(0.005)


def test_switch_to_unlimited_increases_step_rate():
    win = _launch_turn()
    sess = getattr(win, '_session')
    controller = sess.controller  # type: ignore[attr-defined]
    # Ensure unpaused for pacing test
    if controller.is_paused():
        controller.resume()
    # Ensure pacing is explicitly set to 1.0 tps for the baseline slice
    controls = sess.controls  # type: ignore[attr-defined]
    speed_box = getattr(controls, '_speed_box')
    for i in range(speed_box.count()):
        data = speed_box.itemData(i)
        if data == 1.0:
            speed_box.setCurrentIndex(i)
            app.processEvents()
            break
    # Slice 1 at 1.0 tps
    start_steps = controller.ticks()
    _pump(SLICE_SEC)
    mid_steps = controller.ticks()
    slice1 = mid_steps - start_steps
    # Switch to Unlimited (select first index where userData is None)
    for i in range(speed_box.count()):
        if speed_box.itemData(i) is None:
            speed_box.setCurrentIndex(i)
            app.processEvents()
            break
    # Slice 2 at Unlimited
    _pump(SLICE_SEC)
    end_steps = controller.ticks()
    slice2 = end_steps - mid_steps
    # Basic assertions: slice2 should exceed slice1; stronger condition 2x OR +3 absolute.
    assert slice2 > slice1, f"Unlimited slice did not exceed throttled slice (1.0 tps). slice1={slice1} slice2={slice2}"
    assert (slice2 >= 2 * slice1) or (slice2 - slice1 >= 3), (
        f"Unlimited speed increase insufficient: slice1={slice1} slice2={slice2}"
    )
    win.close()
