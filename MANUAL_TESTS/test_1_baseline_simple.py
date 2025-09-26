#!/usr/bin/env python3
"""
Manual Test 1: Baseline Unified Target Selection Test

This test validates unified target selection behavior across different phases
with a baseline configuration of mixed preferences.

Configuration:
- Grid: 30x30
- Agents: 20 with random positions and mixed preferences
- Resource density: 0.25
- Perception radius: 8
- Distance scaling: k=0.0 (default)

Phase Schedule (900 turns total, configurable speed):
1. Turns 1-200: Both foraging and exchange enabled
2. Turns 201-400: Only foraging enabled  
3. Turns 401-600: Only exchange enabled
4. Turns 601-650: Both disabled (agents should idle) - shortened phase
5. Turns 651-850: Both enabled again
6. Turns 851-900: Both disabled (final idle phase)
"""

import sys
import os
import random
import time

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox
from PyQt6.QtCore import QTimer, pyqtSignal
from test_utils import create_speed_control, get_timer_interval, get_estimated_duration, format_duration
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation

class Test1Window(QWidget):
    """Simple test window to observe the simulation."""
    
    def __init__(self):
        super().__init__()
        self.simulation = None
        self.ext_rng = random.Random(789)
        self.current_turn = 0
        self.phase = 1
        
        # Set up UI
        self.setWindowTitle("Manual Test 1: Baseline - Unified Target Selection")
        self.setGeometry(100, 100, 1000, 700)
        
        # Main layout
        main_layout = QHBoxLayout()
        
        # Left side: debug log panel
        debug_layout = QVBoxLayout()
        debug_layout.addWidget(QLabel("Debug Log"))
        
        from PyQt6.QtWidgets import QTextEdit
        from PyQt6.QtGui import QFont
        self.debug_display = QTextEdit()
        self.debug_display.setReadOnly(True)
        self.debug_display.setMinimumWidth(300)
        self.debug_display.setMinimumHeight(600)
        self.debug_display.setStyleSheet("QTextEdit { background:#f2f2f2; border:1px solid #ccc; padding:2px; }")
        self.debug_display.setFont(QFont("Courier", 8))
        debug_layout.addWidget(self.debug_display)
        
        debug_widget = QWidget()
        debug_widget.setLayout(debug_layout)
        debug_widget.setFixedWidth(320)
        main_layout.addWidget(debug_widget)
        
        # Center: pygame viewport (will be initialized with simulation later)
        self.pygame_widget = None  # Will be created with simulation
        self.pygame_placeholder = QLabel("Pygame viewport will appear here when test starts")
        self.pygame_placeholder.setFixedSize(600, 600)
        main_layout.addWidget(self.pygame_placeholder)
        
        # Right side: control panel
        control_layout = QVBoxLayout()
        
        # Status labels
        control_layout.addWidget(QLabel("Manual Test 1: Baseline"))
        self.turn_label = QLabel("Turn: 0")
        self.phase_label = QLabel("Phase: 1 (Both enabled)")
        self.agents_label = QLabel("Agents: 0")
        self.resources_label = QLabel("Resources: 0")
        
        control_layout.addWidget(self.turn_label)
        control_layout.addWidget(self.phase_label)
        control_layout.addWidget(self.agents_label)
        control_layout.addWidget(self.resources_label)
        
        # Speed control
        speed_layout, self.speed_combo = create_speed_control(self, self.on_speed_changed)
        control_layout.addLayout(speed_layout)
        
        # Control button
        self.start_button = QPushButton("Start Test")
        self.start_button.clicked.connect(self.start_test)
        control_layout.addWidget(self.start_button)
        
        # Status text - initial duration calculation
        initial_duration = get_estimated_duration(0)  # Default to index 0 (1 turn/second)
        self.status_text = QLabel(f"Click 'Start Test' to begin the 900-turn test sequence (~{format_duration(initial_duration)}).")
        self.status_text.setWordWrap(True)
        control_layout.addWidget(self.status_text)
        
        # Add control panel to main layout
        control_widget = QWidget()
        control_widget.setLayout(control_layout)
        control_widget.setFixedWidth(350)
        main_layout.addWidget(control_widget)
        
        self.setLayout(main_layout)
        
        # Timer for simulation steps
        self.step_timer = QTimer()
        self.step_timer.timeout.connect(self.simulation_step)
        
        # Timer for debug log updates
        self.debug_timer = QTimer()
        self.debug_timer.timeout.connect(self.update_debug_log)
        self.debug_timer.start(250)  # Update every 250ms
        
        print("Test 1 Window created. Configuration:")
        print("- Grid: 30x30")
        print("- Agents: 20 with mixed preferences") 
        print("- Resource density: 0.25")
        print("- Perception radius: 8")
        print("- Total turns: 900")
        print("- Phase transitions at: 201, 401, 601, 651, 851")
    
    def create_preference_factory(self):
        """Create preference factory for mixed preferences."""
        preferences = ['cobb_douglas', 'leontief', 'perfect_substitutes']
        pref_rng = random.Random(9999)
        
        def preference_factory(idx: int):
            chosen_type = pref_rng.choice(preferences)
            if chosen_type == 'cobb_douglas':
                from econsim.preferences.cobb_douglas import CobbDouglasPreference
                alpha = pref_rng.uniform(0.2, 0.8)
                return CobbDouglasPreference(alpha=alpha)
            elif chosen_type == 'perfect_substitutes':
                from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference
                return PerfectSubstitutesPreference(a=1.0, b=1.0)
            elif chosen_type == 'leontief':
                from econsim.preferences.leontief import LeontiefPreference
                return LeontiefPreference(a=1.0, b=1.0)
        
        return preference_factory
    
    def on_speed_changed(self):
        """Handle speed selection change."""
        if hasattr(self, 'step_timer') and self.step_timer.isActive():
            # Update running timer
            self.step_timer.setInterval(get_timer_interval(self.speed_combo.currentIndex()))
        
        # Update status text
        if self.current_turn == 0:
            duration = get_estimated_duration(self.speed_combo.currentIndex())
            self.status_text.setText(f"Click 'Start Test' to begin the 1050-turn test sequence (~{format_duration(duration)}).")
        else:
            self.update_display()
    
    def start_test(self):
        """Initialize and start the test simulation."""
        try:
            # Enable comprehensive debug logging
            os.environ['ECONSIM_DEBUG_AGENT_MODES'] = '1'
            os.environ['ECONSIM_DEBUG_TRADES'] = '1'
            os.environ['ECONSIM_DEBUG_SIMULATION'] = '1'
            os.environ['ECONSIM_DEBUG_PHASES'] = '1'
            os.environ['ECONSIM_DEBUG_DECISIONS'] = '1'
            os.environ['ECONSIM_DEBUG_RESOURCES'] = '1'
            
            # Set initial environment for Phase 1
            os.environ['ECONSIM_FORAGE_ENABLED'] = '1'
            os.environ['ECONSIM_TRADE_DRAFT'] = '1'
            os.environ['ECONSIM_TRADE_EXEC'] = '1'
            os.environ['ECONSIM_UNIFIED_SELECTION_ENABLE'] = '1'
            
            # Create simulation config
            grid_w, grid_h = 30, 30
            resource_count = int(grid_w * grid_h * 0.25)  # 0.25 density
            
            # Generate resources
            resource_rng = random.Random(12345)
            resources = []
            for _ in range(resource_count):
                x = resource_rng.randint(0, grid_w - 1)
                y = resource_rng.randint(0, grid_h - 1)
                resource_type = resource_rng.choice(['A', 'B'])
                resources.append((x, y, resource_type))
            
            config = SimConfig(
                grid_size=(grid_w, grid_h),
                initial_resources=resources,
                seed=12345,
                enable_respawn=True,
                enable_metrics=True,
                perception_radius=8,
                respawn_target_density=0.25,
                respawn_rate=0.25,
                distance_scaling_factor=0.0
            )
            
            # Create agent positions
            agent_positions = []
            pos_rng = random.Random(54321)
            positions = set()
            while len(positions) < 20:
                x = pos_rng.randint(0, grid_w - 1)
                y = pos_rng.randint(0, grid_h - 1)
                positions.add((x, y))
            agent_positions = list(positions)
            
            # Create simulation
            preference_factory = self.create_preference_factory()
            self.simulation = Simulation.from_config(config, preference_factory, agent_positions=agent_positions)
            
            # Create pygame widget with simulation and replace placeholder
            from econsim.gui.embedded_pygame import EmbeddedPygameWidget
            self.pygame_widget = EmbeddedPygameWidget(simulation=self.simulation)
            self.pygame_widget.setFixedSize(600, 600)
            
            # Replace placeholder with actual pygame widget
            layout = self.layout()
            layout.replaceWidget(self.pygame_placeholder, self.pygame_widget)
            self.pygame_placeholder.hide()
            self.pygame_widget.show()
            
            # Reset counters
            self.current_turn = 0
            self.phase = 1
            
            # Update UI
            self.start_button.setText("Test Running...")
            self.start_button.setEnabled(False)
            self.update_display()
            
            # Start timer with selected speed
            self.step_timer.start(get_timer_interval(self.speed_combo.currentIndex()))
            
            print(f"✅ Test started! Simulation created with {len(self.simulation.agents)} agents")
            print("Phase 1: Both foraging and exchange enabled (turns 1-200)")
            print("🎮 Watch the pygame viewport to observe agent behavior!")
            
        except Exception as e:
            print(f"❌ Error starting test: {e}")
            import traceback
            traceback.print_exc()
    
    def simulation_step(self):
        """Execute one simulation step and handle phase transitions."""
        if not self.simulation:
            return
            
        # Increment turn counter
        self.current_turn += 1
        
        # Check for phase transitions
        self.check_phase_transition()
        
        # Execute simulation step
        self.simulation.step(self.ext_rng, use_decision=True)
        
        # Update display
        self.update_display()
        
        # Log periodic status and progress every 50 turns
        if self.current_turn % 50 == 0:
            agent_count = len(self.simulation.agents)
            resource_count = len(list(self.simulation.grid.iter_resources()))
            status_msg = f"Turn {self.current_turn}: Phase {self.phase}, {agent_count} agents, {resource_count} resources"
            from econsim.gui.debug_logger import log_comprehensive
            log_comprehensive(f"PERIODIC STATUS: {status_msg}", self.current_turn)
        
        # Stop at turn 900
        if self.current_turn >= 900:
            self.step_timer.stop()
            self.start_button.setText("Test Completed!")
            self.status_text.setText("🎉 Test completed! All 900 turns executed with phase transitions.")
            print("=" * 60)
            print("🎉 TEST COMPLETED SUCCESSFULLY!")
            print("All phases executed. Check the behavior observations above.")
            print("=" * 60)
    
    def check_phase_transition(self):
        """Check if we need to transition to a new phase."""
        from econsim.gui.debug_logger import log_phase_transition, log_comprehensive
        new_phase = None
        
        if self.current_turn == 201 and self.phase == 1:
            # Phase 2: Only foraging
            os.environ['ECONSIM_FORAGE_ENABLED'] = '1'
            os.environ['ECONSIM_TRADE_DRAFT'] = '0'
            os.environ['ECONSIM_TRADE_EXEC'] = '0'
            new_phase = 2
            phase_desc = "Only foraging enabled (turns 201-400)"
            log_phase_transition(2, self.current_turn, phase_desc)
            log_comprehensive(f"PHASE TRANSITION: {self.phase} -> 2 at turn {self.current_turn}", self.current_turn)
            
        elif self.current_turn == 401 and self.phase == 2:
            # Phase 3: Only exchange
            os.environ['ECONSIM_FORAGE_ENABLED'] = '0'
            os.environ['ECONSIM_TRADE_DRAFT'] = '1'
            os.environ['ECONSIM_TRADE_EXEC'] = '1'
            new_phase = 3
            phase_desc = "Only exchange enabled (turns 401-600)"
            log_phase_transition(3, self.current_turn, phase_desc)
            log_comprehensive(f"PHASE TRANSITION: {self.phase} -> 3 at turn {self.current_turn}", self.current_turn)
            
        elif self.current_turn == 601 and self.phase == 3:
            # Phase 4: Both disabled (shortened to 50 turns)
            os.environ['ECONSIM_FORAGE_ENABLED'] = '0'
            os.environ['ECONSIM_TRADE_DRAFT'] = '0'
            os.environ['ECONSIM_TRADE_EXEC'] = '0'
            new_phase = 4
            phase_desc = "Both disabled - agents should idle (turns 601-650)"
            log_phase_transition(4, self.current_turn, phase_desc)
            log_comprehensive(f"PHASE TRANSITION: {self.phase} -> 4 at turn {self.current_turn}", self.current_turn)
            
        elif self.current_turn == 651 and self.phase == 4:
            # Phase 5: Both enabled again
            os.environ['ECONSIM_FORAGE_ENABLED'] = '1'
            os.environ['ECONSIM_TRADE_DRAFT'] = '1'
            os.environ['ECONSIM_TRADE_EXEC'] = '1'
            new_phase = 5
            phase_desc = "Both enabled again (turns 651-850)"
            log_phase_transition(5, self.current_turn, phase_desc)
            log_comprehensive(f"PHASE TRANSITION: {self.phase} -> 5 at turn {self.current_turn}", self.current_turn)
            
        elif self.current_turn == 851 and self.phase == 5:
            # Phase 6: Final disabled
            os.environ['ECONSIM_FORAGE_ENABLED'] = '0'
            os.environ['ECONSIM_TRADE_DRAFT'] = '0'
            os.environ['ECONSIM_TRADE_EXEC'] = '0'
            new_phase = 6
            phase_desc = "Final disabled phase (turns 851-900)"
            log_phase_transition(6, self.current_turn, phase_desc)
            log_comprehensive(f"PHASE TRANSITION: {self.phase} -> 6 at turn {self.current_turn}", self.current_turn)
        
        if new_phase:
            self.phase = new_phase
    
    def update_display(self):
        """Update the UI display with current simulation state."""
        if not self.simulation:
            return
            
        agent_count = len(self.simulation.agents)
        resource_count = len(list(self.simulation.grid.iter_resources()))
        
        self.turn_label.setText(f"Turn: {self.current_turn}")
        
        phase_names = {
            1: "Phase 1: Both enabled",
            2: "Phase 2: Foraging only", 
            3: "Phase 3: Exchange only",
            4: "Phase 4: Both disabled",
            5: "Phase 5: Both enabled",
            6: "Phase 6: Final disabled"
        }
        self.phase_label.setText(phase_names.get(self.phase, f"Phase {self.phase}"))
        
        self.agents_label.setText(f"Agents: {agent_count}")
        self.resources_label.setText(f"Resources: {resource_count}")
        
        # Update status
        if self.current_turn == 0:
            duration = get_estimated_duration(self.speed_combo.currentIndex())
            status = f"Ready to start test (~{format_duration(duration)})..."
        elif self.current_turn < 900:
            remaining = 900 - self.current_turn
            interval_s = get_timer_interval(self.speed_combo.currentIndex()) / 1000
            est_seconds = remaining * interval_s
            status = f"Running... {remaining} turns remaining (~{format_duration(est_seconds)})"
        else:
            status = "Test completed!"
        
        self.status_text.setText(status)
    
    def update_debug_log(self):
        """Update the debug log display with content from centralized log files."""
        try:
            # Import is already done at the top level, so we can use it directly
            from econsim.gui.debug_logger import get_gui_logger
            from pathlib import Path
            
            # Get the current log file path
            logger = get_gui_logger()
            log_path = logger.get_current_log_path()
            
            if log_path.exists():
                # Read the latest log content
                with open(log_path, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                
                # Split into lines and take the last N entries (skip header)
                lines = log_content.split('\n')
                # Skip the header lines (first 4 lines: title, timestamp, separator, blank line)
                content_lines = [line for line in lines[4:] if line.strip()]
                
                # Keep only the most recent entries (last 50)
                if len(content_lines) > 50:
                    content_lines = content_lines[-50:]
                
                # Update the debug display with the log file content
                debug_text = '\n'.join(content_lines)
                self.debug_display.setPlainText(debug_text)
                
                # Auto-scroll to bottom to show latest entries
                cursor = self.debug_display.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                self.debug_display.setTextCursor(cursor)
                self.debug_display.ensureCursorVisible()
                
        except Exception:
            # Silent fallback - don't disrupt the test with debug log errors
            pass

def main():
    """Run the baseline test."""
    app = QApplication(sys.argv)
    
    test_window = Test1Window()
    test_window.show()
    
    print("=" * 60)
    print("MANUAL TEST 1: BASELINE UNIFIED TARGET SELECTION")
    print("=" * 60)
    print("This test will run 900 simulation turns with phase transitions.")
    print("Speed is configurable via dropdown (default: 1 turn/second).")
    print("Watch the console output for phase transition announcements.")
    print("=" * 60)
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()