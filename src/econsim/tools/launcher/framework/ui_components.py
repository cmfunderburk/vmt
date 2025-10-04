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
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox
)

from .test_configs import TestConfiguration


## NOTE: DebugPanel removed (GUI log viewer) – rely on JSONL / structured log files on disk.


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
            "🐌 1 turn/second",
            "🚶 3 turns/second", 
            "🏃 10 turns/second",
            "⚡ 20 turns/second",
            "🚀 Unlimited"
        ])
        self.speed_combo.setCurrentIndex(0)  # Default to 1 turn/second
        speed_layout.addWidget(self.speed_combo)
        layout.addLayout(speed_layout)
        
        # Current speed indicator
        self.speed_indicator = QLabel("⏱️  Speed: 1 turn/sec")
        self.speed_indicator.setStyleSheet("color: #4CAF50; font-weight: bold;")
        layout.addWidget(self.speed_indicator)
        
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
        
    def update_display(self, turn: int, phase: int, agent_count: int, resource_count: int, phase_manager=None, turn_rate: float = 0.0):
        """Update all status displays."""
        self.turn_label.setText(f"Turn: {turn}")
        
        # Update speed indicator
        speed_index = self.speed_combo.currentIndex()
        if speed_index == 4 and turn_rate > 0:
            # Unlimited speed - show actual rate
            self.speed_indicator.setText(f"⏱️  Speed: {turn_rate:.0f} turns/sec")
        else:
            # Fixed speed - show nominal rate
            speed_names = ["1 turn/sec", "3 turns/sec", "10 turns/sec", "20 turns/sec", "UNLIMITED"]
            self.speed_indicator.setText(f"⏱️  Speed: {speed_names[speed_index]}")
        
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
            interval_ms = get_timer_interval(self.speed_combo.currentIndex())
            if interval_ms == 0:
                # Unlimited speed - don't show time estimate
                status = f"Running... {remaining} turns remaining (unlimited speed)"
            else:
                interval_s = interval_ms / 1000
                est_seconds = remaining * interval_s
                status = f"Running... {remaining} turns remaining (~{format_duration(est_seconds)})"
        else:
            status = "Test completed!"
        
        self.status_text.setText(status)


class PlaybackControlPanel(QWidget):
    """VCR-style playback controls for simulation playback."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Create playback control layout."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🎮 Playback Controls")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #4CAF50;")
        layout.addWidget(title)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        # Rewind button
        self.rewind_button = QPushButton("⏪ Rewind")
        self.rewind_button.setEnabled(False)
        self.rewind_button.setStyleSheet("QPushButton { padding: 8px 12px; }")
        button_layout.addWidget(self.rewind_button)
        
        # Play/Pause button
        self.play_button = QPushButton("▶️ Play")
        self.play_button.setEnabled(False)
        self.play_button.setStyleSheet("QPushButton { padding: 8px 12px; background-color: #4CAF50; color: white; font-weight: bold; }")
        button_layout.addWidget(self.play_button)
        
        # Fast Forward button
        self.fast_forward_button = QPushButton("⏩ Fast Forward")
        self.fast_forward_button.setEnabled(False)
        self.fast_forward_button.setStyleSheet("QPushButton { padding: 8px 12px; }")
        button_layout.addWidget(self.fast_forward_button)
        
        layout.addLayout(button_layout)
        
        # Speed control
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Playback Speed:"))
        
        self.speed_combo = QComboBox()
        self.speed_combo.addItems([
            "🐌 2 steps/sec",
            "🚶 8 steps/sec", 
            "🏃 20 steps/sec",
            "💨 Unlimited"
        ])
        self.speed_combo.setCurrentIndex(0)  # Default to 2 steps/sec
        speed_layout.addWidget(self.speed_combo)
        layout.addLayout(speed_layout)
        
        # Progress display
        self.progress_label = QLabel("Step: 0 / 0 (0%)")
        self.progress_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        layout.addWidget(self.progress_label)
        
        # Status display
        self.status_label = QLabel("Ready for playback")
        self.status_label.setStyleSheet("color: #888888;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        self.setFixedWidth(300)
    
    def update_progress(self, current_step: int, total_steps: int, is_playing: bool = False):
        """Update progress display."""
        progress = (current_step / total_steps * 100) if total_steps > 0 else 0
        self.progress_label.setText(f"Step: {current_step} / {total_steps} ({progress:.1f}%)")
        
        # Update status
        if is_playing:
            self.status_label.setText("🎬 Playing...")
            self.play_button.setText("⏸️ Pause")
        else:
            self.status_label.setText("⏸️ Paused")
            self.play_button.setText("▶️ Play")
    
    def set_enabled(self, enabled: bool):
        """Enable or disable all controls."""
        self.rewind_button.setEnabled(enabled)
        self.play_button.setEnabled(enabled)
        self.fast_forward_button.setEnabled(enabled)
        self.speed_combo.setEnabled(enabled)
    
    def set_playback_mode(self, is_playback: bool):
        """Set controls to playback mode (different from test mode)."""
        if is_playback:
            self.status_label.setText("🎮 Playback mode ready")
        else:
            self.status_label.setText("Ready for playback")


class TestLayout(QWidget):
    """Layout with pygame viewport, playback controls, and test controls."""

    def __init__(self, test_config: TestConfiguration):
        super().__init__()
        self.config = test_config
        self.setup_ui()

    def setup_ui(self):
        """Setup the complete UI layout."""
        # Main horizontal layout
        main_layout = QHBoxLayout()
        
        # Left side: pygame viewport and playback controls
        left_layout = QVBoxLayout()
        
        # Pygame viewport placeholder
        self.pygame_placeholder = QLabel("Pygame viewport will appear here when test starts")
        self.pygame_placeholder.setFixedSize(self.config.viewport_size, self.config.viewport_size)
        self.pygame_placeholder.setStyleSheet("border: 1px solid #555555; background: #2a2a2a; color: #ffffff;")
        left_layout.addWidget(self.pygame_placeholder)
        
        # Playback controls beneath pygame window
        self.playback_controls = PlaybackControlPanel()
        self.playback_controls.setVisible(False)  # Hidden until playback is ready
        left_layout.addWidget(self.playback_controls)
        
        main_layout.addLayout(left_layout)
        
        # Right side: test control panel
        self.control_panel = ControlPanel(self.config)
        main_layout.addWidget(self.control_panel)
        
        self.setLayout(main_layout)

    def replace_viewport(self, pygame_widget):
        """Replace placeholder with actual pygame widget."""
        # Replace the placeholder with the actual pygame widget
        layout = self.layout()
        left_layout = layout.itemAt(0).layout()  # Get the left VBoxLayout
        
        # Remove placeholder and add pygame widget
        left_layout.removeWidget(self.pygame_placeholder)
        self.pygame_placeholder.hide()
        
        left_layout.insertWidget(0, pygame_widget)  # Insert at position 0
        pygame_widget.show()
    
    def show_playback_controls(self):
        """Show the playback controls."""
        self.playback_controls.setVisible(True)
        self.playback_controls.set_enabled(True)
        self.playback_controls.set_playback_mode(True)
    
    def hide_playback_controls(self):
        """Hide the playback controls."""
        self.playback_controls.setVisible(False)