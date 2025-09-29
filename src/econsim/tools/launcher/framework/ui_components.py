"""
UI Components - Reusable interface elements for manual tests.

Extracts common UI patterns into composable components.
"""

import sys
import os
from pathlib import Path

# Add src to Python path  
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QComboBox
)
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont

from .test_configs import TestConfiguration


class DebugPanel(QWidget):
    """Reusable debug log display with live updating."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_update_timer()
        
    def setup_ui(self):
        """Create debug text display with proper formatting."""
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Debug Log"))
        
        self.debug_display = QTextEdit()
        self.debug_display.setReadOnly(True)
        self.debug_display.setMinimumWidth(300)
        self.debug_display.setMinimumHeight(600)
        self.debug_display.setStyleSheet(
            "QTextEdit { background:#1e1e1e; color:#ffffff; border:1px solid #555555; padding:2px; }"
        )
        self.debug_display.setFont(QFont("Courier", 8))
        layout.addWidget(self.debug_display)
        
        self.setLayout(layout)
        self.setFixedWidth(320)
        
    def setup_update_timer(self):
        """Setup 250ms update timer for log file monitoring."""
        self.debug_timer = QTimer()
        self.debug_timer.timeout.connect(self.update_debug_log)
        self.debug_timer.start(250)
        
    def update_debug_log(self):
        """Update debug log display with latest content from centralized log files."""
        try:
            from econsim.gui.debug_logger import get_gui_logger
            
            # Get the current log file path
            logger = get_gui_logger()
            log_path = logger.get_current_log_path()
            
            if log_path.exists():
                # Read the latest log content
                with open(log_path, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                
                # Update display if content has changed
                current_content = self.debug_display.toPlainText()
                if log_content != current_content:
                    self.debug_display.setPlainText(log_content)
                    
                    # Auto-scroll to bottom
                    cursor = self.debug_display.textCursor()
                    cursor.movePosition(cursor.MoveOperation.End)
                    self.debug_display.setTextCursor(cursor)
                    
        except Exception as e:
            # Don't spam errors, just silently fail for debug display
            pass


class ControlPanel(QWidget):
    """Standardized control panel with speed control and status display."""
    
    def __init__(self, test_config: TestConfiguration, parent=None):
        super().__init__(parent)
        self.config = test_config
        self.setup_ui()
        
    def setup_ui(self):
        """Create control panel layout."""
        layout = QVBoxLayout()
        
        # Test info
        layout.addWidget(QLabel(f"Manual Test {self.config.id}: {self.config.name}"))
        
        # Status labels
        self.turn_label = QLabel("Turn: 0")
        self.phase_label = QLabel("Phase: 1 (Both enabled)")
        self.agents_label = QLabel(f"Agents: {self.config.agent_count}")
        self.resources_label = QLabel("Resources: 0")
        
        layout.addWidget(self.turn_label)
        layout.addWidget(self.phase_label)
        layout.addWidget(self.agents_label)
        layout.addWidget(self.resources_label)
        
        # Speed control
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Test Speed:"))
        
        self.speed_combo = QComboBox()
        self.speed_combo.addItems([
            "1 turn/second",
            "3 turns/second", 
            "10 turns/second",
            "20 turns/second",
            "Unlimited"
        ])
        self.speed_combo.setCurrentIndex(0)  # Default to 1 turn/second
        speed_layout.addWidget(self.speed_combo)
        layout.addLayout(speed_layout)
        
        # Start button
        self.start_button = QPushButton("Start Test")
        layout.addWidget(self.start_button)
        
        # Status text
        from .test_utils import get_estimated_duration, format_duration
        initial_duration = get_estimated_duration(0)  # Default speed
        self.status_text = QLabel(f"Click 'Start Test' to begin the 900-turn test sequence (~{format_duration(initial_duration)}).")
        self.status_text.setWordWrap(True)
        layout.addWidget(self.status_text)
        
        self.setLayout(layout)
        self.setFixedWidth(350)
        
    def update_display(self, turn: int, phase: int, agent_count: int, resource_count: int, phase_manager=None):
        """Update all status displays."""
        self.turn_label.setText(f"Turn: {turn}")
        
        # Get phase description from phase manager if available
        if phase_manager and hasattr(phase_manager, 'get_phase_description'):
            phase_desc = phase_manager.get_phase_description(phase)
            phase_info = phase_manager.get_current_phase_info(turn)
            if phase_info:
                phase_desc = f"Phase {phase}: {phase_info.description}"
            else:
                phase_desc = f"Phase {phase}: Complete"
        else:
            # Fallback to hardcoded names for backward compatibility
            phase_names = {
                1: "Phase 1: Both enabled",
                2: "Phase 2: Foraging only", 
                3: "Phase 3: Exchange only",
                4: "Phase 4: Both disabled",
                5: "Phase 5: Both enabled",
                6: "Phase 6: Final disabled"
            }
            phase_desc = phase_names.get(phase, f"Phase {phase}")
        
        self.phase_label.setText(phase_desc)
        self.agents_label.setText(f"Agents: {agent_count}")
        self.resources_label.setText(f"Resources: {resource_count}")
        
        # Update status - get total turns from phase manager if available
        from .test_utils import get_estimated_duration, format_duration, get_timer_interval
        total_turns = 900  # Default fallback
        if phase_manager and hasattr(phase_manager, 'get_total_turns'):
            try:
                total_turns = phase_manager.get_total_turns()
            except:
                pass  # Use fallback
        
        if turn == 0:
            duration = get_estimated_duration(self.speed_combo.currentIndex(), total_turns)
            status = f"Ready to start {total_turns}-turn test (~{format_duration(duration)})..."
        elif turn < total_turns:
            remaining = total_turns - turn
            interval_s = get_timer_interval(self.speed_combo.currentIndex()) / 1000
            est_seconds = remaining * interval_s
            status = f"Running... {remaining} turns remaining (~{format_duration(est_seconds)})"
        else:
            status = "Test completed!"
        
        self.status_text.setText(status)


class TestLayout(QHBoxLayout):
    """Standard three-panel layout: debug + viewport + controls."""
    
    def __init__(self, test_config: TestConfiguration):
        super().__init__()
        self.config = test_config
        
        # Debug panel (left)
        self.debug_panel = DebugPanel()
        self.addWidget(self.debug_panel)
        
        # Pygame viewport (center) - placeholder initially
        self.pygame_placeholder = QLabel("Pygame viewport will appear here when test starts")
        self.pygame_placeholder.setFixedSize(test_config.viewport_size, test_config.viewport_size)
        self.pygame_placeholder.setStyleSheet("border: 1px solid #555555; background: #2a2a2a; color: #ffffff;")
        self.addWidget(self.pygame_placeholder)
        
        # Control panel (right)
        self.control_panel = ControlPanel(test_config)
        self.addWidget(self.control_panel)
        
    def replace_viewport(self, pygame_widget):
        """Replace placeholder with actual pygame widget."""
        self.replaceWidget(self.pygame_placeholder, pygame_widget)
        self.pygame_placeholder.hide()
        pygame_widget.show()