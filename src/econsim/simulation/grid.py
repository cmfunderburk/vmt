"""Grid abstraction (Gates 3–5 implemented).

Stores typed resources using a dict mapping ``(x,y) -> type`` providing
O(1) average membership, deterministic sorted iteration (for target
selection / hashing), and coordinate validation.

Capabilities:
* Add / remove typed resources (A,B)
* Deterministic serialization & sorted iteration helper
* Backward-compatible boolean removal API (`take_resource`)

Deferred:
* Resource quantities >1 per cell
* Spatial indexing optimizations (performance currently sufficient)
* Rich resource metadata (value, regeneration profile)
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

Coord = tuple[int, int]
ResourceType = str  # For Gate 4: simple 'A','B' literal types


@dataclass(slots=True)
class Grid:
    width: int
    height: int
    _resources: dict[Coord, ResourceType]

    def __init__(
        self,
        width: int,
        height: int,
        resources: Iterable[tuple[int, int] | tuple[int, int, ResourceType]] | None = None,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("Grid dimensions must be positive")
        self.width = width
        self.height = height
        self._resources = {}
        if resources:
            for entry in resources:
                if len(entry) == 2:  # type: ignore[arg-type]
                    x, y = entry  # type: ignore[misc]
                    rtype: ResourceType = "A"
                elif len(entry) == 3:  # type: ignore[arg-type]
                    x, y, rtype = entry  # type: ignore[misc]
                else:  # pragma: no cover (defensive)
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
        self._check_bounds(x, y)
        self._resources[(x, y)] = rtype

    def has_resource(self, x: int, y: int) -> bool:
        self._check_bounds(x, y)
        return (x, y) in self._resources

    def take_resource_type(self, x: int, y: int) -> ResourceType | None:
        """Remove and return resource type if present; else None.

        Raises ValueError for out-of-bounds coordinates.
        """
        self._check_bounds(x, y)
        return self._resources.pop((x, y), None)

    def take_resource(self, x: int, y: int) -> bool:
        """Backward-compatible boolean removal API (Gate 3 compatibility)."""
        return self.take_resource_type(x, y) is not None

    # --- Introspection / Serialization ------------------------------
    def resource_count(self) -> int:
        return len(self._resources)

    # Lightweight iterator for (x,y,type) to support decision logic without exposing internal dict
    def iter_resources(self):  # pragma: no cover (simple generator)
        for (x, y), rtype in self._resources.items():
            yield x, y, rtype

    # Stable sorted iteration (deterministic scoring / hashing order)
    def iter_resources_sorted(self):  # pragma: no cover (simple)
        for (x, y), rtype in sorted(self._resources.items()):
            yield x, y, rtype

    def serialize(self) -> dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "resources": [
                (x, y, rtype) for (x, y), rtype in sorted(self._resources.items())
            ],  # stable order
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Grid:
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
    def __repr__(self) -> str:  # pragma: no cover (debug convenience)
        return f"Grid({self.width}x{self.height}, resources={len(self._resources)})"


__all__ = ["Grid", "Coord", "ResourceType"]
