"""Start Menu Page (Phase A scaffold).

Displays scenario selection + basic parameter inputs. Phase A keeps this minimal:
* Scenarios: baseline_decision, turn_mode, legacy_random
* Free-form advanced inputs for grid size, agents, density, seed
* Preference type (single selection)

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


class StartMenuPage(QWidget):  # pragma: no cover (GUI)
    def __init__(self, on_launch: Callable[[MenuSelection], None], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._on_launch = on_launch
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select Scenario"))

        self.scenario_box = QComboBox()
        self.scenario_box.addItems([
            "baseline_decision",
            "turn_mode",
            "legacy_random",
        ])
        layout.addWidget(self.scenario_box)

        layout.addWidget(QLabel("Preference Type"))
        self.pref_box = QComboBox()
        self.pref_box.addItems(["cobb_douglas", "perfect_substitutes", "leontief"])
        layout.addWidget(self.pref_box)

        grid_row = QHBoxLayout()
        self.grid_w = QSpinBox(); self.grid_w.setRange(4, 128); self.grid_w.setValue(12)
        self.grid_h = QSpinBox(); self.grid_h.setRange(4, 128); self.grid_h.setValue(12)
        grid_row.addWidget(QLabel("Grid W")); grid_row.addWidget(self.grid_w)
        grid_row.addWidget(QLabel("Grid H")); grid_row.addWidget(self.grid_h)
        layout.addLayout(grid_row)

        agent_row = QHBoxLayout()
        self.agents_box = QSpinBox(); self.agents_box.setRange(1, 200); self.agents_box.setValue(4)
        agent_row.addWidget(QLabel("Agents")); agent_row.addWidget(self.agents_box)
        layout.addLayout(agent_row)

        density_row = QHBoxLayout()
        self.density_box = QDoubleSpinBox(); self.density_box.setDecimals(3); self.density_box.setRange(0.0,1.0); self.density_box.setSingleStep(0.05); self.density_box.setValue(0.25)
        density_row.addWidget(QLabel("Density")); density_row.addWidget(self.density_box)
        layout.addLayout(density_row)

        seed_row = QHBoxLayout()
        self.seed_edit = QLineEdit(str(1234))
        rand_btn = QPushButton("Randomize Seed")
        rand_btn.clicked.connect(self._randomize_seed)  # type: ignore[arg-type]
        seed_row.addWidget(QLabel("Seed"))
        seed_row.addWidget(self.seed_edit)
        seed_row.addWidget(rand_btn)
        layout.addLayout(seed_row)

        launch_btn = QPushButton("Launch Simulation")
        launch_btn.clicked.connect(self._emit_selection)  # type: ignore[arg-type]
        layout.addWidget(launch_btn)
        layout.addStretch(1)

    # --- Handlers -------------------------------------------------------------
    def _randomize_seed(self) -> None:
        self.seed_edit.setText(str(random.randint(0, 2**31 - 1)))

    def _emit_selection(self) -> None:
        scenario = self.scenario_box.currentText()
        mode = "legacy" if scenario == "legacy_random" else ("turn" if scenario == "turn_mode" else "continuous")
        selection = MenuSelection(
            scenario=scenario,
            mode=mode,
            seed=int(self.seed_edit.text() or 0),
            grid_size=(self.grid_w.value(), self.grid_h.value()),
            agents=int(self.agents_box.value()),
            density=float(self.density_box.value()),
            enable_respawn=True,
            enable_metrics=True,
            preference_type=self.pref_box.currentText(),
        )
        self._on_launch(selection)

__all__ = ["StartMenuPage", "MenuSelection"]
