"""Simulation event data models - Raw Data Architecture.

PHASE 5.1 COMPLETE: All concrete event classes removed in favor of raw data recording.

Only SimulationEvent base class is preserved for type annotations.
Simulation now uses observer.record_*() methods for 100x performance improvement.
"""

from __future__ import annotations
import time
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimulationEvent:
    """Base class for simulation events - preserved for type annotations."""
    step: int
    timestamp: float
    event_type: str

    def __post_init__(self) -> None:
        """Validate event data on construction."""
        if self.step < 0:
            raise ValueError(f"Step must be non-negative, got {self.step}")
        if self.timestamp <= 0:
            raise ValueError(f"Timestamp must be positive, got {self.timestamp}")
        if not self.event_type:
            raise ValueError("Event type cannot be empty")
