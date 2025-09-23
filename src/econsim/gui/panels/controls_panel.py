"""Controls panel (Phase A + playback pacing).

Contains:
* Pause/Resume
* Step 1 / Step 5
* Determinism hash refresh (shows full + truncated)
* Playback speed dropdown (turns per second) – throttles auto stepping to chosen rate
* Return to Menu

Playback throttling is implemented in `SimulationController` and consulted by
`EmbeddedPygameWidget` each tick. Setting a new speed updates controller state.
"""
from __future__ import annotations

from typing import Callable
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QComboBox

from ..simulation_controller import SimulationController


class ControlsPanel(QWidget):  # pragma: no cover (GUI)
    def __init__(self, on_back: Callable[[], None], controller: SimulationController):
        super().__init__()
        self._controller = controller
        layout = QHBoxLayout(self)
        self._hash_label = QLabel("hash: —")

        # Core buttons
        self._pause_btn = QPushButton("Pause")
        step1 = QPushButton("Step 1")
        step5 = QPushButton("Step 5")
        refresh_hash = QPushButton("Refresh Hash")
        back_btn = QPushButton("Return to Menu")

        # Playback speed dropdown (turns per second)
        self._speed_box = QComboBox()
        self._speeds = [0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0]
        for s in self._speeds:
            self._speed_box.addItem(f"{s} tps", userData=s)
        # Default 1 tps selection
        default_index = self._speeds.index(1.0)
        self._speed_box.setCurrentIndex(default_index)
        # Apply initial throttling (affects both turn & continuous modes in experimental GUI)
        controller.set_playback_tps(1.0)
        self._speed_box.currentIndexChanged.connect(self._change_speed)  # type: ignore[arg-type]

        # Wire signals
        self._pause_btn.clicked.connect(self._toggle_pause)  # type: ignore[arg-type]
        step1.clicked.connect(self._do_step1)  # type: ignore[arg-type]
        step5.clicked.connect(self._do_step5)  # type: ignore[arg-type]
        refresh_hash.clicked.connect(self._refresh_hash)  # type: ignore[arg-type]
        back_btn.clicked.connect(on_back)  # type: ignore[arg-type]

        # Layout ordering
        layout.addWidget(self._pause_btn)
        layout.addWidget(step1)
        layout.addWidget(step5)
        layout.addWidget(refresh_hash)
        layout.addWidget(self._hash_label)
        layout.addWidget(QLabel("Speed:"))
        layout.addWidget(self._speed_box)
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

    def _change_speed(self, idx: int) -> None:
        data = self._speed_box.itemData(idx)
        try:
            val = float(data)
        except (TypeError, ValueError):  # pragma: no cover - GUI safety
            return
        self._controller.set_playback_tps(val)

__all__ = ["ControlsPanel"]
