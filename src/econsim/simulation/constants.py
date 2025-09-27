"""Simulation constants (Gate 4).

Centralizes tunable parameters for decision logic & perception.
"""

from __future__ import annotations

# Perception radius (Manhattan) for candidate resource scan
default_PERCEPTION_RADIUS: int = 8

# Epsilon for Cobb-Douglas bootstrap (strictly positive utilities when a good is zero)
EPSILON_UTILITY: float = 1e-6

# Utility scaling factor to reduce floating-point precision sensitivity
# All utility functions multiply their result by this factor for educational clarity
# and computational robustness. Does not affect economic ordinality.
UTILITY_SCALE_FACTOR: float = 100.0

# Unified target selection distance discount scaling factor (k) default.
# Governs inverse-square distance penalty: discounted = base / (1 + k * d^2)
# Range enforced at config level [0.0, 10.0]. Kept here for deterministic default.
DEFAULT_DISTANCE_SCALING_FACTOR: float = 0.0

__all__ = [
	"default_PERCEPTION_RADIUS",
	"EPSILON_UTILITY",
	"UTILITY_SCALE_FACTOR",
	"DEFAULT_DISTANCE_SCALING_FACTOR",
]
