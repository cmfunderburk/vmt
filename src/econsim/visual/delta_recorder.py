"""
Visual Delta Recorder

Records visual deltas during simulation execution, tracking only what pygame needs to render.
"""

import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict

from .visual_delta import VisualDelta, VisualState


class VisualDeltaRecorder:
    """Records visual deltas during simulation execution."""
    
    def __init__(self, output_path: str):
        """Initialize visual delta recorder.
        
        Args:
            output_path: Path where visual deltas will be saved
        """
        self.output_path = Path(output_path)
        self.visual_deltas: List[VisualDelta] = []
        
        # State tracking for delta detection
        self._last_agent_positions: Dict[int, Tuple[int, int]] = {}
        self._last_agent_states: Dict[int, bool] = {}
        self._last_resources: Dict[Tuple[int, int], str] = {}
        
        # Initial state (step 0)
        self._initial_state: Optional[VisualState] = None
    
    def record_initial_state(self, simulation) -> None:
        """Record the initial visual state (step 0).
        
        Args:
            simulation: Initial simulation state
        """
        agent_positions = {}
        agent_states = {}
        resource_positions = {}
        
        # Record initial agent positions and states
        for agent in simulation.agents:
            agent_positions[agent.id] = (agent.x, agent.y)
            agent_states[agent.id] = getattr(agent, 'carrying', False)
        
        # Record initial resource positions
        try:
            for x, y, resource_type in simulation.grid.iter_resources():
                resource_positions[(x, y)] = str(resource_type)
        except Exception as e:
            print(f"Warning: Could not record initial resources: {e}")
        
        self._initial_state = VisualState(
            step=0,
            agent_positions=agent_positions,
            agent_states=agent_states,
            resource_positions=resource_positions
        )
        
        # Initialize tracking state
        self._last_agent_positions = agent_positions.copy()
        self._last_agent_states = agent_states.copy()
        self._last_resources = resource_positions.copy()
        
        print(f"📊 Recorded initial state: {len(agent_positions)} agents, {len(resource_positions)} resources")
    
    def record_step(self, simulation, step: int) -> VisualDelta:
        """Record visual delta for a simulation step.
        
        Args:
            simulation: Current simulation state
            step: Current step number
            
        Returns:
            VisualDelta containing changes from previous step
        """
        agent_moves = []
        agent_state_changes = []
        resource_changes = []
        
        # Track agent movements and state changes
        for agent in simulation.agents:
            agent_id = agent.id
            current_pos = (agent.x, agent.y)
            current_carrying = getattr(agent, 'carrying', False)
            
            # Check for position changes
            if agent_id in self._last_agent_positions:
                last_pos = self._last_agent_positions[agent_id]
                if current_pos != last_pos:
                    agent_moves.append((agent_id, last_pos[0], last_pos[1], current_pos[0], current_pos[1]))
            
            # Check for state changes
            if agent_id in self._last_agent_states:
                last_carrying = self._last_agent_states[agent_id]
                if current_carrying != last_carrying:
                    agent_state_changes.append((agent_id, current_carrying))
            
            # Update tracking state
            self._last_agent_positions[agent_id] = current_pos
            self._last_agent_states[agent_id] = current_carrying
        
        # Track resource changes (simplified - just record what's currently visible)
        current_resources = {}
        try:
            for x, y, resource_type in simulation.grid.iter_resources():
                current_resources[(x, y)] = str(resource_type)
        except Exception as e:
            print(f"Warning: Could not record resources at step {step}: {e}")
        
        # Find resource changes
        all_resource_positions = set(self._last_resources.keys()) | set(current_resources.keys())
        for pos in all_resource_positions:
            old_type = self._last_resources.get(pos)
            new_type = current_resources.get(pos)
            
            if old_type != new_type:
                resource_changes.append((pos[0], pos[1], new_type))
        
        # Update tracking state
        self._last_resources = current_resources
        
        # Create visual delta
        delta = VisualDelta(
            step=step,
            agent_moves=agent_moves,
            agent_state_changes=agent_state_changes,
            resource_changes=resource_changes
        )
        
        # Store delta
        self.visual_deltas.append(delta)
        
        # Debug output for non-empty deltas
        if not delta.is_empty():
            print(f"🎬 {delta.get_summary()}")
        
        return delta
    
    def save_deltas(self) -> None:
        """Save visual deltas to disk."""
        if not self._initial_state:
            raise RuntimeError("Cannot save deltas without initial state")
        
        data = {
            'initial_state': self._initial_state,
            'visual_deltas': self.visual_deltas,
            'total_steps': len(self.visual_deltas)
        }
        
        with open(self.output_path, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"💾 Saved {len(self.visual_deltas)} visual deltas to {self.output_path}")
    
    @classmethod
    def load_deltas(cls, file_path: str) -> Tuple[VisualState, List[VisualDelta]]:
        """Load visual deltas from disk.
        
        Args:
            file_path: Path to visual delta file
            
        Returns:
            Tuple of (initial_state, visual_deltas)
        """
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        
        initial_state = data['initial_state']
        visual_deltas = data['visual_deltas']
        
        print(f"📁 Loaded {len(visual_deltas)} visual deltas from {file_path}")
        
        return initial_state, visual_deltas
