#!/usr/bin/env python3
"""Configuration Editor Widget for VMT Framework.

Advanced configuration editing interface with:
- Real-time parameter sliders and controls
- Live validation and preview
- Configuration templates and presets
- Custom test generation and launch
- Parameter sensitivity analysis

This module was extracted from MANUAL_TESTS/live_config_editor.py for proper
architectural separation.
"""

import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict, replace
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QPushButton, QSlider, QSpinBox, QDoubleSpinBox, QComboBox,
    QGroupBox, QTextEdit, QTabWidget, QSplitter, QScrollArea,
    QCheckBox, QProgressBar, QListWidget, QListWidgetItem,
    QDialog, QDialogButtonBox, QLineEdit, QFileDialog, QMessageBox,
    QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QAction

# Import from framework using proper package paths
from econsim.tools.launcher.framework.test_configs import TestConfiguration, ALL_TEST_CONFIGS
from econsim.tools.launcher.framework.simulation_factory import SimulationFactory
from econsim.tools.launcher.framework.phase_manager import PhaseManager


@dataclass
class ConfigurationPreset:
    """Saved configuration preset with metadata."""
    name: str
    description: str
    config: TestConfiguration
    created: str
    tags: List[str]


class ParameterSlider(QWidget):
    """Smart parameter slider with validation and live preview."""
    
    valueChanged = pyqtSignal(object)  # Emits the new value
    
    def __init__(self, name: str, min_val: float, max_val: float, 
                 initial_val: float, step: float = 1.0, 
                 suffix: str = "", tooltip: str = "", parent=None):
        super().__init__(parent)
        self.name = name
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.suffix = suffix
        
        self.setup_ui()
        self.set_value(initial_val)
        
        if tooltip:
            self.setToolTip(tooltip)
            
    def setup_ui(self):
        """Create the slider UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        
        # Label with current value
        self.label = QLabel(f"{self.name}: {self.min_val}{self.suffix}")
        self.label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        layout.addWidget(self.label)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(int((self.max_val - self.min_val) / self.step))
        self.slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.slider)
        
        # Min/max labels
        range_layout = QHBoxLayout()
        range_layout.setContentsMargins(0, 0, 0, 0)
        
        min_label = QLabel(f"{self.min_val}{self.suffix}")
        min_label.setStyleSheet("color: #cccccc; font-size: 8px;")
        range_layout.addWidget(min_label)
        
        range_layout.addStretch()
        
        max_label = QLabel(f"{self.max_val}{self.suffix}")
        max_label.setStyleSheet("color: #cccccc; font-size: 8px;")
        range_layout.addWidget(max_label)
        
        layout.addLayout(range_layout)
        
    def _on_slider_changed(self, slider_value: int):
        """Handle slider value change."""
        actual_value = self.min_val + (slider_value * self.step)
        self.label.setText(f"{self.name}: {actual_value:.1f}{self.suffix}")
        self.valueChanged.emit(actual_value)
        
    def get_value(self) -> float:
        """Get current value."""
        slider_value = self.slider.value()
        return self.min_val + (slider_value * self.step)
        
    def set_value(self, value: float):
        """Set current value."""
        # Clamp to valid range
        value = max(self.min_val, min(self.max_val, value))
        slider_value = int((value - self.min_val) / self.step)
        
        self.slider.blockSignals(True)
        self.slider.setValue(slider_value)
        self.slider.blockSignals(False)
        
        self.label.setText(f"{self.name}: {value:.1f}{self.suffix}")


class ConfigurationValidator(QWidget):
    """Real-time configuration validation with warnings and suggestions."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Create validation UI."""
        layout = QVBoxLayout(self)
        
        # Validation status
        self.status_label = QLabel("✅ Configuration Valid")
        self.status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #81c784; background: #1a3d1a; padding: 8px; border-radius: 4px;")
        layout.addWidget(self.status_label)
        
        # Validation details
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(150)
        self.details_text.setReadOnly(True)
        self.details_text.setStyleSheet("background: #1e1e1e; color: #ffffff; font-size: 9px;")
        layout.addWidget(self.details_text)
        
    def validate_config(self, config: TestConfiguration) -> Dict[str, List[str]]:
        """Validate configuration and return issues."""
        issues = {"errors": [], "warnings": [], "info": []}
        
        # Basic validation
        total_cells = config.grid_size[0] * config.grid_size[1]
        distance_k = getattr(config, 'distance_scaling_factor', 0.0)
        
        # Errors (prevent execution)
        if config.agent_count <= 0:
            issues["errors"].append("Agent count must be positive")
        if config.grid_size[0] < 5 or config.grid_size[1] < 5:
            issues["errors"].append("Grid dimensions must be at least 5×5")
        if config.resource_density <= 0 or config.resource_density > 1:
            issues["errors"].append("Resource density must be between 0 and 1")
        if config.perception_radius <= 0:
            issues["errors"].append("Perception radius must be positive")
        if distance_k < 0 or distance_k > 10:
            issues["errors"].append("Distance scaling factor must be between 0 and 10")
        if config.agent_count > total_cells:
            issues["errors"].append("More agents than grid cells")
            
        # Phase validation
        custom_phases = getattr(config, 'custom_phases', None)
        if custom_phases is not None:
            if len(custom_phases) == 0:
                issues["errors"].append("Custom phases configured but empty - add at least one phase")
            else:
                # Validate phase configuration
                try:
                    PhaseManager(custom_phases)  # This will validate the phases
                except Exception as e:
                    issues["errors"].append(f"Invalid phase configuration: {str(e)}")
            
        # Warnings (may cause issues)
        if config.agent_count > 100:
            issues["warnings"].append("Very high agent count may cause performance issues")
        if total_cells > 2500:
            issues["warnings"].append("Very large grid may cause performance issues")
        if config.resource_density < 0.05:
            issues["warnings"].append("Very low resource density may result in minimal activity")
        if config.perception_radius > 15:
            issues["warnings"].append("Very high perception radius may cause performance issues")
        if config.agent_count > (total_cells * 0.3):
            issues["warnings"].append("High agent density may limit movement")
            
        # Info (helpful suggestions)
        expected_resources = int(total_cells * config.resource_density)
        if expected_resources < config.agent_count:
            issues["info"].append("Fewer resources than agents - expect competition")
        elif expected_resources > (config.agent_count * 3):
            issues["info"].append("Abundant resources - expect minimal competition")
            
        agent_perception_area = 3.14159 * (config.perception_radius ** 2)
        if agent_perception_area > (total_cells * 0.5):
            issues["info"].append("Perception covers large portion of grid")
            
        # Distance scaling factor insights
        if distance_k == 0.0:
            issues["info"].append("k=0.0: Agents ignore distance, optimize utility globally")
        elif distance_k >= 5.0:
            issues["info"].append(f"k={distance_k:.1f}: Strong local preference - agents heavily favor nearby targets")
        elif distance_k >= 1.0:
            issues["info"].append(f"k={distance_k:.1f}: Moderate distance penalty - balanced targeting behavior")
        else:
            issues["info"].append(f"k={distance_k:.1f}: Light distance penalty - slight preference for nearby targets")
            
        return issues
        
    def update_validation(self, config: TestConfiguration):
        """Update validation display."""
        issues = self.validate_config(config)
        
        # Update status
        if issues["errors"]:
            self.status_label.setText("❌ Configuration Invalid")
            self.status_label.setStyleSheet("color: #ff6b6b; background: #3d1a1a; padding: 8px; border-radius: 4px;")
        elif issues["warnings"]:
            self.status_label.setText("⚠️ Configuration Has Warnings")
            self.status_label.setStyleSheet("color: #ffb74d; background: #3d2f1a; padding: 8px; border-radius: 4px;")
        else:
            self.status_label.setText("✅ Configuration Valid")
            self.status_label.setStyleSheet("color: #81c784; background: #1a3d1a; padding: 8px; border-radius: 4px;")
            
        # Update details
        details_html = ""
        
        if issues["errors"]:
            details_html += "<b style='color: #ff6b6b;'>Errors (Must Fix):</b><ul>"
            for error in issues["errors"]:
                details_html += f"<li>{error}</li>"
            details_html += "</ul>"
            
        if issues["warnings"]:
            details_html += "<b style='color: #ffb74d;'>Warnings:</b><ul>"
            for warning in issues["warnings"]:
                details_html += f"<li>{warning}</li>"
            details_html += "</ul>"
            
        if issues["info"]:
            details_html += "<b style='color: #64b5f6;'>Information:</b><ul>"
            for info in issues["info"]:
                details_html += f"<li>{info}</li>"
            details_html += "</ul>"
            
        if not details_html:
            details_html = "<span style='color: #81c784;'>All parameters are within recommended ranges.</span>"
            
        self.details_text.setHtml(details_html)
        
        return len(issues["errors"]) == 0  # Return True if valid


class ConfigurationPreview(QWidget):
    """Live preview panel showing configuration effects."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Create preview UI."""
        layout = QVBoxLayout(self)
        
        # Preview title
        title = QLabel("Configuration Preview")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Preview content
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setStyleSheet("background: #1e1e1e; color: #ffffff; border: 1px solid #555555; border-radius: 4px;")
        layout.addWidget(self.preview_text)
        
        # Estimated runtime
        self.runtime_label = QLabel("⏱️ Estimated Runtime: ~15 min")
        self.runtime_label.setStyleSheet("font-style: italic; color: #cccccc; margin-top: 5px;")
        layout.addWidget(self.runtime_label)
        
    def update_preview(self, config: TestConfiguration):
        """Update preview with current configuration."""
        total_cells = config.grid_size[0] * config.grid_size[1]
        expected_resources = int(total_cells * config.resource_density)
        
        # Calculate density ratios
        agent_density = (config.agent_count / total_cells) * 100
        resource_ratio = expected_resources / config.agent_count if config.agent_count > 0 else 0
        
        # Calculate perception coverage
        perception_area = 3.14159 * (config.perception_radius ** 2)
        perception_coverage = min(100, (perception_area / total_cells) * 100)
        
        # Get distance scaling factor with fallback
        distance_k = getattr(config, 'distance_scaling_factor', 0.0)
        
        # Generate preview text
        preview_html = f"""
        <table style='width: 100%; font-size: 10px;'>
        <tr><td><b>Grid:</b></td><td>{config.grid_size[0]} × {config.grid_size[1]} ({total_cells:,} cells)</td></tr>
        <tr><td><b>Agents:</b></td><td>{config.agent_count} ({agent_density:.1f}% density)</td></tr>
        <tr><td><b>Resources:</b></td><td>~{expected_resources} ({resource_ratio:.1f} per agent)</td></tr>
        <tr><td><b>Perception:</b></td><td>{config.perception_radius} radius ({perception_coverage:.1f}% coverage)</td></tr>
        <tr><td><b>Distance Factor (k):</b></td><td>{distance_k:.1f} ({'Global optimization' if distance_k == 0.0 else 'Local preference' if distance_k >= 5.0 else 'Balanced targeting'})</td></tr>
        <tr><td><b>Preferences:</b></td><td>{config.preference_mix.replace('_', ' ').title()}</td></tr>
        </table>
        
        <p style='margin-top: 10px; font-size: 9px; color: #cccccc;'>
        <b>Expected Behavior:</b><br>
        {'High competition for resources' if resource_ratio < 2 else 'Moderate resource availability' if resource_ratio < 4 else 'Abundant resources'}<br>
        {'Agents can see most of the grid' if perception_coverage > 50 else 'Limited visibility encourages exploration' if perception_coverage < 20 else 'Moderate perception range'}<br>
        {'Dense population may limit movement' if agent_density > 20 else 'Sparse population with room to move' if agent_density < 10 else 'Balanced population density'}<br>
        {'Agents prioritize nearby targets strongly' if distance_k >= 5.0 else 'Agents ignore distance in decisions' if distance_k == 0.0 else 'Agents balance utility vs distance'}
        </p>
        """
        
        self.preview_text.setHtml(preview_html)
        
        # Update runtime estimate
        runtime = self._estimate_runtime(config)
        self.runtime_label.setText(f"⏱️ Estimated Runtime: {runtime}")
        
    def _estimate_runtime(self, config: TestConfiguration) -> str:
        """Estimate test runtime based on configuration complexity."""
        base_minutes = 15  # Standard 900-step runtime
        
        # Factors affecting runtime
        total_cells = config.grid_size[0] * config.grid_size[1]
        size_factor = total_cells / 900  # 30x30 baseline
        agent_factor = config.agent_count / 20  # 20 agents baseline
        
        # Combined complexity factor
        complexity = (size_factor + agent_factor) / 2
        estimated_minutes = int(base_minutes * complexity)
        
        if estimated_minutes < 8:
            return "~5-10 min"
        elif estimated_minutes < 15:
            return "~10-15 min"
        elif estimated_minutes < 25:
            return "~15-25 min"
        elif estimated_minutes < 40:
            return "~25-40 min"
        else:
            return "~40+ min (consider reducing complexity)"


class PresetManager(QWidget):
    """Manage configuration presets and templates."""
    
    presetLoaded = pyqtSignal(TestConfiguration)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.presets: List[ConfigurationPreset] = []
        self.presets_file = self._get_presets_file()
        self.setup_ui()
        self.load_presets()
    
    def _get_presets_file(self) -> Path:
        """Get presets file location in MANUAL_TESTS directory."""
        # Store presets in MANUAL_TESTS for project-local configuration
        from pathlib import Path
        import os
        # Navigate to project root and into MANUAL_TESTS
        # This file is in src/econsim/tools/widgets/
        project_root = Path(__file__).parent.parent.parent.parent.parent
        return project_root / "MANUAL_TESTS" / "config_presets.json"
        
    def setup_ui(self):
        """Create preset management UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Configuration Presets")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Preset list
        self.preset_list = QListWidget()
        self.preset_list.itemDoubleClicked.connect(self.load_selected_preset)
        layout.addWidget(self.preset_list)
        
        # Preset controls
        controls_layout = QHBoxLayout()
        
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self.load_selected_preset)
        controls_layout.addWidget(load_btn)
        
        save_btn = QPushButton("Save Current")
        save_btn.clicked.connect(self.save_current_preset)
        controls_layout.addWidget(save_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_selected_preset)
        controls_layout.addWidget(delete_btn)
        
        layout.addLayout(controls_layout)
        
        # Import/Export
        io_layout = QHBoxLayout()
        
        import_btn = QPushButton("Import...")
        import_btn.clicked.connect(self.import_presets)
        io_layout.addWidget(import_btn)
        
        export_btn = QPushButton("Export...")
        export_btn.clicked.connect(self.export_presets)
        io_layout.addWidget(export_btn)
        
        layout.addLayout(io_layout)
        
    def load_presets(self):
        """Load presets from file."""
        if not self.presets_file.exists():
            # Create default presets
            self.create_default_presets()
            return
            
        try:
            with open(self.presets_file, 'r') as f:
                presets_data = json.load(f)
                
            self.presets = []
            for preset_data in presets_data:
                config_data = preset_data["config"]
                config = TestConfiguration(
                    id=config_data["id"],
                    name=config_data["name"],
                    description=config_data["description"],
                    grid_size=tuple(config_data["grid_size"]),
                    agent_count=config_data["agent_count"],
                    resource_density=config_data["resource_density"],
                    perception_radius=config_data["perception_radius"],
                    preference_mix=config_data["preference_mix"],
                    seed=config_data["seed"]
                )
                
                preset = ConfigurationPreset(
                    name=preset_data["name"],
                    description=preset_data["description"],
                    config=config,
                    created=preset_data["created"],
                    tags=preset_data.get("tags", [])
                )
                self.presets.append(preset)
                
        except Exception as e:
            print(f"Error loading presets: {e}")
            self.create_default_presets()
            
        self.refresh_preset_list()
        
    def save_presets(self):
        """Save presets to file."""
        presets_data = []
        for preset in self.presets:
            preset_data = {
                "name": preset.name,
                "description": preset.description,
                "config": asdict(preset.config),
                "created": preset.created,
                "tags": preset.tags
            }
            presets_data.append(preset_data)
            
        try:
            # Ensure directory exists
            self.presets_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.presets_file, 'w') as f:
                json.dump(presets_data, f, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Failed to save presets: {e}")
            
    def create_default_presets(self):
        """Create default configuration presets."""
        # Use existing test configurations as templates
        for config in ALL_TEST_CONFIGS.values():
            preset = ConfigurationPreset(
                name=f"{config.name} (Template)",
                description=f"Based on {config.description}",
                config=config,
                created=datetime.now().isoformat(),
                tags=["template", "default"]
            )
            self.presets.append(preset)
            
        # Add some common educational presets
        educational_presets = [
            ConfigurationPreset(
                name="Small Classroom Demo",
                description="Quick demo for small groups - fast execution",
                config=TestConfiguration(
                    id=999,
                    name="Small Demo",
                    description="Small classroom demonstration",
                    grid_size=(15, 15),
                    agent_count=8,
                    resource_density=0.3,
                    perception_radius=4,
                    preference_mix="mixed",
                    seed=12345
                ),
                created=datetime.now().isoformat(),
                tags=["educational", "demo", "small"]
            ),
            ConfigurationPreset(
                name="Competition Study",
                description="High competition scenario for economic analysis",
                config=TestConfiguration(
                    id=998,
                    name="Competition Study", 
                    description="High competition economic analysis",
                    grid_size=(20, 20),
                    agent_count=30,
                    resource_density=0.15,
                    perception_radius=6,
                    preference_mix="mixed",
                    seed=54321
                ),
                created=datetime.now().isoformat(),
                tags=["educational", "competition", "analysis"]
            )
        ]
        
        self.presets.extend(educational_presets)
        self.save_presets()
        
    def refresh_preset_list(self):
        """Refresh the preset list display."""
        self.preset_list.clear()
        
        for preset in self.presets:
            item_text = f"{preset.name}"
            if preset.tags:
                item_text += f" [{', '.join(preset.tags)}]"
                
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, preset)
            item.setToolTip(f"{preset.description}\n\nGrid: {preset.config.grid_size[0]}×{preset.config.grid_size[1]}\nAgents: {preset.config.agent_count}\nDensity: {preset.config.resource_density}\nCreated: {preset.created[:10]}")
            
            self.preset_list.addItem(item)
            
    def load_selected_preset(self):
        """Load the selected preset."""
        current_item = self.preset_list.currentItem()
        if not current_item:
            return
            
        preset = current_item.data(Qt.ItemDataRole.UserRole)
        self.presetLoaded.emit(preset.config)
        
    def save_current_preset(self):
        """Save current configuration as preset."""
        # This will be connected by the parent editor
        pass
        
    def delete_selected_preset(self):
        """Delete the selected preset."""
        current_item = self.preset_list.currentItem()
        if not current_item:
            return
            
        preset = current_item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(self, "Delete Preset",
            f"Delete preset '{preset.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
        if reply == QMessageBox.StandardButton.Yes:
            self.presets.remove(preset)
            self.save_presets()
            self.refresh_preset_list()
            
    def import_presets(self):
        """Import presets from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Presets", "", "JSON Files (*.json);;All Files (*)")
            
        if not file_path:
            return
            
        try:
            with open(file_path, 'r') as f:
                imported_data = json.load(f)
                
            # Add imported presets (with name conflicts handled)
            imported_count = 0
            for preset_data in imported_data:
                # Check for name conflicts
                base_name = preset_data["name"]
                name = base_name
                counter = 1
                while any(p.name == name for p in self.presets):
                    name = f"{base_name} ({counter})"
                    counter += 1
                    
                preset_data["name"] = name
                
                # Create preset object
                config_data = preset_data["config"]
                config = TestConfiguration(
                    id=config_data["id"],
                    name=config_data["name"],
                    description=config_data["description"],
                    grid_size=tuple(config_data["grid_size"]),
                    agent_count=config_data["agent_count"],
                    resource_density=config_data["resource_density"],
                    perception_radius=config_data["perception_radius"],
                    preference_mix=config_data["preference_mix"],
                    seed=config_data["seed"]
                )
                
                preset = ConfigurationPreset(
                    name=preset_data["name"],
                    description=preset_data["description"],
                    config=config,
                    created=preset_data["created"],
                    tags=preset_data.get("tags", [])
                )
                
                self.presets.append(preset)
                imported_count += 1
                
            self.save_presets()
            self.refresh_preset_list()
            
            QMessageBox.information(self, "Import Complete",
                f"Imported {imported_count} presets successfully.")
                
        except Exception as e:
            QMessageBox.warning(self, "Import Error",
                f"Failed to import presets: {e}")
                
    def export_presets(self):
        """Export presets to file."""
        if not self.presets:
            QMessageBox.information(self, "No Presets",
                "No presets to export.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Presets", "vmt_config_presets.json", 
            "JSON Files (*.json);;All Files (*)")
            
        if not file_path:
            return
            
        try:
            presets_data = []
            for preset in self.presets:
                preset_data = {
                    "name": preset.name,
                    "description": preset.description,
                    "config": asdict(preset.config),
                    "created": preset.created,
                    "tags": preset.tags
                }
                presets_data.append(preset_data)
                
            with open(file_path, 'w') as f:
                json.dump(presets_data, f, indent=2)
                
            QMessageBox.information(self, "Export Complete",
                f"Exported {len(self.presets)} presets to {file_path}")
                
        except Exception as e:
            QMessageBox.warning(self, "Export Error",
                f"Failed to export presets: {e}")


class ConfigEditor(QWidget):
    """Main live configuration editor widget.
    
    This is the public interface for the configuration editor component.
    Renamed from LiveConfigEditor for consistency with module naming.
    """
    
    configChanged = pyqtSignal(TestConfiguration)
    
    def __init__(self, initial_config: Optional[TestConfiguration] = None, parent=None):
        super().__init__(parent)
        
        # Use first test config as default if none provided
        if initial_config is None:
            initial_config = next(iter(ALL_TEST_CONFIGS.values()))
            
        self.current_config = initial_config
        self.custom_phases = None  # Will store List[PhaseDefinition] when configured
        self.setup_ui()
        self.connect_signals()
        self.load_config(initial_config)
        
    def setup_ui(self):
        """Create the configuration editor UI."""
        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        
        # Left panel: Controls
        left_panel = self.create_controls_panel()
        layout.addWidget(left_panel, stretch=2)
        
        # Right panel: Preview and validation
        right_panel = self.create_preview_panel()
        layout.addWidget(right_panel, stretch=1)
        
    def create_controls_panel(self) -> QWidget:
        """Create the parameter controls panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("Live Configuration Editor")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Scroll area for controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        
        # Grid Configuration Group
        grid_group = QGroupBox("Grid Configuration")
        grid_layout = QVBoxLayout(grid_group)
        
        self.grid_width_slider = ParameterSlider(
            "Grid Width", 5, 50, 20, 1, "",
            "Width of the simulation grid (5-50 cells)")
        grid_layout.addWidget(self.grid_width_slider)
        
        self.grid_height_slider = ParameterSlider(
            "Grid Height", 5, 50, 20, 1, "",
            "Height of the simulation grid (5-50 cells)")
        grid_layout.addWidget(self.grid_height_slider)
        
        controls_layout.addWidget(grid_group)
        
        # Agent Configuration Group
        agent_group = QGroupBox("Agent Configuration")
        agent_layout = QVBoxLayout(agent_group)
        
        self.agent_count_slider = ParameterSlider(
            "Agent Count", 1, 100, 20, 1, "",
            "Number of agents in the simulation (1-100)")
        agent_layout.addWidget(self.agent_count_slider)
        
        self.perception_slider = ParameterSlider(
            "Perception Radius", 1, 20, 8, 0.5, "",
            "How far agents can see (1-20 cells)")
        agent_layout.addWidget(self.perception_slider)
        
        self.distance_scaling_slider = ParameterSlider(
            "Distance Scaling (k)", 0.0, 10.0, 0.0, 0.1, "",
            "Distance penalty factor for target selection (0=no penalty, higher=prefer nearby targets)")
        agent_layout.addWidget(self.distance_scaling_slider)
        
        controls_layout.addWidget(agent_group)
        
        # Resource Configuration Group
        resource_group = QGroupBox("Resource Configuration")
        resource_layout = QVBoxLayout(resource_group)
        
        self.density_slider = ParameterSlider(
            "Resource Density", 0.01, 1.0, 0.25, 0.01, "",
            "Fraction of cells containing resources (0.01-1.0)")
        resource_layout.addWidget(self.density_slider)
        
        controls_layout.addWidget(resource_group)
        
        # Preference Configuration Group
        pref_group = QGroupBox("Preference Configuration")
        pref_layout = QFormLayout(pref_group)
        
        self.preference_combo = QComboBox()
        self.preference_combo.addItems([
            "mixed", "cobb_douglas", "leontief", "perfect_substitutes"
        ])
        self.preference_combo.setToolTip("Type of agent preferences")
        pref_layout.addRow("Preference Type:", self.preference_combo)
        
        # Seed configuration
        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(1, 999999)
        self.seed_spin.setValue(12345)
        self.seed_spin.setToolTip("Random seed for reproducible results")
        pref_layout.addRow("Random Seed:", self.seed_spin)
        
        controls_layout.addWidget(pref_group)
        
        # Advanced Options (collapsible)
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QFormLayout(advanced_group)
        
        # Test name and description
        self.test_name_edit = QLineEdit("Custom Test")
        advanced_layout.addRow("Test Name:", self.test_name_edit)
        
        self.test_desc_edit = QLineEdit("Custom configuration test")
        advanced_layout.addRow("Description:", self.test_desc_edit)
        
        # Phase configuration
        phase_config_layout = QHBoxLayout()
        self.phase_config_btn = QPushButton("Configure Phases...")
        self.phase_config_btn.clicked.connect(self.configure_phases)
        phase_config_layout.addWidget(self.phase_config_btn)
        
        self.phase_summary_label = QLabel("Standard 6-phase schedule")
        self.phase_summary_label.setStyleSheet("color: #cccccc; font-size: 9px; font-style: italic;")
        phase_config_layout.addWidget(self.phase_summary_label)
        phase_config_layout.addStretch()
        
        phase_config_widget = QWidget()
        phase_config_widget.setLayout(phase_config_layout)
        advanced_layout.addRow("Test Phases:", phase_config_widget)
        
        controls_layout.addWidget(advanced_group)
        
        # Action buttons
        action_layout = QVBoxLayout()
        
        self.launch_btn = QPushButton("🚀 Launch Test")
        self.launch_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #666666;
            }
        """)
        self.launch_btn.clicked.connect(self.launch_custom_test)
        action_layout.addWidget(self.launch_btn)
        
        self.save_test_btn = QPushButton("💾 Save Custom Test")
        self.save_test_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #666666;
            }
        """)
        self.save_test_btn.clicked.connect(self.save_custom_test)
        action_layout.addWidget(self.save_test_btn)
        
        self.save_preset_btn = QPushButton("💾 Save as Preset")
        self.save_preset_btn.clicked.connect(self.save_as_preset)
        action_layout.addWidget(self.save_preset_btn)
        
        self.reset_btn = QPushButton("🔄 Reset to Template")
        self.reset_btn.clicked.connect(self.reset_to_template)
        action_layout.addWidget(self.reset_btn)
        
        controls_layout.addLayout(action_layout)
        
        controls_layout.addStretch()
        
        scroll.setWidget(controls_widget)
        layout.addWidget(scroll)
        
        return panel
        
    def create_preview_panel(self) -> QWidget:
        """Create the preview and validation panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Tab widget for different views
        tabs = QTabWidget()
        
        # Preview tab
        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        
        self.preview = ConfigurationPreview()
        preview_layout.addWidget(self.preview)
        
        # Validation tab
        self.validator = ConfigurationValidator()
        preview_layout.addWidget(self.validator)
        
        tabs.addTab(preview_tab, "Preview & Validation")
        
        # Presets tab
        self.preset_manager = PresetManager()
        tabs.addTab(self.preset_manager, "Presets")
        
        layout.addWidget(tabs)
        
        return panel
        
    def connect_signals(self):
        """Connect all UI signals."""
        # Parameter sliders
        self.grid_width_slider.valueChanged.connect(self.on_parameter_changed)
        self.grid_height_slider.valueChanged.connect(self.on_parameter_changed)
        self.agent_count_slider.valueChanged.connect(self.on_parameter_changed)
        self.perception_slider.valueChanged.connect(self.on_parameter_changed)
        self.distance_scaling_slider.valueChanged.connect(self.on_parameter_changed)
        self.density_slider.valueChanged.connect(self.on_parameter_changed)
        
        # Other controls
        self.preference_combo.currentTextChanged.connect(self.on_parameter_changed)
        self.seed_spin.valueChanged.connect(self.on_parameter_changed)
        self.test_name_edit.textChanged.connect(self.on_parameter_changed)
        self.test_desc_edit.textChanged.connect(self.on_parameter_changed)
        
        # Preset manager
        self.preset_manager.presetLoaded.connect(self.load_config)
        
    def on_parameter_changed(self):
        """Handle any parameter change."""
        # Update current config
        self.current_config = TestConfiguration(
            id=999,  # Custom config ID
            name=self.test_name_edit.text() or "Custom Test",
            description=self.test_desc_edit.text() or "Custom configuration",
            grid_size=(int(self.grid_width_slider.get_value()), 
                      int(self.grid_height_slider.get_value())),
            agent_count=int(self.agent_count_slider.get_value()),
            resource_density=self.density_slider.get_value(),
            perception_radius=int(self.perception_slider.get_value()),
            distance_scaling_factor=self.distance_scaling_slider.get_value(),
            preference_mix=self.preference_combo.currentText(),
            seed=self.seed_spin.value(),
            custom_phases=self.custom_phases  # Include custom phases
        )
        
        # Update preview and validation
        self.preview.update_preview(self.current_config)
        is_valid = self.validator.update_validation(self.current_config)
        
        # Enable/disable launch button based on validation
        self.launch_btn.setEnabled(is_valid)
        
        # Emit signal
        self.configChanged.emit(self.current_config)
    
    def configure_phases(self):
        """Open phase configuration dialog."""
        try:
            # Import phase_config_editor from MANUAL_TESTS
            # Note: This is still in MANUAL_TESTS as it's not a reusable widget component
            project_root = Path(__file__).parent.parent.parent.parent.parent
            manual_tests = project_root / "MANUAL_TESTS"
            if str(manual_tests) not in sys.path:
                sys.path.insert(0, str(manual_tests))
            
            from phase_config_editor import PhaseConfigDialog
            
            # Use current custom phases if available, otherwise start empty
            initial_phases = self.custom_phases
            
            dialog = PhaseConfigDialog(initial_phases, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.custom_phases = dialog.get_phases()
                self.update_phase_summary()
                self.on_parameter_changed()  # Trigger config update
                
        except ImportError as e:
            QMessageBox.warning(self, "Phase Configuration", 
                              f"Phase configuration editor not available: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Error opening phase configuration: {e}")
    
    def update_phase_summary(self):
        """Update the phase summary label."""
        try:
            if self.custom_phases:
                manager = PhaseManager(self.custom_phases)
                total_turns = manager.get_total_turns()
                phase_count = manager.get_phase_count()
                self.phase_summary_label.setText(f"✅ {phase_count} custom phases ({total_turns} turns)")
            else:
                self.phase_summary_label.setText("📋 Standard 6-phase schedule (900 turns)")
        except Exception as e:
            self.phase_summary_label.setText(f"❌ Invalid phases: {str(e)[:30]}...")
    
    def reset_phases_to_standard(self):
        """Reset to standard phase configuration."""
        self.custom_phases = None
        self.update_phase_summary()
        self.on_parameter_changed()
        
    def load_config(self, config: TestConfiguration):
        """Load a configuration into the editor."""
        self.current_config = config
        
        # Block signals to prevent recursive updates
        self.grid_width_slider.blockSignals(True)
        self.grid_height_slider.blockSignals(True)
        self.agent_count_slider.blockSignals(True)
        self.perception_slider.blockSignals(True)
        self.distance_scaling_slider.blockSignals(True)
        self.density_slider.blockSignals(True)
        self.preference_combo.blockSignals(True)
        self.seed_spin.blockSignals(True)
        self.test_name_edit.blockSignals(True)
        self.test_desc_edit.blockSignals(True)
        
        # Update UI controls
        self.grid_width_slider.set_value(config.grid_size[0])
        self.grid_height_slider.set_value(config.grid_size[1])
        self.agent_count_slider.set_value(config.agent_count)
        self.perception_slider.set_value(config.perception_radius)
        self.distance_scaling_slider.set_value(getattr(config, 'distance_scaling_factor', 0.0))
        self.density_slider.set_value(config.resource_density)
        self.preference_combo.setCurrentText(config.preference_mix)
        self.seed_spin.setValue(config.seed)
        self.test_name_edit.setText(config.name)
        self.test_desc_edit.setText(config.description)
        
        # Load custom phases if available
        self.custom_phases = getattr(config, 'custom_phases', None)
        self.update_phase_summary()
        
        # Re-enable signals
        self.grid_width_slider.blockSignals(False)
        self.grid_height_slider.blockSignals(False)
        self.agent_count_slider.blockSignals(False)
        self.perception_slider.blockSignals(False)
        self.distance_scaling_slider.blockSignals(False)
        self.density_slider.blockSignals(False)
        self.preference_combo.blockSignals(False)
        self.seed_spin.blockSignals(False)
        self.test_name_edit.blockSignals(False)
        self.test_desc_edit.blockSignals(False)
        
        # Update preview and validation
        self.preview.update_preview(config)
        is_valid = self.validator.update_validation(config)
        self.launch_btn.setEnabled(is_valid)
        
    def launch_custom_test(self):
        """Launch test with current custom configuration."""
        if not self.validator.update_validation(self.current_config):
            QMessageBox.warning(self, "Invalid Configuration",
                "Please fix the configuration errors before launching.")
            return
            
        try:
            # Create a temporary test file in MANUAL_TESTS directory
            project_root = Path(__file__).parent.parent.parent.parent.parent
            manual_tests_dir = project_root / "MANUAL_TESTS"
            temp_file = manual_tests_dir / f"temp_custom_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            
            # Generate test code
            temp_test_content = self.generate_test_code(self.current_config)
            
            with open(temp_file, 'w') as f:
                f.write(temp_test_content)
                
            # Make the file executable
            import stat
            temp_file.chmod(temp_file.stat().st_mode | stat.S_IEXEC)
            
            # Launch the test
            process = subprocess.Popen(
                [sys.executable, str(temp_file)], 
                cwd=str(temp_file.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Show success message
            QMessageBox.information(self, "Test Launched",
                f"Custom test '{self.current_config.name}' has been launched!\n\n"
                f"Config: {self.current_config.grid_size[0]}×{self.current_config.grid_size[1]} grid, "
                f"{self.current_config.agent_count} agents, k={getattr(self.current_config, 'distance_scaling_factor', 0.0)}\n"
                f"Temporary file: {temp_file.name}")
            
            # Clean up old temporary test files (keep only last 5)
            self._cleanup_old_temp_files()
                
        except Exception as e:
            QMessageBox.critical(self, "Launch Error",
                f"Failed to launch custom test: {e}")
                
    def save_custom_test(self):
        """Save current configuration as a permanent custom test."""
        if not self.validator.update_validation(self.current_config):
            QMessageBox.warning(self, "Invalid Configuration",
                "Please fix the configuration errors before saving.")
            return
            
        # Ask user for test filename
        suggested_name = self.current_config.name.lower().replace(' ', '_').replace('-', '_')
        # Remove special characters and ensure it's a valid filename
        import re
        suggested_name = re.sub(r'[^a-zA-Z0-9_]', '', suggested_name)
        if not suggested_name:
            suggested_name = "custom_test"
        suggested_name = f"{suggested_name}.py"
        
        filename, ok = QInputDialog.getText(
            self, "Save Custom Test",
            f"Enter filename for '{self.current_config.name}':",
            text=suggested_name
        )
        
        if not ok or not filename:
            return
            
        # Ensure .py extension
        if not filename.endswith('.py'):
            filename += '.py'
            
        try:
            # Create custom_tests directory if it doesn't exist
            project_root = Path(__file__).parent.parent.parent.parent.parent
            custom_tests_dir = project_root / "MANUAL_TESTS" / "custom_tests"
            custom_tests_dir.mkdir(parents=True, exist_ok=True)
            
            test_file = custom_tests_dir / filename
            
            # Check if file already exists
            if test_file.exists():
                reply = QMessageBox.question(
                    self, "File Exists",
                    f"The file '{filename}' already exists. Do you want to overwrite it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # Generate and save the test code
            test_content = self.generate_test_code(self.current_config)
            with open(test_file, 'w') as f:
                f.write(test_content)
                
            # Make the file executable
            import stat
            test_file.chmod(test_file.stat().st_mode | stat.S_IEXEC)
            
            QMessageBox.information(self, "Test Saved",
                f"Custom test '{self.current_config.name}' has been saved!\n\n"
                f"File: {test_file.name}\n"
                f"Location: {test_file.parent}\n\n"
                f"You can now find it in the Enhanced Test Launcher's 'Custom Tests' tab.")
                
        except Exception as e:
            QMessageBox.critical(self, "Save Error",
                f"Failed to save custom test: {e}")
                
    def _cleanup_old_temp_files(self):
        """Clean up old temporary test files, keeping only the most recent 5."""
        try:
            project_root = Path(__file__).parent.parent.parent.parent.parent
            manual_tests_dir = project_root / "MANUAL_TESTS"
            temp_files = list(manual_tests_dir.glob("temp_custom_test_*.py"))
            if len(temp_files) > 5:
                # Sort by creation time and remove oldest
                temp_files.sort(key=lambda f: f.stat().st_mtime)
                for old_file in temp_files[:-5]:
                    old_file.unlink()
        except Exception:
            pass  # Ignore cleanup errors
                
    def generate_test_code(self, config: TestConfiguration) -> str:
        """Generate executable test code for the configuration."""
        code = f'''#!/usr/bin/env python3
"""
Custom Generated Test: {config.name}
{config.description}

Auto-generated by Live Configuration Editor
Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
# Import from new framework location
sys.path.insert(0, str(project_root / "src"))
from econsim.tools.launcher.framework.base_test import StandardPhaseTest
from econsim.tools.launcher.framework.test_configs import TestConfiguration

# Custom test configuration
CUSTOM_CONFIG = TestConfiguration(
    id={config.id},
    name="{config.name}",
    description="{config.description}",
    grid_size=({config.grid_size[0]}, {config.grid_size[1]}),
    agent_count={config.agent_count},
    resource_density={config.resource_density},
    perception_radius={config.perception_radius},
    distance_scaling_factor={getattr(config, 'distance_scaling_factor', 0.0)},
    preference_mix="{config.preference_mix}",
    seed={config.seed}
)

class CustomTest(StandardPhaseTest):
    """Custom test implementation."""
    
    def __init__(self):
        super().__init__(CUSTOM_CONFIG)

def main():
    """Run the custom test."""
    app = QApplication(sys.argv)
    test = CustomTest()
    test.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
'''
        return code
        
    def save_as_preset(self):
        """Save current configuration as a preset."""
        # Get preset details from user
        dialog = QDialog(self)
        dialog.setWindowTitle("Save Configuration Preset")
        dialog.setMinimumSize(400, 200)
        
        layout = QVBoxLayout(dialog)
        
        # Form
        form_layout = QFormLayout()
        
        name_edit = QLineEdit(self.current_config.name)
        form_layout.addRow("Preset Name:", name_edit)
        
        desc_edit = QLineEdit(self.current_config.description)
        form_layout.addRow("Description:", desc_edit)
        
        tags_edit = QLineEdit("custom")
        tags_edit.setPlaceholderText("Comma-separated tags (optional)")
        form_layout.addRow("Tags:", tags_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Create preset
            tags = [tag.strip() for tag in tags_edit.text().split(',') if tag.strip()]
            
            preset = ConfigurationPreset(
                name=name_edit.text() or self.current_config.name,
                description=desc_edit.text() or self.current_config.description,
                config=self.current_config,
                created=datetime.now().isoformat(),
                tags=tags
            )
            
            # Add to preset manager
            self.preset_manager.presets.append(preset)
            self.preset_manager.save_presets()
            self.preset_manager.refresh_preset_list()
            
            QMessageBox.information(self, "Preset Saved",
                f"Configuration saved as preset '{preset.name}'")
                
    def reset_to_template(self):
        """Reset to the original template configuration."""
        # Use first test config as template
        template = next(iter(ALL_TEST_CONFIGS.values()))
        self.load_config(template)


# Standalone execution support
def main():
    """Test the configuration editor standalone."""
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    editor = ConfigEditor()
    editor.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
