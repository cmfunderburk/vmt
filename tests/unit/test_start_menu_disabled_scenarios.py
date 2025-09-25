"""Ensure non-implemented scenarios are disabled in the Start Menu."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from econsim.gui.start_menu import StartMenuPage, MenuSelection

app = QApplication.instance() or QApplication([])


def test_non_baseline_scenarios_disabled():
    captured: dict[str, MenuSelection] = {}

    def _noop(selection: MenuSelection) -> None:
        captured["selection"] = selection

    page = StartMenuPage(on_launch=_noop)
    combo = page.scenario_box
    model = combo.model()
    for name in ("bilateral_exchange", "money_market"):
        idx = combo.findText(name)
        assert idx >= 0, f"Expected scenario {name} in combobox"
        item = model.item(idx)
        assert item is not None
        assert not item.isEnabled(), f"Scenario {name} should be disabled"
        tooltip = item.data(Qt.ItemDataRole.ToolTipRole)
        assert tooltip == "Not implemented yet", f"Expected tooltip for {name}"
    page.deleteLater()
