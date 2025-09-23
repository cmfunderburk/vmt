"""Test that invalid start menu input triggers QMessageBox.warning instead of raising.

Because widget ranges enforce bounds, we simulate an invalid input by monkeypatching
_StartMenuPage._validate_inputs to raise ValueError and ensure the warning path executes.
"""
from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication

from econsim.gui.start_menu import StartMenuPage, MenuSelection

app = QApplication.instance() or QApplication([])


def test_start_menu_invalid_input_shows_dialog(monkeypatch: pytest.MonkeyPatch):
    invoked = {"launched": False}

    def _on_launch(sel: MenuSelection):  # pragma: no cover - should not be called
        invoked["launched"] = True

    page = StartMenuPage(on_launch=_on_launch)

    # Force validation failure
    def fail_validate(w: int, h: int, a: int, d: float):
        raise ValueError("synthetic validation failure")

    monkeypatch.setattr(page, "_validate_inputs", fail_validate)

    calls = {}

    class _DummyMB:
        def warning(self, parent, title, text):  # mimic static signature usage
            calls["title"] = title
            calls["text"] = text
            return None

    # QMessageBox.warning is used as a static method; patch it.
    from PyQt6 import QtWidgets
    monkeypatch.setattr(QtWidgets.QMessageBox, "warning", _DummyMB().warning)

    # Trigger emit selection which should hit our synthetic validation failure
    page._emit_selection()  # type: ignore[attr-defined]
    app.processEvents()

    assert not invoked["launched"], "Launch callback should not be invoked on validation failure"
    assert calls.get("title") == "Input Error", "Expected QMessageBox title 'Input Error'"
    assert "synthetic validation failure" in calls.get("text", ""), "Validation error text missing in warning dialog"
