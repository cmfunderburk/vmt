"""Launcher UI – Card models & card widgets.

Phase 2.1: Extract CustomTestCardWidget from monolith.
This module contains both standard test cards and custom test cards with their
respective UI components and business logic.

Part 2 Gate G11 focuses on deterministic model ordering & purity.
"""
from __future__ import annotations

import sys
import subprocess
from dataclasses import dataclass
from typing import Any, List
from pathlib import Path

try:  # Typed import; ignore if Qt not available in headless minimal test
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QMessageBox
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
except Exception:  # pragma: no cover - allows pure tests without Qt plugin
    QWidget = QFrame = object  # type: ignore
    QVBoxLayout = QHBoxLayout = QLabel = QPushButton = QMessageBox = object  # type: ignore
    Qt = QFont = pyqtSignal = object  # type: ignore

from .registry import TestRegistry
from .comparison import ComparisonController
from .executor import TestExecutor
from .types import TestConfiguration


@dataclass(frozen=True, slots=True)
class TestCardModel:
    """Pure representation of a test configuration for UI rendering.

    Ordering Invariant: Instances will be produced by `build_card_models` in a
    deterministic order (default ascending test id). A future enhancement may
    allow alternate sort strategies but G11 fixes the baseline for snapshot tests.
    """

    id: int
    label: str
    mode: str
    file: Path | None
    order: int
    meta: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:  # convenience for JSON export / tests
        return {
            "id": self.id,
            "label": self.label,
            "mode": self.mode,
            "file": str(self.file) if self.file else None,
            "order": self.order,
            "meta": self.meta,
        }


def build_card_models(registry: TestRegistry) -> List[TestCardModel]:
    """Build deterministic list of card models from the registry.

    Current strategy: ascending by test id. This mirrors the implicit ordering of
    the legacy `ALL_TEST_CONFIGS.values()` iteration (dict insertion order based
    on original construction). If a future divergence is detected we can inject
    a custom ordering map; snapshot tests will highlight changes.
    """
    models: List[TestCardModel] = []
    # registry.all() returns dict[int, TestConfiguration]; iteration order is key order
    for order, (tid, cfg) in enumerate(sorted(registry.all().items()), start=1):
        models.append(
            TestCardModel(
                id=tid,
                label=cfg.label,
                mode=cfg.mode,
                file=cfg.file,
                order=order,
                meta=cfg.meta,
            )
        )
    return models


class TestCard(QWidget):  # pragma: no cover - GUI behaviour will be smoke/integration tested
    """Minimal placeholder widget (will be expanded in later sub-phases).

    Responsibilities kept intentionally thin for initial extraction:
    * Display label
    * Provide basic launch buttons (original / framework) – wired externally
    * Provide comparison add toggle
    """

    def __init__(self, model: TestCardModel, comparison: ComparisonController, executor: TestExecutor):  # type: ignore[override]
        super().__init__()  # type: ignore[misc]
        self._model = model
        self._comparison = comparison
        self._executor = executor
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()  # type: ignore[call-arg]
        layout.addWidget(QLabel(self._model.label))  # type: ignore[arg-type]
        btn_launch_test = QPushButton("Launch Test")  # type: ignore[call-arg]
        btn_compare = QPushButton("Add to Comparison")  # type: ignore[call-arg]

        # Wire actions – deferring robust error handling until later phases
        try:
            btn_launch_test.clicked.connect(lambda: self._executor.launch_framework(self._model.label))  # type: ignore[attr-defined]
            btn_compare.clicked.connect(lambda: self._comparison.add(self._model.label))  # type: ignore[attr-defined]
        except Exception:
            pass  # In headless/type-stub environment signals may be absent

        layout.addWidget(btn_launch_test)  # type: ignore[arg-type]
        layout.addWidget(btn_compare)  # type: ignore[arg-type]
        try:
            self.setLayout(layout)  # type: ignore[attr-defined]
        except Exception:
            pass


class CustomTestCardWidget(QFrame):  # pragma: no cover - GUI component extracted from monolith
    """Card widget for displaying custom test information.
    
    Extracted from enhanced_test_launcher_v2.py in Phase 2.1.
    Handles display and interaction with custom generated test files.
    """
    
    def __init__(self, test_file: Path, test_info: dict, parent_widget=None):
        super().__init__()  # type: ignore[misc]
        self.test_file = test_file
        self.test_info = test_info
        self.parent_widget = parent_widget
        self.setup_ui()
        
    def setup_ui(self):
        """Create the card UI."""
        try:
            self.setFrameStyle(QFrame.Shape.Box)  # type: ignore[attr-defined]
            self.setStyleSheet("""
                QFrame {
                    border: 2px solid #555555;
                    border-radius: 8px;
                    background-color: #1e1e1e;
                    margin: 5px;
                    padding: 10px;
                }
                QFrame:hover {
                    border-color: #0078d4;
                    background-color: #2a2a2a;
                }
            """)
            self.setMinimumHeight(200)  # type: ignore[attr-defined]
            self.setMaximumWidth(300)   # type: ignore[attr-defined]
        except Exception:
            pass  # Headless environment compatibility
        
        layout = QVBoxLayout(self)  # type: ignore[call-arg]
        
        # Test name
        name_label = QLabel(self.test_info['name'])  # type: ignore[call-arg]
        try:
            name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))  # type: ignore[attr-defined]
            name_label.setWordWrap(True)  # type: ignore[attr-defined]
            name_label.setStyleSheet("color: #ffffff;")  # type: ignore[attr-defined]
        except Exception:
            pass
        layout.addWidget(name_label)  # type: ignore[arg-type]
        
        # Creation date
        if self.test_info['created'] != 'Unknown':
            created_label = QLabel(f"Created: {self.test_info['created']}")  # type: ignore[call-arg]
            try:
                created_label.setStyleSheet("color: #cccccc; font-size: 10px;")  # type: ignore[attr-defined]
            except Exception:
                pass
            layout.addWidget(created_label)  # type: ignore[arg-type]
            
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
                config_label = QLabel(" | ".join(config_text))  # type: ignore[call-arg]
                try:
                    config_label.setStyleSheet("color: #cccccc; font-size: 11px; margin: 5px 0;")  # type: ignore[attr-defined]
                    config_label.setWordWrap(True)  # type: ignore[attr-defined]
                except Exception:
                    pass
                layout.addWidget(config_label)  # type: ignore[arg-type]
        
        # File name
        file_label = QLabel(f"File: {self.test_file.name}")  # type: ignore[call-arg]
        try:
            file_label.setStyleSheet("color: #cccccc; font-size: 10px; font-family: 'Monaco', 'Menlo', 'Courier New', monospace;")  # type: ignore[attr-defined]
        except Exception:
            pass
        layout.addWidget(file_label)  # type: ignore[arg-type]
        
        try:
            layout.addStretch()  # type: ignore[attr-defined]
        except Exception:
            pass
        
        # Buttons
        button_layout = QHBoxLayout()  # type: ignore[call-arg]
        
        # Launch button
        launch_btn = QPushButton("🚀 Launch")  # type: ignore[call-arg]
        try:
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
            launch_btn.clicked.connect(self.launch_test)  # type: ignore[attr-defined]
        except Exception:
            pass
        button_layout.addWidget(launch_btn)  # type: ignore[arg-type]
        
        # Edit button
        edit_btn = QPushButton("✏️ Edit")  # type: ignore[call-arg]
        try:
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
            edit_btn.clicked.connect(self.edit_test)  # type: ignore[attr-defined]
        except Exception:
            pass
        button_layout.addWidget(edit_btn)  # type: ignore[arg-type]
        
        # Delete button
        delete_btn = QPushButton("🗑️ Delete")  # type: ignore[call-arg]
        try:
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
            delete_btn.clicked.connect(self.delete_test)  # type: ignore[attr-defined]
        except Exception:
            pass
        button_layout.addWidget(delete_btn)  # type: ignore[arg-type]
        
        layout.addLayout(button_layout)  # type: ignore[arg-type]
        
    def launch_test(self):
        """Launch the custom test."""
        try:
            subprocess.Popen([sys.executable, str(self.test_file)], cwd=str(self.test_file.parent))
        except Exception as e:
            try:
                QMessageBox.critical(self, "Launch Error", f"Failed to launch test: {e}")  # type: ignore[attr-defined]
            except Exception:
                print(f"Launch Error: Failed to launch test: {e}")  # Fallback for headless
            
    def edit_test(self):
        """Open test file in default editor."""
        try:
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
            try:
                QMessageBox.warning(self, "Edit Error", f"Could not open editor: {e}")  # type: ignore[attr-defined]
            except Exception:
                print(f"Edit Error: Could not open editor: {e}")  # Fallback for headless
            
    def delete_test(self):
        """Delete the custom test file after confirmation."""
        try:
            reply = QMessageBox.question(  # type: ignore[attr-defined]
                self, "Delete Custom Test",
                f"Are you sure you want to delete '{self.test_info['name']}'?\n\n"
                f"File: {self.test_file.name}\n\n"
                f"This action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,  # type: ignore[attr-defined]
                QMessageBox.StandardButton.No  # type: ignore[attr-defined]
            )
            
            if reply == QMessageBox.StandardButton.Yes:  # type: ignore[attr-defined]
                try:
                    # Delete the file
                    self.test_file.unlink()
                    
                    # Show success message
                    QMessageBox.information(  # type: ignore[attr-defined]
                        self, "Test Deleted",
                        f"Custom test '{self.test_info['name']}' has been deleted successfully."
                    )
                    
                    # Signal parent to refresh the list
                    if self.parent_widget and hasattr(self.parent_widget, 'populate_custom_tests'):
                        self.parent_widget.populate_custom_tests()
                        
                except Exception as e:
                    QMessageBox.critical(  # type: ignore[attr-defined]
                        self, "Delete Error",
                        f"Failed to delete custom test:\n\n{str(e)}"
                    )
        except Exception as e:
            print(f"Delete operation failed: {e}")  # Fallback for headless environment


class TestCardWidget(QFrame):  # pragma: no cover - GUI component extracted from monolith in Phase 2.2
    """Visual card representation of a test configuration.
    
    Extracted from enhanced_test_launcher_v2.py in Phase 2.2.
    Handles display and interaction with standard test configurations.
    """
    
    launchRequested = pyqtSignal(str, str)  # test_name, test_type  # type: ignore[attr-defined]
    compareRequested = pyqtSignal(str)      # test_name  # type: ignore[attr-defined]
    
    def __init__(self, config: TestConfiguration, parent=None):
        super().__init__(parent)  # type: ignore[misc]
        self.config = config
        self.selected_for_comparison = False
        self.setup_ui()
        
    def setup_ui(self):
        """Create the test card UI."""
        try:
            self.setFrameStyle(QFrame.Shape.StyledPanel)  # type: ignore[attr-defined]
            self.setStyleSheet("""
                QFrame {
                    background-color: #1e1e1e;
                    border: 2px solid #555555;
                    border-radius: 8px;
                    margin: 4px;
                }
                QFrame:hover {
                    border-color: #4CAF50;
                }
            """)
        except Exception:
            pass  # Headless environment compatibility
        
        layout = QVBoxLayout(self)  # type: ignore[call-arg]
        try:
            layout.setSpacing(8)  # type: ignore[attr-defined]
        except Exception:
            pass
        
        # Header with test name
        name_label = QLabel(self.config.name)  # type: ignore[call-arg]
        try:
            name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))  # type: ignore[attr-defined]
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore[attr-defined]
            name_label.setStyleSheet("color: #ffffff;")  # type: ignore[attr-defined]
        except Exception:
            pass
        layout.addWidget(name_label)  # type: ignore[arg-type]
        
        # Description
        desc_label = QLabel(self.config.description)  # type: ignore[call-arg]
        try:
            desc_label.setWordWrap(True)  # type: ignore[attr-defined]
            desc_label.setStyleSheet("color: #cccccc; font-size: 10px;")  # type: ignore[attr-defined]
        except Exception:
            pass
        layout.addWidget(desc_label)  # type: ignore[arg-type]
        
        # Configuration summary
        config_text = f"""
        <b>Configuration:</b><br>
        • Grid: {self.config.grid_size[0]}×{self.config.grid_size[1]}<br>
        • Agents: {self.config.agent_count}<br>
        • Density: {self.config.resource_density:.2f}<br>
        • Perception: {self.config.perception_radius}<br>
        • Type: {self.config.preference_mix.replace('_', ' ').title()}
        """
        config_label = QLabel(config_text)  # type: ignore[call-arg]
        try:
            config_label.setStyleSheet("font-size: 9px; color: #cccccc;")  # type: ignore[attr-defined]
        except Exception:
            pass
        layout.addWidget(config_label)  # type: ignore[arg-type]
        
        # Runtime estimate
        runtime = self._estimate_runtime()
        runtime_label = QLabel(f"⏱️ Runtime: {runtime}")  # type: ignore[call-arg]
        try:
            runtime_label.setStyleSheet("font-size: 9px; color: #aaaaaa; font-style: italic;")  # type: ignore[attr-defined]
        except Exception:
            pass
        layout.addWidget(runtime_label)  # type: ignore[arg-type]
        
        # Action buttons
        button_layout = QVBoxLayout()  # type: ignore[call-arg]
        
        # Launch button
        launch_btn = QPushButton("⚡ Launch Test")  # type: ignore[call-arg]
        try:
            launch_btn.setStyleSheet("""
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
            launch_btn.clicked.connect(lambda: self.launchRequested.emit(self.config.name, "framework"))  # type: ignore[attr-defined]
        except Exception:
            pass
        button_layout.addWidget(launch_btn)  # type: ignore[arg-type]
            
        # Secondary actions
        secondary_layout = QHBoxLayout()  # type: ignore[call-arg]
        
        compare_btn = QPushButton("📊 Compare")  # type: ignore[call-arg]
        try:
            compare_btn.setToolTip("Add to Comparison")  # type: ignore[attr-defined]
            compare_btn.clicked.connect(lambda: self.compareRequested.emit(self.config.name))  # type: ignore[attr-defined]
        except Exception:
            pass
        secondary_layout.addWidget(compare_btn)  # type: ignore[arg-type]
        
        button_layout.addLayout(secondary_layout)  # type: ignore[arg-type]
        layout.addLayout(button_layout)  # type: ignore[arg-type]
        
        # Set size
        try:
            self.setMinimumSize(250, 300)  # type: ignore[attr-defined]
            self.setMaximumSize(300, 350)  # type: ignore[attr-defined]
        except Exception:
            pass
        

        
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
            try:
                self.setStyleSheet("""
                    QFrame {
                        background-color: #2a1a00;
                        border: 3px solid #ff9800;
                        border-radius: 8px;
                        margin: 4px;
                    }
                """)
            except Exception:
                pass
        else:
            try:
                self.setStyleSheet("""
                    QFrame {
                        background-color: #1e1e1e;
                        border: 2px solid #555555;
                        border-radius: 8px;
                        margin: 4px;
                    }
                    QFrame:hover {
                        border-color: #4CAF50;
                    }
                """)
            except Exception:
                pass
