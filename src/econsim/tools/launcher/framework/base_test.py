"""
Base Test Framework - Abstract base classes for manual tests.

Provides common functionality extracted from existing tests.
"""

import sys
import os
import random
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, Any

# Add src to Python path  
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import QTimer

from .test_configs import TestConfiguration
from .ui_components import TestLayout
from .debug_orchestrator import DebugOrchestrator
from .phase_manager import PhaseManager
from .simulation_factory import SimulationFactory

# Phase 2 imports - Comprehensive Delta system
from econsim.recording import HeadlessSimulationRunner
from econsim.delta import ComprehensiveDeltaRecorder, ComprehensivePlaybackController
from econsim.gui.economic_analysis_widget import EconomicAnalysisWidget


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
        
        # Phase 2: Delta system state
        self.delta_controller: Optional[ComprehensivePlaybackController] = None
        self.delta_file_path: Optional[str] = None
        self.economic_analysis_widget: Optional[EconomicAnalysisWidget] = None
        
        # Playback timer for non-blocking playback
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.playback_timer_tick)
        
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
        # TestLayout is now a QWidget, so we need to add it as a widget, not set it as a layout
        layout = QVBoxLayout()
        layout.addWidget(self.test_layout)
        self.setLayout(layout)
        
        # Connect control panel signals
        self.test_layout.control_panel.start_button.clicked.connect(self.start_test)
        self.test_layout.control_panel.speed_combo.currentIndexChanged.connect(self.on_speed_changed)
        
    def setup_debug_orchestrator(self):
        """Configure debug logging for this test."""
        self.debug_orchestrator = DebugOrchestrator(self.config)
        
        # Debug timer is handled by the debug panel
        
    def setup_timers(self):
        """Setup timers for playback controls."""
        # No continuous timer needed - updates happen on step changes via callbacks
        pass
        
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
        """Run headless simulation with delta recording, then load for playback."""
        try:
            # Phase 1: Run headless simulation with delta recording
            self.log_status("🚀 Starting headless simulation with delta recording...")
            self.run_headless_simulation_with_deltas()
            
            # Phase 2: Load delta file for playback
            self.log_status("📁 Loading visual deltas...")
            self.load_delta_file()
            
            # Phase 3: Setup playback controls
            self.log_status("🎮 Setting up playback controls...")
            self.setup_playback_controls()
            
            print(f"✅ Test {self.config.id} completed! Headless simulation → Delta playback ready")
            print("🎮 Use playback controls to watch recorded simulation!")
            
        except Exception as e:
            print(f"❌ Error in test workflow: {e}")
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
    
    def run_headless_simulation_with_deltas(self):
        """Run simulation headless with visual delta recording."""
        # Generate delta file path (MessagePack format)
        with tempfile.NamedTemporaryFile(suffix='.msgpack', delete=False) as tmp_file:
            self.delta_file_path = tmp_file.name
        
        # Convert TestConfiguration to SimConfig
        sim_config = self._convert_to_sim_config()
        
        # Generate agent positions
        agent_positions = self._generate_agent_positions()
        
        # Create comprehensive delta recorder
        delta_recorder = ComprehensiveDeltaRecorder(self.delta_file_path)
        
        # Create simulation using the factory
        simulation = SimulationFactory.create_simulation(self.config)
        
        # Record initial state
        delta_recorder.record_initial_state(simulation)
        
        # Run simulation with delta recording
        total_turns = self.get_total_turns()
        start_time = time.time()
        
        print(f"🎬 Recording comprehensive deltas for {total_turns} steps...")
        
        for step in range(1, total_turns + 1):
            # Start step recording
            delta_recorder.start_step_recording(step)
            
            # Step simulation
            simulation.step(random.Random(self.config.seed + step))
            
            # Record comprehensive delta
            delta_recorder.record_step(simulation, step)
            
            # Progress update
            if step % 100 == 0:
                print(f"  📊 Step {step}/{total_turns}")
        
        # Save deltas
        delta_recorder.save_deltas()
        
        end_time = time.time()
        print(f"✅ Headless simulation with comprehensive delta recording completed: {end_time - start_time:.2f}s")
        print(f"📁 Comprehensive deltas saved to: {self.delta_file_path}")
    
    def load_delta_file(self):
        """Load visual deltas for playback."""
        if not self.delta_file_path or not Path(self.delta_file_path).exists():
            raise RuntimeError("No visual delta file found")
        
        # Prevent multiple loads
        if hasattr(self, 'delta_controller') and self.delta_controller:
            print("📁 Delta file already loaded, skipping...")
            return
        
        print(f"📁 Loading delta file: {self.delta_file_path}")
        print(f"📊 File size: {os.path.getsize(self.delta_file_path)} bytes")
        
        # Load comprehensive delta controller
        print("🔄 Loading ComprehensivePlaybackController...")
        load_start = time.time()
        self.delta_controller = ComprehensivePlaybackController.load_from_file(self.delta_file_path)
        load_end = time.time()
        print(f"✅ ComprehensivePlaybackController loaded in {load_end - load_start:.2f}s")
        
        # Initialize to step 0
        print("🔄 Initializing delta playback to step 0...")
        init_start = time.time()
        # No seeking - start at step 1
        init_end = time.time()
        print(f"✅ Delta playback initialized in {init_end - init_start:.2f}s")
        
        # Create pygame widget for delta rendering (only if not already created)
        if not hasattr(self, 'pygame_widget') or not self.pygame_widget:
            from econsim.gui.embedded_pygame_delta import EmbeddedPygameWidget
            self.pygame_widget = EmbeddedPygameWidget(
                delta_controller=self.delta_controller
            )
            self.pygame_widget.setFixedSize(self.config.viewport_size, self.config.viewport_size)
            
            # Replace placeholder in layout
            self.test_layout.replace_viewport(self.pygame_widget)
        else:
            # Update existing widget's delta controller
            self.pygame_widget.delta_controller = self.delta_controller
        
        print(f"📁 Loaded delta file: {self.delta_controller.get_total_steps()} steps")
    
    def setup_playback_controls(self):
        """Setup VCR-style playback controls."""
        # Show the playback controls beneath the pygame window
        self.test_layout.show_playback_controls()
        
        # Connect playback control buttons
        playback_controls = self.test_layout.playback_controls
        playback_controls.play_button.clicked.connect(self.toggle_playback)
        playback_controls.rewind_button.clicked.connect(self.rewind_playback)
        playback_controls.fast_forward_button.clicked.connect(self.fast_forward_playback)
        playback_controls.speed_combo.currentIndexChanged.connect(self.on_playback_speed_changed)
        
        # Connect comprehensive delta controller callbacks to update GUI
        self.delta_controller.add_step_callback(self.on_comprehensive_step_changed)
        self.delta_controller.add_state_change_callback(self.on_comprehensive_state_changed)
        
        # Update display to show playback state
        self.update_playback_display()
        
        print("🎮 Playback controls ready - use VCR controls to watch simulation")
    
    def playback_timer_tick(self):
        """Handle playback timer tick."""
        if self.delta_controller and self.delta_controller.current_state.is_playing:
            # Try to step forward - returns False if at end
            if not self.delta_controller.step_forward():
                # Reached the end, pause playback
                self.delta_controller.pause()
                self.playback_timer.stop()
    
    def toggle_playback(self):
        """Toggle playback play/pause."""
        if not self.delta_controller:
            return
            
        if self.delta_controller.current_state.is_playing:
            self.delta_controller.pause()
            self.playback_timer.stop()
        else:
            self.delta_controller.play()
            # Start timer with appropriate interval based on playback speed
            interval_ms = int(1000 / self.delta_controller.current_state.playback_speed)
            self.playback_timer.start(interval_ms)
    
    def rewind_playback(self):
        """Rewind playback to the beginning."""
        # No seeking - start at step 1
    
    def fast_forward_playback(self):
        """Fast forward playback to the end."""
        total_steps = self.delta_controller.get_total_steps()
        # Fast forward to end (step by step)
        while self.delta_controller.step_forward():
            pass
    
    def on_playback_speed_changed(self, index: int):
        """Handle playback speed change."""
        speed_map = [2.0, 8.0, 20.0, 0]  # 0 = unlimited
        speed = speed_map[index]
        self.delta_controller.set_playback_speed(speed)
        
        # Restart timer if currently playing
        if self.delta_controller.current_state.is_playing:
            self.playback_timer.stop()
            if speed > 0:
                interval_ms = int(1000 / speed)
                self.playback_timer.start(interval_ms)
        
        # Update status
        speed_names = ["2 steps/sec", "8 steps/sec", "20 steps/sec", "Unlimited"]
        print(f"🎬 Playback speed changed to: {speed_names[index]}")
    
    def on_comprehensive_step_changed(self, step: int):
        """Called when comprehensive playback advances to a new step."""
        # Update pygame widget for this specific step
        if hasattr(self, 'pygame_widget') and self.pygame_widget:
            self.pygame_widget.update_for_step(step)
        
        # Update the UI display
        self.update_playback_display()
    
    def on_comprehensive_state_changed(self, visual_state):
        """Called when comprehensive visual state changes during playback."""
        # Update playback controls display
        playback_controls = self.test_layout.playback_controls
        current_step = self.delta_controller.get_current_step()
        total_steps = self.delta_controller.get_total_steps()
        playback_controls.update_progress(current_step, total_steps, self.delta_controller.current_state.is_playing)
        
        # Update display
        self.update_playback_display()
    
    def get_economic_analysis(self, step: Optional[int] = None) -> Dict[str, Any]:
        """Get economic analysis data for a specific step or current step.
        
        Args:
            step: Step number (None for current step)
            
        Returns:
            Dictionary containing economic analysis data
        """
        if not self.delta_controller:
            return {}
        
        return self.delta_controller.get_economic_data(step)
    
    def get_agent_analysis(self, agent_id: int, step: Optional[int] = None) -> Dict[str, Any]:
        """Get agent analysis data for a specific agent and step.
        
        Args:
            agent_id: Agent ID
            step: Step number (None for current step)
            
        Returns:
            Dictionary containing agent analysis data
        """
        if not self.delta_controller:
            return {}
        
        return self.delta_controller.get_agent_state(agent_id, step)
    
    def show_economic_analysis(self):
        """Show the economic analysis widget."""
        if not self.delta_controller:
            print("No delta controller available for economic analysis")
            return
        
        if not self.economic_analysis_widget:
            self.economic_analysis_widget = EconomicAnalysisWidget()
            self.economic_analysis_widget.set_delta_controller(self.delta_controller)
        
        self.economic_analysis_widget.show()
        self.economic_analysis_widget.raise_()
        self.economic_analysis_widget.activateWindow()
    
    def update_playback_display(self):
        """Update UI display with current playback state."""
        if not self.delta_controller:
            return
            
        current_step = self.delta_controller.get_current_step()
        total_steps = self.delta_controller.get_total_steps()
        progress = (current_step / max(1, total_steps)) * 100 if total_steps > 0 else 0
        
        # Update control panel with playback state
        self.test_layout.control_panel.update_display(
            turn=current_step,
            phase=1,  # Phase tracking would need to be reconstructed from playback
            agent_count=self.config.agent_count,  # Static from config
            resource_count=0,  # Would need to be reconstructed from playback
            phase_manager=None,
            turn_rate=0.0  # Playback rate, not simulation rate
        )
        
        # Update status text
        status = f"Playback: Step {current_step}/{total_steps} ({progress:.1f}%)"
        self.test_layout.control_panel.status_text.setText(status)
        
        # Update playback controls progress
        if hasattr(self.test_layout, 'playback_controls'):
            playback_controls = self.test_layout.playback_controls
            is_playing = self.delta_controller.current_state.is_playing
            playback_controls.update_progress(current_step, total_steps, is_playing)
    
    def _convert_to_sim_config(self):
        """Convert TestConfiguration to SimConfig for HeadlessSimulationRunner."""
        from econsim.simulation.config import SimConfig
        
        # Generate resources using existing factory logic
        resources = SimulationFactory._generate_resources(self.config)
        
        return SimConfig(
            grid_size=self.config.grid_size,
            initial_resources=resources,
            seed=self.config.seed,
            enable_respawn=True,
            enable_metrics=True,
            perception_radius=self.config.perception_radius,
            respawn_target_density=self.config.resource_density,
            respawn_rate=0.25,
            distance_scaling_factor=getattr(self.config, 'distance_scaling_factor', 0.0),
            viewport_size=self.config.viewport_size
        )
    
    def _generate_agent_positions(self):
        """Generate agent positions for the simulation."""
        agent_positions = []
        rng = random.Random(self.config.seed)
        
        for i in range(self.config.agent_count):
            x = rng.randint(0, self.config.grid_size[0] - 1)
            y = rng.randint(0, self.config.grid_size[1] - 1)
            agent_positions.append((x, y))
        
        return agent_positions
    
    def log_status(self, message: str):
        """Log status message and update UI."""
        print(message)
        if hasattr(self, 'test_layout') and hasattr(self.test_layout, 'control_panel'):
            self.test_layout.control_panel.status_text.setText(message)


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