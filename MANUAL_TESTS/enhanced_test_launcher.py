#!/usr/bin/env python3
"""
Enhanced Test Launcher for VMT Framework
========================================

Modern, framework-aware test launcher with visual test cards showing both
original and framework implementations with quick launch capabilities.

Usage:
    python enhanced_test_launcher.py
"""

import sys
import subprocess
from pathlib import Path
from typing import Dict, List

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys    def _update_comparison_ui(self):
        """Update comparison mode UI elements."""
        count = len(self.comparison_selection)
        
        self.clear_comparison_btn.setEnabled(count > 0)
        self.launch_comparison_btn.setEnabled(count >= 2)
        
        status_bar = self.statusBar()
        if status_bar:
            if count > 0:
                status_bar.showMessage(f"Selected {count} tests for comparison: {', '.join(self.comparison_selection)}")
            else:
                status_bar.showMessage("Ready to launch tests")
                
    def log_status(self, message: str):
        """Add message to status area."""
        self.status_area.append(f"• {message}")
        
        # Keep status area from growing too large
        if self.status_area.document().lineCount() > 20:
            cursor = self.status_area.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deletePreviousChar()  # Remove the newlinet(0, str(project_root))

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QGridLayout, QScrollArea, QLabel, QPushButton, 
        QFrame, QMessageBox, QCheckBox, QTextEdit
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
except ImportError as e:
    print(f"❌ PyQt6 import failed: {e}")
    print("Please ensure PyQt6 is installed in your virtual environment.")
    sys.exit(1)

# Import framework components - try new location first, fallback to legacy
try:
    import os
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(repo_root, "src"))
    from econsim.tools.launcher.framework.test_configs import TestConfiguration, ALL_TEST_CONFIGS
except ImportError:
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
        
        # Status area
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
        
        for config in ALL_TEST_CONFIGS:
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
        status_bar = self.statusBar()
        if status_bar:
            status_bar.showMessage(f"Loaded {len(ALL_TEST_CONFIGS)} tests")
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
        # Map test names to original file names
        name_map = {
            "Baseline": "test_1_baseline_simple.py",
            "Sparse Long-Range": "test_2_sparse_longrange.py", 
            "Dense Short-Range": "test_3_dense_shortrange.py",
            "Mixed Preferences": "test_4_mixed_preferences.py",
            "Pure Cobb-Douglas": "test_5_pure_cobbdouglas.py",
            "Pure Leontief": "test_6_pure_leontief.py",
            "Pure Perfect Substitutes": "test_7_pure_perfectsubstitutes.py"
        }
        
        original_file = name_map.get(test_name)
        if not original_file:
            QMessageBox.warning(self, "Error", f"Original test not found for: {test_name}")
            return
            
        # Launch in subprocess
        test_path = Path(__file__).parent / original_file
        if not test_path.exists():
            QMessageBox.warning(self, "Error", f"Test file not found: {original_file}")
            return
            
        self.statusBar().showMessage(f"Launching original {test_name}...")
        subprocess.Popen([sys.executable, str(test_path)], cwd=str(test_path.parent))
        
    def _launch_framework_test(self, test_name: str):
        """Launch framework test implementation."""
        # Map test names to framework file names
        name_map = {
            "Baseline": "test_1_framework_version.py",
            "Sparse Long-Range": "test_2_framework_version.py", 
            "Dense Short-Range": "test_3_framework_version.py",
            "Mixed Preferences": "test_4_framework_version.py",
            "Pure Cobb-Douglas": "test_5_framework_version.py",
            "Pure Leontief": "test_6_framework_version.py",
            "Pure Perfect Substitutes": "test_7_framework_version.py"
        }
        
        framework_file = name_map.get(test_name)
        if not framework_file:
            QMessageBox.warning(self, "Error", f"Framework test not found for: {test_name}")
            return
            
        # Launch in subprocess
        test_path = Path(__file__).parent / framework_file
        if not test_path.exists():
            QMessageBox.warning(self, "Error", f"Test file not found: {framework_file}")
            return
            
        self.statusBar().showMessage(f"Launching framework {test_name}...")
        subprocess.Popen([sys.executable, str(test_path)], cwd=str(test_path.parent))
        
    def add_to_comparison(self, test_name: str):
        """Add/remove test from comparison selection."""
        if not self.comparison_toggle.isChecked():
            # Auto-enable comparison mode
            self.comparison_toggle.setChecked(True)
            
        if test_name in self.comparison_selection:
            self.comparison_selection.remove(test_name)
            self.test_cards[test_name].set_comparison_selected(False)
        else:
            if len(self.comparison_selection) >= 4:  # Limit to 4 comparisons
                QMessageBox.information(self, "Comparison Limit", 
                    "Maximum 4 tests can be compared simultaneously.")
                return
                
            self.comparison_selection.append(test_name)
            self.test_cards[test_name].set_comparison_selected(True)
            
        self._update_comparison_ui()
        
    def configure_test(self, test_name: str):
        """Open configuration editor for specific test."""
        # Switch to configuration tab and select the test
        self.tab_widget.setCurrentIndex(1)  # Config tab
        self.config_test_combo.setCurrentText(test_name)
        
    def toggle_comparison_mode(self, enabled: bool):
        """Toggle comparison mode UI."""
        if not enabled:
            self.clear_comparison()
            
        self._update_comparison_ui()
        
    def clear_comparison(self):
        """Clear all comparison selections."""
        for test_name in self.comparison_selection.copy():
            self.test_cards[test_name].set_comparison_selected(False)
        self.comparison_selection.clear()
        self._update_comparison_ui()
        
    def launch_comparison(self):
        """Launch selected tests for comparison."""
        if len(self.comparison_selection) < 2:
            QMessageBox.warning(self, "Comparison Error", 
                "Please select at least 2 tests to compare.")
            return
            
        # For now, launch each test individually
        # TODO: Implement side-by-side comparison interface
        for test_name in self.comparison_selection:
            self._launch_framework_test(test_name)
            
        self.statusBar().showMessage(f"Launched {len(self.comparison_selection)} tests for comparison")
        
    def _update_comparison_ui(self):
        """Update comparison mode UI elements."""
        count = len(self.comparison_selection)
        
        self.clear_comparison_btn.setEnabled(count > 0)
        self.launch_comparison_btn.setEnabled(count >= 2)
        
        if count > 0:
            self.statusBar().showMessage(f"Selected {count} tests for comparison")
        else:
            self.statusBar().showMessage("Ready to launch tests")
            
    def load_config_for_test(self, test_name: str):
        """Load configuration for selected test."""
        # Find config by name
        config = None
        for c in ALL_TEST_CONFIGS:
            if c.name == test_name:
                config = c
                break
                
        if config:
            self.current_config = config
            self.config_editor.load_config(config)
            self.update_config_preview()
            
    def on_config_changed(self, config: TestConfiguration):
        """Handle configuration changes."""
        self.current_config = config
        self.update_config_preview()
        self.validate_config()
        
    def update_config_preview(self):
        """Update configuration preview text."""
        if self.current_config:
            preview_text = f"""
Test Configuration: {self.current_config.name}

Grid Size: {self.current_config.grid_width} × {self.current_config.grid_height}
Total Cells: {self.current_config.grid_width * self.current_config.grid_height}

Agents: {self.current_config.agent_count}
Perception Radius: {self.current_config.perception_radius}

Resources:
  Density: {self.current_config.resource_density}
  Expected Count: ~{int(self.current_config.grid_width * self.current_config.grid_height * self.current_config.resource_density)}

Preferences: {self.current_config.preference_type.replace('_', ' ').title()}
            """.strip()
            
            self.config_preview.setText(preview_text)
            
    def validate_config(self):
        """Validate current configuration and show results."""
        if not self.current_config:
            return
            
        validation_messages = []
        warnings = []
        
        # Basic validation
        if self.current_config.agent_count <= 0:
            validation_messages.append("❌ Agent count must be positive")
        elif self.current_config.agent_count > 200:
            warnings.append("⚠️ Very high agent count may cause performance issues")
            
        if self.current_config.grid_width < 5 or self.current_config.grid_height < 5:
            validation_messages.append("❌ Grid dimensions must be at least 5×5")
        elif (self.current_config.grid_width * self.current_config.grid_height) > 2000:
            warnings.append("⚠️ Very large grid may cause performance issues")
            
        if self.current_config.resource_density <= 0 or self.current_config.resource_density > 1:
            validation_messages.append("❌ Resource density must be between 0 and 1")
        elif self.current_config.resource_density < 0.01:
            warnings.append("⚠️ Very low resource density may result in minimal activity")
            
        if self.current_config.perception_radius <= 0:
            validation_messages.append("❌ Perception radius must be positive")
        elif self.current_config.perception_radius > 20:
            warnings.append("⚠️ Very high perception radius may cause performance issues")
            
        # Ratio validation
        total_cells = self.current_config.grid_width * self.current_config.grid_height
        if self.current_config.agent_count > total_cells:
            validation_messages.append("❌ More agents than grid cells")
        elif self.current_config.agent_count > (total_cells * 0.5):
            warnings.append("⚠️ High agent density may limit movement")
            
        # Build validation text
        if validation_messages:
            validation_text = "Validation Issues:\n" + "\n".join(validation_messages)
            if warnings:
                validation_text += "\n\nWarnings:\n" + "\n".join(warnings)
        elif warnings:
            validation_text = "Warnings:\n" + "\n".join(warnings)
        else:
            validation_text = "✅ Configuration is valid"
            
        self.validation_text.setText(validation_text)
        
        # Enable/disable launch button
        self.launch_custom_btn.setEnabled(not bool(validation_messages))
        
    def launch_custom_config(self):
        """Launch test with custom configuration."""
        if not self.current_config:
            return
            
        # TODO: Implement custom config launcher
        QMessageBox.information(self, "Custom Launch", 
            f"Custom configuration launch for {self.current_config.name}\n"
            f"This feature will be implemented in the next iteration.")
            
    def save_custom_bookmark(self):
        """Save current configuration as bookmark."""
        if not self.current_config:
            return
            
        # Get bookmark name from user
        name, ok = QInputDialog.getText(self, "Save Bookmark", 
            f"Enter name for this configuration:")
            
        if ok and name:
            bookmark_data = {
                "name": name,
                "config": asdict(self.current_config),
                "created": datetime.now().isoformat(),
                "description": f"Custom configuration based on {self.current_config.name}"
            }
            
            self.settings.bookmarked_configs.append(bookmark_data)
            self.save_settings()
            self.refresh_bookmarks()
            
            QMessageBox.information(self, "Bookmark Saved", f"Configuration saved as '{name}'")
            
    # Implement remaining methods (batch runner, bookmarks, settings)...
    def add_all_to_batch(self):
        """Add all tests to batch queue.""" 
        self.batch_list.clear()
        for config in ALL_TEST_CONFIGS:
            item = QListWidgetItem(f"{config.name} (Framework)")
            item.setData(Qt.ItemDataRole.UserRole, ("framework", config.name))
            self.batch_list.addItem(item)
            
            if self._check_original_available(config.name):
                item = QListWidgetItem(f"{config.name} (Original)")
                item.setData(Qt.ItemDataRole.UserRole, ("original", config.name))
                self.batch_list.addItem(item)
                
    def clear_batch_queue(self):
        """Clear batch queue."""
        self.batch_list.clear()
        
    def run_batch_tests(self):
        """Run all tests in batch queue."""
        # Placeholder implementation
        QMessageBox.information(self, "Batch Runner", 
            "Batch test execution will be implemented in the next iteration.")
            
    def load_selected_bookmark(self):
        """Load selected bookmark configuration."""
        # Placeholder implementation
        pass
        
    def delete_selected_bookmark(self):
        """Delete selected bookmark."""
        # Placeholder implementation  
        pass
        
    def export_bookmarks(self):
        """Export bookmarks to file."""
        # Placeholder implementation
        pass
        
    def import_bookmarks(self):
        """Import bookmarks from file."""
        # Placeholder implementation
        pass
        
    def refresh_bookmarks(self):
        """Refresh bookmarks list."""
        # Placeholder implementation
        pass
        
    def load_settings(self):
        """Load persistent settings."""
        # Placeholder implementation
        pass
        
    def save_settings(self):
        """Save persistent settings."""
        # Placeholder implementation
        pass
        

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
        QTabWidget::pane {
            border: 1px solid #ddd;
            background-color: white;
        }
        QTabBar::tab {
            background-color: #e9ecef;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 1px solid white;
        }
    """)
    
    # Create and show main window
    launcher = EnhancedTestLauncher()
    launcher.show()
    
    # Start application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()