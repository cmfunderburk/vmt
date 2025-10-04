"""
Playback Engine

This module provides the core playback engine for recorded simulation runs.
It manages loading, seeking, and state reconstruction from SimulationOutputFile data.

Key Features:
- Load recorded simulation output files
- Fast seeking to any step via StateReconstructor
- Real-time playback with configurable speed
- Integration with SimulationCallbacks for progress updates
- Memory-efficient streaming playback

Performance Targets:
- Loading time: < 1 second for complete simulation
- Seeking time: < 0.1 seconds to any step
- Memory usage: < 2x simulation memory during playback
- Playback overhead: < 5% of real-time simulation speed
"""

from __future__ import annotations

import time
import threading
from typing import Optional, Callable, Dict, Any
from pathlib import Path
from dataclasses import dataclass

from ..recording.simulation_output import SimulationOutputFile, load_simulation_output
from ..simulation.world import Simulation
from .state_reconstructor import StateReconstructor, ReconstructionMetrics


@dataclass
class PlaybackState:
    """Current state of the playback engine."""
    current_step: int = 0
    total_steps: int = 0
    is_playing: bool = False
    playback_speed: float = 1.0
    is_at_end: bool = False


class PlaybackEngine:
    """Core playback engine for recorded simulation runs.
    
    Provides VCR-style playback capabilities:
    - Load recorded simulation output files
    - Seek to any step with fast state reconstruction
    - Real-time playback with configurable speed
    - Integration with callbacks for progress updates
    
    Architecture:
    - Uses StateReconstructor for efficient state reconstruction
    - Maintains playback state and timing
    - Supports both manual stepping and automatic playback
    - Thread-safe for GUI integration
    """
    
    def __init__(self, output_file: SimulationOutputFile):
        """Initialize playback engine with a loaded simulation output file.
        
        Args:
            output_file: Loaded SimulationOutputFile containing recorded data
        """
        self.output_file = output_file
        self.reconstructor = StateReconstructor(output_file)
        
        # Playback state
        self.state = PlaybackState(
            current_step=0,
            total_steps=output_file.header.total_steps,
            is_playing=False,
            playback_speed=2.0,  # Default to 2 steps per second
            is_at_end=False
        )
        
        # Playback timing
        self._playback_thread: Optional[threading.Thread] = None
        self._stop_playback = threading.Event()
        self._playback_lock = threading.Lock()
        
        # Callbacks for external integration
        self.step_callbacks: list[Callable[[int, Simulation], None]] = []
        self.state_change_callbacks: list[Callable[[PlaybackState], None]] = []
        self.error_callbacks: list[Callable[[str], None]] = []
        
        # Performance tracking
        self._last_step_time = 0.0
        
        # Cached simulation state for efficient incremental playback
        self._cached_simulation: Optional[Simulation] = None
        self._cached_step: int = 0
        self._step_times: list[float] = []
        
    @classmethod
    def load(cls, filepath: Path | str) -> PlaybackEngine:
        """Load a playback engine from a simulation output file.
        
        Args:
            filepath: Path to the .vmt simulation output file
            
        Returns:
            PlaybackEngine instance
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file is invalid or corrupted
        """
        output_file = load_simulation_output(filepath)
        return cls(output_file)
    
    def get_current_simulation(self) -> Simulation:
        """Get the current simulation state.
        
        Returns:
            Simulation object representing current state
            
        Raises:
            ValueError: If no step has been loaded yet
        """
        if self.state.current_step == 0:
            raise ValueError("No step loaded yet. Use seek_to_step() first.")
        
        simulation, _ = self.reconstructor.reconstruct_state_at_step(self.state.current_step)
        return simulation
    
    def seek_to_step(self, step: int) -> ReconstructionMetrics:
        """Seek to a specific step and reconstruct the simulation state.
        
        Args:
            step: Target step number (1-based)
            
        Returns:
            ReconstructionMetrics for performance tracking
            
        Raises:
            ValueError: If step is out of bounds
        """
        if step < 1 or step > self.state.total_steps:
            raise ValueError(f"Step {step} is out of bounds (1-{self.state.total_steps})")
        
        with self._playback_lock:
            # Stop any ongoing playback
            self._stop_playback.set()
            
            # Reconstruct state at target step
            simulation, metrics = self.reconstructor.reconstruct_state_at_step(step)
            
            # Update playback state
            old_step = self.state.current_step
            self.state.current_step = step
            self.state.is_at_end = (step == self.state.total_steps)
            
            # Cache the simulation state for efficient playback
            self._cached_simulation = simulation
            self._cached_step = step
            
            # Notify callbacks
            self._notify_step_callbacks(step, simulation)
            if old_step != step:
                self._notify_state_change_callbacks()
            
            return metrics
    
    def play(self) -> None:
        """Start automatic playback from current step.
        
        Playback will continue until paused, stopped, or reaching the end.
        Uses the current playback speed setting.
        """
        with self._playback_lock:
            if self.state.is_playing:
                return  # Already playing
            
            if self.state.is_at_end:
                return  # At end, can't play
            
            self.state.is_playing = True
            self._stop_playback.clear()
            self._notify_state_change_callbacks()
            
            # Start playback thread
            self._playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
            self._playback_thread.start()
    
    def pause(self) -> None:
        """Pause automatic playback.
        
        Current step remains unchanged.
        """
        with self._playback_lock:
            if not self.state.is_playing:
                return  # Not playing
            
            self.state.is_playing = False
            self._stop_playback.set()
            self._notify_state_change_callbacks()
    
    def stop(self) -> None:
        """Stop playback and reset to beginning.
        
        Equivalent to pause() + seek_to_step(1).
        """
        with self._playback_lock:
            self.state.is_playing = False
            self._stop_playback.set()
            
            # Reset to beginning
            self.state.current_step = 0
            self.state.is_at_end = False
            self._notify_state_change_callbacks()
    
    def set_playback_speed(self, speed: float) -> None:
        """Set the playback speed multiplier.
        
        Args:
            speed: Speed multiplier (1.0 = normal, 2.0 = 2x, 0.5 = half speed)
        """
        if speed <= 0:
            raise ValueError("Playback speed must be positive")
        
        with self._playback_lock:
            self.state.playback_speed = speed
    
    def step_forward(self) -> ReconstructionMetrics:
        """Step forward by one step.
        
        Returns:
            ReconstructionMetrics for performance tracking
            
        Raises:
            ValueError: If already at the end
        """
        if self.state.is_at_end:
            raise ValueError("Already at the end of simulation")
        
        return self.seek_to_step(self.state.current_step + 1)
    
    def step_backward(self) -> ReconstructionMetrics:
        """Step backward by one step.
        
        Returns:
            ReconstructionMetrics for performance tracking
            
        Raises:
            ValueError: If already at the beginning
        """
        if self.state.current_step <= 1:
            raise ValueError("Already at the beginning of simulation")
        
        return self.seek_to_step(self.state.current_step - 1)
    
    def _playback_loop(self) -> None:
        """Main playback loop running in background thread."""
        try:
            while not self._stop_playback.is_set() and not self.state.is_at_end:
                loop_start = time.time()
                
                # Step forward efficiently without expensive reconstruction
                try:
                    self._step_forward_efficient()
                except ValueError:
                    # Reached the end
                    break
                
                # Calculate sleep time based on playback speed
                # For unlimited speed, only sleep if speed is limited
                if self.state.playback_speed > 0:
                    target_step_duration = 1.0 / self.state.playback_speed
                    elapsed = time.time() - loop_start
                    sleep_time = max(0, target_step_duration - elapsed)
                    
                    if sleep_time > 0 and not self._stop_playback.wait(sleep_time):
                        # Sleep completed normally
                        continue
                    else:
                        # Sleep was interrupted or no sleep needed
                        break
                # For unlimited speed (playback_speed <= 0), don't sleep at all
                    
        except Exception as e:
            self._notify_error_callbacks(f"Playback error: {e}")
        finally:
            # Ensure we're marked as not playing
            with self._playback_lock:
                self.state.is_playing = False
                self._notify_state_change_callbacks()
    
    def _step_forward_efficient(self) -> None:
        """Step forward efficiently by caching reconstruction results."""
        if self.state.is_at_end:
            raise ValueError("Already at the end of simulation")
        
        next_step = self.state.current_step + 1
        
        # Check if we can use cached result
        if (self._cached_simulation and 
            self._cached_step == self.state.current_step and 
            next_step <= self.state.total_steps):
            
            # We already have the simulation state for current step
            # Just do a quick reconstruction for the next step
            try:
                # Use the reconstructor but with caching
                simulation, _ = self.reconstructor.reconstruct_state_at_step(next_step)
                
                # Update state
                self.state.current_step = next_step
                self.state.is_at_end = (next_step == self.state.total_steps)
                
                # Cache the new simulation state
                self._cached_simulation = simulation
                self._cached_step = next_step
                
                # Notify callbacks
                self._notify_step_callbacks(next_step, simulation)
                self._notify_state_change_callbacks()
                
                return
                
            except Exception:
                # Fall back to full seek_to_step if reconstruction fails
                pass
        
        # Fall back to full reconstruction (this will also cache the result)
        self.seek_to_step(next_step)
    
    def _notify_step_callbacks(self, step: int, simulation: Simulation) -> None:
        """Notify step callbacks of a step change."""
        for callback in self.step_callbacks:
            try:
                callback(step, simulation)
            except Exception as e:
                self._notify_error_callbacks(f"Step callback error: {e}")
    
    def _notify_state_change_callbacks(self) -> None:
        """Notify state change callbacks of playback state changes."""
        for callback in self.state_change_callbacks:
            try:
                callback(self.state)
            except Exception as e:
                self._notify_error_callbacks(f"State callback error: {e}")
    
    def _notify_error_callbacks(self, error: str) -> None:
        """Notify error callbacks of an error."""
        for callback in self.error_callbacks:
            try:
                callback(error)
            except Exception:
                pass  # Don't let error callbacks cause more errors
    
    def add_step_callback(self, callback: Callable[[int, Simulation], None]) -> None:
        """Add a callback for step changes.
        
        Args:
            callback: Function called with (step, simulation) on each step change
        """
        self.step_callbacks.append(callback)
    
    def add_state_change_callback(self, callback: Callable[[PlaybackState], None]) -> None:
        """Add a callback for playback state changes.
        
        Args:
            callback: Function called with PlaybackState on state changes
        """
        self.state_change_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[str], None]) -> None:
        """Add a callback for errors.
        
        Args:
            callback: Function called with error message on errors
        """
        self.error_callbacks.append(callback)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the playback engine.
        
        Returns:
            Dictionary with performance metrics
        """
        cache_stats = self.reconstructor.get_cache_stats()
        
        return {
            'current_step': self.state.current_step,
            'total_steps': self.state.total_steps,
            'playback_speed': self.state.playback_speed,
            'is_playing': self.state.is_playing,
            'is_at_end': self.state.is_at_end,
            'cache_stats': cache_stats,
            'reconstructor_available': self.reconstructor is not None
        }
    
    def is_playing(self) -> bool:
        """Check if playback is currently active.
        
        Returns:
            True if playing, False if paused/stopped
        """
        return self.state.is_playing
    
    def is_at_end(self) -> bool:
        """Check if playback is at the end of the simulation.
        
        Returns:
            True if at the end, False otherwise
        """
        return self.state.is_at_end
    
    def get_current_step(self) -> int:
        """Get the current step number.
        
        Returns:
            Current step number (1-based)
        """
        return self.state.current_step
    
    def get_total_steps(self) -> int:
        """Get the total number of steps.
        
        Returns:
            Total number of steps in the simulation
        """
        return self.state.total_steps
    
    def get_playback_speed(self) -> float:
        """Get the current playback speed.
        
        Returns:
            Current playback speed multiplier
        """
        return self.state.playback_speed
    
    def cleanup(self) -> None:
        """Clean up resources and stop playback."""
        with self._playback_lock:
            self.state.is_playing = False
            self._stop_playback.set()
            
            # Wait for playback thread to finish
            if self._playback_thread and self._playback_thread.is_alive():
                self._playback_thread.join(timeout=1.0)
            
            # Clear caches
            self.reconstructor.clear_cache()
            
            # Clear callbacks
            self.step_callbacks.clear()
            self.state_change_callbacks.clear()
            self.error_callbacks.clear()
