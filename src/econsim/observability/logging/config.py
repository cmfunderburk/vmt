"""Configuration classes for economic logging system.

This module provides configuration classes that are specifically
designed for the economic logging system, separate from the main
simulation configuration to avoid circular dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


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
