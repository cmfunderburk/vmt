"""Metrics mini-panel (Phase A).

Displays ticks, remaining resources, steps/sec estimate (placeholder), updated on demand.
Future: convert to active polling with throttle.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QTimer

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
        # Optional auto-refresh via env flag ECONSIM_METRICS_AUTO=1 (interval ms override via ECONSIM_METRICS_AUTO_INTERVAL_MS)
        import os
        if os.environ.get("ECONSIM_METRICS_AUTO") == "1":
            try:
                interval = int(os.environ.get("ECONSIM_METRICS_AUTO_INTERVAL_MS", "500"))
            except ValueError:
                interval = 500
            # Enforce minimum interval (4 Hz max) per checklist requirement
            if interval < 250:
                interval = 250
            self._auto_timer = QTimer(self)
            self._auto_timer.timeout.connect(self._update_values)  # type: ignore[arg-type]
            self._auto_timer.start(max(100, interval))
            self._auto_interval_ms = interval
        else:
            self._auto_timer = None
            self._auto_interval_ms = None

    def _update_values(self) -> None:
        self.ticks_lbl.setText(f"ticks: {self._controller.ticks()}")
        self.res_lbl.setText(f"resources: {self._controller.remaining_resources()}")
        self.sps_lbl.setText(f"steps/sec: {self._controller.steps_per_second_estimate():.1f}")

__all__ = ["MetricsPanel"]
