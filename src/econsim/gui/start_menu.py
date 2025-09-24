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


class StartMenuPage(QWidget):  # pragma: no cover (GUI)
    def __init__(self, on_launch: Callable[[MenuSelection], None], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._on_launch = on_launch
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select Scenario"))

        self.scenario_box = QComboBox()
        self.scenario_box.addItems([
            "baseline_decision",
            "legacy_random",
        ])
        layout.addWidget(self.scenario_box)

        layout.addWidget(QLabel("Preference Type"))
        self.pref_box = QComboBox()
        self.pref_box.addItems(["cobb_douglas", "perfect_substitutes", "leontief"])
        layout.addWidget(self.pref_box)
        # Grid size inputs
        grid_row = QHBoxLayout()
        self.grid_w = QSpinBox()
        self.grid_w.setRange(4, 128)
        self.grid_w.setValue(12)
        self.grid_h = QSpinBox()
        self.grid_h.setRange(4, 128)
        self.grid_h.setValue(12)
        grid_row.addWidget(QLabel("Grid W"))
        grid_row.addWidget(self.grid_w)
        grid_row.addWidget(QLabel("Grid H"))
        grid_row.addWidget(self.grid_h)
        layout.addLayout(grid_row)

        # Agent count input
        agent_row = QHBoxLayout()
        self.agents_box = QSpinBox()
        self.agents_box.setRange(1, 200)
        self.agents_box.setValue(4)
        agent_row.addWidget(QLabel("Agents"))
        agent_row.addWidget(self.agents_box)
        layout.addLayout(agent_row)

        # Density input
        density_row = QHBoxLayout()
        self.density_box = QDoubleSpinBox()
        self.density_box.setDecimals(3)
        self.density_box.setRange(0.0, 1.0)
        self.density_box.setSingleStep(0.05)
        self.density_box.setValue(0.25)
        density_row.addWidget(QLabel("Density"))
        density_row.addWidget(self.density_box)
        layout.addLayout(density_row)

        # Seed controls
        seed_row = QHBoxLayout()
        self.seed_edit = QLineEdit(str(1234))
        rand_btn = QPushButton("Randomize Seed")
        rand_btn.clicked.connect(self._randomize_seed)  # type: ignore[arg-type]
        seed_row.addWidget(QLabel("Seed"))
        seed_row.addWidget(self.seed_edit)
        seed_row.addWidget(rand_btn)
        layout.addLayout(seed_row)

        # Start Paused toggle
        from PyQt6.QtWidgets import QCheckBox  # local import to avoid expanding top imports
        pause_row = QHBoxLayout()
        self.start_paused_cb = QCheckBox("Start Paused")
        self.start_paused_cb.setChecked(False)
        pause_row.addWidget(self.start_paused_cb)
        layout.addLayout(pause_row)

        # Launch
        launch_btn = QPushButton("Launch Simulation")
        launch_btn.clicked.connect(self._emit_selection)  # type: ignore[arg-type]
        layout.addWidget(launch_btn)
        layout.addStretch(1)

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
        selection = MenuSelection(
            scenario=scenario,
            mode=mode,
            seed=seed_val,
            grid_size=(grid_w, grid_h),
            agents=agents,
            density=density_val,
            enable_respawn=True,
            enable_metrics=True,
            preference_type=self.pref_box.currentText(),
            start_paused=bool(self.start_paused_cb.isChecked()),
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
