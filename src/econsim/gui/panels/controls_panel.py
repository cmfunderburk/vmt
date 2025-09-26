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
from PyQt6.QtWidgets import QDoubleSpinBox


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
        self._speed_box.setToolTip("Turn pacing rate (turns per second)")
        self._speed_box.setAccessibleName("turn-rate-combo")
        self._speeds: list[float | None] = [0.5, 1.0, 5.0, 10.0, 20.0, None]
        for s in self._speeds:
            if s is None:
                self._speed_box.addItem("Unlimited", userData=None)
            else:
                self._speed_box.addItem(f"{s} tps", userData=s)
        # Set default to 5 turns per second
        self._speed_box.setCurrentText("5.0 tps")
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
        # Set default to "Every 5"
        self._respawn_box.setCurrentText("Every 5")
        respawn_row.addWidget(self._respawn_box)
        layout.addLayout(respawn_row)
        
        # Respawn rate control (percentage of deficit)
        respawn_rate_row = QHBoxLayout()
        respawn_rate_row.addWidget(QLabel("Respawn Rate:"))
        self._respawn_rate_box = QComboBox()
        self._respawn_rate_box.setToolTip("Percentage of resource deficit to respawn each time")
        self._respawn_rate_box.setAccessibleName("respawn-rate-combo")
        self._respawn_rate_options: list[tuple[str, float]] = [
            ("10%", 0.1),
            ("25%", 0.25),
            ("50%", 0.5),
            ("75%", 0.75),
            ("100%", 1.0),
        ]
        for label, val in self._respawn_rate_options:
            self._respawn_rate_box.addItem(label, userData=val)
        # Set to current respawn rate from controller
        try:
            current_rate = self._controller.respawn_rate()  # type: ignore[attr-defined]
            for i, (label, val) in enumerate(self._respawn_rate_options):
                if abs(val - current_rate) < 0.01:  # Close enough match
                    self._respawn_rate_box.setCurrentIndex(i)
                    break
            else:
                # Default to "25%" if no match found
                self._respawn_rate_box.setCurrentText("25%")
        except Exception:
            # Default to "25%" for moderate replenishment
            self._respawn_rate_box.setCurrentText("25%")
        respawn_rate_row.addWidget(self._respawn_rate_box)
        layout.addLayout(respawn_rate_row)

        # Decision parameter group (distance scaling k)
        decision_group = QGroupBox("Decision Params")
        decision_form = QFormLayout()
        self._k_spin = QDoubleSpinBox()
        self._k_spin.setDecimals(2)
        self._k_spin.setRange(0.0, 10.0)
        self._k_spin.setSingleStep(0.1)
        # Initialize from simulation config if present
        try:
            current_k = float(getattr(self._controller.simulation.config, 'distance_scaling_factor', 0.0))  # type: ignore[attr-defined]
        except Exception:
            current_k = 0.0
        self._k_spin.setValue(current_k)
        self._k_spin.setToolTip("Distance scaling factor k for unified selection (ΔU / (1 + k·dist²))")
        decision_form.addRow(QLabel("k:"), self._k_spin)
        decision_group.setLayout(decision_form)
        layout.addWidget(decision_group)
        
        # Behavior controls group (simplified from complex 4-checkbox system)
        behavior_group = QGroupBox("Behavior Controls")
        behavior_form = QFormLayout()

        # Foraging behavior
        self._forage_cb = QCheckBox("Foraging")
        self._forage_cb.setToolTip("Agents collect resources from the environment")
        try:
            self._forage_cb.setChecked(self._controller.forage_enabled())  # type: ignore[attr-defined]
        except Exception:
            self._forage_cb.setChecked(True)

        # Bilateral exchange behavior
        self._bilateral_cb = QCheckBox("Bilateral Exchange")
        self._bilateral_cb.setToolTip("Agents can trade resources with each other")
        try:
            self._bilateral_cb.setChecked(self._controller.bilateral_enabled())  # type: ignore[attr-defined]
        except Exception:
            self._bilateral_cb.setChecked(False)

        behavior_form.addRow(self._forage_cb)
        behavior_form.addRow(self._bilateral_cb)
        behavior_group.setLayout(behavior_form)
        layout.addWidget(behavior_group)

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
        self._respawn_rate_box.currentIndexChanged.connect(self._change_respawn_rate)  # type: ignore[arg-type]
        # Simplified behavior controls
        self._forage_cb.stateChanged.connect(self._toggle_forage)  # type: ignore[arg-type]
        self._bilateral_cb.stateChanged.connect(self._toggle_bilateral)  # type: ignore[arg-type]
        self._k_spin.valueChanged.connect(self._change_k)  # type: ignore[arg-type]
        
        # Initialize controller with default speed (5.0 tps)
        self._controller.set_playback_tps(5.0)

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

    def _change_respawn_rate(self, idx: int) -> None:
        data = self._respawn_rate_box.itemData(idx)
        try:
            if data is not None:
                self._controller.set_respawn_rate(float(data))  # type: ignore[attr-defined]
        except Exception:
            pass

    def _toggle_forage(self) -> None:
        """Toggle foraging behavior on/off."""
        try:
            enable = self._forage_cb.isChecked()
            self._controller.set_forage_enabled(enable)  # type: ignore[attr-defined]
        except Exception:
            pass

    def _toggle_bilateral(self) -> None:
        """Toggle bilateral exchange behavior on/off (simplified from 4-checkbox system)."""
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
        except Exception:
            pass

    def _change_k(self, val: float) -> None:
        """Live update distance scaling factor k in simulation config (append-only field)."""
        try:
            sim = self._controller.simulation
            cfg = getattr(sim, 'config', None)
            if cfg is not None and hasattr(cfg, 'distance_scaling_factor'):
                # Clamp just in case
                setattr(cfg, 'distance_scaling_factor', max(0.0, min(10.0, float(val))))
        except Exception:
            pass

    # --- Mode Configuration -------------------------------------------------
    def configure_for_mode(self, mode: str) -> None:
        """Adjust default playback based on launch mode.

        All modes now default to 5.0 tps (moderate educational pacing).
        """
        # Find indices
        def _find(value: float | None) -> int:
            for i in range(self._speed_box.count()):
                if self._speed_box.itemData(i) == value:
                    return i
            return 0
        # Set default to 5.0 tps for all modes
        idx_5 = _find(5.0)
        self._speed_box.setCurrentIndex(idx_5)
        self._controller.set_playback_tps(5.0)

__all__ = ["ControlsPanel"]
