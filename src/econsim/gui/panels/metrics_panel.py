"""Metrics mini-panel (Phase A).

Displays ticks, remaining resources, steps/sec estimate (placeholder), updated on demand.
Future: convert to active polling with throttle.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

from ..simulation_controller import SimulationController


class MetricsPanel(QWidget):  # pragma: no cover
    def __init__(self, controller: SimulationController):
        super().__init__()
        self._controller = controller
        layout = QHBoxLayout(self)
        self.ticks_lbl = QLabel("ticks: 0")
        self.res_lbl = QLabel("resources: 0")
        self.sps_lbl = QLabel("steps/sec: 0.0")
        refresh = QPushButton("Update Metrics")
        refresh.clicked.connect(self._update_values)  # type: ignore[arg-type]
        layout.addWidget(self.ticks_lbl)
        layout.addWidget(self.res_lbl)
        layout.addWidget(self.sps_lbl)
        layout.addWidget(refresh)
        layout.addStretch(1)

    def _update_values(self) -> None:
        self.ticks_lbl.setText(f"ticks: {self._controller.ticks()}")
        self.res_lbl.setText(f"resources: {self._controller.remaining_resources()}")
        self.sps_lbl.setText(f"steps/sec: {self._controller.steps_per_second_estimate():.1f}")

__all__ = ["MetricsPanel"]
