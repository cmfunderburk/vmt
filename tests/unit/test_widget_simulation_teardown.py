"""Widget teardown test with injected Simulation (Gate 4).

Ensures that:
 - `EmbeddedPygameWidget` can be constructed with a Simulation instance.
 - After `close()`, pygame is no longer initialized (pygame.get_init() == False).
 - Frame counter advanced at least one tick (sanity the timer ran).

Headless safe: sets QT_QPA_PLATFORM=offscreen if DISPLAY absent.
"""

from __future__ import annotations

import os
import time

import pygame
from PyQt6.QtWidgets import QApplication

from econsim.gui.embedded_pygame import EmbeddedPygameWidget
from econsim.simulation.agent import Agent
from econsim.simulation.grid import Grid
from econsim.simulation.world import Simulation
from econsim.preferences.cobb_douglas import CobbDouglasPreference


def _build_sim() -> Simulation:
    grid = Grid(6, 6, resources=[(2, 2, "A"), (4, 4, "B")])
    pref = CobbDouglasPreference(alpha=0.5)
    agents = [Agent(id=0, x=0, y=0, preference=pref)]
    return Simulation(grid, agents)


def test_widget_teardown_with_simulation():
    if not os.environ.get("DISPLAY"):
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication([])
    sim = _build_sim()
    widget = EmbeddedPygameWidget(simulation=sim)
    widget.show()

    # Process event cycles allowing QTimer (~16ms) to fire; break early if a frame appears
    frame_count = 0
    for _ in range(50):
        app.processEvents()
        time.sleep(0.005)  # allow timer to elapse in headless CI
        frame_count = getattr(widget, "_frame", 0)
        if frame_count > 0:
            break
    assert frame_count > 0, "Expected widget frame counter to advance with simulation attached (after waits)"

    # Close & process teardown
    widget.close()
    app.processEvents()

    # After close, pygame should be quit
    assert not pygame.get_init(), "pygame should be uninitialized after widget closeEvent"
