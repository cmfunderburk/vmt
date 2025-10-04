"""Simulation configuration and factory integration.

Provides authoritative parameter bundle for deterministic simulation construction.
The `Simulation.from_config` factory method consumes this configuration to
initialize simulation state, attach optional hooks, and seed RNG systems.

Supports comprehensive parameter validation and serves as the single source
of truth for simulation behavioral configuration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence, Union, Optional
from pathlib import Path

ResourceEntry = Union[tuple[int, int], tuple[int, int, str]]




@dataclass(slots=True)
class SimConfig:
    """Comprehensive simulation configuration with validation and factory integration.
    
    Defines all parameters for deterministic simulation construction including
    core simulation settings, behavioral flags, algorithm tuning, and GUI integration.
    
    Attributes:
        grid_size: Grid dimensions as (width, height)
        initial_resources: Resource placement as (x, y) or (x, y, type) tuples
        perception_radius: Agent decision scan radius (Manhattan distance)
        respawn_target_density: Target resource density fraction (0..1]
        respawn_rate: Fraction of resource deficit addressed per step (0..1] 
        max_spawn_per_tick: Maximum resources spawned per step (rate limiting)
        seed: Base RNG seed for deterministic behavior
        enable_respawn: Enable automatic resource regeneration
        enable_metrics: Enable metrics collection and determinism hashing
        viewport_size: GUI viewport dimension in pixels (320-800)
        distance_scaling_factor: Utility distance discount factor k in ΔU/(1+k*d²)
    """
    grid_size: tuple[int, int]
    initial_resources: Sequence[ResourceEntry]
    perception_radius: int = 8
    respawn_target_density: float = 0.25
    respawn_rate: float = 0.25  # Partial replenishment default (GUI configurable)
    max_spawn_per_tick: int = 100  # Sufficient for full deficit handling
    seed: int = 0
    enable_respawn: bool = True
    enable_metrics: bool = True
    viewport_size: int = 320
    distance_scaling_factor: float = 0.0  # No distance penalty default

    def validate(self) -> None:
        """Validate configuration parameters for simulation construction.
        
        Ensures all parameters are within acceptable ranges and constraints
        required for deterministic simulation behavior.
        """
        gw, gh = self.grid_size
        if gw <= 0 or gh <= 0:
            raise ValueError("grid_size dimensions must be positive")
        if not (0.0 <= self.respawn_target_density <= 1.0):
            raise ValueError("respawn_target_density must be within [0,1]")
        if self.respawn_rate < 0:
            raise ValueError("respawn_rate must be non-negative")
        if not (320 <= self.viewport_size <= 800):
            raise ValueError("viewport_size must be within [320, 800]")
        if self.max_spawn_per_tick < 0:
            raise ValueError("max_spawn_per_tick must be non-negative")
        if not (0.0 <= self.distance_scaling_factor <= 10.0):
            raise ValueError("distance_scaling_factor must be within [0,10]")
        # Boolean flags validated implicitly by type system


__all__ = ["SimConfig", "ResourceEntry"]
