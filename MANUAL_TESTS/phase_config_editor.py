#!/usr/bin/env python3
"""
Phase Configuration Editor - GUI for creating custom phase schedules.

Allows users to configure test phases by specifying:
- Phase behavior (forage only, exchange only, both, or neither)
- Duration in turns
- Order of phases

Generates custom phase configurations for use with the manual test framework.
"""

import sys
import os
from typing import List, Tuple, Optional

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QSpinBox, QTableWidget, QTableWidgetItem, QGroupBox,
    QFormLayout, QMessageBox, QDialog, QDialogButtonBox, QTextEdit,
    QHeaderView, QAbstractItemView, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from framework.phase_manager import PhaseDefinition, PhaseBehavior, PhaseManager
from framework.test_configs import TestConfiguration


class PhaseConfigRow(QWidget):
    """A single row for configuring one phase."""
    
    phaseChanged = pyqtSignal()
    removeRequested = pyqtSignal(int)  # Emit row index
    
    def __init__(self, row_index: int, behavior: PhaseBehavior = None, duration: int = 100, parent=None):
        super().__init__(parent)
        self.row_index = row_index
        self.setup_ui()
        
        if behavior:
            self.set_behavior(behavior)
        self.duration_spin.setValue(duration)
    
    def setup_ui(self):
        """Create the row UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Remove button (leftmost)
        self.remove_btn = QPushButton("−")
        self.remove_btn.setFixedSize(25, 25)
        self.remove_btn.setStyleSheet("QPushButton { color: red; font-weight: bold; background: #ffe6e6; border: 1px solid #ff9999; border-radius: 3px; }")
        self.remove_btn.setToolTip("Remove this phase")
        self.remove_btn.clicked.connect(lambda: self.removeRequested.emit(self.row_index))
        layout.addWidget(self.remove_btn)
        
        # Phase number label
        self.phase_label = QLabel(f"Phase {self.row_index + 1}:")
        self.phase_label.setMinimumWidth(60)
        layout.addWidget(self.phase_label)
        
        # Behavior selection
        self.behavior_combo = QComboBox()
        self.behavior_combo.addItem("Both enabled", PhaseBehavior.both_enabled())
        self.behavior_combo.addItem("Forage only", PhaseBehavior.forage_only())
        self.behavior_combo.addItem("Exchange only", PhaseBehavior.exchange_only())
        self.behavior_combo.addItem("Both disabled", PhaseBehavior.both_disabled())
        self.behavior_combo.currentIndexChanged.connect(self.phaseChanged.emit)
        layout.addWidget(self.behavior_combo)
        
        # Duration
        layout.addWidget(QLabel("Duration:"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 10000)
        self.duration_spin.setValue(100)
        self.duration_spin.setSuffix(" turns")
        self.duration_spin.valueChanged.connect(self.phaseChanged.emit)
        layout.addWidget(self.duration_spin)
        
    def update_phase_number(self, new_index: int):
        """Update the phase number display."""
        self.row_index = new_index
        self.phase_label.setText(f"Phase {new_index + 1}:")
        
    def get_behavior(self) -> PhaseBehavior:
        """Get the selected behavior."""
        return self.behavior_combo.currentData()
        
    def set_behavior(self, behavior: PhaseBehavior):
        """Set the selected behavior."""
        for i in range(self.behavior_combo.count()):
            if self.behavior_combo.itemData(i).name == behavior.name:
                self.behavior_combo.setCurrentIndex(i)
                break
                
    def get_duration(self) -> int:
        """Get the duration in turns."""
        return self.duration_spin.value()
        
    def set_duration(self, duration: int):
        """Set the duration in turns."""
        self.duration_spin.setValue(duration)


class PhaseConfigEditor(QWidget):
    """Main phase configuration editor widget."""
    
    configChanged = pyqtSignal(list)  # Emit list of PhaseDefinitions
    
    def __init__(self, initial_phases: Optional[List[PhaseDefinition]] = None, parent=None):
        super().__init__(parent)
        self.phase_rows: List[PhaseConfigRow] = []
        self.setup_ui()
        
        if initial_phases:
            self.load_phases(initial_phases)
        # Note: Start with empty phase list - user must manually add phases
            
    def setup_ui(self):
        """Create the configuration editor UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Phase Schedule Configuration")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Instructions
        instructions = QLabel(
            "Create your custom test phases by clicking \"+ Add Phase\" below. Each phase has:\n"
            "• Behavior: which systems are enabled (forage, exchange, both, or neither)\n"
            "• Duration: number of simulation turns for this phase\n"
            "• Order: phases run in the sequence shown (use templates for quick setup)"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; margin: 10px 0; background: #f9f9f9; padding: 8px; border-left: 3px solid #007acc;")
        layout.addWidget(instructions)
        
        # Phase list container
        self.phases_container = QWidget()
        self.phases_layout = QVBoxLayout(self.phases_container)
        layout.addWidget(self.phases_container)
        
        # Add phase button
        self.add_btn = QPushButton("+ Add Phase")
        self.add_btn.clicked.connect(self.add_new_phase)
        layout.addWidget(self.add_btn)
        
        # Summary section
        summary_group = QGroupBox("Phase Schedule Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("font-family: monospace; background: #f5f5f5; padding: 10px; border: 1px solid #ddd;")
        summary_layout.addWidget(self.summary_label)
        
        layout.addWidget(summary_group)
        
        # Quick templates section
        templates_group = QGroupBox("Quick Templates")
        templates_layout = QHBoxLayout(templates_group)
        
        standard_btn = QPushButton("Standard 6-Phase")
        standard_btn.clicked.connect(self.load_standard_template)
        templates_layout.addWidget(standard_btn)
        
        simple_btn = QPushButton("Simple: Forage → Both → Idle")
        simple_btn.clicked.connect(self.load_simple_template)
        templates_layout.addWidget(simple_btn)
        
        bilateral_btn = QPushButton("Bilateral Focus: Exchange → Both")
        bilateral_btn.clicked.connect(self.load_bilateral_template)
        templates_layout.addWidget(bilateral_btn)
        
        layout.addWidget(templates_group)
        
        self.update_summary()
        
    def add_phase_row(self, behavior: PhaseBehavior = None, duration: int = 100) -> PhaseConfigRow:
        """Add a new phase configuration row."""
        if behavior is None:
            behavior = PhaseBehavior.both_enabled()
            
        row_index = len(self.phase_rows)
        row = PhaseConfigRow(row_index, behavior, duration)
        row.phaseChanged.connect(self.on_phase_changed)
        row.removeRequested.connect(self.remove_phase_row)
        
        self.phase_rows.append(row)
        self.phases_layout.addWidget(row)
        
        # Update all phase numbers
        self.update_phase_numbers()
        self.update_summary()
        
        return row
        
    def remove_phase_row(self, row_index: int):
        """Remove a phase row."""
        # Allow removing all phases - user can add them back
        if 0 <= row_index < len(self.phase_rows):
            row = self.phase_rows.pop(row_index)
            row.setParent(None)
            row.deleteLater()
            
            # Update remaining phase numbers
            self.update_phase_numbers()
            self.update_summary()
            
    def update_phase_numbers(self):
        """Update phase number labels for all rows."""
        for i, row in enumerate(self.phase_rows):
            row.update_phase_number(i)
            
    def add_new_phase(self):
        """Add a new phase with default settings."""
        self.add_phase_row(PhaseBehavior.both_enabled(), 100)
        
    def on_phase_changed(self):
        """Handle phase configuration changes."""
        self.update_summary()
        self.configChanged.emit(self.get_phase_definitions())
        
    def get_phase_definitions(self) -> List[PhaseDefinition]:
        """Generate PhaseDefinition objects from current configuration."""
        phases = []
        current_turn = 1
        
        for i, row in enumerate(self.phase_rows):
            behavior = row.get_behavior()
            duration = row.get_duration()
            turn_end = current_turn + duration - 1
            
            phase = PhaseDefinition(
                number=i + 1,
                turn_start=current_turn,
                turn_end=turn_end,
                description=behavior.description,
                forage_enabled=behavior.forage_enabled,
                trade_enabled=behavior.trade_enabled
            )
            phases.append(phase)
            current_turn = turn_end + 1
            
        return phases
        
    def load_phases(self, phases: List[PhaseDefinition]):
        """Load existing phase definitions into the editor."""
        # Clear existing rows
        for row in self.phase_rows:
            row.setParent(None)
            row.deleteLater()
        self.phase_rows.clear()
        
        # Add rows for each phase
        for phase in phases:
            behavior = PhaseBehavior(
                name="custom",
                description=phase.description,
                forage_enabled=phase.forage_enabled,
                trade_enabled=phase.trade_enabled
            )
            self.add_phase_row(behavior, phase.duration)
            
        self.update_summary()
        
    def update_summary(self):
        """Update the phase schedule summary."""
        phases = self.get_phase_definitions()
        if not phases:
            self.summary_label.setText("📝 No phases configured yet. Click '+ Add Phase' to get started.")
            return
            
        try:
            manager = PhaseManager(phases)
            summary = manager.get_phase_summary()
            total_turns = manager.get_total_turns()
            phase_count = manager.get_phase_count()
            
            text = f"✅ {phase_count} phase{'s' if phase_count != 1 else ''} | {total_turns} total turns\n"
            text += f"📋 Schedule: {summary}"
            self.summary_label.setText(text)
        except Exception as e:
            self.summary_label.setText(f"❌ Configuration Error: {str(e)}")
            # Also clear invalid phases to prevent confusion
            if "continuous sequence" in str(e):
                pass  # Keep phases for user to fix
            
    def load_standard_template(self):
        """Load the standard 6-phase template."""
        phases = PhaseManager.create_standard_phases().phases
        self.load_phases(list(phases.values()))
        
    def load_simple_template(self):
        """Load a simple 3-phase template."""
        manager = PhaseManager.create_simple_phases(
            forage_only=150,
            both_enabled=200,
            both_disabled=50
        )
        self.load_phases(list(manager.phases.values()))
        
    def load_bilateral_template(self):
        """Load a bilateral exchange focused template."""
        manager = PhaseManager.create_custom_phases([
            (PhaseBehavior.exchange_only(), 200),
            (PhaseBehavior.both_enabled(), 300),
            (PhaseBehavior.both_disabled(), 50)
        ])
        self.load_phases(list(manager.phases.values()))


class PhaseConfigDialog(QDialog):
    """Dialog for configuring test phases."""
    
    def __init__(self, initial_phases: Optional[List[PhaseDefinition]] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Test Phases")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Editor
        self.editor = PhaseConfigEditor(initial_phases)
        self.editor.configChanged.connect(self.validate_phases)
        layout.addWidget(self.editor)
        
        # Buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept_if_valid)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        
        # Initial validation
        self.validate_phases()
        
    def validate_phases(self):
        """Enable/disable OK button based on phase validity."""
        phases = self.editor.get_phase_definitions()
        has_phases = len(phases) > 0
        
        ok_button = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setEnabled(has_phases)
            if not has_phases:
                ok_button.setToolTip("Add at least one phase to continue")
            else:
                ok_button.setToolTip("")
    
    def accept_if_valid(self):
        """Only accept if we have valid phases."""
        phases = self.editor.get_phase_definitions()
        if not phases:
            # Import here to avoid circular imports
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Phases Configured", 
                              "Please add at least one phase before continuing.")
            return
        
        try:
            # Validate by attempting to create PhaseManager
            PhaseManager(phases)
            self.accept()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Invalid Phase Configuration", 
                               f"Phase configuration error:\n\n{str(e)}")
        
    def get_phases(self) -> List[PhaseDefinition]:
        """Get the configured phase definitions."""
        return self.editor.get_phase_definitions()


def main():
    """Demo the phase configuration editor."""
    app = QApplication(sys.argv)
    
    # Test the dialog
    dialog = PhaseConfigDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        phases = dialog.get_phases()
        print("Configured Phases:")
        for phase in phases:
            print(f"  Phase {phase.number}: {phase.description} ({phase.turn_start}-{phase.turn_end})")
        
        # Test creating a PhaseManager with these phases
        try:
            manager = PhaseManager(phases)
            print(f"\nSummary: {manager.get_phase_summary()}")
            print(f"Total turns: {manager.get_total_turns()}")
        except Exception as e:
            print(f"Error creating PhaseManager: {e}")
    else:
        print("Configuration cancelled")


if __name__ == "__main__":
    main()