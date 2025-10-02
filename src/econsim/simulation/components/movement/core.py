"""Agent movement component for spatial navigation and pathfinding."""

from __future__ import annotations
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...grid import Grid

Position = tuple[int, int]

class AgentMovement:
    """Handles all agent movement operations with deterministic pathfinding."""
    
    def __init__(self, agent_id: int):
        self.agent_id = agent_id
    
    def move_random(self, current_pos: Position, grid: 'Grid', rng: random.Random) -> Position:
        """
        Move one step randomly in 4-neighborhood or stay put.
        
        Determinism: Uses fixed move list order, RNG only for selection.
        """
        x, y = current_pos
        moves = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]
        dx, dy = rng.choice(moves)
        nx, ny = x + dx, y + dy
        
        if 0 <= nx < grid.width and 0 <= ny < grid.height:
            return (nx, ny)
        return current_pos
    
    def move_toward_target(self, current_pos: Position, target: Position) -> Position:
        """
        Move one step toward target using greedy pathfinding.
        
        Tie-break: Horizontal priority if abs(dx) > abs(dy).
        """
        x, y = current_pos
        tx, ty = target
        
        if (x, y) == (tx, ty):
            return current_pos
        
        dx = tx - x
        dy = ty - y
        
        # Greedy: horizontal priority if abs(dx) > abs(dy)
        if abs(dx) > abs(dy):
            new_x = x + (1 if dx > 0 else -1)
            return (new_x, y)
        elif dy != 0:
            new_y = y + (1 if dy > 0 else -1)
            return (x, new_y)
        else:
            return current_pos
    
    def move_toward_meeting_point(self, current_pos: Position, meeting_point: Position) -> Position:
        """Move one step toward established meeting point."""
        return self.move_toward_target(current_pos, meeting_point)
