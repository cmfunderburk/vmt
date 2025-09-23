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
from PyQt6.QtCore import QTimer

from ..simulation_controller import SimulationController


class ControlsPanel(QWidget):  # pragma: no cover (GUI)
    def __init__(self, on_back: Callable[[], None], controller: SimulationController):
        super().__init__()
        self._controller = controller
        layout = QHBoxLayout(self)
        self._hash_label = QLabel("hash: —")

        # Core buttons
        # Pause button label reflects initial controller state (start paused in turn mode scenarios)
        initial_label = "Resume" if controller.is_paused() else "Pause"
        self._pause_btn = QPushButton(initial_label)
        step1 = QPushButton("Step 1")
        step5 = QPushButton("Step 5")
        refresh_hash = QPushButton("Refresh Hash")
        back_btn = QPushButton("Return to Menu")

        # Playback speed dropdown (turns per second). Adds an explicit Unlimited option (None => per-frame).
        self._speed_box = QComboBox()
        self._speed_box.setToolTip(
            "Select a turn pacing rate. 'Unlimited' executes a decision step each frame; other values throttle to N turns/sec."
        )
        self._speeds = [None, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0]  # None represents Unlimited
        for s in self._speeds:
            if s is None:
                self._speed_box.addItem("Unlimited", userData=None)
            else:
                self._speed_box.addItem(f"{s} tps", userData=s)
        # Default selection will be finalized by configure_for_mode() invoked by MainWindow after construction.
        self._speed_box.currentIndexChanged.connect(self._change_speed)  # type: ignore[arg-type]
        # Small pacing label that appears only when throttled (not Unlimited)
        self._pacing_label = QLabel("")
        self._pacing_label.setObjectName("pacingLabel")

        # Wire signals
        self._pause_btn.clicked.connect(self._toggle_pause)  # type: ignore[arg-type]
        step1.clicked.connect(self._do_step1)  # type: ignore[arg-type]
        step5.clicked.connect(self._do_step5)  # type: ignore[arg-type]
        refresh_hash.clicked.connect(self._refresh_hash)  # type: ignore[arg-type]
        back_btn.clicked.connect(on_back)  # type: ignore[arg-type]

        # Agent metrics UI (dropdown + carry + utility labels)
        self._agent_box = QComboBox()
        self._agent_box.setToolTip("Select an agent to inspect its current carrying bundle and utility")
        self._agent_carry_label = QLabel("carry: —")
        self._agent_util_label = QLabel("U: —")
        # Populate agent list once (will remain stable deterministically)
        try:
            for aid in self._controller.list_agent_ids():  # type: ignore[attr-defined]
                self._agent_box.addItem(f"A{aid}", userData=aid)
        except Exception:
            pass
        self._agent_box.currentIndexChanged.connect(self._update_agent_metrics)  # type: ignore[arg-type]

        # Layout ordering
        layout.addWidget(self._pause_btn)
        layout.addWidget(step1)
        layout.addWidget(step5)
        layout.addWidget(refresh_hash)
        layout.addWidget(self._hash_label)
        layout.addWidget(QLabel("Agent:"))
        layout.addWidget(self._agent_box)
        layout.addWidget(self._agent_carry_label)
        layout.addWidget(self._agent_util_label)
        layout.addWidget(QLabel("Turn Rate:"))
        layout.addWidget(self._speed_box)
        layout.addWidget(self._pacing_label)
        layout.addStretch(1)
        layout.addWidget(back_btn)

        # Periodic refresh timer (decoupled from simulation tick to avoid altering simulation pacing).
        # Low frequency (4 Hz) to avoid overhead; purely reads existing state.
        self._agent_update_timer = QTimer(self)
        self._agent_update_timer.timeout.connect(self._update_agent_metrics)  # type: ignore[arg-type]
        self._agent_update_timer.start(250)
        self._update_agent_metrics()

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
            if data is None:
                # Unlimited
                self._controller.set_playback_tps(None)
                self._pacing_label.setText("")
                return
            val = float(data)
        except (TypeError, ValueError):  # pragma: no cover - GUI safety
            return
        self._controller.set_playback_tps(val)
        # Show pacing hint when throttled at common educational rate
        if val == 1.0:
            self._pacing_label.setText("(pacing)")
        else:
            self._pacing_label.setText("")

    # --- Mode Configuration -------------------------------------------------
    def configure_for_mode(self, mode: str) -> None:
        """Adjust default playback based on launch mode.

        Turn mode: start at 1.0 tps (educational pacing) with pacing label.
        Continuous / legacy: start Unlimited (no throttle).
        """
        # Find indices
        def _find(value):
            for i in range(self._speed_box.count()):
                if self._speed_box.itemData(i) == value:
                    return i
            return 0
        if mode == "turn":
            idx_1 = _find(1.0)
            self._speed_box.setCurrentIndex(idx_1)
            self._controller.set_playback_tps(1.0)
            self._pacing_label.setText("(pacing)")
        else:
            idx_unl = _find(None)
            self._speed_box.setCurrentIndex(idx_unl)
            self._controller.set_playback_tps(None)
            self._pacing_label.setText("")

    # --- Agent metrics updates ----------------------------------------------
    def _update_agent_metrics(self) -> None:
        # Determine selected agent id
        idx = self._agent_box.currentIndex()
        if idx < 0:
            return
        aid = self._agent_box.itemData(idx)
        try:
            if aid is None:
                return
            bundle = self._controller.agent_carry_bundle(int(aid))  # type: ignore[attr-defined]
            util = self._controller.agent_carry_utility(int(aid))  # type: ignore[attr-defined]
            self._agent_carry_label.setText(f"carry: ({bundle[0]},{bundle[1]})")
            if util is None:
                self._agent_util_label.setText("U: —")
            else:
                self._agent_util_label.setText(f"U: {util:.2f}")
        except Exception:
            # Fail silently (GUI robustness) without affecting simulation determinism.
            pass

__all__ = ["ControlsPanel"]
