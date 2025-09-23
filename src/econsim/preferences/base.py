"""Base Preference interface (Gate 2 foundation).

A Preference encapsulates a utility representation over a 2-good bundle.
The minimal Gate 2 contract intentionally omits optimization logic; it
focuses on utility evaluation, parameter management, and serialization.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .types import Bundle


class PreferenceError(ValueError):
    """Domain or parameter validation error for a preference."""


@dataclass
class PreferenceMeta:
    type_name: str
    description: str


class Preference(ABC):
    """Abstract base for all preference types (2-good Gate 2 scope).

    Extension points:
    - Add N-good support by generalizing Bundle alias (types.py) and updating implementations.
    - Introduce optimization helpers (e.g., marginal rates) in Gate 3+.
    Keep this surface minimal now to prevent premature coupling to agents/grid.
    """

    meta: PreferenceMeta

    def __init__(self, meta: PreferenceMeta) -> None:
        self.meta = meta

    # --- Core API -----------------------------------------------------
    @abstractmethod
    def utility(self, bundle: Bundle) -> float:
        """Return utility for (x,y).
        Implementations must be pure (no mutation) and fast.
        """

    @abstractmethod
    def describe_parameters(self) -> Mapping[str, str]:
        """Return mapping param_name -> human readable constraint summary."""

    @abstractmethod
    def update_params(self, **params: Any) -> None:
        """Validate and update internal parameters atomically.
        Should raise PreferenceError on invalid input.
        """

    @abstractmethod
    def serialize(self) -> dict[str, Any]:
        """Return canonical dict: {"type": str, "params": {...}}"""

    @classmethod
    @abstractmethod
    def deserialize(cls, payload: Mapping[str, Any]) -> Preference:
        """Reconstruct instance from serialize() output."""

    # --- Helpers ------------------------------------------------------
    @staticmethod
    def _ensure_non_negative(bundle: Bundle) -> None:
        x, y = bundle
        if x < 0 or y < 0:
            raise PreferenceError("Bundle values must be non-negative")


__all__ = [
    "Preference",
    "PreferenceMeta",
    "PreferenceError",
]
