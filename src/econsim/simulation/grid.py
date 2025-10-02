"""2D grid for typed resource storage with deterministic iteration.

Stores typed resources using a dict mapping (x,y) -> type providing
O(1) membership testing, deterministic sorted iteration for reproducible
behavior, and coordinate validation.

Features:
* Add/remove typed resources (A, B types)
* Deterministic serialization with stable ordering
* Backward-compatible boolean removal API
* Coordinate bounds checking

Current scope: Single resource per cell, simple A/B typing.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Set

Coord = tuple[int, int]
ResourceType = str  # A, B resource types


@dataclass(slots=True)
class Grid:
    """2D grid storing typed resources with coordinate validation.
    
    Uses dict-based storage for O(1) operations and provides deterministic
    iteration order for reproducible simulations.
    
    Performance optimizations:
    - Maintains _empty_cells set for O(1) empty cell access
    - Caches _resource_count to avoid len() calls
    """
    width: int
    height: int
    _resources: dict[Coord, ResourceType]
    _empty_cells: Set[Coord]
    _resource_count: int

    def __init__(
        self,
        width: int,
        height: int,
        resources: Iterable[tuple[int, int] | tuple[int, int, ResourceType]] | None = None,
    ) -> None:
        """Initialize grid with optional resources.
        
        Args:
            width: Grid width (must be positive)
            height: Grid height (must be positive) 
            resources: Optional iterable of (x,y) or (x,y,type) tuples.
                      Default type 'A' used for (x,y) entries.
        """
        if width <= 0 or height <= 0:
            raise ValueError("Grid dimensions must be positive")
        self.width = width
        self.height = height
        self._resources = {}
        
        # Initialize empty cells set with all possible coordinates
        self._empty_cells = set((x, y) for x in range(width) for y in range(height))
        self._resource_count = 0
        
        if resources:
            for entry in resources:
                if len(entry) == 2:  # type: ignore[arg-type]
                    x, y = entry  # type: ignore[misc]
                    rtype: ResourceType = "A"
                elif len(entry) == 3:  # type: ignore[arg-type]
                    x, y, rtype = entry  # type: ignore[misc]
                else:
                    raise ValueError("Resource entry must have length 2 or 3")
                self.add_resource(int(x), int(y), str(rtype))

    # --- Validation -------------------------------------------------
    def _check_bounds(self, x: int, y: int) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(
                f"Coordinate ({x},{y}) out of bounds for {self.width}x{self.height} grid"
            )

    # --- Core API ---------------------------------------------------
    def add_resource(self, x: int, y: int, rtype: ResourceType = "A") -> None:
        """Add resource of specified type at position."""
        self._check_bounds(x, y)
        coord = (x, y)
        
        # Only update caches if cell was empty
        if coord in self._empty_cells:
            self._empty_cells.remove(coord)
            self._resource_count += 1
        
        self._resources[coord] = rtype

    def has_resource(self, x: int, y: int) -> bool:
        """Check if resource exists at position."""
        self._check_bounds(x, y)
        return (x, y) in self._resources

    def take_resource_type(self, x: int, y: int) -> ResourceType | None:
        """Remove and return resource type at position, or None if empty."""
        self._check_bounds(x, y)
        coord = (x, y)
        rtype = self._resources.pop(coord, None)
        
        if rtype is not None:
            self._empty_cells.add(coord)
            self._resource_count -= 1
        
        return rtype

    def take_resource(self, x: int, y: int) -> bool:
        """Remove resource at position, returning True if found."""
        return self.take_resource_type(x, y) is not None

    # --- Introspection / Serialization ------------------------------
    def resource_count(self) -> int:
        """Return total number of resources on grid (cached)."""
        return self._resource_count

    def get_empty_cells(self) -> Set[Coord]:
        """Get set of empty cells (O(1) operation)."""
        return self._empty_cells.copy()

    def get_empty_cells_list(self) -> list[Coord]:
        """Get list of empty cells (O(empty_count) operation)."""
        return list(self._empty_cells)

    def iter_resources(self):
        """Iterate over resources as (x, y, type) tuples."""
        for (x, y), rtype in self._resources.items():
            yield x, y, rtype

    def iter_resources_sorted(self):
        """Iterate over resources in deterministic sorted order."""
        for (x, y), rtype in sorted(self._resources.items()):
            yield x, y, rtype

    def serialize(self) -> dict[str, Any]:
        """Export grid state to JSON-serializable dict with stable ordering."""
        return {
            "width": self.width,
            "height": self.height,
            "resources": [
                (x, y, rtype) for (x, y), rtype in sorted(self._resources.items())
            ],  # stable order
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Grid:
        """Create grid from serialized data dict."""
        width = int(data["width"])  # may raise KeyError/ValueError intentionally
        height = int(data["height"])
        resources_raw = data.get("resources", [])
        if not isinstance(resources_raw, list):
            raise ValueError("Serialized grid 'resources' must be a list")
        typed_resources: list[tuple[int, int, ResourceType]] = []
        for entry in resources_raw:  # type: ignore[assignment]
            if not isinstance(entry, (list, tuple)) or len(entry) not in (2, 3):  # type: ignore[arg-type]
                raise ValueError("Each resource entry must be (x,y) or (x,y,type)")
            x = int(entry[0])  # type: ignore[index]
            y = int(entry[1])  # type: ignore[index]
            rtype: ResourceType = str(entry[2]) if len(entry) == 3 else "A"  # type: ignore[index]
            typed_resources.append((x, y, rtype))
        return cls(width, height, typed_resources)

    # --- Representation ---------------------------------------------
    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return f"Grid({self.width}x{self.height}, resources={len(self._resources)})"


__all__ = ["Grid", "Coord", "ResourceType"]
