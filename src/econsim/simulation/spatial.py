"""Spatial indexing optimization for efficient agent proximity queries.

Provides AgentSpatialGrid for fast agent-to-agent lookups within Manhattan
distance perception radius. Essential for unified target selection and
bilateral trading systems where agents need to find nearby trading partners.

Performance: O(n) rebuild per step, O(agents_in_radius) queries with
deterministic ordering guarantees for simulation reproducibility.
"""
from __future__ import annotations
from typing import List, Dict, Tuple, Iterable

from .agent import Agent

Cell = Tuple[int, int]  # Grid coordinate (x, y)

class AgentSpatialGrid:
    """Spatial index for efficient agent proximity queries with deterministic ordering.
    
    Optimizes agent-to-agent lookups by partitioning agents into grid cells,
    enabling fast radius-based queries for trading partner discovery and
    unified target selection. Maintains deterministic ordering for reproducible
    simulation behavior.
    
    Typical usage:
        index = AgentSpatialGrid(grid_width, grid_height)
        for agent in agents:
            index.add_agent(agent.x, agent.y, agent)
        nearby = index.get_agents_in_radius(x, y, perception_radius)
    """
    __slots__ = ("width", "height", "_cells")

    def __init__(self, width: int, height: int) -> None:
        """Initialize spatial grid with specified dimensions.
        
        Args:
            width: Grid width in cells
            height: Grid height in cells
        """
        self.width = int(width)
        self.height = int(height)
        # Dict preserves insertion order for deterministic behavior
        self._cells: Dict[Cell, List[Agent]] = {}

    def clear(self) -> None:
        """Clear all agents from spatial index for rebuilding."""
        self._cells.clear()

    def add_agent(self, x: int, y: int, agent: Agent) -> None:
        """Add agent to spatial index at specified coordinates.
        
        Args:
            x: Agent x coordinate
            y: Agent y coordinate  
            agent: Agent instance to index
        """
        # Coordinates assumed valid (enforced by simulation)
        cell = (int(x), int(y))
        bucket = self._cells.get(cell)
        if bucket is None:
            self._cells[cell] = [agent]
        else:
            bucket.append(agent)

    def get_agents_in_radius(self, x: int, y: int, radius: int) -> List[Agent]:
        """Find all agents within Manhattan distance radius of coordinates.
        
        Uses optimized bounding box scan with Manhattan distance constraint
        to minimize cell iterations. Results sorted deterministically by
        distance then agent ID for reproducible simulation behavior.
        
        Args:
            x: Center x coordinate
            y: Center y coordinate
            radius: Maximum Manhattan distance to search
            
        Returns:
            List of agents within radius, sorted by (distance, agent_id)
        """
        cx, cy = int(x), int(y)
        r = int(radius)
        candidates: List[Agent] = []
        
        # Scan bounding box with Manhattan distance constraint
        for dx in range(-r, r + 1):
            rx = cx + dx
            if rx < 0 or rx >= self.width:
                continue
            # Limit dy by remaining Manhattan budget
            max_dy = r - abs(dx)
            for dy in range(-max_dy, max_dy + 1):
                ry = cy + dy
                if ry < 0 or ry >= self.height:
                    continue
                bucket = self._cells.get((rx, ry))
                if not bucket:
                    continue
                # Collect agents from cell (preserving insertion order)
                for agent in bucket:
                    if agent.x == cx and agent.y == cy:  # Skip self-queries
                        continue
                    candidates.append(agent)
        
        # Deterministic ordering by distance then agent ID
        candidates.sort(key=lambda a: (abs(a.x - cx) + abs(a.y - cy), a.id))
        return candidates

__all__ = ["AgentSpatialGrid"]
