#!/usr/bin/env python3
"""
Manual Test 6: Pure Leontief Unified Target Selection Test

This test validates unified target selection behavior with agents that all
have Leontief preferences, focusing on complementary resource requirements.

Configuration:
- Grid: 25x25
- Agents: 25 with random positions and all Leontief preferences
- Resource density: 0.4 (moderate density)
- Perception radius: 6 (moderate awareness)
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

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QTextEdit
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
from econsim.gui.embedded_pygame import EmbeddedPygameWidget
from test_utils import create_speed_control, get_timer_interval, get_estimated_duration, format_duration

class Test6Window(QWidget):
    """Test window with pygame viewport for observing the simulation."""
    
    def __init__(self):
        super().__init__()
        self.simulation = None
        self.ext_rng = random.Random(1414)
        self.current_turn = 0
        self.phase = 1
        
        # Set up UI
        self.setWindowTitle("Manual Test 6: Pure Leontief - Unified Target Selection")
        self.setGeometry(100, 100, 1000, 700)
        
        # Main layout
        main_layout = QHBoxLayout()
        
        # Left side: debug display
        self.debug_display = QTextEdit()
        self.debug_display.setReadOnly(True)
        self.debug_display.setMaximumWidth(300)
        self.debug_display.setFont(QFont("Consolas", 9))
        main_layout.addWidget(self.debug_display)
        
        # Middle: pygame viewport (will be initialized with simulation later)
        self.pygame_widget = None  # Will be created with simulation
        self.pygame_placeholder = QLabel("Pygame viewport will appear here when test starts")
        self.pygame_placeholder.setFixedSize(600, 600)
        main_layout.addWidget(self.pygame_placeholder)
        
        # Right side: control panel
        control_layout = QVBoxLayout()
        
        # Status labels
        control_layout.addWidget(QLabel("Manual Test 6: Pure Leontief"))
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
        
        # Status text  
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
        self.debug_timer.start(250)
        
        print("Test 6 Window created. Configuration:")
        print("- Grid: 25x25")
        print("- Agents: 25 with ALL Leontief preferences") 
        print("- Resource density: 0.4 (moderate)")
        print("- Perception radius: 6 (moderate)")
        print("- Total turns: 900")
        print("- Phase transitions at: 201, 401, 601, 651, 851")
    
    def create_preference_factory(self):
        """Create preference factory for pure Leontief preferences."""
        pref_rng = random.Random(16666)
        
        def preference_factory(idx: int):
            # All agents have Leontief preferences with varied coefficients
            from econsim.preferences.leontief import LeontiefPreference
            a = pref_rng.uniform(0.5, 2.0)  # Vary a coefficient
            b = pref_rng.uniform(0.5, 2.0)  # Vary b coefficient
            return LeontiefPreference(a=a, b=b)
        
        return preference_factory
    
    def update_debug_log(self):
        """Update debug log display with latest content from log files."""
        gui_logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gui_logs")
        
        if not os.path.exists(gui_logs_dir):
            return
        
        log_files = [f for f in os.listdir(gui_logs_dir) if f.endswith('.log')]
        if not log_files:
            return
        
        # Get the most recent log file
        latest_file = max(log_files, key=lambda f: os.path.getctime(os.path.join(gui_logs_dir, f)))
        log_path = os.path.join(gui_logs_dir, latest_file)
        
        try:
            with open(log_path, 'r') as f:
                content = f.read()
            
            # Update display and auto-scroll to bottom
            self.debug_display.setPlainText(content)
            cursor = self.debug_display.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.debug_display.setTextCursor(cursor)
        except (FileNotFoundError, OSError):
            pass  # Silently ignore file access issues
    
    def on_speed_changed(self):
        """Handle speed selection change."""
        if hasattr(self, 'step_timer') and self.step_timer.isActive():
            # Update running timer
            self.step_timer.setInterval(get_timer_interval(self.speed_combo.currentIndex()))
        
        # Update status text
        if self.current_turn == 0:
            duration = get_estimated_duration(self.speed_combo.currentIndex())
            self.status_text.setText(f"Click 'Start Test' to begin the 900-turn test sequence (~{format_duration(duration)}).")
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
            
            # Create simulation config - moderate grid with Leontief agents
            grid_w, grid_h = 25, 25
            resource_count = int(grid_w * grid_h * 0.4)  # 0.4 density = moderate
            
            # Generate resources
            resource_rng = random.Random(66666)
            resources = []
            for _ in range(resource_count):
                x = resource_rng.randint(0, grid_w - 1)
                y = resource_rng.randint(0, grid_h - 1)
                resource_type = resource_rng.choice(['A', 'B'])
                resources.append((x, y, resource_type))
            
            config = SimConfig(
                grid_size=(grid_w, grid_h),
                initial_resources=resources,
                seed=66666,
                enable_respawn=True,
                enable_metrics=True,
                perception_radius=6,  # Moderate perception
                respawn_target_density=0.4,
                respawn_rate=0.2,
                distance_scaling_factor=0.0,
                viewport_size=600
            )
            
            # Create agent positions (moderate distribution)
            agent_positions = []
            pos_rng = random.Random(77777)
            positions = set()
            while len(positions) < 25:  # 25 agents in 25x25 grid = moderate density
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
            print("🎮 Watch the pygame viewport to observe Leontief behavior!")
            print("💡 Pure Leontief = complementary resources, min(a*A, b*B) utility")
            
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
        
        # Status logging handled by centralized debug logger
        
        # Stop at turn 900
        if self.current_turn >= 900:
            self.step_timer.stop()
            self.start_button.setText("Test Completed!")
            self.status_text.setText("🎉 Test completed! All 900 turns executed with phase transitions.")
            print("=" * 60)
            print("🎉 TEST 6 COMPLETED SUCCESSFULLY!")
            print("Pure Leontief behavior validated. Check observations above.")
            print("=" * 60)
    
    def check_phase_transition(self):
        """Check if we need to transition to a new phase."""
        new_phase = None
        
        if self.current_turn == 201 and self.phase == 1:
            # Phase 2: Only foraging
            os.environ['ECONSIM_FORAGE_ENABLED'] = '1'
            os.environ['ECONSIM_TRADE_DRAFT'] = '0'
            os.environ['ECONSIM_TRADE_EXEC'] = '0'
            new_phase = 2
            print("\n📋 Phase 2: Only foraging enabled (turns 201-400)")
            print("   Expected: Complementary resource seeking, balanced A/B needs")
            
        elif self.current_turn == 401 and self.phase == 2:
            # Phase 3: Only exchange
            os.environ['ECONSIM_FORAGE_ENABLED'] = '0'
            os.environ['ECONSIM_TRADE_DRAFT'] = '1'
            os.environ['ECONSIM_TRADE_EXEC'] = '1'
            new_phase = 3
            print("\n🔄 Phase 3: Only exchange enabled (turns 401-600)")
            print("   Expected: Strategic trades to balance A/B ratios, min() optimization")
            
        elif self.current_turn == 601 and self.phase == 3:
            # Phase 4: Both disabled (shortened to 50 turns)
            os.environ['ECONSIM_FORAGE_ENABLED'] = '0'
            os.environ['ECONSIM_TRADE_DRAFT'] = '0'
            os.environ['ECONSIM_TRADE_EXEC'] = '0'
            new_phase = 4
            print("\n⏸️  Phase 4: Both disabled - agents should idle (turns 601-650)")
            print("   Expected: Return home with Leontief agents preserving inventory")
            
        elif self.current_turn == 651 and self.phase == 4:
            # Phase 5: Both enabled again
            os.environ['ECONSIM_FORAGE_ENABLED'] = '1'
            os.environ['ECONSIM_TRADE_DRAFT'] = '1'
            os.environ['ECONSIM_TRADE_EXEC'] = '1'
            new_phase = 5
            print("\n🔄 Phase 5: Both enabled again (turns 651-850)")
            print("   Expected: Resume complementary resource optimization")
            
        elif self.current_turn == 851 and self.phase == 5:
            # Phase 6: Final disabled
            os.environ['ECONSIM_FORAGE_ENABLED'] = '0'
            os.environ['ECONSIM_TRADE_DRAFT'] = '0'
            os.environ['ECONSIM_TRADE_EXEC'] = '0'
            new_phase = 6
            print("\n⏹️  Phase 6: Final disabled phase (turns 851-900)")
        
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

    
    def closeEvent(self, event):
        """Clean up timers on close."""
        if hasattr(self, 'debug_timer'):
            self.debug_timer.stop()
        if hasattr(self, 'step_timer'):
            self.step_timer.stop()
        super().closeEvent(event)

def main():
    """Run the pure Leontief test."""
    app = QApplication(sys.argv)
    
    test_window = Test6Window()
    test_window.show()
    
    print("=" * 60)
    print("MANUAL TEST 6: PURE LEONTIEF UNIFIED TARGET SELECTION")
    print("=" * 60)
    print("This test will run 900 simulation turns with phase transitions.")
    print("Speed is configurable via dropdown (default: 1 turn/second).")
    print("Watch the pygame viewport AND console output for Leontief behavior.")
    print("Focus: Complementary resources, min() utility, strategic balancing")
    print("=" * 60)
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()