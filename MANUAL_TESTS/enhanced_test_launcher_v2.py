#!/usr/bin/env python3
"""
Enhanced Test Launcher for VMT Framework
========================================

Simple enhanced test launcher with visual test cards showing both original 
and framework implementations with quick launch capabilities.

Features:
- Visual test cards with configuration details
- Side-by-side original vs framework launch options  
- Test comparison selection

Usage:
    python enhanced_test_launcher.py
"""

import sys
import subprocess
from pathlib import Path
from typing import Dict, List

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QGridLayout, QScrollArea, QLabel, QPushButton, 
        QFrame, QMessageBox, QCheckBox, QTextEdit, QTabWidget
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
except ImportError as e:
    print(f"❌ PyQt6 import failed: {e}")
    print("Please ensure PyQt6 is installed in your virtual environment.")
    sys.exit(1)

# Import framework components
try:
    from framework.test_configs import TestConfiguration, ALL_TEST_CONFIGS
except ImportError as e:
    print(f"❌ Framework import failed: {e}")
    print("Please ensure you're running from the MANUAL_TESTS directory.")
    sys.exit(1)


class TestCardWidget(QFrame):
    """Visual card representation of a test configuration."""
    
    launchRequested = pyqtSignal(str, str)  # test_name, version ("original" or "framework")
    compareRequested = pyqtSignal(str)  # test_name
    
    def __init__(self, config: TestConfiguration, parent=None):
        super().__init__(parent)
        self.config = config
        self.selected_for_comparison = False
        self.setup_ui()
        
    def setup_ui(self):
        """Create the test card UI."""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin: 4px;
            }
            QFrame:hover {
                border-color: #4CAF50;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Header with test name
        name_label = QLabel(self.config.name)
        name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        
        # Description
        desc_label = QLabel(self.config.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(desc_label)
        
        # Configuration summary
        config_text = f"""
        <b>Configuration:</b><br>
        • Grid: {self.config.grid_size[0]}×{self.config.grid_size[1]}<br>
        • Agents: {self.config.agent_count}<br>
        • Density: {self.config.resource_density:.2f}<br>
        • Perception: {self.config.perception_radius}<br>
        • Type: {self.config.preference_mix.replace('_', ' ').title()}
        """
        config_label = QLabel(config_text)
        config_label.setStyleSheet("font-size: 9px; color: #555;")
        layout.addWidget(config_label)
        
        # Runtime estimate
        runtime = self._estimate_runtime()
        runtime_label = QLabel(f"⏱️ Runtime: {runtime}")
        runtime_label.setStyleSheet("font-size: 9px; color: #888; font-style: italic;")
        layout.addWidget(runtime_label)
        
        # Action buttons
        button_layout = QVBoxLayout()
        
        # Launch buttons
        if self._check_original_available():
            original_btn = QPushButton("🚀 Launch Original")
            original_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 6px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            original_btn.clicked.connect(lambda: self.launchRequested.emit(self.config.name, "original"))
            button_layout.addWidget(original_btn)
            
        framework_btn = QPushButton("⚡ Launch Framework")
        framework_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        framework_btn.clicked.connect(lambda: self.launchRequested.emit(self.config.name, "framework"))
        button_layout.addWidget(framework_btn)
            
        # Secondary actions
        secondary_layout = QHBoxLayout()
        
        compare_btn = QPushButton("📊 Compare")
        compare_btn.setToolTip("Add to Comparison")
        compare_btn.clicked.connect(lambda: self.compareRequested.emit(self.config.name))
        secondary_layout.addWidget(compare_btn)
        
        button_layout.addLayout(secondary_layout)
        layout.addLayout(button_layout)
        
        # Set size
        self.setMinimumSize(250, 300)
        self.setMaximumSize(300, 350)
        
    def _check_original_available(self) -> bool:
        """Check if original test implementation is available."""
        # Map test config IDs to original file names
        id_to_file = {
            1: "test_1_baseline_simple.py",
            2: "test_2_sparse_longrange.py", 
            3: "test_3_dense_shortrange.py",
            4: "test_4_mixed_preferences.py",
            5: "test_5_pure_cobbdouglas.py",
            6: "test_6_pure_leontief.py",
            7: "test_7_pure_perfectsubstitutes.py"
        }
        
        original_file = id_to_file.get(self.config.id)
        if original_file:
            return (Path(__file__).parent / original_file).exists()
        return False
        
    def _estimate_runtime(self) -> str:
        """Estimate test runtime based on configuration."""
        # Base time: 15 minutes for standard 900 steps
        base_minutes = 15
        
        # Adjust for grid size
        total_cells = self.config.grid_size[0] * self.config.grid_size[1]
        size_factor = total_cells / 900  # 30x30 baseline
        
        # Adjust for agent count
        agent_factor = self.config.agent_count / 20  # 20 agents baseline
        
        # Combined factor
        total_factor = (size_factor + agent_factor) / 2
        estimated_minutes = int(base_minutes * total_factor)
        
        if estimated_minutes < 10:
            return "~5-10 min"
        elif estimated_minutes < 20:
            return "~10-20 min" 
        elif estimated_minutes < 30:
            return "~20-30 min"
        else:
            return "~30+ min"
            
    def set_comparison_selected(self, selected: bool):
        """Visual feedback for comparison selection."""
        self.selected_for_comparison = selected
        if selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #fff3e0;
                    border: 3px solid #ff9800;
                    border-radius: 8px;
                    margin: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 2px solid #ddd;
                    border-radius: 8px;
                    margin: 4px;
                }
                QFrame:hover {
                    border-color: #4CAF50;
                }
            """)


class EnhancedTestLauncher(QMainWindow):
    """Enhanced test launcher with framework awareness."""
    
    def __init__(self):
        super().__init__()
        self.test_cards: Dict[str, TestCardWidget] = {}
        self.comparison_selection: List[str] = []
        self.setup_ui()
        self.populate_tests()
        
    def setup_ui(self):
        """Create the main UI."""
        self.setWindowTitle("VMT Enhanced Test Launcher")
        self.setMinimumSize(1000, 700)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Header
        header = QLabel("🧪 VMT Enhanced Test Launcher")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                padding: 12px;
                border-radius: 6px;
                color: #333;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(header)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Comparison mode toggle
        self.comparison_toggle = QCheckBox("Comparison Mode")
        self.comparison_toggle.toggled.connect(self.toggle_comparison_mode)
        controls_layout.addWidget(self.comparison_toggle)
        
        # Clear comparison
        self.clear_comparison_btn = QPushButton("Clear Selection")
        self.clear_comparison_btn.clicked.connect(self.clear_comparison)
        self.clear_comparison_btn.setEnabled(False)
        controls_layout.addWidget(self.clear_comparison_btn)
        
        # Launch comparison
        self.launch_comparison_btn = QPushButton("🔍 Launch Selected")
        self.launch_comparison_btn.clicked.connect(self.launch_comparison)
        self.launch_comparison_btn.setEnabled(False)
        controls_layout.addWidget(self.launch_comparison_btn)
        
        controls_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.populate_tests)
        controls_layout.addWidget(refresh_btn)
        
        layout.addLayout(controls_layout)
        
        # Test cards scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Grid layout for test cards
        self.cards_widget = QWidget()
        self.cards_layout = QGridLayout(self.cards_widget)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.cards_widget)
        layout.addWidget(scroll)
        
        # Add configuration editor, batch runner, and bookmark manager tabs
        try:
            from live_config_editor import LiveConfigEditor
            from batch_test_runner import BatchTestRunner
            from test_bookmarks import TestBookmarkManager
            
            # Create tab widget for main content
            main_tabs = QTabWidget()
            
            # Gallery tab (existing content)
            gallery_widget = QWidget()
            gallery_layout = QVBoxLayout(gallery_widget)
            
            # Move existing scroll area to gallery tab
            gallery_layout.addWidget(scroll)
            
            # Status area in gallery
            self.status_area = QTextEdit()
            self.status_area.setReadOnly(True)
            self.status_area.setMaximumHeight(100)
            self.status_area.setStyleSheet("background-color: #f8f9fa;")
            gallery_layout.addWidget(self.status_area)
            
            main_tabs.addTab(gallery_widget, "🖼️ Test Gallery")
            
            # Configuration editor tab
            config_editor = LiveConfigEditor()
            main_tabs.addTab(config_editor, "⚙️ Configuration Editor")
            
            # Batch test runner tab
            batch_runner = BatchTestRunner()
            main_tabs.addTab(batch_runner, "🔄 Batch Runner")
            
            # Bookmark manager tab
            bookmark_manager = TestBookmarkManager()
            main_tabs.addTab(bookmark_manager, "⭐ Bookmarks")
            
            layout.addWidget(main_tabs)
            
        except ImportError:
            # Fallback if config editor not available
            layout.addWidget(scroll)
            
            self.status_area = QTextEdit()
            self.status_area.setReadOnly(True)
            self.status_area.setMaximumHeight(100)
            self.status_area.setStyleSheet("background-color: #f8f9fa;")
            layout.addWidget(self.status_area)
        
        # Status bar
        self.statusBar().showMessage("Ready to launch tests")
        
    def populate_tests(self):
        """Populate the test gallery with available tests."""
        # Clear existing cards
        for card in self.test_cards.values():
            card.setParent(None)
        self.test_cards.clear()
        
        # Clear comparison selection
        self.comparison_selection.clear()
        self._update_comparison_ui()
            
        # Create test cards
        row, col = 0, 0
        max_cols = 3
        
        for config in ALL_TEST_CONFIGS.values():
            # Create card widget
            card_widget = TestCardWidget(config)
            card_widget.launchRequested.connect(self.launch_test)
            card_widget.compareRequested.connect(self.add_to_comparison)
            
            # Add to layout
            self.cards_layout.addWidget(card_widget, row, col)
            self.test_cards[config.name] = card_widget
            
            # Update grid position
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
        # Update status
        self.statusBar().showMessage(f"Loaded {len(ALL_TEST_CONFIGS)} tests")
        self.log_status("Enhanced test launcher initialized")
        self.log_status(f"Found {len(ALL_TEST_CONFIGS)} test configurations")
        
    def launch_test(self, test_name: str, version: str):
        """Launch a specific test version."""
        try:
            if version == "original":
                self._launch_original_test(test_name)
            elif version == "framework":
                self._launch_framework_test(test_name)
            else:
                QMessageBox.warning(self, "Error", f"Unknown test version: {version}")
                
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", f"Failed to launch {test_name} ({version}):\n{str(e)}")
            
    def _launch_original_test(self, test_name: str):
        """Launch original test implementation."""
        # Find config by name to get ID
        config_id = None
        for config in ALL_TEST_CONFIGS.values():
            if config.name == test_name:
                config_id = config.id
                break
                
        if config_id is None:
            QMessageBox.warning(self, "Error", f"Configuration not found for: {test_name}")
            return
        
        # Map config IDs to original file names
        id_to_file = {
            1: "test_1_baseline_simple.py",
            2: "test_2_sparse_longrange.py", 
            3: "test_3_dense_shortrange.py",
            4: "test_4_mixed_preferences.py",
            5: "test_5_pure_cobbdouglas.py",
            6: "test_6_pure_leontief.py",
            7: "test_7_pure_perfectsubstitutes.py"
        }
        
        original_file = id_to_file.get(config_id)
        if not original_file:
            QMessageBox.warning(self, "Error", f"Original test not found for: {test_name}")
            return
            
        # Launch in subprocess
        test_path = Path(__file__).parent / original_file
        if not test_path.exists():
            QMessageBox.warning(self, "Error", f"Test file not found: {original_file}")
            return
            
        self.log_status(f"Launching original {test_name}...")
        subprocess.Popen([sys.executable, str(test_path)], cwd=str(test_path.parent))
        
    def _launch_framework_test(self, test_name: str):
        """Launch framework test implementation."""
        # Find config by name to get ID
        config_id = None
        for config in ALL_TEST_CONFIGS.values():
            if config.name == test_name:
                config_id = config.id
                break
                
        if config_id is None:
            QMessageBox.warning(self, "Error", f"Configuration not found for: {test_name}")
            return
        
        # Map config IDs to framework file names
        id_to_file = {
            1: "test_1_framework_version.py",
            2: "test_2_framework_version.py", 
            3: "test_3_framework_version.py",
            4: "test_4_framework_version.py",
            5: "test_5_framework_version.py",
            6: "test_6_framework_version.py",
            7: "test_7_framework_version.py"
        }
        
        framework_file = id_to_file.get(config_id)
        if not framework_file:
            QMessageBox.warning(self, "Error", f"Framework test not found for: {test_name}")
            return
            
        # Launch in subprocess  
        test_path = Path(__file__).parent / framework_file
        if not test_path.exists():
            QMessageBox.warning(self, "Error", f"Test file not found: {framework_file}")
            return
            
        self.log_status(f"Launching framework {test_name}...")
        subprocess.Popen([sys.executable, str(test_path)], cwd=str(test_path.parent))
        
    def add_to_comparison(self, test_name: str):
        """Add/remove test from comparison selection."""
        if not self.comparison_toggle.isChecked():
            # Auto-enable comparison mode
            self.comparison_toggle.setChecked(True)
            
        if test_name in self.comparison_selection:
            self.comparison_selection.remove(test_name)
            self.test_cards[test_name].set_comparison_selected(False)
            self.log_status(f"Removed {test_name} from comparison")
        else:
            if len(self.comparison_selection) >= 4:  # Limit to 4 comparisons
                QMessageBox.information(self, "Comparison Limit", 
                    "Maximum 4 tests can be compared simultaneously.")
                return
                
            self.comparison_selection.append(test_name)
            self.test_cards[test_name].set_comparison_selected(True)
            self.log_status(f"Added {test_name} to comparison")
            
        self._update_comparison_ui()
        
    def toggle_comparison_mode(self, enabled: bool):
        """Toggle comparison mode UI."""
        if not enabled:
            self.clear_comparison()
            self.log_status("Comparison mode disabled")
        else:
            self.log_status("Comparison mode enabled")
            
        self._update_comparison_ui()
        
    def clear_comparison(self):
        """Clear all comparison selections."""
        for test_name in self.comparison_selection.copy():
            self.test_cards[test_name].set_comparison_selected(False)
        self.comparison_selection.clear()
        self.log_status("Cleared all comparison selections")
        self._update_comparison_ui()
        
    def launch_comparison(self):
        """Launch selected tests for comparison."""
        if len(self.comparison_selection) < 2:
            QMessageBox.warning(self, "Comparison Error", 
                "Please select at least 2 tests to compare.")
            return
            
        self.log_status(f"Launching {len(self.comparison_selection)} tests for comparison...")
        
        # Launch each test (framework version by default for comparison)
        for test_name in self.comparison_selection:
            self._launch_framework_test(test_name)
            
        self.statusBar().showMessage(f"Launched {len(self.comparison_selection)} tests for comparison")
        
    def _update_comparison_ui(self):
        """Update comparison mode UI elements."""
        count = len(self.comparison_selection)
        
        self.clear_comparison_btn.setEnabled(count > 0)
        self.launch_comparison_btn.setEnabled(count >= 2)
        
        if count > 0:
            self.statusBar().showMessage(f"Selected {count} tests for comparison: {', '.join(self.comparison_selection)}")
        else:
            self.statusBar().showMessage("Ready to launch tests")
            
    def log_status(self, message: str):
        """Add message to status area."""
        self.status_area.append(f"• {message}")
        
        # Keep status area from growing too large
        if self.status_area.document().lineCount() > 20:
            cursor = self.status_area.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deletePreviousChar()  # Remove the newline


def main():
    """Main entry point for enhanced test launcher."""
    # Ensure we're in a virtual environment for safety
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not running in a virtual environment")
        print("   It's recommended to activate your vmt-dev environment first")
        
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("VMT Enhanced Test Launcher")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("VMT Project")
    
    # Apply modern styling
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f8f9fa;
        }
        QPushButton {
            font-weight: bold;
            padding: 8px 16px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        QPushButton:hover {
            border-color: #007bff;
        }
        QCheckBox {
            font-weight: bold;
            spacing: 8px;
        }
    """)
    
    # Create and show main window
    launcher = EnhancedTestLauncher()
    launcher.show()
    
    # Start application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()