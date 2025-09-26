import os

import pygame
from PyQt6.QtWidgets import QApplication

from econsim.gui.embedded_pygame import EmbeddedPygameWidget


def test_widget_shutdown_refcount_allows_pygame_persistence():
    # Ensure dummy video driver in headless contexts
    if not os.environ.get("DISPLAY"):
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    w = EmbeddedPygameWidget()
    w.show()
    # Process a few event cycles
    for _ in range(5):
        app.processEvents()
    w.close()
    app.processEvents()
    # New behavior: ref-counted quit deferred; pygame may remain initialized if other subsystems (or tests) reuse it.
    # We simply assert that the widget's internal surface reference is cleared to prevent segmentation faults.
    assert w._surface is None, "EmbeddedPygameWidget surface should be cleared on close to avoid reuse after shutdown"
