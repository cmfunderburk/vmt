"""Custom Tests Tab - extracted from monolithic launcher.

Widget for discovering and displaying custom generated tests.
Extracted from enhanced_test_launcher_v2.py in Phase 2.3.
"""
from __future__ import annotations

import re
import sys
import subprocess
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, 
        QScrollArea, QWidget
    )
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
except Exception:  # pragma: no cover - allows pure tests without Qt plugin
    QVBoxLayout = QHBoxLayout = QGridLayout = QLabel = QPushButton = object  # type: ignore
    QScrollArea = QWidget = object  # type: ignore
    Qt = QFont = object  # type: ignore

from .base_tab import AbstractTab
from ..cards import CustomTestCardWidget


class CustomTestsTab(AbstractTab):  # pragma: no cover - GUI component extracted from monolith
    """Tab widget for discovering and displaying custom generated tests.
    
    Extracted from enhanced_test_launcher_v2.py in Phase 2.3.
    Handles custom test file discovery, parsing, and display in a grid layout.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tab_title = "Custom Generated Tests"
        self._tab_id = "custom_tests"
        self.setup_ui()
        self.populate_custom_tests()
    
    def get_custom_tests_dir(self) -> Path:
        """Get custom tests directory (always in project)."""
        # Always use project-local custom tests directory  
        # This keeps user-created tests with the project for easy access and version control choice
        project_root = Path(__file__).parent.parent.parent.parent.parent
        return project_root / "MANUAL_TESTS" / "custom_tests"
        
    def setup_ui(self):
        """Create the custom tests UI."""
        layout = QVBoxLayout(self)  # type: ignore[call-arg]
        
        # Set dark mode background for the main widget
        try:
            self.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")  # type: ignore[attr-defined]
        except Exception:
            pass
        
        # Header
        header_layout = QHBoxLayout()  # type: ignore[call-arg]
        
        title = QLabel("Custom Generated Tests")  # type: ignore[call-arg]
        try:
            title.setFont(QFont("Arial", 16, QFont.Weight.Bold))  # type: ignore[attr-defined]
            title.setStyleSheet("color: #ffffff;")  # type: ignore[attr-defined]
        except Exception:
            pass
        header_layout.addWidget(title)  # type: ignore[arg-type]
        
        try:
            header_layout.addStretch()  # type: ignore[attr-defined]
        except Exception:
            pass
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")  # type: ignore[call-arg]
        try:
            refresh_btn.clicked.connect(self.populate_custom_tests)  # type: ignore[attr-defined]
        except Exception:
            pass
        header_layout.addWidget(refresh_btn)  # type: ignore[arg-type]
        
        # Open folder button
        open_folder_btn = QPushButton("📁 Open Folder")  # type: ignore[call-arg]
        try:
            open_folder_btn.clicked.connect(self.open_custom_tests_folder)  # type: ignore[attr-defined]
        except Exception:
            pass
        header_layout.addWidget(open_folder_btn)  # type: ignore[arg-type]
        
        layout.addLayout(header_layout)  # type: ignore[arg-type]
        
        # Info text
        info_text = QLabel(  # type: ignore[call-arg]
            "Custom tests are created using the Configuration Editor. " +
            "Use the 'Open Folder' button to see the custom tests directory."
        )
        try:
            info_text.setStyleSheet("color: #cccccc; margin: 5px 0;")  # type: ignore[attr-defined]
            info_text.setWordWrap(True)  # type: ignore[attr-defined]
        except Exception:
            pass
        layout.addWidget(info_text)  # type: ignore[arg-type]
        
        # Scroll area for custom tests
        self.scroll_area = QScrollArea()  # type: ignore[call-arg]
        try:
            self.scroll_area.setWidgetResizable(True)  # type: ignore[attr-defined]
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # type: ignore[attr-defined]
            self.scroll_area.setStyleSheet("background-color: #2b2b2b;")  # type: ignore[attr-defined]
        except Exception:
            pass
        
        self.scroll_widget = QWidget()  # type: ignore[call-arg]
        self.grid_layout = QGridLayout(self.scroll_widget)  # type: ignore[call-arg]
        try:
            self.scroll_area.setWidget(self.scroll_widget)  # type: ignore[attr-defined]
            self.scroll_widget.setStyleSheet("background-color: #2b2b2b;")  # type: ignore[attr-defined]
        except Exception:
            pass
        
        layout.addWidget(self.scroll_area)  # type: ignore[arg-type]
        
        # Status label
        self.status_label = QLabel("Loading custom tests...")  # type: ignore[call-arg]
        try:
            self.status_label.setStyleSheet("color: #cccccc; font-style: italic;")  # type: ignore[attr-defined]
        except Exception:
            pass
        layout.addWidget(self.status_label)  # type: ignore[arg-type]
        
    def populate_custom_tests(self):
        """Discover and display custom test files."""
        # Clear existing widgets
        try:
            for i in reversed(range(self.grid_layout.count())):  # type: ignore[attr-defined]
                child = self.grid_layout.itemAt(i).widget()  # type: ignore[attr-defined]
                if child:
                    child.setParent(None)  # type: ignore[attr-defined]
        except Exception:
            pass
        
        # Find custom test files
        custom_tests_dir = self.get_custom_tests_dir()
        
        if not custom_tests_dir.exists():
            try:
                self.status_label.setText("No custom tests directory found. Create custom tests using the Configuration Editor.")  # type: ignore[attr-defined]
            except Exception:
                pass
            return
            
        test_files = list(custom_tests_dir.glob("*.py"))
        
        if not test_files:
            try:
                self.status_label.setText("No custom tests found. Create custom tests using the Configuration Editor.")  # type: ignore[attr-defined]
            except Exception:
                pass
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
                    self.grid_layout.addWidget(card, row, col)  # type: ignore[attr-defined]
                    
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
                        
            except Exception as e:
                print(f"Error parsing {test_file.name}: {e}")
                
        try:
            self.status_label.setText(f"Found {len(test_files)} custom test{'s' if len(test_files) != 1 else ''}")  # type: ignore[attr-defined]
        except Exception:
            pass
        
    def parse_test_file(self, test_file: Path) -> dict | None:
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
        custom_tests_dir = self.get_custom_tests_dir()
        
        if not custom_tests_dir.exists():
            custom_tests_dir.mkdir(parents=True, exist_ok=True)
            
        if sys.platform == "win32":
            subprocess.run(["explorer", str(custom_tests_dir)])
        elif sys.platform == "darwin":
            subprocess.run(["open", str(custom_tests_dir)])
        else:
            subprocess.run(["xdg-open", str(custom_tests_dir)])
    
    def refresh_content(self) -> None:
        """Refresh the tab content. Called when tab becomes active or data changes."""
        self.populate_custom_tests()
    
    def cleanup(self) -> None:
        """Clean up resources when tab is being destroyed."""
        # Clear grid layout
        try:
            for i in reversed(range(self.grid_layout.count())):  # type: ignore[attr-defined]
                child = self.grid_layout.itemAt(i).widget()  # type: ignore[attr-defined]
                if child:
                    child.setParent(None)  # type: ignore[attr-defined]
        except Exception:
            pass