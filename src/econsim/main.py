"""Application entry point for EconSim VMT.

Gate 1 Objective: Launch a PyQt6 window (no embedded pygame yet) to verify
basic event loop and packaging skeleton. Pygame integration will be added in
`gui/embedded_pygame.py` in a subsequent increment.
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QMainWindow

from econsim.gui.embedded_pygame import EmbeddedPygameWidget


def create_window() -> QMainWindow:
    window = QMainWindow()
    window.setWindowTitle("EconSim – Gate 1 Bootstrap")
    widget = EmbeddedPygameWidget()
    window.setCentralWidget(widget)
    window.resize(640, 480)
    return window


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = create_window()
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
