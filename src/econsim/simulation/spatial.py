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
    
    Performance optimizations:
    - Supports incremental updates to avoid full rebuilds
    - Tracks agent positions for efficient updates
    - Maintains cache consistency for deterministic behavior
    
    Typical usage:
        index = AgentSpatialGrid(grid_width, grid_height)
        for agent in agents:
            index.add_agent(agent.x, agent.y, agent)
        nearby = index.get_agents_in_radius(x, y, perception_radius)
        
    Cached usage:
        index.update_agent_positions(agents)  # Incremental update
        nearby = index.get_agents_in_radius(x, y, perception_radius)
    """
    __slots__ = ("width", "height", "_cells", "_agent_positions")

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
        # Track agent positions for incremental updates
        self._agent_positions: Dict[int, Cell] = {}

    def clear(self) -> None:
        """Clear all agents from spatial index for rebuilding."""
        self._cells.clear()
        self._agent_positions.clear()

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
        
        # Track agent position for incremental updates
        self._agent_positions[agent.id] = cell

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

    def update_agent_positions(self, agents: List[Agent]) -> None:
        """Update spatial index with current agent positions (incremental update).
        
        This method provides significant performance improvement over rebuilding
        the entire spatial index every step. It only updates agents that have
        moved since the last update.
        
        Args:
            agents: List of agents with current positions
        """
        # Track which agents need to be updated
        agents_to_update = []
        
        for agent in agents:
            current_pos = (agent.x, agent.y)
            old_pos = self._agent_positions.get(agent.id)
            
            if old_pos != current_pos:
                agents_to_update.append((agent, old_pos, current_pos))
        
        # Update only agents that have moved
        for agent, old_pos, new_pos in agents_to_update:
            # Remove from old position if it existed
            if old_pos is not None:
                old_bucket = self._cells.get(old_pos)
                if old_bucket is not None:
                    try:
                        old_bucket.remove(agent)
                        if not old_bucket:  # Remove empty bucket
                            del self._cells[old_pos]
                    except ValueError:
                        pass  # Agent not in old bucket (shouldn't happen)
            
            # Add to new position
            new_bucket = self._cells.get(new_pos)
            if new_bucket is None:
                self._cells[new_pos] = [agent]
            else:
                new_bucket.append(agent)
            
            # Update position tracking
            self._agent_positions[agent.id] = new_pos

    def rebuild_from_agents(self, agents: List[Agent]) -> None:
        """Rebuild spatial index from scratch (fallback for cache invalidation).
        
        Args:
            agents: List of agents to index
        """
        self.clear()
        for agent in agents:
            self.add_agent(agent.x, agent.y, agent)

__all__ = ["AgentSpatialGrid"]
