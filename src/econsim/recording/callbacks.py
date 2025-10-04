"""
Simple callback system for real-time simulation monitoring.

This replaces the complex observer system with a lightweight callback approach.
"""

import time
from typing import Callable, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SimulationCallbacks:
    """Simple callback system for real-time monitoring without complex inheritance."""
    
    def __init__(self):
        self.step_callbacks: List[Callable[[int], None]] = []
        self.error_callbacks: List[Callable[[str], None]] = []
        self.warning_callbacks: List[Callable[[str], None]] = []
        self.progress_callbacks: List[Callable[[int, int], None]] = []  # current, total
        self.performance_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        # Internal state
        self._enabled = True
        self._closed = False
        self._step_count = 0
        self._start_time = None
    
    def enable(self) -> None:
        """Enable callbacks."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable callbacks."""
        self._enabled = False
    
    def close(self) -> None:
        """Close callback system."""
        self._closed = True
        self._enabled = False
    
    def is_enabled(self) -> bool:
        """Check if callbacks are enabled."""
        return self._enabled and not self._closed
    
    def start_monitoring(self, total_steps: int) -> None:
        """Start monitoring a simulation run."""
        if not self.is_enabled():
            return
        
        self._step_count = 0
        self._start_time = time.time()
        
        logger.info(f"Starting simulation monitoring: {total_steps} steps")
    
    def notify_step(self, step: int) -> None:
        """Notify that a simulation step completed."""
        if not self.is_enabled():
            return
        
        self._step_count = step
        
        # Call step callbacks
        for callback in self.step_callbacks:
            try:
                callback(step)
            except Exception as e:
                logger.warning(f"Step callback failed: {e}")
    
    def notify_progress(self, current: int, total: int) -> None:
        """Notify progress update."""
        if not self.is_enabled():
            return
        
        # Call progress callbacks
        for callback in self.progress_callbacks:
            try:
                callback(current, total)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
    
    def notify_error(self, message: str) -> None:
        """Notify error occurred."""
        if not self.is_enabled():
            return
        
        logger.error(f"Simulation error: {message}")
        
        # Call error callbacks
        for callback in self.error_callbacks:
            try:
                callback(message)
            except Exception as e:
                logger.warning(f"Error callback failed: {e}")
    
    def notify_warning(self, message: str) -> None:
        """Notify warning occurred."""
        if not self.is_enabled():
            return
        
        logger.warning(f"Simulation warning: {message}")
        
        # Call warning callbacks
        for callback in self.warning_callbacks:
            try:
                callback(message)
            except Exception as e:
                logger.warning(f"Warning callback failed: {e}")
    
    def notify_performance(self, metrics: Dict[str, Any]) -> None:
        """Notify performance metrics update."""
        if not self.is_enabled():
            return
        
        # Call performance callbacks
        for callback in self.performance_callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.warning(f"Performance callback failed: {e}")
    
    def finish_monitoring(self) -> Dict[str, Any]:
        """Finish monitoring and return summary."""
        if not self._start_time:
            return {}
        
        duration = time.time() - self._start_time
        
        summary = {
            'total_steps': self._step_count,
            'duration_seconds': duration,
            'steps_per_second': self._step_count / duration if duration > 0 else 0,
            'enabled': self.is_enabled()
        }
        
        logger.info(f"Monitoring completed: {duration:.2f}s, {self._step_count} steps")
        return summary
    
    # Callback registration methods
    def on_step(self, callback: Callable[[int], None]) -> None:
        """Register step callback."""
        self.step_callbacks.append(callback)
    
    def on_error(self, callback: Callable[[str], None]) -> None:
        """Register error callback."""
        self.error_callbacks.append(callback)
    
    def on_warning(self, callback: Callable[[str], None]) -> None:
        """Register warning callback."""
        self.warning_callbacks.append(callback)
    
    def on_progress(self, callback: Callable[[int, int], None]) -> None:
        """Register progress callback."""
        self.progress_callbacks.append(callback)
    
    def on_performance(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register performance callback."""
        self.performance_callbacks.append(callback)


def create_simple_progress_callback(interval: int = 1000) -> Callable[[int], None]:
    """Create a simple progress logging callback."""
    def progress_callback(step: int) -> None:
        if step % interval == 0:
            logger.info(f"Simulation progress: step {step}")
    return progress_callback


def create_performance_callback(interval: int = 1000) -> Callable[[int], None]:
    """Create a simple performance monitoring callback."""
    last_time = time.time()
    
    def performance_callback(step: int) -> None:
        nonlocal last_time
        if step % interval == 0:
            current_time = time.time()
            elapsed = current_time - last_time
            steps_per_second = interval / elapsed if elapsed > 0 else 0
            logger.info(f"Performance: {steps_per_second:.1f} steps/second")
            last_time = current_time
    
    return performance_callback
