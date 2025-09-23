"""Simulation package.

Deterministic spatial grid + agent model (Gates 3–5) including decision
logic and optional hooks (respawn, metrics) prepared for Gate 6 factory
integration. Deferrals: prices, budgets, pathfinding, multi-resource
optimization heuristics, trading/markets.
"""

from .grid import Grid

__all__ = ["Grid"]
