"""Spatial indexing utilities for unified target selection.

AgentSpatialGrid provides O(n) rebuild + near O(agents_in_radius) queries
for agents within a Manhattan perception radius. Deterministic ordering is
achieved by preserving insertion order and applying a stable sort key when
emitting query results.
"""
from __future__ import annotations
from typing import List, Dict, Tuple, Iterable

from .agent import Agent

Cell = Tuple[int, int]

class AgentSpatialGrid:
    __slots__ = ("width", "height", "_cells")

    def __init__(self, width: int, height: int) -> None:
        self.width = int(width)
        self.height = int(height)
        # Dict[Cell, List[Agent]]; Python 3.11 dict preserves insertion order
        self._cells: Dict[Cell, List[Agent]] = {}

    def clear(self) -> None:
        self._cells.clear()

    def add_agent(self, x: int, y: int, agent: Agent) -> None:
        # No bounds enforcement here (Simulation ensures agent positions valid)
        cell = (int(x), int(y))
        bucket = self._cells.get(cell)
        if bucket is None:
            self._cells[cell] = [agent]
        else:
            bucket.append(agent)

    def get_agents_in_radius(self, x: int, y: int, radius: int) -> List[Agent]:
        # Collect candidate cells via square scan then filter by Manhattan distance (still O(k))
        cx, cy = int(x), int(y)
        r = int(radius)
        candidates: List[Agent] = []
        # Bounding box; radius expected small (<= default_PERCEPTION_RADIUS)
        for dx in range(-r, r + 1):
            rx = cx + dx
            if rx < 0 or rx >= self.width:
                continue
            # Limit dy by remaining manhattan budget to reduce iterations
            max_dy = r - abs(dx)
            for dy in range(-max_dy, max_dy + 1):
                ry = cy + dy
                if ry < 0 or ry >= self.height:
                    continue
                bucket = self._cells.get((rx, ry))
                if not bucket:
                    continue
                # Append in stored order (insertion order = original agent ordering for that cell)
                for agent in bucket:
                    if agent.x == cx and agent.y == cy and agent.id != getattr(agent, 'id', None):  # defensive no-op
                        continue
                    candidates.append(agent)
        # Deterministic ordering: sort once by (distance, id)
        candidates.sort(key=lambda a: (abs(a.x - cx) + abs(a.y - cy), a.id))
        return candidates

__all__ = ["AgentSpatialGrid"]
