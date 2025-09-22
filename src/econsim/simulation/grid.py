"""Grid abstraction (Gate 3).

Minimal 2D grid storing resource locations as coordinate tuples.

Design goals:
- O(1) average membership & removal using a set of (x,y) tuples.
- Validation of coordinates to prevent silent out-of-bounds logic errors.
- Simple, explicit API; no iteration helpers yet (add later if needed).

Deferrals:
- Resource types / quantities.
- Dynamic respawn.
- Spatial indexing optimizations (unnecessary at current scale).
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

Coord = tuple[int, int]


@dataclass(slots=True)
class Grid:
    width: int
    height: int
    _resources: set[Coord]

    def __init__(self, width: int, height: int, resources: Iterable[Coord] | None = None) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("Grid dimensions must be positive")
        self.width = width
        self.height = height
        self._resources = set()
        if resources:
            for coord in resources:
                self.add_resource(*coord)

    # --- Validation -------------------------------------------------
    def _check_bounds(self, x: int, y: int) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(f"Coordinate ({x},{y}) out of bounds for {self.width}x{self.height} grid")

    # --- Core API ---------------------------------------------------
    def add_resource(self, x: int, y: int) -> None:
        self._check_bounds(x, y)
        self._resources.add((x, y))

    def has_resource(self, x: int, y: int) -> bool:
        self._check_bounds(x, y)
        return (x, y) in self._resources

    def take_resource(self, x: int, y: int) -> bool:
        """Remove resource if present; return True if removed, else False.
        Raises ValueError for out-of-bounds coordinates.
        """
        self._check_bounds(x, y)
        try:
            self._resources.remove((x, y))
            return True
        except KeyError:
            return False

    # --- Introspection / Serialization ------------------------------
    def resource_count(self) -> int:
        return len(self._resources)

    def serialize(self) -> dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "resources": sorted(self._resources),  # stable order for deterministic tests
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Grid:
        width = int(data["width"])  # may raise KeyError/ValueError intentionally
        height = int(data["height"])
        resources = data.get("resources", [])
        if not isinstance(resources, list):  # defensive
            raise ValueError("Serialized grid 'resources' must be a list")
        typed_resources: list[Coord] = []
        for r in resources:  # type: ignore[assignment]
            # Accept list/tuple of two numeric-like values
            if not isinstance(r, (list, tuple)):
                raise ValueError("Each resource must be a sequence of length 2")
            if len(r) != 2:  # type: ignore[arg-type]
                raise ValueError("Each resource must have length 2")
            x_raw, y_raw = r  # type: ignore[misc]
            x, y = int(x_raw), int(y_raw)  # type: ignore[arg-type]
            typed_resources.append((x, y))
        return cls(width, height, typed_resources)

    # --- Representation ---------------------------------------------
    def __repr__(self) -> str:  # pragma: no cover (debug convenience)
        return f"Grid({self.width}x{self.height}, resources={len(self._resources)})"

__all__ = ["Grid", "Coord"]
