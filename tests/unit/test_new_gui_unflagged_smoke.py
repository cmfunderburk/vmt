"""Smoke test: instantiate MainWindow without ECONSIM_NEW_GUI flag to ensure it does not auto-launch legacy-only code paths.

This verifies new GUI objects can be constructed even if the opt-in flag is absent (we don't show it).
"""
from __future__ import annotations

from PyQt6.QtWidgets import QApplication

from econsim.gui.main_window import MainWindow

app = QApplication.instance() or QApplication([])


def test_new_gui_instantiation_without_flag():
    # Ensure env flag absent
    import os
    if 'ECONSIM_NEW_GUI' in os.environ:
        del os.environ['ECONSIM_NEW_GUI']
    win = MainWindow()
    # No crash constructing; menu page should be current (index 0)
    stack = getattr(win, '_stack')
    assert stack.currentIndex() == 0, 'MainWindow should start on menu page'
    win.close()
