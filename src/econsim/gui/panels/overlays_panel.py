"""OverlaysPanel – UI for toggling Phase A overlays.

Provides three checkboxes:
* Grid
* Agent IDs
* Target Arrows

They mutate the shared OverlayState object owned by the EmbeddedPygameWidget.
No heavy logic; each toggle sets the corresponding boolean.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QCheckBox

from ..overlay_state import OverlayState


class OverlaysPanel(QWidget):  # pragma: no cover (simple wiring; behavior tested separately)
    def __init__(self, overlay_state: OverlayState):
        super().__init__()
        self._state = overlay_state
        layout = QHBoxLayout(self)
        self._grid_cb = QCheckBox("Grid")
        self._ids_cb = QCheckBox("Agent IDs")
        self._arrow_cb = QCheckBox("Target Arrows")

        # Initialize from current state
        self._grid_cb.setChecked(self._state.show_grid)
        self._ids_cb.setChecked(self._state.show_agent_ids)
        self._arrow_cb.setChecked(self._state.show_target_arrow)

        self._grid_cb.toggled.connect(self._on_grid)  # type: ignore[arg-type]
        self._ids_cb.toggled.connect(self._on_ids)  # type: ignore[arg-type]
        self._arrow_cb.toggled.connect(self._on_arrow)  # type: ignore[arg-type]

        layout.addWidget(self._grid_cb)
        layout.addWidget(self._ids_cb)
        layout.addWidget(self._arrow_cb)
        layout.addStretch(1)

    def _on_grid(self, checked: bool) -> None:
        self._state.show_grid = bool(checked)

    def _on_ids(self, checked: bool) -> None:
        self._state.show_agent_ids = bool(checked)

    def _on_arrow(self, checked: bool) -> None:
        self._state.show_target_arrow = bool(checked)

__all__ = ["OverlaysPanel"]
