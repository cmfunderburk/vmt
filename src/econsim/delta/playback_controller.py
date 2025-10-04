"""
Comprehensive Delta Playback Controller

Provides playback functionality for comprehensive simulation deltas, supporting both
visual rendering and economic analysis. Replaces the current DeltaPlaybackController
with a system that can reconstruct complete simulation state from comprehensive deltas.
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
    """Comprehensive playback controller for simulation deltas."""
    
    def __init__(self):
        """Initialize the playback controller."""
        self.deltas: List[SimulationDelta] = []
        self.current_state: PlaybackState = PlaybackState()
        self.serializer = DeltaSerializer()
        
        # Callbacks for external components
        self.step_callbacks: List[Callable[[int], None]] = []
        self.state_change_callbacks: List[Callable[[VisualState], None]] = []
        self.economic_callbacks: List[Callable[[List[EconomicDecision]], None]] = []
        
        # Reconstructed state for analysis
        self._reconstructed_visual_state: Optional[VisualState] = None
        self._reconstructed_agent_states: Dict[int, Dict[str, Any]] = {}
        self._reconstructed_economic_state: Dict[str, Any] = {}
    
    @classmethod
    def load_from_file(cls, file_path: str) -> ComprehensivePlaybackController:
        """Load comprehensive deltas from a MessagePack file.
        
        Args:
            file_path: Path to the delta file
            
        Returns:
            ComprehensivePlaybackController with loaded deltas
        """
        controller = cls()
        controller.deltas = controller.serializer.load_from_file(file_path)
        controller.current_state.total_steps = len(controller.deltas)
        
        if controller.deltas:
            # Initialize to first step
            controller.current_state.current_step = 1
            controller._reconstruct_state_at_step(1)
        
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
        return self._reconstructed_visual_state
    
    def get_economic_data(self, step: Optional[int] = None) -> Dict[str, Any]:
        """Get economic data for a specific step or current step.
        
        Args:
            step: Step number (None for current step)
            
        Returns:
            Dictionary containing economic data
        """
        target_step = step if step is not None else self.current_state.current_step
        
        if target_step < 1 or target_step > len(self.deltas):
            return {}
        
        delta = self.deltas[target_step - 1]
        
        return {
            'step': target_step,
            'trade_events': [event.__dict__ for event in delta.trade_events],
            'trade_intents': [intent.__dict__ for intent in delta.trade_intents],
            'economic_decisions': [decision.__dict__ for decision in delta.economic_decisions],
            'agent_utility_changes': [change.__dict__ for change in delta.agent_utility_changes],
            'performance_metrics': delta.performance_metrics.__dict__ if delta.performance_metrics else None
        }
    
    def get_agent_state(self, agent_id: int, step: Optional[int] = None) -> Dict[str, Any]:
        """Get the state of a specific agent at a specific step.
        
        Args:
            agent_id: Agent ID
            step: Step number (None for current step)
            
        Returns:
            Dictionary containing agent state
        """
        target_step = step if step is not None else self.current_state.current_step
        
        if target_step < 1 or target_step > len(self.deltas):
            return {}
        
        delta = self.deltas[target_step - 1]
        
        # Find agent-specific events
        agent_moves = [move for move in delta.agent_moves if move.agent_id == agent_id]
        agent_mode_changes = [change for change in delta.agent_mode_changes if change.agent_id == agent_id]
        agent_inventory_changes = [change for change in delta.agent_inventory_changes if change.agent_id == agent_id]
        agent_target_changes = [change for change in delta.agent_target_changes if change.agent_id == agent_id]
        agent_utility_changes = [change for change in delta.agent_utility_changes if change.agent_id == agent_id]
        
        return {
            'agent_id': agent_id,
            'step': target_step,
            'moves': [move.__dict__ for move in agent_moves],
            'mode_changes': [change.__dict__ for change in agent_mode_changes],
            'inventory_changes': [change.__dict__ for change in agent_inventory_changes],
            'target_changes': [change.__dict__ for change in agent_target_changes],
            'utility_changes': [change.__dict__ for change in agent_utility_changes]
        }
    
    def play(self) -> None:
        """Start playing the deltas."""
        self.current_state.is_playing = True
        self.current_state.is_paused = False
        # Note: Playback loop should be handled by external timer, not blocking call
    
    def pause(self) -> None:
        """Pause playback."""
        self.current_state.is_playing = False
        self.current_state.is_paused = True
    
    def step_forward(self) -> None:
        """Step forward one step if playing."""
        if self.current_state.is_playing and self.current_state.current_step < self.current_state.total_steps:
            next_step = self.current_state.current_step + 1
            self._step_forward_efficient(next_step)
    
    def stop(self) -> None:
        """Stop playback and reset to beginning."""
        self.current_state.is_playing = False
        self.current_state.is_paused = False
        self.seek_to_step(1)
    
    def seek_to_step(self, step: int) -> None:
        """Seek to a specific step.
        
        Args:
            step: Target step number (1-based)
        """
        if step < 1 or step > self.current_state.total_steps:
            return
        
        self.current_state.current_step = step
        self._reconstruct_state_at_step(step)
        
        # Notify callbacks
        for callback in self.step_callbacks:
            callback(step)
        
        if self._reconstructed_visual_state:
            for callback in self.state_change_callbacks:
                callback(self._reconstructed_visual_state)
    
    def set_playback_speed(self, steps_per_second: float) -> None:
        """Set the playback speed.
        
        Args:
            steps_per_second: Number of steps to advance per second
        """
        self.current_state.playback_speed = steps_per_second
    
    def get_playback_speed(self) -> float:
        """Get the current playback speed."""
        return self.current_state.playback_speed
    
    def _playback_loop(self) -> None:
        """Main playback loop."""
        while self.current_state.is_playing and self.current_state.current_step <= self.current_state.total_steps:
            start_time = time.time()
            
            # Advance to next step
            next_step = self.current_state.current_step + 1
            if next_step <= self.current_state.total_steps:
                self._step_forward_efficient(next_step)
            
            # Calculate sleep time based on playback speed
            if self.current_state.playback_speed > 0:
                elapsed = time.time() - start_time
                target_interval = 1.0 / self.current_state.playback_speed
                sleep_time = max(0, target_interval - elapsed)
                time.sleep(sleep_time)
    
    def _step_forward_efficient(self, target_step: int) -> None:
        """Efficiently step forward to target step by applying only the next delta.
        
        Args:
            target_step: Target step number
        """
        if target_step < 1 or target_step > self.current_state.total_steps:
            return
        
        # Apply the delta for the target step
        delta = self.deltas[target_step - 1]
        self._apply_delta(delta)
        
        self.current_state.current_step = target_step
        
        # Notify callbacks
        for callback in self.step_callbacks:
            callback(target_step)
        
        if self._reconstructed_visual_state:
            for callback in self.state_change_callbacks:
                callback(self._reconstructed_visual_state)
        
        # Notify economic callbacks
        if delta.economic_decisions:
            for callback in self.economic_callbacks:
                callback(delta.economic_decisions)
    
    def _reconstruct_state_at_step(self, step: int) -> None:
        """Reconstruct complete state at a specific step.
        
        Args:
            step: Target step number (1-based)
        """
        if step < 1 or step > self.current_state.total_steps:
            return
        
        # Start from initial state and apply all deltas up to target step
        self._reset_to_initial_state()
        
        for i in range(step):
            delta = self.deltas[i]
            self._apply_delta(delta)
    
    def _reset_to_initial_state(self) -> None:
        """Reset to initial state (step 0)."""
        # Initialize empty state
        self._reconstructed_visual_state = VisualState(
            step=0,
            agent_positions={},
            agent_states={},
            resource_positions={}
        )
        self._reconstructed_agent_states = {}
        self._reconstructed_economic_state = {}
    
    def _apply_delta(self, delta: SimulationDelta) -> None:
        """Apply a delta to the reconstructed state.
        
        Args:
            delta: Delta to apply
        """
        # Apply visual changes
        self._apply_visual_delta(delta.visual_changes)
        
        # Apply agent changes
        self._apply_agent_changes(delta)
        
        # Apply resource changes
        self._apply_resource_changes(delta)
        
        # Update economic state
        self._update_economic_state(delta)
    
    def _apply_visual_delta(self, visual_delta: VisualDelta) -> None:
        """Apply visual delta to reconstructed visual state."""
        if not self._reconstructed_visual_state:
            return
        
        # Apply agent moves
        for agent_id, old_x, old_y, new_x, new_y in visual_delta.agent_moves:
            self._reconstructed_visual_state.agent_positions[agent_id] = (new_x, new_y)
        
        # Apply agent state changes
        for agent_id, is_carrying in visual_delta.agent_state_changes:
            self._reconstructed_visual_state.agent_states[agent_id] = is_carrying
        
        # Apply resource changes
        for x, y, resource_type in visual_delta.resource_changes:
            pos = (x, y)
            if resource_type is None:
                # Resource was depleted
                if pos in self._reconstructed_visual_state.resource_positions:
                    del self._reconstructed_visual_state.resource_positions[pos]
            else:
                # Resource was spawned or changed
                self._reconstructed_visual_state.resource_positions[pos] = resource_type
        
        # Update step
        self._reconstructed_visual_state.step = visual_delta.step
    
    def _apply_agent_changes(self, delta: SimulationDelta) -> None:
        """Apply agent changes to reconstructed agent states."""
        # This would track agent mode, inventory, target, utility changes
        # For now, we'll focus on visual state reconstruction
        pass
    
    def _apply_resource_changes(self, delta: SimulationDelta) -> None:
        """Apply resource changes to reconstructed resource state."""
        # This would track resource spawns, depletions, collections
        # For now, we'll focus on visual state reconstruction
        pass
    
    def _update_economic_state(self, delta: SimulationDelta) -> None:
        """Update reconstructed economic state."""
        # This would track trade events, economic decisions, utility changes
        # For now, we'll focus on visual state reconstruction
        pass
    
    def get_summary(self) -> str:
        """Get a summary of the current playback state."""
        return (f"Step {self.current_state.current_step}/{self.current_state.total_steps} "
                f"({'Playing' if self.current_state.is_playing else 'Paused'}) "
                f"Speed: {self.current_state.playback_speed:.1f} steps/sec")
