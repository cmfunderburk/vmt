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
        
        # Turn rate tracking for speed display
        from time import perf_counter
        self.turn_rate_start_time = perf_counter()
        self.turn_rate_start_turn = 0
        self.current_turn_rate = 0.0  # Actual turns/second
        
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
        """Create standardized layout (viewport + control panel; debug panel removed)."""
        self.setWindowTitle(f"Manual Test {self.config.id}: {self.config.name}")
        # Narrower width now that the debug panel is removed
        self.setGeometry(100, 100, 900, 700)
        
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
            
            # Create pygame widget in RENDER-ONLY mode (test framework drives simulation)
            from econsim.gui.embedded_pygame import EmbeddedPygameWidget
            self.pygame_widget = EmbeddedPygameWidget(
                simulation=self.simulation,
                drive_simulation=False  # Render only - framework drives simulation
            )
            self.pygame_widget.setFixedSize(self.config.viewport_size, self.config.viewport_size)
            
            # Replace placeholder in layout
            self.test_layout.replace_viewport(self.pygame_widget)
            
            # Reset counters
            self.current_turn = 0
            self.phase = 1
            
            # Reset turn rate tracking
            from time import perf_counter
            self.turn_rate_start_time = perf_counter()
            self.turn_rate_start_turn = 0
            self.current_turn_rate = 0.0
            
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
        
        # Check if test is complete BEFORE processing next turn
        total_turns = self.get_total_turns()
        if self.current_turn >= total_turns:
            # Test already complete, stop test timer (pygame continues rendering)
            if self.step_timer.isActive():
                self.step_timer.stop()
                print(f"⏹️  Test timer stopped - test complete at {total_turns} turns")
            return
            
        # Increment turn counter
        self.current_turn += 1
        
        # Calculate actual turn rate (updated every 10 turns for smoothness)
        if self.current_turn % 10 == 0:
            from time import perf_counter
            current_time = perf_counter()
            elapsed = current_time - self.turn_rate_start_time
            if elapsed > 0:
                turns_elapsed = self.current_turn - self.turn_rate_start_turn
                self.current_turn_rate = turns_elapsed / elapsed
                # Reset tracking window
                self.turn_rate_start_time = current_time
                self.turn_rate_start_turn = self.current_turn
        
        # Check for phase transitions (implemented by subclasses)
        self.check_phase_transition()
        
        # Execute simulation step
        self.simulation.step(self.ext_rng)
        
        # Update display
        self.update_display()
        
        # Log periodic status and economic metrics
        if self.current_turn % 50 == 0:
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
            
            # Log performance metrics via observer system instead of console
            if hasattr(self.simulation, '_observer_registry'):
                for observer in self.simulation._observer_registry._observers:
                    if hasattr(observer, 'record_performance_monitor'):
                        observer.record_performance_monitor(
                            step=self.current_turn,
                            metric_name='launcher_performance_summary',
                            metric_value=steps_per_sec,
                            details=f'{steps_per_sec:.1f} steps/sec, {frame_ms:.1f}ms/frame, {agent_count} agents, {resource_count} resources, Phase {self.phase}',
                            frame_ms=frame_ms,
                            agent_count=agent_count,
                            resource_count=resource_count,
                            phase=self.phase
                        )
            
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
            
            # Log economics data via observer system instead of console
            if hasattr(self.simulation, '_observer_registry'):
                for observer in self.simulation._observer_registry._observers:
                    if hasattr(observer, 'record_economic_decision'):
                        observer.record_economic_decision(
                            step=self.current_turn,
                            agent_id=-1,  # System-level economic analysis
                            decision_type='economic_summary',
                            decision_context=f'Grid: good1={resource_by_type["good1"]}, good2={resource_by_type["good2"]} | Carrying: good1={total_carrying["good1"]}, good2={total_carrying["good2"]} | Home: good1={total_home_inventory["good1"]}, good2={total_home_inventory["good2"]}',
                            grid_resources=resource_by_type,
                            agent_carrying=total_carrying,
                            agent_home_inventory=total_home_inventory,
                            agent_count=agent_count,
                            category='economic_flow_analysis'
                        )
            
            # Spatial analytics (legacy debug logging removed - observer system handles structured logging)
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
                
                # Log spatial analytics via observer system instead of console
                if hasattr(self.simulation, '_observer_registry'):
                    for observer in self.simulation._observer_registry._observers:
                        if hasattr(observer, 'record_debug_log'):
                            observer.record_debug_log(
                                step=self.current_turn,
                                category='spatial_analytics',
                                message=f'Spatial T{self.current_turn}: Center: ({center_x:.1f}, {center_y:.1f}) | Avg distance from center: {avg_distance_from_center:.1f} | Avg inter-agent distance: {avg_inter_distance:.1f}',
                                agent_id=-1,  # System-level spatial analysis
                                center_x=center_x,
                                center_y=center_y,
                                avg_distance_from_center=avg_distance_from_center,
                                avg_inter_agent_distance=avg_inter_distance,
                                agent_count=len(agent_positions)
                            )
        
        # Check if we just completed the final turn
        total_turns = self.get_total_turns()
        if self.current_turn >= total_turns:
            self.step_timer.stop()
            
            # Close all observers to write raw data to disk
            if self.simulation and hasattr(self.simulation, '_observer_registry'):
                print("🔧 Closing observers to write raw data to disk...")
                self.simulation._observer_registry.close_all()
                print("✅ Observer cleanup complete - raw data written to disk")
            
            print("🔧 Test logging session complete (observer system)")
            
            self.test_layout.control_panel.start_button.setText("Test Completed!")
            self.test_layout.control_panel.status_text.setText(f"🎉 Test completed! All {total_turns} turns executed with phase transitions.")
            print("=" * 60)
            print(f"🎉 TEST COMPLETED SUCCESSFULLY! ({total_turns} turns)")
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
    
    def get_total_turns(self) -> int:
        """Get the total number of turns for this test. Override in subclasses."""
        return 900  # Default for legacy tests
        
    def update_display(self):
        """Update the UI display with current simulation state."""
        if not self.simulation:
            return
            
        agent_count = len(self.simulation.agents)
        resource_count = len(list(self.simulation.grid.iter_resources()))
        
        # Update control panel with turn rate
        self.test_layout.control_panel.update_display(
            turn=self.current_turn,
            phase=self.phase,
            agent_count=agent_count,
            resource_count=resource_count,
            phase_manager=getattr(self, 'phase_manager', None),
            turn_rate=self.current_turn_rate
        )
        
    def on_speed_changed(self, index):
        """Handle speed selection change."""
        from .test_utils import get_timer_interval
        
        speed_names = ["1 turn/sec", "3 turns/sec", "10 turns/sec", "20 turns/sec", "UNLIMITED (as fast as possible)"]
        interval = get_timer_interval(index)
        
        if hasattr(self, 'step_timer') and self.step_timer.isActive():
            # Update running timer interval
            self.step_timer.setInterval(interval)
            if interval == 0:
                print(f"⏱️  Speed changed to: UNLIMITED - running as fast as possible!")
            else:
                print(f"⏱️  Speed changed to: {speed_names[index]} (interval: {interval}ms)")
        
        # Update status display to reflect new speed
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
            
            # Log phase transition via observer system instead of console
            if hasattr(self.simulation, '_observer_registry'):
                for observer in self.simulation._observer_registry._observers:
                    if hasattr(observer, 'record_debug_log'):
                        observer.record_debug_log(
                            step=self.current_turn,
                            category='phase_transition',
                            message=f'Phase Transition: Phase {transition.new_phase} at turn {self.current_turn} - {transition.description}',
                            agent_id=-1,  # System-level event
                            phase_number=transition.new_phase,
                            forage_enabled=transition.forage_enabled,
                            trade_enabled=transition.trade_enabled,
                            phase_description=transition.description
                        )
    
    def get_total_turns(self) -> int:
        """Get the total number of turns from phase manager."""
        return self.phase_manager.get_total_turns()


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
            
            # Log phase transition via observer system instead of console
            if hasattr(self.simulation, '_observer_registry'):
                for observer in self.simulation._observer_registry._observers:
                    if hasattr(observer, 'record_debug_log'):
                        observer.record_debug_log(
                            step=self.current_turn,
                            category='phase_transition',
                            message=f'Phase Transition: Phase {transition.new_phase} at turn {self.current_turn} - {transition.description}',
                            agent_id=-1,  # System-level event
                            phase_number=transition.new_phase,
                            forage_enabled=transition.forage_enabled,
                            trade_enabled=transition.trade_enabled,
                            phase_description=transition.description
                        )