"""
Minimal Observer: Real-time monitoring for simulation execution.

This observer provides minimal real-time monitoring capabilities without
the overhead of the full observer system. Focuses only on critical
real-time events needed for monitoring and debugging.

Key Features:
- Real-time progress monitoring
- Performance warnings
- Error detection and reporting
- Development debugging support
- Zero overhead for non-critical events

Performance Targets:
- < 0.01% overhead for monitoring
- Real-time feedback for long-running simulations
- Minimal memory usage
- Fast error detection

Usage:
    from econsim.recording import MinimalObserver
    
    # Create minimal observer
    observer = MinimalObserver(
        progress_interval=1000,
        enable_debugging=True
    )
    
    # Register with simulation
    simulation._observer_registry.register(observer)
"""

from __future__ import annotations

import time
import logging
from typing import Any, Dict, Optional, Set
from dataclasses import dataclass

from ..observability.observers import BaseObserver

try:
    from ..observability.events import SimulationEvent
except ImportError:
    # Fallback for type checking
    SimulationEvent = Any


@dataclass
class MonitoringStats:
    """Real-time monitoring statistics."""
    start_time: float = 0.0
    current_step: int = 0
    total_steps: int = 0
    last_progress_time: float = 0.0
    error_count: int = 0
    warning_count: int = 0
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time since start."""
        return time.time() - self.start_time
    
    def get_progress_percentage(self) -> float:
        """Get progress percentage."""
        if self.total_steps <= 0:
            return 0.0
        return (self.current_step / self.total_steps) * 100.0
    
    def get_estimated_completion(self) -> float:
        """Get estimated completion time in seconds."""
        if self.current_step <= 0:
            return 0.0
        
        elapsed = self.get_elapsed_time()
        steps_per_second = self.current_step / elapsed
        remaining_steps = self.total_steps - self.current_step
        
        return remaining_steps / steps_per_second if steps_per_second > 0 else 0.0


class MinimalObserver(BaseObserver):
    """Minimal observer for real-time monitoring and debugging.
    
    Provides essential real-time monitoring capabilities without the overhead
    of the full observer system. Focuses on critical events only:
    
    - Progress monitoring for long-running simulations
    - Performance warnings and error detection
    - Development debugging support
    - Real-time feedback for interactive use
    
    Architecture:
    - Inherits from BaseObserver for configuration
    - Minimal event processing - only critical events
    - Real-time logging and progress reporting
    - Performance monitoring with warnings
    """
    
    def __init__(self, 
                 progress_interval: int = 1000,
                 enable_debugging: bool = False,
                 enable_performance_monitoring: bool = True,
                 log_level: int = logging.INFO,
                 enabled: bool = True):
        """Initialize minimal observer.
        
        Args:
            progress_interval: Steps between progress reports (default 1000)
            enable_debugging: Whether to enable detailed debugging (default False)
            enable_performance_monitoring: Whether to monitor performance (default True)
            log_level: Logging level (default INFO)
            enabled: Whether observer is enabled (default True)
        """
        super().__init__(enabled=enabled)
        
        self.progress_interval = progress_interval
        self.enable_debugging = enable_debugging
        self.enable_performance_monitoring = enable_performance_monitoring
        
        # Monitoring state
        self.stats = MonitoringStats()
        self.last_step_time = 0.0
        self.step_times = []
        self.max_step_times = 100  # Keep last 100 step times
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        # Event filtering - only critical events
        self._enabled_event_types = self._initialize_event_filtering()
    
    def _initialize_event_filtering(self) -> Set[str]:
        """Initialize event type filtering for minimal monitoring."""
        events = {
            # Critical events only
            'error',
            'performance_warning',
            'simulation_start',
            'simulation_end'
        }
        
        if self.enable_debugging:
            events.update({
                'agent_move',
                'resource_collect',
                'trade_execute',
                'agent_mode_change'
            })
        
        return events
    
    def start_monitoring(self, total_steps: int) -> None:
        """Start monitoring a simulation run.
        
        Args:
            total_steps: Total number of steps to run
        """
        if not self.enabled:
            return
        
        self.stats = MonitoringStats(
            start_time=time.time(),
            total_steps=total_steps,
            current_step=0
        )
        
        self.logger.info(f"Starting simulation monitoring: {total_steps} steps")
    
    def notify(self, event: SimulationEvent) -> None:
        """Handle simulation event with minimal processing.
        
        Args:
            event: Simulation event to process
        """
        if not self.enabled:
            return
        
        if not self.is_enabled(event.event_type):
            return
        
        step = getattr(event, 'step', 0)
        
        if event.event_type == 'error':
            self._handle_error(event, step)
        elif event.event_type == 'performance_warning':
            self._handle_performance_warning(event, step)
        elif event.event_type == 'simulation_start':
            self._handle_simulation_start(event, step)
        elif event.event_type == 'simulation_end':
            self._handle_simulation_end(event, step)
        elif self.enable_debugging:
            self._handle_debug_event(event, step)
    
    def flush_step(self, step: int) -> None:
        """Handle end-of-step boundary.
        
        Args:
            step: The simulation step that just completed
        """
        if not self.enabled:
            return
        
        self.stats.current_step = step
        
        # Performance monitoring
        if self.enable_performance_monitoring:
            self._monitor_step_performance(step)
        
        # Progress reporting
        if step % self.progress_interval == 0:
            self._report_progress(step)
    
    def _handle_error(self, event: SimulationEvent, step: int) -> None:
        """Handle error events."""
        self.stats.error_count += 1
        
        error_message = getattr(event, 'message', 'Unknown error')
        self.logger.error(f"Step {step}: ERROR - {error_message}")
    
    def _handle_performance_warning(self, event: SimulationEvent, step: int) -> None:
        """Handle performance warning events."""
        self.stats.warning_count += 1
        
        warning_message = getattr(event, 'message', 'Performance warning')
        self.logger.warning(f"Step {step}: PERFORMANCE - {warning_message}")
    
    def _handle_simulation_start(self, event: SimulationEvent, step: int) -> None:
        """Handle simulation start events."""
        self.logger.info("Simulation started")
    
    def _handle_simulation_end(self, event: SimulationEvent, step: int) -> None:
        """Handle simulation end events."""
        elapsed_time = self.stats.get_elapsed_time()
        self.logger.info(f"Simulation completed: {elapsed_time:.2f}s, "
                        f"{self.stats.error_count} errors, "
                        f"{self.stats.warning_count} warnings")
    
    def _handle_debug_event(self, event: SimulationEvent, step: int) -> None:
        """Handle debug events (only when debugging enabled)."""
        if event.event_type == 'agent_move':
            agent_id = getattr(event, 'agent_id', -1)
            x = getattr(event, 'x', -1)
            y = getattr(event, 'y', -1)
            self.logger.debug(f"Step {step}: Agent {agent_id} moved to ({x}, {y})")
        
        elif event.event_type == 'resource_collect':
            agent_id = getattr(event, 'agent_id', -1)
            resource_type = getattr(event, 'resource_type', '')
            self.logger.debug(f"Step {step}: Agent {agent_id} collected {resource_type}")
        
        elif event.event_type == 'trade_execute':
            seller_id = getattr(event, 'seller_id', -1)
            buyer_id = getattr(event, 'buyer_id', -1)
            self.logger.debug(f"Step {step}: Trade between agent {seller_id} and {buyer_id}")
        
        elif event.event_type == 'agent_mode_change':
            agent_id = getattr(event, 'agent_id', -1)
            old_mode = getattr(event, 'old_mode', '')
            new_mode = getattr(event, 'new_mode', '')
            self.logger.debug(f"Step {step}: Agent {agent_id} changed from {old_mode} to {new_mode}")
    
    def _monitor_step_performance(self, step: int) -> None:
        """Monitor step performance and detect issues."""
        current_time = time.time()
        
        if self.last_step_time > 0:
            step_duration = current_time - self.last_step_time
            self.step_times.append(step_duration)
            
            # Keep only recent step times
            if len(self.step_times) > self.max_step_times:
                self.step_times.pop(0)
            
            # Check for performance issues
            if len(self.step_times) >= 10:  # Need some history
                avg_step_time = sum(self.step_times) / len(self.step_times)
                
                # Warn if step time is unusually long
                if step_duration > avg_step_time * 3.0:  # 3x average
                    self.logger.warning(f"Step {step}: Slow step detected - "
                                      f"{step_duration:.3f}s (avg: {avg_step_time:.3f}s)")
        
        self.last_step_time = current_time
    
    def _report_progress(self, step: int) -> None:
        """Report simulation progress."""
        progress = self.stats.get_progress_percentage()
        elapsed_time = self.stats.get_elapsed_time()
        estimated_completion = self.stats.get_estimated_completion()
        
        self.logger.info(f"Progress: {progress:.1f}% ({step}/{self.stats.total_steps}) - "
                        f"Elapsed: {elapsed_time:.1f}s - "
                        f"ETA: {estimated_completion:.1f}s")
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get current monitoring statistics.
        
        Returns:
            Dictionary with monitoring metrics
        """
        return {
            'current_step': self.stats.current_step,
            'total_steps': self.stats.total_steps,
            'progress_percentage': self.stats.get_progress_percentage(),
            'elapsed_time': self.stats.get_elapsed_time(),
            'estimated_completion': self.stats.get_estimated_completion(),
            'error_count': self.stats.error_count,
            'warning_count': self.stats.warning_count,
            'average_step_time': self._calculate_average_step_time(),
            'enabled': self.enabled,
            'debugging_enabled': self.enable_debugging,
            'performance_monitoring_enabled': self.enable_performance_monitoring
        }
    
    def _calculate_average_step_time(self) -> float:
        """Calculate average step time from recent history."""
        if not self.step_times:
            return 0.0
        
        return sum(self.step_times) / len(self.step_times)
    
    def close(self) -> None:
        """Clean up monitoring resources."""
        if self.stats.current_step > 0:
            elapsed_time = self.stats.get_elapsed_time()
            self.logger.info(f"Monitoring completed: {elapsed_time:.2f}s, "
                           f"{self.stats.error_count} errors, "
                           f"{self.stats.warning_count} warnings")
    
    def __repr__(self) -> str:
        """String representation of minimal observer."""
        return (f"MinimalObserver(progress_interval={self.progress_interval}, "
                f"debugging={self.enable_debugging}, "
                f"enabled={self.enabled})")
