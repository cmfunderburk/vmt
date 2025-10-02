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
class EconomicLoggingConfig:
    """Configuration for economic logging system.
    
    Provides comprehensive configuration for economic behavior logging
    with optimized serialization and performance features.
    
    Attributes:
        enabled: Whether economic logging is enabled
        log_level: Logging level (DEBUG, INFO, WARN, ERROR)
        categories: List of event categories to log
        output_dir: Directory for log files (None = auto-generated)
        format: Output format (optimized, jsonl, json, csv)
        buffer_size: Event buffer size for batch processing
        auto_rotate: Whether to automatically rotate log files
        max_file_size: Maximum file size before rotation (bytes)
        use_optimized_format: Enable 73%+ size reduction optimization
        batch_size: Events per batch for optimized format
        enable_relative_timestamps: Use relative timestamps within steps
    """
    enabled: bool = True
    log_level: str = "INFO"
    categories: list[str] = field(default_factory=lambda: ["ALL"])
    output_dir: Optional[Path] = None
    format: str = "optimized"  # optimized, jsonl, json, csv
    buffer_size: int = 1000
    auto_rotate: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # Optimized format configuration
    use_optimized_format: bool = True  # Enable 73%+ size reduction
    batch_size: int = 5  # Events per batch for optimized format
    enable_relative_timestamps: bool = True  # Relative timestamps within steps
    
    @classmethod
    def from_dict(cls, data: dict) -> EconomicLoggingConfig:
        """Create config from dictionary."""
        return cls(**data)
    
    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "enabled": self.enabled,
            "log_level": self.log_level,
            "categories": self.categories,
            "output_dir": str(self.output_dir) if self.output_dir else None,
            "format": self.format,
            "buffer_size": self.buffer_size,
            "auto_rotate": self.auto_rotate,
            "max_file_size": self.max_file_size,
            "use_optimized_format": self.use_optimized_format,
            "batch_size": self.batch_size,
            "enable_relative_timestamps": self.enable_relative_timestamps,
        }
    
    def get_effective_output_dir(self, base_dir: Optional[Path] = None) -> Path:
        """Get the effective output directory for log files.
        
        Args:
            base_dir: Base directory if output_dir is None
            
        Returns:
            Path to use for log file output
        """
        if self.output_dir is not None:
            return self.output_dir
        
        # Default to economic_analysis_logs for consistency
        return Path("economic_analysis_logs")


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
    economic_logging: Optional[EconomicLoggingConfig] = None

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


__all__ = ["SimConfig", "ResourceEntry", "EconomicLoggingConfig"]
