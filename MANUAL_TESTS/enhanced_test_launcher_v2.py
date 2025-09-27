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

# Transitional launcher module imports (Phase 2.4 integration)
try:  # Soft dependency during refactor; if missing we fall back to legacy logic
    from econsim.tools.launcher.adapters import load_registry_from_monolith
    from econsim.tools.launcher.comparison import ComparisonController
    from econsim.tools.launcher.executor import TestExecutor
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

# Import framework components
try:
    from framework.test_configs import TestConfiguration, ALL_TEST_CONFIGS
except ImportError as e:
    print(f"❌ Framework import failed: {e}")
    print("Please ensure you're running from the MANUAL_TESTS directory.")
    sys.exit(1)


class CustomTestsWidget(QWidget):
    """Widget for discovering and displaying custom generated tests."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.populate_custom_tests()
        
    def setup_ui(self):
        """Create the custom tests UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Custom Generated Tests")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.populate_custom_tests)
        header_layout.addWidget(refresh_btn)
        
        # Open folder button
        open_folder_btn = QPushButton("📁 Open Folder")
        open_folder_btn.clicked.connect(self.open_custom_tests_folder)
        header_layout.addWidget(open_folder_btn)
        
        layout.addLayout(header_layout)
        
        # Info text
        info_text = QLabel(
            "Custom tests are created using the Configuration Editor. "
            "They are saved in the MANUAL_TESTS/custom_tests/ directory."
        )
        info_text.setStyleSheet("color: #666; margin: 5px 0;")
        info_text.setWordWrap(True)
        layout.addWidget(info_text)
        
        # Scroll area for custom tests
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.scroll_widget = QWidget()
        self.grid_layout = QGridLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        
        layout.addWidget(self.scroll_area)
        
        # Status label
        self.status_label = QLabel("Loading custom tests...")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
        
    def populate_custom_tests(self):
        """Discover and display custom test files."""
        # Clear existing widgets
        for i in reversed(range(self.grid_layout.count())):
            child = self.grid_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Find custom test files
        custom_tests_dir = Path(__file__).parent / "custom_tests"
        
        if not custom_tests_dir.exists():
            self.status_label.setText("No custom tests directory found. Create custom tests using the Configuration Editor.")
            return
            
        test_files = list(custom_tests_dir.glob("*.py"))
        
        if not test_files:
            self.status_label.setText("No custom tests found. Create custom tests using the Configuration Editor.")
            return
            
        # Create cards for each custom test
        row = 0
        col = 0
        max_cols = 3
        
        for test_file in sorted(test_files):
            try:
                # Parse test metadata from file
                test_info = self.parse_test_file(test_file)
                
                if test_info:
                    # Create card widget with parent reference
                    card = CustomTestCardWidget(test_file, test_info, self)
                    self.grid_layout.addWidget(card, row, col)
                    
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
                        
            except Exception as e:
                print(f"Error parsing {test_file.name}: {e}")
                
        self.status_label.setText(f"Found {len(test_files)} custom test{'s' if len(test_files) != 1 else ''}")
        
    def parse_test_file(self, test_file: Path) -> dict:
        """Parse test file to extract metadata."""
        try:
            with open(test_file, 'r') as f:
                content = f.read()
                
            # Extract metadata from the file header and configuration
            info = {
                'name': 'Unknown Test',
                'description': 'Custom generated test',
                'created': 'Unknown',
                'config': {}
            }
            
            # Parse docstring for metadata
            import re
            
            # Extract test name from docstring
            name_match = re.search(r'Custom Generated Test: (.+)', content)
            if name_match:
                info['name'] = name_match.group(1).strip()
                
            # Extract creation date
            date_match = re.search(r'Created: (.+)', content)
            if date_match:
                info['created'] = date_match.group(1).strip()
                
            # Extract configuration parameters
            config_match = re.search(r'CUSTOM_CONFIG = TestConfiguration\((.*?)\)', content, re.DOTALL)
            if config_match:
                config_text = config_match.group(1)
                
                # Parse key parameters
                grid_match = re.search(r'grid_size=\((\d+), (\d+)\)', config_text)
                if grid_match:
                    info['config']['grid_size'] = f"{grid_match.group(1)}×{grid_match.group(2)}"
                    
                agent_match = re.search(r'agent_count=(\d+)', config_text)
                if agent_match:
                    info['config']['agent_count'] = agent_match.group(1)
                    
                density_match = re.search(r'resource_density=([0-9.]+)', config_text)
                if density_match:
                    info['config']['resource_density'] = f"{float(density_match.group(1)):.2f}"
                    
                pref_match = re.search(r'preference_mix="([^"]+)"', config_text)
                if pref_match:
                    info['config']['preference_mix'] = pref_match.group(1)
                    
            return info
            
        except Exception as e:
            print(f"Error parsing {test_file}: {e}")
            return None
            
    def open_custom_tests_folder(self):
        """Open the custom tests directory in file explorer."""
        custom_tests_dir = Path(__file__).parent / "custom_tests"
        
        if not custom_tests_dir.exists():
            custom_tests_dir.mkdir(exist_ok=True)
            
        import subprocess
        import sys
        
        if sys.platform == "win32":
            subprocess.run(["explorer", str(custom_tests_dir)])
        elif sys.platform == "darwin":
            subprocess.run(["open", str(custom_tests_dir)])
        else:
            subprocess.run(["xdg-open", str(custom_tests_dir)])


class TestCardWidget(QFrame):
    """Visual card representation of a test configuration."""


class CustomTestCardWidget(QFrame):
    """Card widget for displaying custom test information."""
    
    def __init__(self, test_file: Path, test_info: dict, parent_widget=None):
        super().__init__()
        self.test_file = test_file
        self.test_info = test_info
        self.parent_widget = parent_widget
        self.setup_ui()
        
    def setup_ui(self):
        """Create the card UI."""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
                margin: 5px;
                padding: 10px;
            }
            QFrame:hover {
                border-color: #007acc;
                background-color: #f0f8ff;
            }
        """)
        self.setMinimumHeight(200)
        self.setMaximumWidth(300)
        
        layout = QVBoxLayout(self)
        
        # Test name
        name_label = QLabel(self.test_info['name'])
        name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Creation date
        if self.test_info['created'] != 'Unknown':
            created_label = QLabel(f"Created: {self.test_info['created']}")
            created_label.setStyleSheet("color: #666; font-size: 10px;")
            layout.addWidget(created_label)
            
        # Configuration details
        config = self.test_info['config']
        if config:
            config_text = []
            if 'grid_size' in config:
                config_text.append(f"Grid: {config['grid_size']}")
            if 'agent_count' in config:
                config_text.append(f"Agents: {config['agent_count']}")
            if 'resource_density' in config:
                config_text.append(f"Density: {config['resource_density']}")
            if 'preference_mix' in config:
                config_text.append(f"Prefs: {config['preference_mix']}")
                
            if config_text:
                config_label = QLabel(" | ".join(config_text))
                config_label.setStyleSheet("color: #444; font-size: 11px; margin: 5px 0;")
                config_label.setWordWrap(True)
                layout.addWidget(config_label)
        
        # File name
        file_label = QLabel(f"File: {self.test_file.name}")
        file_label.setStyleSheet("color: #666; font-size: 10px; font-family: monospace;")
        layout.addWidget(file_label)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Launch button
        launch_btn = QPushButton("🚀 Launch")
        launch_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        launch_btn.clicked.connect(self.launch_test)
        button_layout.addWidget(launch_btn)
        
        # Edit button
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        edit_btn.clicked.connect(self.edit_test)
        button_layout.addWidget(edit_btn)
        
        # Delete button
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        delete_btn.clicked.connect(self.delete_test)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        
    def launch_test(self):
        """Launch the custom test."""
        try:
            subprocess.Popen([sys.executable, str(self.test_file)], cwd=str(self.test_file.parent))
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", f"Failed to launch test: {e}")
            
    def edit_test(self):
        """Open test file in default editor."""
        try:
            import subprocess
            import sys
            
            if sys.platform == "win32":
                subprocess.run(["notepad", str(self.test_file)])
            elif sys.platform == "darwin":
                subprocess.run(["open", "-t", str(self.test_file)])
            else:
                # Try common Linux editors
                for editor in ["code", "gedit", "nano", "vim"]:
                    try:
                        subprocess.run([editor, str(self.test_file)])
                        break
                    except FileNotFoundError:
                        continue
                else:
                    subprocess.run(["xdg-open", str(self.test_file)])
                    
        except Exception as e:
            QMessageBox.warning(self, "Edit Error", f"Could not open editor: {e}")
            
    def delete_test(self):
        """Delete the custom test file after confirmation."""
        reply = QMessageBox.question(
            self, "Delete Custom Test",
            f"Are you sure you want to delete '{self.test_info['name']}'?\n\n"
            f"File: {self.test_file.name}\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Delete the file
                self.test_file.unlink()
                
                # Show success message
                QMessageBox.information(
                    self, "Test Deleted",
                    f"Custom test '{self.test_info['name']}' has been deleted successfully."
                )
                
                # Signal parent to refresh the list
                if self.parent_widget and hasattr(self.parent_widget, 'populate_custom_tests'):
                    self.parent_widget.populate_custom_tests()
                    
            except Exception as e:
                QMessageBox.critical(
                    self, "Delete Error",
                    f"Failed to delete custom test:\n\n{str(e)}"
                )


class TestCardWidget(QFrame):
    """Visual card representation of a test configuration."""
    
    launchRequested = pyqtSignal(str, str)  # test_name, test_type
    compareRequested = pyqtSignal(str)      # test_name
    
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
            
            # Custom tests tab
            custom_tests_widget = CustomTestsWidget()
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