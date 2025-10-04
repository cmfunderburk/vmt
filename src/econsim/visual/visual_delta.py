"""
Visual Delta Data Structure

Represents the visual changes that occurred at a single simulation step.
Only tracks what pygame needs to render, not full simulation state.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass(frozen=True)
class VisualDelta:
    """Represents visual changes at a single simulation step."""
    
    step: int
    agent_moves: List[Tuple[int, int, int, int, int]]  # (agent_id, old_x, old_y, new_x, new_y)
    agent_state_changes: List[Tuple[int, bool]]  # (agent_id, is_carrying)
    resource_changes: List[Tuple[int, int, Optional[str]]]  # (x, y, resource_type_or_None)
    
    def is_empty(self) -> bool:
        """Check if this delta has any changes."""
        return (len(self.agent_moves) == 0 and 
                len(self.agent_state_changes) == 0 and 
                len(self.resource_changes) == 0)
    
    def get_summary(self) -> str:
        """Get a human-readable summary of changes."""
        parts = []
        if self.agent_moves:
            parts.append(f"{len(self.agent_moves)} agent moves")
        if self.agent_state_changes:
            parts.append(f"{len(self.agent_state_changes)} state changes")
        if self.resource_changes:
            parts.append(f"{len(self.resource_changes)} resource changes")
        
        if parts:
            return f"Step {self.step}: {', '.join(parts)}"
        else:
            return f"Step {self.step}: No changes"


@dataclass
class VisualState:
    """Current visual state for pygame rendering."""
    
    step: int
    agent_positions: dict[int, Tuple[int, int]]  # agent_id -> (x, y)
    agent_states: dict[int, bool]  # agent_id -> is_carrying
    resource_positions: dict[Tuple[int, int], str]  # (x, y) -> resource_type
    
    def get_agent_list(self) -> List[Tuple[int, int, int, bool]]:
        """Get agents as list of (id, x, y, carrying)."""
        return [
            (agent_id, x, y, self.agent_states.get(agent_id, False))
            for agent_id, (x, y) in self.agent_positions.items()
        ]
    
    def get_resource_list(self) -> List[Tuple[int, int, str]]:
        """Get resources as list of (x, y, resource_type)."""
        return [
            (x, y, resource_type)
            for (x, y), resource_type in self.resource_positions.items()
        ]
