"""Application entry point for EconSim VMT.

Gate 1 Objective: Launch a PyQt6 window (no embedded pygame yet) to verify
basic event loop and packaging skeleton. Pygame integration will be added in
`gui/embedded_pygame.py` in a subsequent increment.
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QMainWindow

from econsim.gui.embedded_pygame import EmbeddedPygameWidget
try:  # feature flag import (optional during transition)
    from econsim.gui.main_window import MainWindow, should_use_new_gui
except Exception:  # pragma: no cover - fallback if new GUI not present
    MainWindow = None  # type: ignore
    def should_use_new_gui() -> bool:  # type: ignore
        return False


def create_window() -> QMainWindow:
    # Feature flag path
    if should_use_new_gui():
        if MainWindow is None:  # defensive
            raise RuntimeError("New GUI requested but unavailable")
        return MainWindow()
    # Legacy bootstrap
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
