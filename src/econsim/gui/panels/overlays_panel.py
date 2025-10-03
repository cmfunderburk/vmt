"""OverlaysPanel – UI for toggling visual overlays.

Checkboxes (all enabled by default):
* Grid
* Agent IDs
* Target Arrows
* Home Labels (H{id})

They mutate the shared OverlayState object owned by the EmbeddedPygameWidget.
No heavy logic; each toggle sets the corresponding boolean.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QCheckBox
from typing import Any

from ..overlay_state import OverlayState


class OverlaysPanel(QWidget):  # pragma: no cover (simple wiring; behavior tested separately)
    def __init__(self, overlay_state: OverlayState):
        super().__init__()
        self._state = overlay_state
        layout = QHBoxLayout(self)
        self._grid_cb = QCheckBox("Grid")
        self._ids_cb = QCheckBox("Agent IDs")
        self._arrow_cb = QCheckBox("Target Arrows")
        self._homes_cb = QCheckBox("Home Labels")

        self._grid_cb.setToolTip("Toggle grid line overlay")
        self._grid_cb.setAccessibleName("overlay-toggle-grid")
        self._ids_cb.setToolTip("Toggle agent ID labels")
        self._ids_cb.setAccessibleName("overlay-toggle-agent-ids")
        self._arrow_cb.setToolTip("Toggle agent target arrows")
        self._arrow_cb.setAccessibleName("overlay-toggle-target-arrows")
        self._homes_cb.setToolTip("Toggle agent home labels")
        self._homes_cb.setAccessibleName("overlay-toggle-home-labels")

        # Initialize from current state
        self._grid_cb.setChecked(self._state.show_grid)
        self._ids_cb.setChecked(self._state.show_agent_ids)
        self._arrow_cb.setChecked(self._state.show_target_arrow)
        self._homes_cb.setChecked(self._state.show_home_labels)

        self._grid_cb.toggled.connect(self._on_grid)  # type: ignore[arg-type]
        self._ids_cb.toggled.connect(self._on_ids)  # type: ignore[arg-type]
        self._arrow_cb.toggled.connect(self._on_arrow)  # type: ignore[arg-type]
        self._homes_cb.toggled.connect(self._on_homes)  # type: ignore[arg-type]

        layout.addWidget(self._grid_cb)
        layout.addWidget(self._ids_cb)
        layout.addWidget(self._arrow_cb)
        layout.addWidget(self._homes_cb)
        layout.addStretch(1)

    def _on_grid(self, checked: bool) -> None:
        self._state.show_grid = bool(checked)
        self._emit_overlay_state()

    def _on_ids(self, checked: bool) -> None:
        self._state.show_agent_ids = bool(checked)
        self._emit_overlay_state()

    def _on_arrow(self, checked: bool) -> None:
        self._state.show_target_arrow = bool(checked)
        self._emit_overlay_state()

    def _on_homes(self, checked: bool) -> None:
        self._state.show_home_labels = bool(checked)
        self._emit_overlay_state()

    def _emit_overlay_state(self) -> None:
        # GUI overlay state logging removed - will be rebuilt with current architecture if needed
        pass

__all__ = ["OverlaysPanel"]
