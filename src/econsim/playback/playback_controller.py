"""
Playback Controller

This module provides a high-level controller for simulation playback with VCR-style controls.
It bridges between the PlaybackEngine and GUI components, providing a clean API for
playback management and integration with SimulationCallbacks.

Key Features:
- VCR-style controls (play, pause, stop, seek, speed)
- Integration with SimulationCallbacks for progress updates
- Thread-safe operations for GUI integration
- Event-driven architecture with Qt signals (when available)
- Performance monitoring and error handling

Usage:
    controller = PlaybackController(playback_engine)
    controller.play()
    controller.set_speed(2.0)
    controller.seek_to_step(5000)
    controller.pause()
"""

from __future__ import annotations

import time
from typing import Optional, Callable, Dict, Any
from pathlib import Path

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QTimer
    from PyQt6.QtWidgets import QWidget
    _qt_available = True
except ImportError:
    # Fallback for environments without Qt
    QObject = object
    pyqtSignal = None
    QTimer = None
    QWidget = object
    _qt_available = False

from .playback_engine import PlaybackEngine, PlaybackState
from ..recording.callbacks import SimulationCallbacks


class PlaybackController(QObject if _qt_available else object):
    """High-level controller for simulation playback with VCR-style controls.
    
    Provides a clean API for playback management and integrates with both
    PlaybackEngine and SimulationCallbacks for comprehensive monitoring.
    
    Features:
    - VCR-style controls (play, pause, stop, seek, speed)
    - Qt signal integration for GUI components
    - Progress monitoring via SimulationCallbacks
    - Thread-safe operations
    - Performance tracking and error handling
    """
    
    # Qt signals (only available when Qt is present)
    if _qt_available:
        step_changed = pyqtSignal(int)  # Emitted when current step changes
        playback_state_changed = pyqtSignal(object)  # Emitted when playback state changes
        progress_updated = pyqtSignal(int, int)  # Emitted with (current_step, total_steps)
        error_occurred = pyqtSignal(str)  # Emitted when an error occurs
        performance_updated = pyqtSignal(dict)  # Emitted with performance metrics
    
    def __init__(self, playback_engine: PlaybackEngine, progress_callback_interval: int = 100):
        """Initialize playback controller.
        
        Args:
            playback_engine: PlaybackEngine instance to control
            progress_callback_interval: Steps between progress callbacks (default 100)
        """
        if _qt_available:
            super().__init__()
        
        self.playback_engine = playback_engine
        self.progress_callback_interval = progress_callback_interval
        
        # Create monitoring callbacks for progress tracking
        self.monitoring_callbacks = SimulationCallbacks()
        
        # Setup engine callbacks
        self._setup_engine_callbacks()
        
        # Performance tracking
        self._last_progress_time = 0.0
        self._progress_update_interval = 1.0  # seconds
        
        # State tracking
        self._last_notified_step = 0
    
    def play(self) -> None:
        """Start playback from current step."""
        try:
            self.playback_engine.play()
        except Exception as e:
            self._handle_error(f"Failed to start playback: {e}")
    
    def pause(self) -> None:
        """Pause playback."""
        try:
            self.playback_engine.pause()
        except Exception as e:
            self._handle_error(f"Failed to pause playback: {e}")
    
    def stop(self) -> None:
        """Stop playback and reset to beginning."""
        try:
            self.playback_engine.stop()
        except Exception as e:
            self._handle_error(f"Failed to stop playback: {e}")
    
    def seek_to_step(self, step: int) -> None:
        """Seek to a specific step.
        
        Args:
            step: Target step number (1-based)
        """
        try:
            metrics = self.playback_engine.seek_to_step(step)
            self._log_seek_performance(step, metrics)
        except Exception as e:
            self._handle_error(f"Failed to seek to step {step}: {e}")
    
    def step_forward(self) -> None:
        """Step forward by one step."""
        try:
            metrics = self.playback_engine.step_forward()
            self._log_seek_performance(self.playback_engine.state.current_step, metrics)
        except Exception as e:
            self._handle_error(f"Failed to step forward: {e}")
    
    def step_backward(self) -> None:
        """Step backward by one step."""
        try:
            metrics = self.playback_engine.step_backward()
            self._log_seek_performance(self.playback_engine.state.current_step, metrics)
        except Exception as e:
            self._handle_error(f"Failed to step backward: {e}")
    
    def set_speed(self, speed: float) -> None:
        """Set playback speed multiplier.
        
        Args:
            speed: Speed multiplier (1.0 = normal, 2.0 = 2x, 0.5 = half speed)
        """
        try:
            self.playback_engine.set_playback_speed(speed)
        except Exception as e:
            self._handle_error(f"Failed to set playback speed to {speed}: {e}")
    
    def get_current_step(self) -> int:
        """Get the current step number.
        
        Returns:
            Current step number (1-based)
        """
        return self.playback_engine.state.current_step
    
    def get_total_steps(self) -> int:
        """Get the total number of steps.
        
        Returns:
            Total number of steps in the simulation
        """
        return self.playback_engine.state.total_steps
    
    def get_playback_speed(self) -> float:
        """Get the current playback speed.
        
        Returns:
            Current playback speed multiplier
        """
        return self.playback_engine.state.playback_speed
    
    def is_playing(self) -> bool:
        """Check if playback is currently active.
        
        Returns:
            True if playing, False if paused/stopped
        """
        return self.playback_engine.state.is_playing
    
    def is_at_end(self) -> bool:
        """Check if playback is at the end of the simulation.
        
        Returns:
            True if at the end, False otherwise
        """
        return self.playback_engine.state.is_at_end
    
    def get_current_simulation(self) -> Optional[Any]:
        """Get the current simulation state.
        
        Returns:
            Simulation object representing current state, or None if not loaded
        """
        try:
            return self.playback_engine.get_current_simulation()
        except ValueError:
            return None
        except Exception as e:
            self._handle_error(f"Failed to get current simulation: {e}")
            return None
    
    def get_progress_percentage(self) -> float:
        """Get playback progress as a percentage.
        
        Returns:
            Progress percentage (0.0 to 100.0)
        """
        if self.get_total_steps() == 0:
            return 0.0
        
        return (self.get_current_step() / self.get_total_steps()) * 100.0
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        stats = self.playback_engine.get_performance_stats()
        
        # Add controller-specific metrics
        stats.update({
            'progress_percentage': self.get_progress_percentage(),
            'is_playing': self.is_playing(),
            'is_at_end': self.is_at_end(),
            'monitoring_callbacks_enabled': self.monitoring_callbacks.is_enabled()
        })
        
        return stats
    
    def _setup_engine_callbacks(self) -> None:
        """Setup callbacks between playback engine and controller."""
        # Step change callback
        self.playback_engine.add_step_callback(self._on_step_changed)
        
        # State change callback
        self.playback_engine.add_state_change_callback(self._on_playback_state_changed)
        
        # Error callback
        self.playback_engine.add_error_callback(self._on_error)
    
    def _on_step_changed(self, step: int, simulation: Any) -> None:
        """Handle step change from playback engine."""
        # Update monitoring callbacks
        self.monitoring_callbacks.notify_step(step)
        
        # Check if we should emit progress update
        current_time = time.time()
        if (current_time - self._last_progress_time >= self._progress_update_interval or
            step % self.progress_callback_interval == 0 or
            step == self.get_total_steps()):
            
            self.monitoring_callbacks.notify_progress(step, self.get_total_steps())
            self._last_progress_time = current_time
            
            # Emit Qt signals if available
            if _qt_available:
                self.progress_updated.emit(step, self.get_total_steps())
        
        # Emit Qt signals if available
        if _qt_available:
            self.step_changed.emit(step)
    
    def _on_playback_state_changed(self, state: PlaybackState) -> None:
        """Handle playback state change from playback engine."""
        # Emit Qt signals if available
        if _qt_available:
            self.playback_state_changed.emit(state)
    
    def _on_error(self, error: str) -> None:
        """Handle error from playback engine."""
        self._handle_error(error)
    
    def _handle_error(self, error: str) -> None:
        """Handle and report an error."""
        # Notify monitoring callbacks
        self.monitoring_callbacks.notify_error(error)
        
        # Emit Qt signals if available
        if _qt_available:
            self.error_occurred.emit(error)
        
        # Log error (could be enhanced with proper logging)
        print(f"PlaybackController error: {error}")
    
    def _log_seek_performance(self, step: int, metrics: Any) -> None:
        """Log seek performance metrics."""
        if hasattr(metrics, 'reconstruction_time_ms'):
            # Emit performance update if significant
            if metrics.reconstruction_time_ms > 10:  # Only log slow seeks
                performance_data = {
                    'step': step,
                    'reconstruction_time_ms': metrics.reconstruction_time_ms,
                    'events_applied': getattr(metrics, 'events_applied', 0),
                    'snapshot_distance': getattr(metrics, 'snapshot_distance', 0),
                    'memory_usage_mb': getattr(metrics, 'memory_usage_mb', 0)
                }
                
                if _qt_available:
                    self.performance_updated.emit(performance_data)
    
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self.playback_engine.cleanup()
            self.monitoring_callbacks.close()
        except Exception as e:
            self._handle_error(f"Failed to cleanup playback controller: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors during destruction
