"""
Delta Playback Controller

Manages delta-based playback for pygame visualization.
Reconstructs visual state by applying deltas sequentially.
"""

import threading
import time
from typing import List, Optional, Callable, Tuple
from dataclasses import dataclass

from .visual_delta import VisualDelta, VisualState
from .delta_recorder import VisualDeltaRecorder


@dataclass
class PlaybackState:
    """Current playback state."""
    current_step: int
    total_steps: int
    is_playing: bool
    is_at_end: bool
    playback_speed: float  # steps per second, 0 = unlimited


class DeltaPlaybackController:
    """Controls delta-based playback for pygame visualization."""
    
    def __init__(self, initial_state: VisualState, visual_deltas: List[VisualDelta]):
        """Initialize delta playback controller.
        
        Args:
            initial_state: Initial visual state (step 0)
            visual_deltas: List of visual deltas for each step
        """
        self.initial_state = initial_state
        self.visual_deltas = visual_deltas
        self.total_steps = len(visual_deltas)
        
        # Current visual state
        self.current_visual_state = initial_state
        self.current_step = 0
        
        # Playback state
        self.state = PlaybackState(
            current_step=0,
            total_steps=self.total_steps,
            is_playing=False,
            is_at_end=False,
            playback_speed=2.0  # Default: 2 steps per second
        )
        
        # Playback control
        self._playback_thread: Optional[threading.Thread] = None
        self._stop_playback = threading.Event()
        self._playback_lock = threading.Lock()
        
        # Callbacks
        self._step_callbacks: List[Callable[[int, VisualState], None]] = []
        self._state_change_callbacks: List[Callable[[PlaybackState], None]] = []
    
    def seek_to_step(self, step: int) -> None:
        """Seek to a specific step and reconstruct visual state.
        
        Args:
            step: Target step number (0-based)
        """
        if step < 0 or step > self.total_steps:
            raise ValueError(f"Step {step} is out of bounds (0-{self.total_steps})")
        
        with self._playback_lock:
            # Stop any ongoing playback
            self._stop_playback.set()
            
            # Reconstruct visual state up to target step
            self._reconstruct_visual_state(step)
            
            # Update playback state
            old_step = self.state.current_step
            self.state.current_step = step
            self.state.is_at_end = (step == self.total_steps)
            
            # Notify callbacks
            self._notify_step_callbacks(step, self.current_visual_state)
            if old_step != step:
                self._notify_state_change_callbacks()
    
    def _reconstruct_visual_state(self, target_step: int) -> None:
        """Reconstruct visual state by applying deltas up to target step."""
        # Start with initial state
        self.current_visual_state = VisualState(
            step=0,
            agent_positions=self.initial_state.agent_positions.copy(),
            agent_states=self.initial_state.agent_states.copy(),
            resource_positions=self.initial_state.resource_positions.copy()
        )
        
        # Apply deltas up to target step
        for i in range(target_step):
            if i < len(self.visual_deltas):
                delta = self.visual_deltas[i]
                self._apply_delta(delta)
                self.current_visual_state.step = i + 1
        
        self.current_step = target_step
    
    def _apply_delta(self, delta: VisualDelta) -> None:
        """Apply a visual delta to current state."""
        # Apply agent moves
        for agent_id, old_x, old_y, new_x, new_y in delta.agent_moves:
            self.current_visual_state.agent_positions[agent_id] = (new_x, new_y)
        
        # Apply agent state changes
        for agent_id, is_carrying in delta.agent_state_changes:
            self.current_visual_state.agent_states[agent_id] = is_carrying
        
        # Apply resource changes
        for x, y, resource_type in delta.resource_changes:
            if resource_type is not None:
                self.current_visual_state.resource_positions[(x, y)] = resource_type
            else:
                # Resource removed
                self.current_visual_state.resource_positions.pop((x, y), None)
    
    def play(self) -> None:
        """Start playback from current step."""
        if self.state.is_at_end:
            return
        
        with self._playback_lock:
            if self.state.is_playing:
                return  # Already playing
            
            self.state.is_playing = True
            self._stop_playback.clear()
            
            # Start playback thread
            self._playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
            self._playback_thread.start()
            
            self._notify_state_change_callbacks()
    
    def pause(self) -> None:
        """Pause playback."""
        with self._playback_lock:
            self.state.is_playing = False
            self._stop_playback.set()
            
            if self._playback_thread and self._playback_thread.is_alive():
                self._playback_thread.join(timeout=0.1)
            
            self._notify_state_change_callbacks()
    
    def stop(self) -> None:
        """Stop playback and reset to beginning."""
        self.pause()
        self.seek_to_step(0)
    
    def _playback_loop(self) -> None:
        """Main playback loop (runs in separate thread)."""
        while not self._stop_playback.is_set() and not self.state.is_at_end:
            start_time = time.time()
            
            # Move to next step
            next_step = self.state.current_step + 1
            if next_step <= self.total_steps:
                # Use efficient step forward instead of full seek
                self._step_forward_efficient(next_step)
            
            # Check current speed dynamically (allows speed changes during playback)
            current_speed = self.state.playback_speed
            step_interval = 1.0 / current_speed if current_speed > 0 else 0
            
            # Wait for next step (if not unlimited speed)
            if step_interval > 0:
                elapsed = time.time() - start_time
                sleep_time = max(0, step_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
    
    def _step_forward_efficient(self, target_step: int) -> None:
        """Efficiently step forward by applying only the next delta."""
        if target_step > self.total_steps or target_step < 0:
            return
        
        # Apply the delta for this step
        if target_step > 0 and target_step <= len(self.visual_deltas):
            delta = self.visual_deltas[target_step - 1]
            self._apply_delta(delta)
        
        # Update state
        old_step = self.state.current_step
        self.state.current_step = target_step
        self.state.is_at_end = (target_step == self.total_steps)
        
        # Update current visual state
        self.current_visual_state.step = target_step
        
        # Notify callbacks
        self._notify_step_callbacks(target_step, self.current_visual_state)
        if old_step != target_step:
            self._notify_state_change_callbacks()
    
    def set_playback_speed(self, speed: float) -> None:
        """Set playback speed in steps per second (0 = unlimited)."""
        with self._playback_lock:
            self.state.playback_speed = speed
    
    def get_current_step(self) -> int:
        """Get current step number."""
        return self.state.current_step
    
    def get_total_steps(self) -> int:
        """Get total number of steps."""
        return self.state.total_steps
    
    def get_visual_state(self) -> VisualState:
        """Get current visual state for pygame rendering."""
        return self.current_visual_state
    
    def is_playing(self) -> bool:
        """Check if currently playing."""
        return self.state.is_playing
    
    def is_at_end(self) -> bool:
        """Check if at the end."""
        return self.state.is_at_end
    
    def get_playback_state(self) -> PlaybackState:
        """Get current playback state."""
        return self.state
    
    # Callback management
    def add_step_callback(self, callback: Callable[[int, VisualState], None]) -> None:
        """Add callback for step changes."""
        self._step_callbacks.append(callback)
    
    def add_state_change_callback(self, callback: Callable[[PlaybackState], None]) -> None:
        """Add callback for playback state changes."""
        self._state_change_callbacks.append(callback)
    
    def _notify_step_callbacks(self, step: int, visual_state: VisualState) -> None:
        """Notify step change callbacks."""
        for callback in self._step_callbacks:
            try:
                callback(step, visual_state)
            except Exception as e:
                print(f"Warning: Step callback error: {e}")
    
    def _notify_state_change_callbacks(self) -> None:
        """Notify state change callbacks."""
        for callback in self._state_change_callbacks:
            try:
                callback(self.state)
            except Exception as e:
                print(f"Warning: State callback error: {e}")
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'DeltaPlaybackController':
        """Load delta playback controller from file.
        
        Args:
            file_path: Path to visual delta file
            
        Returns:
            DeltaPlaybackController instance
        """
        initial_state, visual_deltas = VisualDeltaRecorder.load_deltas(file_path)
        return cls(initial_state, visual_deltas)
