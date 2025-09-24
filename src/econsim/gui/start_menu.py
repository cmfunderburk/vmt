"""Start Menu Page (Phase A scaffold).

Displays scenario selection + basic parameter inputs.
Consolidated: removed separate turn_mode scenario. A "Start Paused" checkbox
replaces it so users can launch baseline in a paused state and use manual step.
Scenarios now: baseline_decision, legacy_random.

Validation kept intentionally light; SessionFactory will perform deeper checks.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional
import random

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QGroupBox,

)


@dataclass
class MenuSelection:
    scenario: str
    mode: str
    seed: int
    grid_size: tuple[int, int]
    agents: int
    density: float | None
    enable_respawn: bool
    enable_metrics: bool
    preference_type: str
    start_paused: bool
    respawn_interval: Optional[int]  # None = Off, or 1,2,5,10 steps
    decision_mode_enabled: bool
    endowment_pattern: str
    perception_radius: int


class StartMenuPage(QWidget):  # pragma: no cover (GUI)
    def __init__(self, on_launch: Callable[[MenuSelection], None], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._on_launch = on_launch
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("VMT EconSim (Start Menu)")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Scenario selection
        scenario_row = QHBoxLayout()
        scenario_row.addWidget(QLabel("Scenario:"))
        self.scenario_box = QComboBox()
        self.scenario_box.addItems([  # type: ignore[arg-type]
            "baseline", 
            "bilateral_exchange", 
            "money_market"
        ])
        # For now, only baseline is functional
        self.scenario_box.setCurrentText("baseline")
        self.scenario_box.setEnabled(False)  # Disable until other scenarios implemented
        scenario_row.addWidget(self.scenario_box)
        scenario_row.addStretch()
        layout.addLayout(scenario_row)
        
        # Preferences section
        layout.addWidget(QLabel("Preferences (initial agents)"))
        
        # Agent count (disabled for baseline as noted in ASCII)
        count_row = QHBoxLayout()
        count_row.addWidget(QLabel("  Count:"))
        self.agents_box = QSpinBox()
        self.agents_box.setRange(1, 200)
        self.agents_box.setValue(4)
        self.agents_box.setEnabled(False)  # Disabled until scenario supports agent input
        count_row.addWidget(self.agents_box)
        count_row.addWidget(QLabel("(disabled until scenario supports agent input)"))
        count_row.addStretch()
        layout.addLayout(count_row)
        
        # Preference type
        pref_row = QHBoxLayout()
        pref_row.addWidget(QLabel("  Pref Mix:"))
        self.pref_box = QComboBox()
        self.pref_box.addItems(["Cobb-Douglas", "Perfect Substitutes", "Leontief"])  # type: ignore[arg-type]
        pref_row.addWidget(self.pref_box)
        pref_row.addStretch()
        layout.addLayout(pref_row)
        
        # Endowment Pattern (inactive in baseline per ASCII)
        endow_row = QHBoxLayout()
        endow_row.addWidget(QLabel("Endowment Pattern:"))
        self.endowment_box = QComboBox()
        self.endowment_box.addItems(["uniform", "random", "clustered"])  # type: ignore[arg-type]
        self.endowment_box.setEnabled(False)  # Inactive in baseline
        endow_row.addWidget(self.endowment_box)
        endow_row.addWidget(QLabel("(inactive in baseline)"))
        endow_row.addStretch()
        layout.addLayout(endow_row)
        
        # Seed controls with Start Paused
        seed_row = QHBoxLayout()
        seed_row.addWidget(QLabel("Seed:"))
        self.seed_edit = QLineEdit(str(1234))
        seed_row.addWidget(self.seed_edit)
        rand_btn = QPushButton("Randomize")
        rand_btn.clicked.connect(self._randomize_seed)  # type: ignore[arg-type]
        seed_row.addWidget(rand_btn)
        
        self.start_paused_cb = QCheckBox("Start Paused")
        self.start_paused_cb.setChecked(False)
        seed_row.addWidget(self.start_paused_cb)
        seed_row.addStretch()
        layout.addLayout(seed_row)
        
        # Respawn Interval
        respawn_row = QHBoxLayout()
        respawn_row.addWidget(QLabel("Respawn Interval:"))
        self.respawn_box = QComboBox()
        self.respawn_box.addItems(["Off", "1", "2", "5", "10"])  # type: ignore[arg-type]
        respawn_row.addWidget(self.respawn_box)
        respawn_row.addStretch()
        layout.addLayout(respawn_row)
        
        # Decision Mode radio buttons
        decision_row = QHBoxLayout()
        decision_row.addWidget(QLabel("Decision Mode:"))
        self.decision_enabled = QRadioButton("Enabled")
        self.decision_disabled = QRadioButton("Disabled") 
        self.decision_enabled.setChecked(True)  # Default to enabled
        self.decision_group = QButtonGroup()
        self.decision_group.addButton(self.decision_enabled)
        self.decision_group.addButton(self.decision_disabled)
        decision_row.addWidget(self.decision_enabled)
        decision_row.addWidget(self.decision_disabled)
        decision_row.addStretch()
        layout.addLayout(decision_row)
        
        # Advanced panel (collapsed by default)
        self.advanced_group = QGroupBox("Advanced")
        self.advanced_group.setCheckable(True)
        self.advanced_group.setChecked(False)  # Collapsed by default
        advanced_layout = QVBoxLayout(self.advanced_group)
        
        # Perception Radius
        perception_row = QHBoxLayout()
        perception_row.addWidget(QLabel("Perception Radius:"))
        self.perception_box = QSpinBox()
        self.perception_box.setRange(1, 20)
        self.perception_box.setValue(8)
        perception_row.addWidget(self.perception_box)
        perception_row.addStretch()
        advanced_layout.addLayout(perception_row)
        
        # Metrics Enabled
        self.metrics_cb = QCheckBox("Metrics Enabled")
        self.metrics_cb.setChecked(True)
        advanced_layout.addWidget(self.metrics_cb)
        
        layout.addWidget(self.advanced_group)
        
        # Hidden legacy fields for compatibility (grid size, density)
        self.grid_w = QSpinBox()
        self.grid_w.setRange(4, 128)
        self.grid_w.setValue(12)
        self.grid_w.hide()
        self.grid_h = QSpinBox()
        self.grid_h.setRange(4, 128) 
        self.grid_h.setValue(12)
        self.grid_h.hide()
        self.density_box = QDoubleSpinBox()
        self.density_box.setDecimals(3)
        self.density_box.setRange(0.0, 1.0)
        self.density_box.setSingleStep(0.05)
        self.density_box.setValue(0.25)
        self.density_box.hide()
        
        # Launch buttons
        button_row = QHBoxLayout()
        launch_btn = QPushButton("Launch Simulation")
        launch_btn.clicked.connect(self._emit_selection)  # type: ignore[arg-type]
        button_row.addWidget(launch_btn)
        
        quit_btn = QPushButton("Quit")
        quit_btn.clicked.connect(self._quit_application)  # type: ignore[arg-type]
        button_row.addWidget(quit_btn)
        button_row.addStretch()
        layout.addLayout(button_row)
        
        layout.addStretch()
    def _quit_application(self) -> None:
        """Handle quit button click."""
        import sys
        sys.exit(0)

    # --- Handlers -------------------------------------------------------------
    def _randomize_seed(self) -> None:
        self.seed_edit.setText(str(random.randint(0, 2**31 - 1)))

    def _emit_selection(self) -> None:
        scenario = self.scenario_box.currentText()
        # Mode mapping: legacy_random keeps legacy path; baseline_decision => continuous.
        mode = "legacy" if scenario == "legacy_random" else "continuous"
        # Extract raw values
        seed_text = self.seed_edit.text().strip()
        try:
            seed_val = int(seed_text)
        except ValueError:
            # Fallback to random deterministic-ish seed path; could surface UI error later
            seed_val = 0
        grid_w = self.grid_w.value()
        grid_h = self.grid_h.value()
        agents = int(self.agents_box.value())
        density_val = float(self.density_box.value())
        try:
            self._validate_inputs(grid_w, grid_h, agents, density_val)
        except ValueError as exc:  # pragma: no cover - GUI feedback path
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Input Error", str(exc))
            return
        # Get respawn interval
        respawn_text = self.respawn_box.currentText()
        respawn_interval = None if respawn_text == "Off" else int(respawn_text)
        
        # Get decision mode
        decision_mode_enabled = self.decision_enabled.isChecked()
        
        # Get advanced settings
        perception_radius = self.perception_box.value()
        metrics_enabled = bool(self.metrics_cb.isChecked())
        
        # Map preference type back to internal format
        pref_map = {
            "Cobb-Douglas": "cobb_douglas",
            "Perfect Substitutes": "perfect_substitutes",
            "Leontief": "leontief"
        }
        pref_type = pref_map.get(self.pref_box.currentText(), "cobb_douglas")
        
        selection = MenuSelection(
            scenario=scenario,
            mode=mode,
            seed=seed_val,
            grid_size=(grid_w, grid_h),
            agents=agents,
            density=density_val,
            enable_respawn=True,
            enable_metrics=metrics_enabled,
            preference_type=pref_type,
            start_paused=bool(self.start_paused_cb.isChecked()),
            respawn_interval=respawn_interval,
            decision_mode_enabled=decision_mode_enabled,
            endowment_pattern=self.endowment_box.currentText(),
            perception_radius=perception_radius,
        )
        self._on_launch(selection)

    # --- Validation ---------------------------------------------------------
    def _validate_inputs(self, w: int, h: int, agents: int, density: float) -> None:
        """Raise ValueError if any input outside allowed fast-path bounds.

        Bounds intentionally conservative to protect perf & determinism expectations.
        """
        if not (4 <= w <= 64 and 4 <= h <= 64):
            raise ValueError(f"Grid size out of bounds (4-64): {w}x{h}")
        if not (1 <= agents <= 64):
            raise ValueError(f"Agents out of bounds (1-64): {agents}")
        if not (0.0 <= density <= 1.0):
            raise ValueError(f"Density out of bounds [0,1]: {density}")

__all__ = ["StartMenuPage", "MenuSelection"]
