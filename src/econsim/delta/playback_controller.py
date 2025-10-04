"""
Comprehensive Delta Playback Controller

Simplified step-by-step playback controller for comprehensive simulation deltas.
Eliminates complex seeking behavior in favor of efficient forward/backward stepping.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Callable, Any
from dataclasses import dataclass

from .data_structures import (
    SimulationDelta, VisualDelta, VisualState,
    AgentMove, AgentModeChange, InventoryChange, TargetChange, UtilityChange,
    ResourceCollection, ResourceSpawn, ResourceDepletion,
    TradeEvent, TradeIntent, EconomicDecision,
    PerformanceMetrics, DebugEvent
)
from .serializer import DeltaSerializer


@dataclass
class PlaybackState:
    """Current state of the playback controller."""
    current_step: int = 0
    is_playing: bool = False
    playback_speed: float = 2.0  # steps per second
    total_steps: int = 0
    is_paused: bool = False


class ComprehensivePlaybackController:
    """Simplified step-by-step playback controller for simulation deltas."""
    
    def __init__(self):
        """Initialize the playback controller."""
        self.deltas: List[SimulationDelta] = []
        self.current_state: PlaybackState = PlaybackState()
        self.serializer = DeltaSerializer()
        
        # Callbacks for external components
        self.step_callbacks: List[Callable[[int], None]] = []
        self.state_change_callbacks: List[Callable[[VisualState], None]] = []
        self.economic_callbacks: List[Callable[[List[EconomicDecision]], None]] = []
        
        # Current visual state (maintained step-by-step, no reconstruction)
        self._current_visual_state: Optional[VisualState] = None
        
        # Store grid dimensions from initial state
        self._grid_width: int = 20  # Default
        self._grid_height: int = 20  # Default
    
    @classmethod
    def load_from_file(cls, file_path: str) -> ComprehensivePlaybackController:
        """Load comprehensive deltas from a MessagePack file.
        
        Args:
            file_path: Path to the delta file
            
        Returns:
            ComprehensivePlaybackController with loaded deltas
        """
        controller = cls()
        controller.deltas, initial_state = controller.serializer.load_from_file_with_initial_state(file_path)
        controller.current_state.total_steps = len(controller.deltas)
        
        # Extract grid dimensions from initial state if available
        if initial_state:
            controller._grid_width = initial_state.grid_width
            controller._grid_height = initial_state.grid_height
        
        if controller.deltas:
            # Initialize visual state from first delta's visual changes
            controller._initialize_visual_state_from_first_delta()
            
            # Set to step 1 (first delta represents step 1)
            controller.current_state.current_step = 1
        
        print(f"📁 Loaded {len(controller.deltas)} comprehensive deltas from {file_path}")
        return controller
    
    def add_step_callback(self, callback: Callable[[int], None]) -> None:
        """Add a callback for step changes."""
        self.step_callbacks.append(callback)
    
    def add_state_change_callback(self, callback: Callable[[VisualState], None]) -> None:
        """Add a callback for visual state changes."""
        self.state_change_callbacks.append(callback)
    
    def add_economic_callback(self, callback: Callable[[List[EconomicDecision]], None]) -> None:
        """Add a callback for economic state changes."""
        self.economic_callbacks.append(callback)
    
    def get_current_step(self) -> int:
        """Get the current step number."""
        return self.current_state.current_step
    
    def get_total_steps(self) -> int:
        """Get the total number of steps."""
        return self.current_state.total_steps
    
    def get_visual_state(self) -> Optional[VisualState]:
        """Get the current visual state for pygame rendering."""
        return self._current_visual_state
    
    def get_economic_data(self, step: Optional[int] = None) -> Dict[str, Any]:
        """Get economic data for a specific step or current step.
        
        Args:
            step: Step number (None for current step)
            
        Returns:
            Dictionary containing economic data
        """
        target_step = step or self.current_state.current_step
        if target_step < 1 or target_step > len(self.deltas):
            return {}
        
        delta = self.deltas[target_step - 1]
        return {
            "trade_events": len(delta.trade_events),
            "trade_intents": len(delta.trade_intents),
            "economic_decisions": len(delta.economic_decisions),
            "agent_moves": len(delta.agent_moves),
            "resource_collections": len(delta.resource_collections),
            "resource_spawns": len(delta.resource_spawns),
            "resource_depletions": len(delta.resource_depletions),
        }
    
    def play(self) -> None:
        """Start playback."""
        self.current_state.is_playing = True
        self.current_state.is_paused = False
    
    def pause(self) -> None:
        """Pause playback."""
        self.current_state.is_playing = False
        self.current_state.is_paused = True
    
    def step_forward(self) -> bool:
        """Step forward one step in playback.
        
        Returns:
            True if step was successful, False if at end
        """
        if self.current_state.current_step < self.current_state.total_steps:
            # Apply the current delta to move to next step
            delta = self.deltas[self.current_state.current_step - 1]  # 0-based index
            self._apply_delta_forward(delta)
            self.current_state.current_step += 1
            self._notify_callbacks()
            return True
        return False
    
    def step_backward(self) -> bool:
        """Step backward one step in playback.
        
        Returns:
            True if step was successful, False if at beginning
        """
        if self.current_state.current_step > 1:
            # Undo the previous delta to go back
            delta = self.deltas[self.current_state.current_step - 2]  # Previous delta (0-based index)
            self._apply_delta_backward(delta)
            self.current_state.current_step -= 1
            self._notify_callbacks()
            return True
        return False
    
    def stop(self) -> None:
        """Stop playback and reset to beginning."""
        self.current_state.is_playing = False
        self.current_state.is_paused = False
        self.current_state.current_step = 1
        self._initialize_visual_state_from_first_delta()
        self._notify_callbacks()
    
    def set_playback_speed(self, steps_per_second: float) -> None:
        """Set the playback speed.
        
        Args:
            steps_per_second: Number of steps to advance per second
        """
        self.current_state.playback_speed = max(0.1, min(100.0, steps_per_second))
    
    def _initialize_visual_state_from_first_delta(self) -> None:
        """Initialize visual state from the first delta's visual changes."""
        if not self.deltas:
            return
            
        first_delta = self.deltas[0]
        visual_delta = first_delta.visual_changes
        
        # Extract initial agent positions from agent moves
        agent_positions = {}
        agent_states = {}
        
        # Process agent moves to get initial positions
        for agent_id, old_x, old_y, new_x, new_y in visual_delta.agent_moves:
            # Store the new position (where agent ends up after step 1)
            agent_positions[agent_id] = (new_x, new_y)
            # Initialize carrying state (will be updated by state changes)
            agent_states[agent_id] = False
        
        # Apply agent state changes from first delta
        for agent_id, is_carrying in visual_delta.agent_state_changes:
            agent_states[agent_id] = is_carrying
        
        # Extract initial resource positions from resource changes
        resource_positions = {}
        for x, y, resource_type in visual_delta.resource_changes:
            if resource_type is not None:
                resource_positions[(x, y)] = resource_type
        
        # Use the grid dimensions from the initial state
        self._current_visual_state = VisualState(
            step=1,
            agent_positions=agent_positions,
            agent_states=agent_states,
            resource_positions=resource_positions,
            grid_width=self._grid_width,
            grid_height=self._grid_height
        )
    
    def _apply_delta_forward(self, delta: SimulationDelta) -> None:
        """Apply a delta forward to advance the visual state."""
        if not self._current_visual_state:
            return
            
        visual_delta = delta.visual_changes
        
        # Apply agent moves
        for agent_id, old_x, old_y, new_x, new_y in visual_delta.agent_moves:
            self._current_visual_state.agent_positions[agent_id] = (new_x, new_y)
        
        # Apply agent state changes
        for agent_id, is_carrying in visual_delta.agent_state_changes:
            self._current_visual_state.agent_states[agent_id] = is_carrying
        
        # Apply resource changes
        for x, y, resource_type in visual_delta.resource_changes:
            if resource_type is not None:
                self._current_visual_state.resource_positions[(x, y)] = resource_type
            elif (x, y) in self._current_visual_state.resource_positions:
                # Resource was removed
                del self._current_visual_state.resource_positions[(x, y)]
        
        # Update step number
        self._current_visual_state.step = delta.step
    
    def _apply_delta_backward(self, delta: SimulationDelta) -> None:
        """Apply a delta backward to reverse the visual state."""
        if not self._current_visual_state:
            return
            
        visual_delta = delta.visual_changes
        
        # Reverse agent moves
        for agent_id, old_x, old_y, new_x, new_y in visual_delta.agent_moves:
            self._current_visual_state.agent_positions[agent_id] = (old_x, old_y)
        
        # Note: Agent state changes and resource changes are harder to reverse
        # For now, we'll leave them as-is since backward playback is less critical
        
        # Update step number
        self._current_visual_state.step = delta.step
    
    def _notify_callbacks(self) -> None:
        """Notify all registered callbacks."""
        # Notify step callbacks
        for callback in self.step_callbacks:
            callback(self.current_state.current_step)
        
        # Notify visual state callbacks
        if self._current_visual_state:
            for callback in self.state_change_callbacks:
                callback(self._current_visual_state)
    
    def get_summary(self) -> str:
        """Get a summary of the current playback state."""
        return (f"Step {self.current_state.current_step}/{self.current_state.total_steps} "
                f"({'Playing' if self.current_state.is_playing else 'Paused'}) "
                f"Speed: {self.current_state.playback_speed:.1f} steps/sec")