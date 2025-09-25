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
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QComboBox, QGridLayout, QCheckBox, QGroupBox, QFormLayout


from ..simulation_controller import SimulationController


class ControlsPanel(QWidget):  # pragma: no cover (GUI)
    def __init__(self, on_back: Callable[[], None], controller: SimulationController):
        super().__init__()
        self._controller = controller
        layout = QVBoxLayout(self)
        
        # Use grid layout for compact button arrangement
        button_layout = QGridLayout()
        
        # Core control buttons in compact 2x2 grid
        initial_label = "Resume" if controller.is_paused() else "Pause"
        self._pause_btn = QPushButton(initial_label)
        step1 = QPushButton("Step 1")
        step5 = QPushButton("Step 5") 
        refresh_hash = QPushButton("Refresh")

        self._pause_btn.setToolTip("Pause or resume the simulation")
        self._pause_btn.setAccessibleName("pause-resume-button")
        step1.setToolTip("Advance the simulation by one step")
        step1.setAccessibleName("step-one-button")
        step5.setToolTip("Advance the simulation by five steps")
        step5.setAccessibleName("step-five-button")
        refresh_hash.setToolTip("Recompute the determinism hash for the current state")
        refresh_hash.setAccessibleName("refresh-hash-button")
        
        button_layout.addWidget(self._pause_btn, 0, 0)
        button_layout.addWidget(step1, 0, 1)
        button_layout.addWidget(step5, 1, 0)
        button_layout.addWidget(refresh_hash, 1, 1)
        layout.addLayout(button_layout)
        
        # Hash display (compact format)
        self._hash_label = QLabel("hash: —")
        self._hash_label.setWordWrap(True)
        self._hash_label.setStyleSheet("font-size: 10px; color: gray;")
        layout.addWidget(self._hash_label)
        
        # Turn Rate control
        turn_row = QHBoxLayout()
        turn_row.addWidget(QLabel("Rate:"))
        self._speed_box = QComboBox()
        self._speed_box.setToolTip("Turn pacing rate")
        self._speed_box.setAccessibleName("turn-rate-combo")
        self._speeds: list[float | None] = [None, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0]
        for s in self._speeds:
            if s is None:
                self._speed_box.addItem("Unlimited", userData=None)
            else:
                self._speed_box.addItem(f"{s} tps", userData=s)
        turn_row.addWidget(self._speed_box)
        layout.addLayout(turn_row)
        
        # Respawn control
        respawn_row = QHBoxLayout()
        respawn_row.addWidget(QLabel("Respawn:"))
        self._respawn_box = QComboBox()
        self._respawn_box.setToolTip("Respawn frequency")
        self._respawn_box.setAccessibleName("respawn-frequency-combo")
        self._respawn_options: list[tuple[str, int | None]] = [
            ("Off", None),
            ("Every 1", 1),
            ("Every 5", 5),
            ("Every 10", 10),
            ("Every 20", 20),
        ]
        for label, val in self._respawn_options:
            self._respawn_box.addItem(label, userData=val)
        # Set default to "Every 20"
        self._respawn_box.setCurrentText("Every 20")
        respawn_row.addWidget(self._respawn_box)
        layout.addLayout(respawn_row)
        
        # Trade controls group
        trade_group = QGroupBox("Trade Controls")
        trade_form = QFormLayout()

        self._bilateral_cb = QCheckBox("Master (Draft+Exec)")
        self._bilateral_cb.setToolTip("Enable both trade draft enumeration and execution (sets both flags).")
        try:
            self._bilateral_cb.setChecked(self._controller.bilateral_enabled())  # type: ignore[attr-defined]
        except Exception:
            self._bilateral_cb.setChecked(False)

        self._trade_draft_cb = QCheckBox("Draft Intents")
        self._trade_draft_cb.setToolTip("Enumerate potential bilateral trade intents (no execution).")
        try:
            self._trade_draft_cb.setChecked(self._controller.trade_draft_enabled())  # type: ignore[attr-defined]
        except Exception:
            self._trade_draft_cb.setChecked(False)

        self._trade_exec_cb = QCheckBox("Execute Trades")
        self._trade_exec_cb.setToolTip("Execute the highest-priority drafted trade each step (implies draft).")
        try:
            self._trade_exec_cb.setChecked(self._controller.trade_exec_enabled())  # type: ignore[attr-defined]
        except Exception:
            self._trade_exec_cb.setChecked(False)

        self._trade_debug_cb = QCheckBox("Debug Overlay")
        self._trade_debug_cb.setToolTip("Show first few drafted trade intents and last executed trade summary.")
        try:
            self._trade_debug_cb.setChecked(self._controller.trade_debug_enabled())  # type: ignore[attr-defined]
        except Exception:
            self._trade_debug_cb.setChecked(False)

        trade_form.addRow(self._bilateral_cb)
        trade_form.addRow(self._trade_draft_cb)
        trade_form.addRow(self._trade_exec_cb)
        trade_form.addRow(self._trade_debug_cb)
        trade_group.setLayout(trade_form)
        layout.addWidget(trade_group)

        # Foraging enable toggle (new)
        self._forage_cb = QCheckBox("Foraging Enabled")
        self._forage_cb.setToolTip("Enable/disable baseline resource foraging (when off, agents only trade or return home).")
        try:
            self._forage_cb.setChecked(self._controller.forage_enabled())  # type: ignore[attr-defined]
        except Exception:
            self._forage_cb.setChecked(True)
        layout.addWidget(self._forage_cb)

        # Back to menu button
        back_btn = QPushButton("Back to Menu")
        back_btn.setToolTip("Return to the start menu and end the current simulation")
        back_btn.setAccessibleName("back-to-menu-button")
        layout.addWidget(back_btn)

        # Wire signals
        self._pause_btn.clicked.connect(self._toggle_pause)  # type: ignore[arg-type]
        step1.clicked.connect(self._do_step1)  # type: ignore[arg-type]
        step5.clicked.connect(self._do_step5)  # type: ignore[arg-type]
        refresh_hash.clicked.connect(self._refresh_hash)  # type: ignore[arg-type]
        back_btn.clicked.connect(on_back)  # type: ignore[arg-type]
        self._speed_box.currentIndexChanged.connect(self._change_speed)  # type: ignore[arg-type]
        self._respawn_box.currentIndexChanged.connect(self._change_respawn_interval)  # type: ignore[arg-type]
        self._bilateral_cb.stateChanged.connect(self._toggle_bilateral)  # type: ignore[arg-type]
        # Granular trade controls
        self._trade_draft_cb.stateChanged.connect(self._toggle_trade_draft)  # type: ignore[arg-type]
        self._trade_exec_cb.stateChanged.connect(self._toggle_trade_exec)  # type: ignore[arg-type]
        self._trade_debug_cb.stateChanged.connect(self._toggle_trade_debug)  # type: ignore[arg-type]
        self._forage_cb.stateChanged.connect(self._toggle_forage)  # type: ignore[arg-type]

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
                return
            val = float(data)
        except (TypeError, ValueError):  # pragma: no cover - GUI safety
            return
        self._controller.set_playback_tps(val)

    def _change_respawn_interval(self, idx: int) -> None:
        data = self._respawn_box.itemData(idx)
        try:
            if data is None:
                self._controller.set_respawn_interval(None)
            else:
                self._controller.set_respawn_interval(int(data))
        except Exception:
            pass

    def _toggle_bilateral(self) -> None:
        try:
            enable = self._bilateral_cb.isChecked()
            self._controller.set_bilateral_enabled(enable)  # type: ignore[attr-defined]
            # Clear stale intents if disabling so overlay/inspector empties quickly
            if not enable:
                sim = getattr(self._controller, 'simulation', None)
                if sim is not None and hasattr(sim, 'trade_intents'):
                    try:
                        sim.trade_intents = None  # type: ignore[attr-defined]
                    except Exception:
                        pass
            # Sync granular boxes to reflect master state
            if enable:
                self._trade_draft_cb.setChecked(True)
                self._trade_exec_cb.setChecked(True)
        except Exception:
            pass

    def _toggle_trade_draft(self) -> None:
        try:
            enable = self._trade_draft_cb.isChecked()
            self._controller.set_trade_draft_enabled(enable)  # type: ignore[attr-defined]
            # If draft turned off, also uncheck execution & master
            if not enable:
                if self._trade_exec_cb.isChecked():
                    self._trade_exec_cb.setChecked(False)
                if self._bilateral_cb.isChecked():
                    self._bilateral_cb.setChecked(False)
        except Exception:
            pass

    def _toggle_trade_exec(self) -> None:
        try:
            enable = self._trade_exec_cb.isChecked()
            self._controller.set_trade_exec_enabled(enable)  # type: ignore[attr-defined]
            if enable:
                # Ensure draft + master reflect execution dependency
                if not self._trade_draft_cb.isChecked():
                    self._trade_draft_cb.setChecked(True)
                if not self._bilateral_cb.isChecked():
                    self._bilateral_cb.setChecked(True)
            else:
                # Execution off -> master might still be off if only draft remains
                if self._bilateral_cb.isChecked():
                    self._bilateral_cb.setChecked(False)
        except Exception:
            pass

    def _toggle_trade_debug(self) -> None:
        try:
            enable = self._trade_debug_cb.isChecked()
            self._controller.set_trade_debug_enabled(enable)  # type: ignore[attr-defined]
        except Exception:
            pass

    def _toggle_forage(self) -> None:
        try:
            enable = self._forage_cb.isChecked()
            self._controller.set_forage_enabled(enable)  # type: ignore[attr-defined]
        except Exception:
            pass

    # --- Mode Configuration -------------------------------------------------
    def configure_for_mode(self, mode: str) -> None:
        """Adjust default playback based on launch mode.

        Turn mode: start at 1.0 tps (educational pacing).
        Continuous / legacy: start Unlimited (no throttle).
        """
        # Find indices
        def _find(value: float | None) -> int:
            for i in range(self._speed_box.count()):
                if self._speed_box.itemData(i) == value:
                    return i
            return 0
        if mode == "turn":
            idx_1 = _find(1.0)
            self._speed_box.setCurrentIndex(idx_1)
            self._controller.set_playback_tps(1.0)
        else:
            idx_unl = _find(None)
            self._speed_box.setCurrentIndex(idx_unl)
            self._controller.set_playback_tps(None)

__all__ = ["ControlsPanel"]
