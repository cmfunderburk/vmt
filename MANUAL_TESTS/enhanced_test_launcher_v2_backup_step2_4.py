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
import os
import subprocess
from pathlib import Path
from typing import Dict, List

# Transitional launcher module imports (Phase 2.2 integration)
try:  # Soft dependency during refactor; if missing we fall back to legacy logic
    from econsim.tools.launcher.adapters import load_registry_from_monolith
    from econsim.tools.launcher.comparison import ComparisonController
    from econsim.tools.launcher.executor import TestExecutor
    from econsim.tools.launcher.cards import CustomTestCardWidget, TestCardWidget
    from econsim.tools.launcher.tabs import CustomTestsTab
    _launcher_modules_available = True
except Exception:  # pragma: no cover - fallback path
    _launcher_modules_available = False

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

# Import framework components - try new location first, fallback to legacy
try:
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


# CustomTestsWidget extracted to src/econsim/tools/launcher/tabs/custom_tests_tab.py in Phase 2.3

# Fallback implementations for when extracted modules aren't available
if not _launcher_modules_available:
    class CustomTestsTab(QWidget):  # pragma: no cover - fallback during refactor
        """Fallback implementation when extracted module not available."""
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("CustomTestsTab not available - using fallback"))

# CustomTestCardWidget extracted to src/econsim/tools/launcher/cards.py in Phase 2.1
# TestCardWidget extracted to src/econsim/tools/launcher/cards.py in Phase 2.2


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
            
            # Custom tests tab
            custom_tests_widget = CustomTestsTab()
            main_tabs.addTab(custom_tests_widget, "🔧 Custom Tests")
            
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
        
        # Initialize / clear comparison selection (delegated when new modules present)
        if _launcher_modules_available:
            # Lazy initialize on first population to avoid import cost earlier
            if not hasattr(self, "_comparison_controller"):
                self._comparison_controller = ComparisonController(max_selections=4)
            else:
                self._comparison_controller.clear()
            self.comparison_selection = self._comparison_controller.selected()  # backward compatibility view
        else:
            self.comparison_selection.clear()
        self._update_comparison_ui()
            
        # Create test cards
        row, col = 0, 0
        max_cols = 3

        for config in ALL_TEST_CONFIGS.values():  # Builtin list still authoritative for card ordering
            card_widget = TestCardWidget(config)
            card_widget.launchRequested.connect(self.launch_test)
            card_widget.compareRequested.connect(self.add_to_comparison)
            self.cards_layout.addWidget(card_widget, row, col)
            self.test_cards[config.name] = card_widget

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
            
        if _launcher_modules_available:
            # Use executor for command building (still spawn subprocess to maintain behavior)
            if not hasattr(self, "_executor"):
                self._init_executor()
            # Record attempt (executor command currently points to launcher script; we ignore it for actual spawn)
            _ = self._executor.launch_original(test_name)
            self.log_status(f"Launching original {test_name}...")
            subprocess.Popen([sys.executable, str(test_path)], cwd=str(test_path.parent))
        else:
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
            
        if _launcher_modules_available:
            if not hasattr(self, "_executor"):
                self._init_executor()
            # Record attempt; ignore executor's command path (still launcher) and run actual test file
            _ = self._executor.launch_framework(test_name)
            self.log_status(f"Launching framework {test_name}...")
            subprocess.Popen([sys.executable, str(test_path)], cwd=str(test_path.parent))
        else:
            self.log_status(f"Launching framework {test_name}...")
            subprocess.Popen([sys.executable, str(test_path)], cwd=str(test_path.parent))
        
    def add_to_comparison(self, test_name: str):
        """Add/remove test from comparison selection."""
        if not self.comparison_toggle.isChecked():
            # Auto-enable comparison mode
            self.comparison_toggle.setChecked(True)
            
        if _launcher_modules_available:
            if not hasattr(self, "_comparison_controller"):
                self._comparison_controller = ComparisonController(max_selections=4)
            # Toggle semantic: if already present remove
            if self._comparison_controller.contains(test_name):
                self._comparison_controller.remove(test_name)
                self.test_cards[test_name].set_comparison_selected(False)
                self.log_status(f"Removed {test_name} from comparison")
            else:
                add_res = self._comparison_controller.add(test_name)
                if not add_res.added:
                    if add_res.reason == "capacity":
                        QMessageBox.information(self, "Comparison Limit", "Maximum 4 tests can be compared simultaneously.")
                    # Silently ignore duplicate/invalid as per legacy behavior (duplicate acted as toggle previously)
                    return
                self.test_cards[test_name].set_comparison_selected(True)
                self.log_status(f"Added {test_name} to comparison")
            self.comparison_selection = self._comparison_controller.selected()
        else:
            if test_name in self.comparison_selection:
                self.comparison_selection.remove(test_name)
                self.test_cards[test_name].set_comparison_selected(False)
                self.log_status(f"Removed {test_name} from comparison")
            else:
                if len(self.comparison_selection) >= 4:
                    QMessageBox.information(self, "Comparison Limit", "Maximum 4 tests can be compared simultaneously.")
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
        if _launcher_modules_available and hasattr(self, "_comparison_controller"):
            for test_name in self._comparison_controller.selected():
                self.test_cards[test_name].set_comparison_selected(False)
            self._comparison_controller.clear()
            self.comparison_selection = []
        else:
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
            
        if _launcher_modules_available:
            if not hasattr(self, "_executor"):
                self._init_executor()
            labels = list(self.comparison_selection)
            result = self._executor.launch_comparison(labels)
            if result.success:
                self.log_status(f"Launching {len(labels)} tests for comparison...")
                # Launch each framework version (preserve legacy multi-window behavior)
                for lab in labels:
                    self._launch_framework_test(lab)
                self.statusBar().showMessage(f"Launched {len(labels)} tests for comparison")
            else:
                QMessageBox.warning(self, "Comparison Error", ", ".join(result.errors))
            return
        else:
            self.log_status(f"Launching {len(self.comparison_selection)} tests for comparison...")
            for test_name in self.comparison_selection:
                self._launch_framework_test(test_name)
            self.statusBar().showMessage(f"Launched {len(self.comparison_selection)} tests for comparison")
        
    def _update_comparison_ui(self):
        """Update comparison mode UI elements."""
        # When controller present keep mirror list in sync
        if _launcher_modules_available and hasattr(self, "_comparison_controller"):
            self.comparison_selection = self._comparison_controller.selected()
        count = len(self.comparison_selection)
        self.clear_comparison_btn.setEnabled(count > 0)
        self.launch_comparison_btn.setEnabled(count >= 2)
        if count > 0:
            self.statusBar().showMessage(f"Selected {count} tests for comparison: {', '.join(self.comparison_selection)}")
        else:
            self.statusBar().showMessage("Ready to launch tests")

    # ------------------------------------------------------------------
    # New helper initializers for transitional integration
    # ------------------------------------------------------------------
    def _init_executor(self):  # pragma: no cover - thin glue
        if not hasattr(self, "_registry"):
            self._registry = load_registry_from_monolith()
        if not hasattr(self, "_executor"):
            # For now we pass the path to this launcher file to keep command shape consistent.
            self._executor = TestExecutor(self._registry, launcher_script=Path(__file__))
            
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
        
    # Configure environment for better cross-platform compatibility
    import os
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("VMT Enhanced Test Launcher")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("VMT Project")
    
    # Apply platform-specific styling fixes (extracted module)
    try:
        from econsim.tools.launcher.style import PlatformStyler  # type: ignore
        PlatformStyler.configure_application(app)
    except Exception as exc:  # pragma: no cover - styling fallback
        print(f"[Launcher Styling Warning] {exc}")
    
    # Create and show main window
    launcher = EnhancedTestLauncher()
    launcher.show()
    
    # Start application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()