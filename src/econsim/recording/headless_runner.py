"""
Headless Simulation Runner: Runs simulations with recording for playback.

This module provides a headless simulation runner that executes simulations
without GUI dependencies and automatically records them for playback.
Integrates with the recording system to create efficient simulation output files.

Key Features:
- Runs simulations without GUI dependencies
- Automatic recording with configurable snapshot intervals
- Performance monitoring and optimization
- Integration with existing simulation infrastructure
- Clean separation from GUI components

Performance Targets:
- Recording overhead: < 10% of simulation time
- Memory usage: < 2x simulation memory
- File size: < 50MB for 10,000 steps with 100 agents
- Deterministic execution guarantees

Usage:
    from econsim.recording import HeadlessSimulationRunner
    
    # Create runner with recording
    runner = HeadlessSimulationRunner(
        config=simulation_config,
        output_path="simulation.vmt",
        snapshot_interval=100
    )
    
    # Run simulation with recording
    runner.run(steps=1000)
    
    # Get output file path
    output_file = runner.output_file_path
"""

from __future__ import annotations

import time
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..simulation.world import Simulation
from .minimal_observer import MinimalObserver
from .simulation_output import SimulationOutputFile

try:
    from ..simulation.config import SimConfig
except ImportError:
    # Fallback for type checking
    SimConfig = Any


class HeadlessSimulationRunner:
    """Headless simulation runner with automatic recording.
    
    Executes simulations without GUI dependencies and automatically records
    them using the recording observer system. Provides clean separation
    between simulation logic and GUI components.
    
    Architecture:
    - Uses SimulationFactory for simulation creation
    - Integrates RecordingObserver for automatic recording
    - Provides performance monitoring and optimization
    - Maintains deterministic execution guarantees
    - Clean error handling and resource management
    """
    
    def __init__(self, 
                 config: Any,
                 output_path: Union[str, Path],
                 snapshot_interval: int = 100,
                 config_hash: str = "",
                 enable_recording: bool = True,
                 log_level: int = logging.INFO):
        """Initialize headless simulation runner.
        
        Args:
            config: Simulation configuration
            output_path: Path where simulation output will be saved
            snapshot_interval: Steps between snapshots (default 100)
            config_hash: Configuration hash for validation
            enable_recording: Whether to enable recording (default True)
            log_level: Logging level (default INFO)
        """
        self.config = config
        self.output_path = Path(output_path)
        self.snapshot_interval = snapshot_interval
        self.config_hash = config_hash
        self.enable_recording = enable_recording
        
        # Simulation state
        self.simulation: Optional[Simulation] = None
        self.output_file: Optional[SimulationOutputFile] = None
        self.monitoring_observer: Optional[MinimalObserver] = None
        self.output_file_path: Optional[Path] = None
        
        # Performance tracking
        self.start_time = 0.0
        self.end_time = 0.0
        self.total_steps_run = 0
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate simulation configuration."""
        if self.config is None:
            raise ValueError("Simulation config cannot be None")
        
        if self.enable_recording and not self.output_path:
            raise ValueError("Output path required when recording is enabled")
        
        if self.snapshot_interval <= 0:
            raise ValueError("Snapshot interval must be positive")
    
    def run(self, steps: int, seed: Optional[int] = None) -> Dict[str, Any]:
        """Run simulation with recording.
        
        Args:
            steps: Number of simulation steps to run
            seed: Optional random seed for deterministic execution
            
        Returns:
            Dictionary with execution results and performance metrics
            
        Raises:
            RuntimeError: If simulation execution fails
            ValueError: If parameters are invalid
        """
        if steps <= 0:
            raise ValueError("Steps must be positive")
        
        self.logger.info(f"Starting headless simulation: {steps} steps")
        self.start_time = time.time()
        
        try:
            # Create simulation
            self.simulation = self._create_simulation(seed)
            
            # Setup recording and monitoring
            self._setup_recording_and_monitoring()
            
            # Run simulation steps
            self._run_simulation_steps(steps)
            
            # Finalize recording
            self._finalize_recording()
            
            # Calculate performance metrics
            self.end_time = time.time()
            metrics = self._calculate_metrics()
            
            self.logger.info(f"Simulation completed: {metrics['total_time_seconds']:.2f}s")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Simulation execution failed: {e}")
            raise RuntimeError(f"Simulation execution failed: {e}") from e
        
        finally:
            self._cleanup()
    
    def _create_simulation(self, seed: Optional[int]) -> Simulation:
        """Create simulation instance."""
        self.logger.info("Creating simulation instance")
        
        # Use Simulation.from_config to create simulation
        simulation = Simulation.from_config(self.config)
        
        # Set seed if provided
        if seed is not None:
            import random
            simulation._rng = random.Random(seed)
        
        self.logger.info(f"Simulation created: {len(simulation.agents)} agents, "
                        f"{simulation.grid.width}x{simulation.grid.height} grid")
        
        return simulation
    
    def _setup_recording_and_monitoring(self) -> None:
        """Setup direct recording and minimal monitoring."""
        # Setup direct recording if enabled
        if self.enable_recording:
            self.logger.info("Setting up direct recording")
            
            # Create simulation output file for direct recording
            self.output_file = SimulationOutputFile.create(
                self.output_path,
                snapshot_interval=self.snapshot_interval,
                config_hash=self.config_hash
            )
            
            self.output_file_path = self.output_path
            self.logger.info(f"Direct recording enabled: {self.output_path}")
        
        # Setup minimal monitoring observer
        self.logger.info("Setting up minimal monitoring")
        
        self.monitoring_observer = MinimalObserver(
            progress_interval=1000,  # Report every 1000 steps
            enable_debugging=False,  # Disable detailed debugging for performance
            enable_performance_monitoring=True,
            enabled=True
        )
        
        # Register with simulation
        if self.simulation:
            self.simulation._observer_registry.register(self.monitoring_observer)
        
        # Start monitoring (will be updated when we know total steps)
        self.monitoring_observer.start_monitoring(0)
    
    def _run_simulation_steps(self, steps: int) -> None:
        """Run simulation steps with progress monitoring."""
        self.logger.info(f"Running {steps} simulation steps")
        
        # Update monitoring with correct total steps
        if self.monitoring_observer:
            self.monitoring_observer.start_monitoring(steps)
        
        # Import RNG for simulation stepping
        import random
        rng = random.Random()
        
        # Progress reporting intervals
        progress_interval = max(1, steps // 10)  # Report every 10%
        
        for step in range(1, steps + 1):
            # Run single step
            if self.simulation:
                self.simulation.step(rng)
                self.total_steps_run = step
                
                # Record step directly if recording enabled
                if self.output_file:
                    self.output_file.record_step(self.simulation, step)
        
        self.logger.info(f"Completed {self.total_steps_run} simulation steps")
    
    def _finalize_recording(self) -> None:
        """Finalize recording and write to disk."""
        if not self.output_file:
            return
        
        self.logger.info("Finalizing recording")
        
        # Finalize simulation output file
        self.output_file.finalize_recording()
        
        # Get recording statistics
        file_info = self.output_file.get_file_info()
        
        self.logger.info(f"Recording finalized: {file_info['file_size_bytes']} bytes, "
                        f"{file_info['snapshot_count']} snapshots, "
                        f"{file_info['event_count']} events")
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics."""
        total_time = self.end_time - self.start_time
        steps_per_second = self.total_steps_run / total_time if total_time > 0 else 0
        
        metrics = {
            'total_steps_run': self.total_steps_run,
            'total_time_seconds': total_time,
            'steps_per_second': steps_per_second,
            'simulation_created': self.simulation is not None,
            'recording_enabled': self.enable_recording,
            'output_file_path': str(self.output_file_path) if self.output_file_path else None
        }
        
        # Add recording metrics if available
        if self.output_file:
            file_info = self.output_file.get_file_info()
            metrics.update({
                'recording_time_seconds': file_info.get('recording_duration', 0),
                'file_size_bytes': file_info.get('file_size_bytes', 0),
                'snapshot_count': file_info.get('snapshot_count', 0),
                'event_count': file_info.get('event_count', 0),
                'snapshot_interval': file_info.get('snapshot_interval', 0)
            })
        
        # Add monitoring metrics if available
        if self.monitoring_observer:
            monitoring_stats = self.monitoring_observer.get_monitoring_stats()
            metrics.update({
                'error_count': monitoring_stats.get('error_count', 0),
                'warning_count': monitoring_stats.get('warning_count', 0),
                'average_step_time': monitoring_stats.get('average_step_time', 0)
            })
        
        return metrics
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        if self.output_file:
            self.output_file = None
        
        if self.monitoring_observer:
            self.monitoring_observer.close()
            self.monitoring_observer = None
        
        self.simulation = None
    
    def get_simulation_state(self) -> Optional[Simulation]:
        """Get current simulation state.
        
        Returns:
            Current simulation instance or None if not running
        """
        return self.simulation
    
    def get_recording_stats(self) -> Dict[str, Any]:
        """Get recording statistics.
        
        Returns:
            Dictionary with recording performance metrics
        """
        if not self.output_file:
            return {}
        
        return self.output_file.get_file_info()
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics.
        
        Returns:
            Dictionary with monitoring performance metrics
        """
        if not self.monitoring_observer:
            return {}
        
        return self.monitoring_observer.get_monitoring_stats()
    
    def is_recording_enabled(self) -> bool:
        """Check if recording is enabled.
        
        Returns:
            True if recording is enabled
        """
        return self.enable_recording and self.output_file is not None
    
    def __repr__(self) -> str:
        """String representation of runner."""
        return (f"HeadlessSimulationRunner(config={type(self.config).__name__}, "
                f"output_path={self.output_path}, "
                f"recording={self.enable_recording})")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def run_headless_simulation(config: Any,
                           steps: int,
                           output_path: Union[str, Path],
                           snapshot_interval: int = 100,
                           seed: Optional[int] = None,
                           config_hash: str = "") -> Dict[str, Any]:
    """Run headless simulation with recording.
    
    Args:
        config: Simulation configuration
        steps: Number of simulation steps to run
        output_path: Path where simulation output will be saved
        snapshot_interval: Steps between snapshots (default 100)
        seed: Optional random seed for deterministic execution
        config_hash: Configuration hash for validation
        
    Returns:
        Dictionary with execution results and performance metrics
    """
    runner = HeadlessSimulationRunner(
        config=config,
        output_path=output_path,
        snapshot_interval=snapshot_interval,
        config_hash=config_hash,
        enable_recording=True
    )
    
    return runner.run(steps, seed)


def run_headless_simulation_no_recording(config: Any,
                                        steps: int,
                                        seed: Optional[int] = None) -> Dict[str, Any]:
    """Run headless simulation without recording.
    
    Args:
        config: Simulation configuration
        steps: Number of simulation steps to run
        seed: Optional random seed for deterministic execution
        
    Returns:
        Dictionary with execution results and performance metrics
    """
    runner = HeadlessSimulationRunner(
        config=config,
        output_path="",  # No output path
        enable_recording=False
    )
    
    return runner.run(steps, seed)
