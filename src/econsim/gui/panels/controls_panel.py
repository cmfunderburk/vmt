"""Controls panel scaffold (Phase A).

Contains: Run/Pause (placeholder wiring), Step 1, Step 5, Return to Menu button,
Hash refresh button (shows full + truncated hash).
"""
from __future__ import annotations

from typing import Callable
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel

from ..simulation_controller import SimulationController


class ControlsPanel(QWidget):  # pragma: no cover (GUI)
    def __init__(self, on_back: Callable[[], None], controller: SimulationController):
        super().__init__()
        self._controller = controller
        layout = QHBoxLayout(self)
        self._hash_label = QLabel("hash: —")

        self._pause_btn = QPushButton("Pause")
        step1 = QPushButton("Step 1")
        step5 = QPushButton("Step 5")
        refresh_hash = QPushButton("Refresh Hash")
        back_btn = QPushButton("Return to Menu")

        self._pause_btn.clicked.connect(self._toggle_pause)  # type: ignore[arg-type]
        step1.clicked.connect(self._do_step1)  # type: ignore[arg-type]
        step5.clicked.connect(self._do_step5)  # type: ignore[arg-type]
        refresh_hash.clicked.connect(self._refresh_hash)  # type: ignore[arg-type]
        back_btn.clicked.connect(on_back)  # type: ignore[arg-type]

        layout.addWidget(self._pause_btn)
        layout.addWidget(step1)
        layout.addWidget(step5)
        layout.addWidget(refresh_hash)
        layout.addWidget(self._hash_label)
        layout.addStretch(1)
        layout.addWidget(back_btn)

    def _toggle_pause(self) -> None:
        if self._controller.is_paused():
            self._controller.resume()
            self._pause_btn.setText("Pause")
        else:
            self._controller.pause()
            self._pause_btn.setText("Resume")

    def _do_step1(self) -> None:
        was_paused = self._controller.is_paused()
        if not was_paused:
            # Ensure consistent manual stepping semantics – pause to make isolated
            self._controller.pause()
        self._controller.manual_step()
        if not was_paused:
            self._controller.resume()

    def _do_step5(self) -> None:
        was_paused = self._controller.is_paused()
        if not was_paused:
            self._controller.pause()
        self._controller.manual_step(count=5)
        if not was_paused:
            self._controller.resume()

    def _refresh_hash(self) -> None:
        h = self._controller.refresh_hash()
        short = h[:8] if len(h) > 8 else h
        self._hash_label.setText(f"hash: {short} ({h})")

__all__ = ["ControlsPanel"]
