import os

import pygame
from PyQt6.QtWidgets import QApplication

from econsim.gui.embedded_pygame import EmbeddedPygameWidget


def test_widget_shutdown_cleans_pygame():
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
    assert not pygame.get_init(), "pygame should be quit after widget close"
