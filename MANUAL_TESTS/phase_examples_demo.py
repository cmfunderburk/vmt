#!/usr/bin/env python3
"""
Simple Phase Configuration Examples

Demonstrates various ways to create custom phase schedules using the 
new phase configuration system. Shows both programmatic and GUI approaches.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent  
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from framework.phase_manager import PhaseManager, PhaseBehavior
from framework.test_configs import TestConfiguration
from framework.base_test import StandardPhaseTest
from phase_config_editor import PhaseConfigDialog


class PhaseExamplesWindow(QMainWindow):
    """Window showing different phase configuration examples."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Phase Configuration Examples")
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()
        
    def setup_ui(self):
        """Create the UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Custom Phase Configuration Examples")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "The new phase system allows you to create custom test schedules by specifying:\n"
            "• Which behaviors are enabled (forage, exchange, both, or neither)\n"
            "• How long each phase lasts (in simulation turns)\n"
            "• The order of phases\n\n"
            "Click the buttons below to see examples or open the phase editor."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("margin: 10px; color: #666;")
        layout.addWidget(desc)
        
        # Example buttons
        button_layout = QVBoxLayout()
        
        # Standard phases
        standard_btn = QPushButton("Show Standard 6-Phase Schedule")
        standard_btn.clicked.connect(self.show_standard_phases)
        button_layout.addWidget(standard_btn)
        
        # Simple phases
        simple_btn = QPushButton("Show Simple 3-Phase Schedule")
        simple_btn.clicked.connect(self.show_simple_phases)
        button_layout.addWidget(simple_btn)
        
        # Bilateral focused
        bilateral_btn = QPushButton("Show Bilateral Exchange Focused")
        bilateral_btn.clicked.connect(self.show_bilateral_phases)
        button_layout.addWidget(bilateral_btn)
        
        # Foraging focused
        forage_btn = QPushButton("Show Foraging Focused Schedule")
        forage_btn.clicked.connect(self.show_forage_phases)
        button_layout.addWidget(forage_btn)
        
        # Custom editor
        editor_btn = QPushButton("Open Phase Configuration Editor")
        editor_btn.setStyleSheet("font-weight: bold; background: #4CAF50; color: white; padding: 10px;")
        editor_btn.clicked.connect(self.open_phase_editor)
        button_layout.addWidget(editor_btn)
        
        layout.addLayout(button_layout)
        
        # Output area
        output_label = QLabel("Phase Schedule Details:")
        output_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Courier", 10))
        layout.addWidget(self.output_text)
        
        # Show standard phases by default
        self.show_standard_phases()
        
    def show_phase_info(self, manager: PhaseManager, title: str, description: str):
        """Display information about a phase configuration."""
        text = f"=== {title} ===\n\n"
        text += f"{description}\n\n"
        text += f"Total Turns: {manager.get_total_turns()}\n"
        text += f"Number of Phases: {manager.get_phase_count()}\n"
        text += f"Summary: {manager.get_phase_summary()}\n\n"
        text += "Detailed Breakdown:\n"
        
        sorted_phases = sorted(manager.phases.values(), key=lambda p: p.turn_start)
        for phase in sorted_phases:
            behavior = "Both" if phase.forage_enabled and phase.trade_enabled else \
                      "Forage" if phase.forage_enabled else \
                      "Exchange" if phase.trade_enabled else \
                      "Idle"
            text += f"  Phase {phase.number}: Turns {phase.turn_start}-{phase.turn_end} ({phase.duration} turns) - {behavior}\n"
        
        text += f"\nProgrammatic Creation:\n"
        text += self.generate_code_example(manager, title)
        
        self.output_text.setText(text)
        
    def generate_code_example(self, manager: PhaseManager, title: str) -> str:
        """Generate example code for creating this phase configuration."""
        sorted_phases = sorted(manager.phases.values(), key=lambda p: p.turn_start)
        
        code = "# Method 1: Using create_custom_phases()\n"
        code += "manager = PhaseManager.create_custom_phases([\n"
        
        for phase in sorted_phases:
            if phase.forage_enabled and phase.trade_enabled:
                behavior = "PhaseBehavior.both_enabled()"
            elif phase.forage_enabled:
                behavior = "PhaseBehavior.forage_only()" 
            elif phase.trade_enabled:
                behavior = "PhaseBehavior.exchange_only()"
            else:
                behavior = "PhaseBehavior.both_disabled()"
            
            code += f"    ({behavior}, {phase.duration}),\n"
        
        code += "])\n\n"
        
        # Add simple method if applicable
        if len(sorted_phases) <= 4:
            code += "# Method 2: Using create_simple_phases() (if applicable)\n"
            forage_only = next((p.duration for p in sorted_phases 
                              if p.forage_enabled and not p.trade_enabled), 0)
            both_enabled = next((p.duration for p in sorted_phases 
                               if p.forage_enabled and p.trade_enabled), 0)
            exchange_only = next((p.duration for p in sorted_phases 
                                if not p.forage_enabled and p.trade_enabled), 0)
            both_disabled = next((p.duration for p in sorted_phases 
                                if not p.forage_enabled and not p.trade_enabled), 0)
            
            if forage_only or both_enabled or exchange_only or both_disabled:
                code += f"manager = PhaseManager.create_simple_phases(\n"
                if forage_only: code += f"    forage_only={forage_only},\n"
                if both_enabled: code += f"    both_enabled={both_enabled},\n"
                if exchange_only: code += f"    exchange_only={exchange_only},\n"
                if both_disabled: code += f"    both_disabled={both_disabled}\n"
                code += ")\n"
        
        return code
        
    def show_standard_phases(self):
        """Show the standard 6-phase configuration."""
        manager = PhaseManager.create_standard_phases()
        self.show_phase_info(
            manager, 
            "Standard 6-Phase Schedule",
            "The traditional educational pattern used by all existing manual tests. "
            "Provides comprehensive coverage of all behavioral combinations."
        )
        
    def show_simple_phases(self):
        """Show a simple 3-phase configuration."""
        manager = PhaseManager.create_simple_phases(
            forage_only=150,
            both_enabled=200, 
            both_disabled=50
        )
        self.show_phase_info(
            manager,
            "Simple 3-Phase Schedule", 
            "A streamlined schedule focusing on the core behavioral transition from "
            "foraging to trading, ending with idle observation."
        )
        
    def show_bilateral_phases(self):
        """Show a bilateral exchange focused configuration."""
        manager = PhaseManager.create_custom_phases([
            (PhaseBehavior.forage_only(), 100),      # Build up resources
            (PhaseBehavior.exchange_only(), 250),    # Focus on trading
            (PhaseBehavior.both_enabled(), 150),     # Combined behavior
            (PhaseBehavior.both_disabled(), 25)      # Quick idle check
        ])
        self.show_phase_info(
            manager,
            "Bilateral Exchange Focused",
            "Designed for studying trading dynamics with extended exchange-only periods. "
            "Agents first collect resources, then engage in pure trading behavior."
        )
        
    def show_forage_phases(self):
        """Show a foraging focused configuration.""" 
        manager = PhaseManager.create_custom_phases([
            (PhaseBehavior.forage_only(), 300),      # Extended foraging
            (PhaseBehavior.both_enabled(), 100),     # Brief trading intro
            (PhaseBehavior.forage_only(), 100),      # Return to foraging
        ])
        self.show_phase_info(
            manager,
            "Foraging Focused Schedule",
            "Emphasizes resource collection behavior with minimal trading. "
            "Useful for studying spatial movement patterns and resource competition."
        )
        
    def open_phase_editor(self):
        """Open the phase configuration editor."""
        try:
            dialog = PhaseConfigDialog(None, self)
            if dialog.exec():
                phases = dialog.get_phases()
                manager = PhaseManager(phases)
                self.show_phase_info(
                    manager,
                    "Custom Configuration",
                    "User-defined phase schedule created with the phase editor."
                )
        except Exception as e:
            self.output_text.setText(f"Error opening phase editor: {e}")


def main():
    """Run the phase examples application."""
    app = QApplication(sys.argv)
    window = PhaseExamplesWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()