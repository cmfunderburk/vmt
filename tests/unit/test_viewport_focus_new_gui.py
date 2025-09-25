"""Verify that the Pygame viewport receives focus on launch."""
from __future__ import annotations

from PyQt6.QtWidgets import QApplication

from econsim.gui.main_window import MainWindow
from econsim.gui.start_menu import MenuSelection

app = QApplication.instance() or QApplication([])


def test_viewport_has_focus_after_launch():
    win = MainWindow()
    selection = MenuSelection(
        scenario="baseline",
        mode="continuous",
        seed=99,
        grid_size=(6, 6),
        agents=2,
        density=0.2,
        enable_respawn=False,
        enable_metrics=True,
        preference_type="cobb_douglas",
    )
    win._on_launch_requested(selection)  # type: ignore[attr-defined]
    win.show()
    app.processEvents()
    sess = getattr(win, "_session")
    viewport = sess.pygame_widget  # type: ignore[attr-defined]
    assert viewport.focusPolicy().name == "StrongFocus", "Viewport should accept strong focus"
    viewport.setFocus()
    app.processEvents()
    assert win.focusWidget() is viewport, "Viewport should become the focused widget"
    win.close()
