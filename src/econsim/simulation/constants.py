"""Simulation constants (Gate 4).

Centralizes tunable parameters for decision logic & perception.
"""

from __future__ import annotations

# Perception radius (Manhattan) for candidate resource scan
default_PERCEPTION_RADIUS: int = 8

# Epsilon for Cobb-Douglas bootstrap (strictly positive utilities when a good is zero)
EPSILON_UTILITY: float = 1e-6

__all__ = ["default_PERCEPTION_RADIUS", "EPSILON_UTILITY"]
