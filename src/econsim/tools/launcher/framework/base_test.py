"""
Base Test Framework - Abstract base classes for manual tests.

Provides common functionality extracted from existing tests.
"""

import sys
import os
import random

# Add src to Python path  
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))

from PyQt6.QtWidgets import QWidget, QHBoxLayout
from PyQt6.QtCore import QTimer

from .test_configs import TestConfiguration
from .ui_components import TestLayout
from .debug_orchestrator import DebugOrchestrator
from .phase_manager import PhaseManager
from .simulation_factory import SimulationFactory


class BaseManualTest(QWidget):
    """Abstract base class for all manual tests with common functionality."""
    
    def __init__(self, config: TestConfiguration):
        super().__init__()
        self.config = config
        self.simulation = None
        self.current_turn = 0
        self.phase = 1
        self.ext_rng = random.Random(789)  # External RNG for legacy compatibility
        
        # Setup common components
        self.setup_ui()
        self.setup_debug_orchestrator() 
        self.setup_timers()
        
        # Store batch mode flag for use in showEvent
        import os
        self.batch_mode = os.environ.get('ECONSIM_BATCH_UNLIMITED_SPEED') == '1'
        if self.batch_mode:
            print("🚀 Batch mode detected - Will auto-start after GUI is shown")
        
    def setup_ui(self):
        """Create standardized three-panel layout."""
        self.setWindowTitle(f"Manual Test {self.config.id}: {self.config.name}")
        self.setGeometry(100, 100, 1200, 700)
        
        # Create main layout using TestLayout component
        self.test_layout = TestLayout(self.config)
        self.setLayout(self.test_layout)
        
        # Connect control panel signals
        self.test_layout.control_panel.start_button.clicked.connect(self.start_test)
        self.test_layout.control_panel.speed_combo.currentIndexChanged.connect(self.on_speed_changed)
        
    def setup_debug_orchestrator(self):
        """Configure debug logging for this test."""
        self.debug_orchestrator = DebugOrchestrator(self.config)
        
    def setup_timers(self):
        """Setup simulation and debug update timers."""
        # Timer for simulation steps
        self.step_timer = QTimer()
        self.step_timer.timeout.connect(self.simulation_step)
        
        # Debug timer is handled by the debug panel
        
    def showEvent(self, event):
        """Override showEvent to auto-start in batch mode after GUI is visible."""
        super().showEvent(event)
        
        # Auto-start if in batch mode and not already started
        if self.batch_mode and not hasattr(self, '_auto_start_attempted'):
            self._auto_start_attempted = True
            print("🚀 GUI is now visible - Auto-starting test in batch mode...")
            # Use QTimer to allow the GUI to fully render
            from PyQt6.QtCore import QTimer
            self.auto_start_timer = QTimer(self)  # Store as instance variable with parent
            self.auto_start_timer.setSingleShot(True)
            self.auto_start_timer.timeout.connect(self.auto_start_test)
            self.auto_start_timer.start(1000)  # Start after 1 second
            print("🔧 Auto-start timer created and started")
    
    def auto_start_test(self):
        """Auto-start the test in batch mode by calling start_test directly."""
        print("🚀 Auto-starting test in batch mode...")
        try:
            # Check if the UI is properly set up
            if hasattr(self, 'test_layout') and hasattr(self.test_layout, 'control_panel'):
                button = self.test_layout.control_panel.start_button
                print(f"🔧 Button state: enabled={button.isEnabled()}, text='{button.text()}'")
                
                # Ensure button is enabled before starting
                if not button.isEnabled():
                    button.setEnabled(True)
                    print("🔧 Enabled start button for auto-start")
                
                # Call start_test method directly
                self.start_test()
                print("✅ Auto-start test initiated successfully")
            else:
                print("❌ Auto-start failed - UI components not ready")
        except Exception as e:
            print(f"❌ Auto-start failed with error: {e}")
            import traceback
            traceback.print_exc()
        
    def start_test(self):
        """Initialize and start the test simulation."""
        try:
            # Create simulation using factory
            self.simulation = SimulationFactory.create_simulation(self.config)
            
            # Create pygame widget and replace placeholder
            from econsim.gui.embedded_pygame import EmbeddedPygameWidget
            self.pygame_widget = EmbeddedPygameWidget(simulation=self.simulation)
            self.pygame_widget.setFixedSize(self.config.viewport_size, self.config.viewport_size)
            
            # Replace placeholder in layout
            self.test_layout.replace_viewport(self.pygame_widget)
            
            # Reset counters
            self.current_turn = 0
            self.phase = 1
            
            # Update UI
            self.test_layout.control_panel.start_button.setText("Test Running...")
            self.test_layout.control_panel.start_button.setEnabled(False)
            self.update_display()
            
            # Start timer with selected speed (or unlimited if in batch mode)
            from .test_utils import get_timer_interval
            import os
            
            # Check if running in batch mode with unlimited speed
            if os.environ.get('ECONSIM_BATCH_UNLIMITED_SPEED') == '1':
                # Force unlimited speed for batch processing
                speed_index = 4  # Unlimited speed index
                self.test_layout.control_panel.speed_combo.setCurrentIndex(4)
                print("🚀 Batch mode detected - running at unlimited speed for efficiency")
            else:
                speed_index = self.test_layout.control_panel.speed_combo.currentIndex()
            
            self.step_timer.start(get_timer_interval(speed_index))
            
            print(f"✅ Test {self.config.id} started! Simulation created with {len(self.simulation.agents)} agents")
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
        
        # Check for phase transitions (implemented by subclasses)
        self.check_phase_transition()
        
        # Execute simulation step
        self.simulation.step(self.ext_rng, use_decision=True)
        
        # Update display
        self.update_display()
        
        # Log periodic status and economic metrics
        if self.current_turn % 50 == 0:
            print(f"DEBUG: Periodic logging triggered at turn {self.current_turn}")
            agent_count = len(self.simulation.agents)
            resource_count = len(list(self.simulation.grid.iter_resources()))
            
            # Calculate performance metrics like the main simulation does
            steps_per_sec = 60.0  # Default fallback
            frame_ms = 16.7  # Default fallback
            
            if hasattr(self.simulation, '_step_times') and len(self.simulation._step_times) >= 2:
                time_window = self.simulation._step_times[-1] - self.simulation._step_times[0]
                if time_window > 0:
                    steps_per_sec = (len(self.simulation._step_times) - 1) / time_window
                    frame_ms = (time_window / (len(self.simulation._step_times) - 1)) * 1000
            
            from econsim.gui.debug_logger import log_periodic_summary, log_economics
            log_periodic_summary(steps_per_sec, frame_ms, agent_count, resource_count, self.phase, self.current_turn)
            print(f"DEBUG: log_periodic_summary called successfully")
            
            # Resource flow analysis
            resource_by_type = {"good1": 0, "good2": 0}
            for resource in self.simulation.grid.iter_resources():
                _, _, res_type = resource
                resource_by_type[str(res_type)] = resource_by_type.get(str(res_type), 0) + 1
            
            # Agent inventory analysis
            total_carrying = {"good1": 0, "good2": 0}
            total_home_inventory = {"good1": 0, "good2": 0}
            for agent in self.simulation.agents:
                for res_type, count in agent.carrying.items():
                    total_carrying[res_type] = total_carrying.get(res_type, 0) + count
                for res_type, count in agent.home_inventory.items():
                    total_home_inventory[res_type] = total_home_inventory.get(res_type, 0) + count
            
            print(f"DEBUG: About to call log_economics")
            log_economics(f"Resource distribution - Grid: good1={resource_by_type['good1']}, good2={resource_by_type['good2']} | Carrying: good1={total_carrying['good1']}, good2={total_carrying['good2']} | Home: good1={total_home_inventory['good1']}, good2={total_home_inventory['good2']}", self.current_turn)
            print(f"DEBUG: log_economics called successfully")
            
            # Spatial analytics
            from econsim.gui.debug_logger import log_spatial
            agent_positions = [(agent.x, agent.y) for agent in self.simulation.agents]
            
            # Calculate center of mass
            if agent_positions:
                center_x = sum(pos[0] for pos in agent_positions) / len(agent_positions)
                center_y = sum(pos[1] for pos in agent_positions) / len(agent_positions)
                
                # Calculate average distance from center (clustering metric)
                total_distance = sum(((pos[0] - center_x)**2 + (pos[1] - center_y)**2)**0.5 for pos in agent_positions)
                avg_distance_from_center = total_distance / len(agent_positions)
                
                # Calculate average inter-agent distance (sample first 5 agents for performance)
                sample_agents = self.simulation.agents[:min(5, len(self.simulation.agents))]
                inter_distances = []
                for i, agent1 in enumerate(sample_agents):
                    for agent2 in sample_agents[i+1:]:
                        dist = ((agent1.x - agent2.x)**2 + (agent1.y - agent2.y)**2)**0.5
                        inter_distances.append(dist)
                
                avg_inter_distance = sum(inter_distances) / len(inter_distances) if inter_distances else 0
                
                print(f"DEBUG: About to call log_spatial")
                log_spatial(f"Agent clustering - Center: ({center_x:.1f}, {center_y:.1f}) | Avg distance from center: {avg_distance_from_center:.1f} | Avg inter-agent distance: {avg_inter_distance:.1f}", self.current_turn)
                print(f"DEBUG: log_spatial called successfully")        # Stop at turn 900
        if self.current_turn >= 900:
            self.step_timer.stop()
            
            # Finalize debug logging to prevent noise during cleanup
            try:
                from econsim.gui.debug_logger import finalize_log_session
                finalize_log_session()
                print("🔧 Debug logging session finalized")
            except Exception as e:
                print(f"⚠️  Could not finalize debug logging: {e}")
            
            self.test_layout.control_panel.start_button.setText("Test Completed!")
            self.test_layout.control_panel.status_text.setText("🎉 Test completed! All 900 turns executed with phase transitions.")
            print("=" * 60)
            print("🎉 TEST COMPLETED SUCCESSFULLY!")
            print("All phases executed. Check the behavior observations above.")
            print("=" * 60)
            
            # Auto-exit if running in batch mode
            import os
            if os.environ.get('ECONSIM_BATCH_UNLIMITED_SPEED') == '1':
                print("🚀 Batch mode - Auto-exiting after completion")
                # Use QTimer to allow GUI to finish processing before exit
                from PyQt6.QtCore import QTimer
                self.exit_timer = QTimer(self)  # Store as instance variable with parent
                self.exit_timer.setSingleShot(True)
                self.exit_timer.timeout.connect(self.batch_mode_exit)
                self.exit_timer.start(3000)  # Exit after 3 second delay
                print("🔧 Auto-exit timer created and started")
    
    def batch_mode_exit(self):
        """Exit the application when in batch mode."""
        print("🚀 Batch mode - Exiting application NOW")
        print("🔧 Closing window...")
        self.close()
        
        print("🔧 Quitting QApplication...")
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.quit()
            print("🔧 QApplication quit() called")
        else:
            print("⚠️  No QApplication instance found")
        
        print("🔧 Calling sys.exit(0)...")
        import sys
        sys.exit(0)
        
    def check_phase_transition(self):
        """Check if we need to transition to a new phase. Override in subclasses."""
        pass
        
    def update_display(self):
        """Update the UI display with current simulation state."""
        if not self.simulation:
            return
            
        agent_count = len(self.simulation.agents)
        resource_count = len(list(self.simulation.grid.iter_resources()))
        
        # Update control panel
        self.test_layout.control_panel.update_display(
            turn=self.current_turn,
            phase=self.phase,
            agent_count=agent_count,
            resource_count=resource_count,
            phase_manager=getattr(self, 'phase_manager', None)
        )
        
    def on_speed_changed(self, index):
        """Handle speed selection change."""
        if hasattr(self, 'step_timer') and self.step_timer.isActive():
            # Update running timer
            from .test_utils import get_timer_interval
            self.step_timer.setInterval(get_timer_interval(index))
        
        # Update status display
        self.update_display()


class StandardPhaseTest(BaseManualTest):
    """Standard 6-phase test with common phase transitions."""
    
    def __init__(self, config: TestConfiguration):
        super().__init__(config)
        # Use custom phases if provided, otherwise use standard phases
        if config.custom_phases:
            self.phase_manager = PhaseManager(config.custom_phases)
        else:
            self.phase_manager = PhaseManager.create_standard_phases()
        
    def check_phase_transition(self):
        """Check for phase transitions."""
        transition = self.phase_manager.check_transition(self.current_turn, self.phase)
        if transition:
            self.phase = transition.new_phase


class CustomPhaseTest(BaseManualTest): 
    """For tests with custom phase schedules."""
    
    def __init__(self, config: TestConfiguration):
        super().__init__(config)
        # Custom phases are required for this test type
        if not config.custom_phases:
            raise ValueError("CustomPhaseTest requires custom_phases in TestConfiguration")
        self.phase_manager = PhaseManager(config.custom_phases)
        
    def check_phase_transition(self):
        """Check for custom phase transitions."""
        transition = self.phase_manager.check_transition(self.current_turn, self.phase)
        if transition:
            self.phase = transition.new_phase