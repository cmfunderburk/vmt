"""Step execution context for handler coordination.

This module defines the immutable context object passed between step handlers
during simulation execution. The context encapsulates all necessary state and
configuration needed for deterministic step processing.

Design Principles:
- Immutable context prevents accidental state mutation between handlers
- Centralized access to simulation state, configuration, and observer registry
- Type-safe interfaces for handler coordination
- Performance-focused with minimal overhead per step
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..features import SimulationFeatures
    from ..world import Simulation


@dataclass(frozen=True, slots=True)
class StepContext:
    """Immutable context passed between step handlers.
    
    Encapsulates all state and configuration needed for deterministic
    step processing. Handlers receive this context and return results
    without directly mutating simulation state.
    
    Attributes:
        simulation: Reference to the main simulation instance
        step_number: Current step number for temporal tracking  
        ext_rng: External RNG for legacy random movement mode
        feature_flags: Centralized feature flag configuration
    """
    simulation: 'Simulation'
    step_number: int
    ext_rng: random.Random
    feature_flags: 'SimulationFeatures'
    
    def __post_init__(self) -> None:
        """Validate context invariants."""
        if self.step_number < 0:
            raise ValueError(f"Step number must be non-negative, got {self.step_number}")
