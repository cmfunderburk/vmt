#!/usr/bin/env python3
"""
Unified Manual Test Start Menu

Central GUI launcher for all manual tests of the unified target selection behavior.
Provides an overview of available tests and easy access to launch them.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                            QScrollArea, QFrame, QGridLayout, QGroupBox)
from PyQt6.QtCore import Qt, QProcess
from PyQt6.QtGui import QFont, QPalette, QColor
from test_utils import format_duration, get_estimated_duration

class TestCard(QFrame):
    """Individual test card widget."""
    
    def __init__(self, test_info, parent=None):
        super().__init__(parent)
        self.test_info = test_info
        self.process = None
        
        # Style the card
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setStyleSheet("""
            TestCard {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin: 4px;
            }
            TestCard:hover {
                border-color: #0d6efd;
                background-color: #e7f1ff;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Test title
        title = QLabel(f"Test {test_info['id']}: {test_info['name']}")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 4px;")
        layout.addWidget(title)
        
        # Test description
        desc = QLabel(test_info['description'])
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #5a6c7d; font-size: 10px;")
        layout.addWidget(desc)
        
        # Configuration info
        config_layout = QGridLayout()
        config_layout.setSpacing(2)
        
        config_items = [
            ("Grid:", test_info['grid']),
            ("Agents:", test_info['agents']),
            ("Density:", test_info['density']),
            ("Radius:", test_info['radius']),
            ("Preferences:", test_info['preferences'])
        ]
        
        for i, (label, value) in enumerate(config_items):
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 9px; color: #6c757d; font-weight: bold;")
            val = QLabel(str(value))
            val.setStyleSheet("font-size: 9px; color: #495057;")
            
            row = i // 2
            col = (i % 2) * 2
            config_layout.addWidget(lbl, row, col)
            config_layout.addWidget(val, row, col + 1)
        
        config_widget = QWidget()
        config_widget.setLayout(config_layout)
        layout.addWidget(config_widget)
        
        # Timing info
        duration_1 = format_duration(get_estimated_duration(0))  # 1 turn/second
        duration_unlimited = format_duration(get_estimated_duration(4))  # unlimited
        timing = QLabel(f"Duration: {duration_1} (1 turn/sec) / {duration_unlimited} (unlimited)")
        timing.setStyleSheet("font-size: 9px; color: #6c757d; font-style: italic;")
        layout.addWidget(timing)
        
        # Launch button
        self.launch_button = QPushButton("Launch Test")
        self.launch_button.clicked.connect(self.launch_test)
        self.launch_button.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
            QPushButton:pressed {
                background-color: #0a58ca;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        layout.addWidget(self.launch_button)
        
        self.setLayout(layout)
        self.setFixedSize(280, 200)
    
    def launch_test(self):
        """Launch the test in a separate process."""
        try:
            script_path = Path(__file__).parent / self.test_info['script']
            
            # Disable button while process is running
            self.launch_button.setText("Running...")
            self.launch_button.setEnabled(False)
            
            # Start the test process
            self.process = QProcess()
            self.process.finished.connect(self.on_process_finished)
            
            # Use the virtual environment python
            venv_path = Path(__file__).parent.parent / "vmt-dev" / "bin" / "python"
            if venv_path.exists():
                self.process.start(str(venv_path), [str(script_path)])
            else:
                # Fallback to system python
                self.process.start("python", [str(script_path)])
            
            print(f"🚀 Launching {self.test_info['name']}...")
            
        except Exception as e:
            print(f"❌ Error launching test: {e}")
            self.on_process_finished()
    
    def on_process_finished(self):
        """Handle process completion."""
        self.launch_button.setText("Launch Test")
        self.launch_button.setEnabled(True)
        if self.process:
            print(f"✅ {self.test_info['name']} completed")


class ManualTestStartMenu(QMainWindow):
    """Main start menu for manual tests."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manual Test Start Menu - Unified Target Selection")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set up main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        
        # Header
        self.create_header(layout)
        
        # Test grid
        self.create_test_grid(layout)
        
        # Footer info
        self.create_footer(layout)
        
        main_widget.setLayout(layout)
        
        # Apply global stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QLabel {
                color: #2c3e50;
            }
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        
        print("Manual Test Start Menu initialized")
        print("Available tests: 1 (Baseline), 2 (Sparse Long-Range)")
        print("Tests 3-7 will be available once implemented")
    
    def create_header(self, layout):
        """Create the header section."""
        header_widget = QWidget()
        header_layout = QVBoxLayout()
        
        # Title
        title = QLabel("Manual Tests for Unified Target Selection")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 16px;")
        header_layout.addWidget(title)
        
        # Description
        desc_text = """
These tests validate the unified target selection behavior across different scenarios and phases.
Each test runs through 6 phases with different combinations of foraging and exchange enabled/disabled.
Select a test below to launch it with a visual pygame interface and configurable speed control.
        """.strip()
        
        description = QLabel(desc_text)
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setStyleSheet("color: #5a6c7d; margin-bottom: 16px; font-size: 12px;")
        header_layout.addWidget(description)
        
        # Phase schedule info
        phase_info = QLabel("Phase Schedule: Both enabled (1-200) → Forage only (201-400) → Exchange only (401-600) → Both disabled (601-650) → Both enabled (651-850) → Final disabled (851-900)")
        phase_info.setWordWrap(True)
        phase_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        phase_info.setStyleSheet("color: #6c757d; margin-bottom: 20px; font-size: 10px; font-style: italic;")
        header_layout.addWidget(phase_info)
        
        header_widget.setLayout(header_layout)
        layout.addWidget(header_widget)
    
    def create_test_grid(self, layout):
        """Create the grid of test cards."""
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QGridLayout()
        scroll_layout.setSpacing(16)
        
        # Test configurations
        tests = [
            {
                'id': 1,
                'name': 'Baseline',
                'description': 'Baseline behavior test with mixed preferences and standard configuration. Good starting point for observing normal unified target selection behavior.',
                'grid': '30×30',
                'agents': '20',
                'density': '0.25',
                'radius': '8',
                'preferences': 'Mixed (Cobb-Douglas, Leontief, Perfect Substitutes)',
                'script': 'test_1_baseline_simple.py',
                'available': True
            },
            {
                'id': 2,
                'name': 'Sparse Long-Range',
                'description': 'Tests distance-based decision making with sparse resources and long perception radius. Validates behavior when agents must travel far to find targets.',
                'grid': '50×50',
                'agents': '10',
                'density': '0.1',
                'radius': '15',
                'preferences': 'Mixed',
                'script': 'test_2_sparse_new.py',
                'available': True
            },
            {
                'id': 3,
                'name': 'High Density Local',
                'description': 'Tests crowding behavior with many agents in small space with short perception. Validates local competition and resource contention.',
                'grid': '15×15',
                'agents': '30',
                'density': '0.8',
                'radius': '3',
                'preferences': 'Mixed',
                'script': 'test_3_highdensity_local.py',
                'available': True
            },
            {
                'id': 4,
                'name': 'Large World Global',
                'description': 'Tests long-distance decisions in sparse large world with global perception. Validates behavior across vast spaces.',
                'grid': '60×60',
                'agents': '15',
                'density': '0.05',
                'radius': '25',
                'preferences': 'Mixed',
                'script': 'test_4_largeworld_global.py',
                'available': True
            },
            {
                'id': 5,
                'name': 'Pure Cobb-Douglas',
                'description': 'Single preference type validation with Cobb-Douglas preferences of varying alpha values. Tests balanced utility optimization.',
                'grid': '25×25',
                'agents': '25',
                'density': '0.4',
                'radius': '6',
                'preferences': 'Cobb-Douglas only (mixed α)',
                'script': 'test_5_pure_cobbdouglas.py',
                'available': True
            },
            {
                'id': 6,
                'name': 'Pure Leontief',
                'description': 'Single preference type validation with Leontief (perfect complements) preferences. Tests complementary resource requirements.',
                'grid': '25×25',
                'agents': '25',
                'density': '0.4',
                'radius': '6',
                'preferences': 'Leontief only (mixed coefficients)',
                'script': 'test_6_pure_leontief.py',
                'available': True
            },
            {
                'id': 7,
                'name': 'Pure Perfect Substitutes',
                'description': 'Single preference type validation with Perfect Substitutes preferences. Tests resource interchangeability behavior.',
                'grid': '25×25',
                'agents': '25',
                'density': '0.4',
                'radius': '6',
                'preferences': 'Perfect Substitutes only (mixed coefficients)',
                'script': 'test_7_pure_perfectsubstitutes.py',
                'available': True
            }
        ]
        
        # Create test cards in a 3-column grid
        for i, test_info in enumerate(tests):
            card = TestCard(test_info)
            
            # Disable unavailable tests
            if not test_info['available']:
                card.launch_button.setText("Coming Soon")
                card.launch_button.setEnabled(False)
                card.setStyleSheet(card.styleSheet() + """
                    TestCard {
                        opacity: 0.6;
                    }
                """)
            
            row = i // 3
            col = i % 3
            scroll_layout.addWidget(card, row, col)
        
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
    
    def create_footer(self, layout):
        """Create the footer section."""
        footer_widget = QWidget()
        footer_layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("Instructions: Click 'Launch Test' to start any available test. Each test opens in a separate window with pygame visualization and speed controls.")
        instructions.setWordWrap(True)
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setStyleSheet("color: #6c757d; font-size: 11px; margin-top: 16px;")
        footer_layout.addWidget(instructions)
        
        # Additional info
        info = QLabel("💡 Tip: Use 1 turn/second for detailed observation, or Unlimited speed for quick validation. Watch for phase transitions at turns 201, 401, 601, 651, 851.")
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #6c757d; font-size: 10px; font-style: italic; margin-bottom: 16px;")
        footer_layout.addWidget(info)
        
        footer_widget.setLayout(footer_layout)
        layout.addWidget(footer_widget)


def main():
    """Run the manual test start menu."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Manual Test Start Menu")
    app.setApplicationVersion("1.0")
    
    # Create and show the start menu
    start_menu = ManualTestStartMenu()
    start_menu.show()
    
    print("=" * 60)
    print("MANUAL TEST START MENU")
    print("=" * 60)
    print("Select any available test to launch it in a separate window.")
    print("Available tests: Baseline, Sparse Long-Range")
    print("Coming soon: High Density Local, Large World Global, Pure preference tests")
    print("=" * 60)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()