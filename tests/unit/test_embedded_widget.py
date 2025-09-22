import pytest

from econsim.gui.embedded_pygame import EmbeddedPygameWidget
from PyQt6.QtWidgets import QApplication


def test_widget_construct_and_close():
    app = QApplication.instance() or QApplication([])
    w = EmbeddedPygameWidget()
    w.show()  # show briefly
    # simulate a few ticks
    for _ in range(5):
        app.processEvents()
    w.close()
    assert True  # reached without exception
