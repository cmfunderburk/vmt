"""Enhanced logging configuration system for VMT EconSim.

Provides runtime configuration capabilities for the debug logging system,
including dynamic log level changes, category filtering, and performance
monitoring without requiring simulation restart.

Environment Variables:
    ECONSIM_LOG_LEVEL: Controls verbosity (CRITICAL|EVENTS|PERIODIC|VERBOSE)
    ECONSIM_LOG_FORMAT: Output format (COMPACT|STRUCTURED) 
    ECONSIM_LOG_CATEGORIES: Comma-separated list of enabled categories
    ECONSIM_LOG_PERF_THRESHOLD: Performance logging threshold (steps/sec change %)
    ECONSIM_LOG_MAX_FILE_SIZE: Maximum log file size in MB before rotation
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Set, Optional, Dict, Any
from pathlib import Path
from enum import Enum


class LogLevel(Enum):
    """Logging verbosity levels."""
    CRITICAL = "CRITICAL"
    EVENTS = "EVENTS"
    PERIODIC = "PERIODIC"
    VERBOSE = "VERBOSE"


class LogFormat(Enum):
    """Log output formats."""
    COMPACT = "COMPACT"
    STRUCTURED = "STRUCTURED"


@dataclass
class LogConfig:
    """Runtime configuration for the debug logging system."""
    
    # Core settings
    # Default elevated to VERBOSE so full educational / diagnostic context is available
    level: LogLevel = LogLevel.VERBOSE
    format: LogFormat = LogFormat.COMPACT
    
    # Category filtering
    enabled_categories: Set[str] = field(default_factory=lambda: {
        "CRITICAL", "ERROR", "WARNING", "PHASE", "TRADE", "UTILITY", 
        "MODE", "SIMULATION", "PERFORMANCE"
    })
    disabled_categories: Set[str] = field(default_factory=lambda: set())
    
    # Performance monitoring
    perf_threshold_percent: float = 10.0  # Log when performance changes by this %
    perf_log_interval: int = 25  # Log performance every N steps
    
    # File management
    max_file_size_mb: float = 50.0  # Rotate logs when they exceed this size
    keep_rotated_files: int = 5  # Number of old log files to keep
    
    # Educational features
    include_explanations: bool = False  # Add educational context to economic events
    explain_decisions: bool = False  # Add decision reasoning to agent actions
    
    @classmethod
    def from_environment(cls) -> "LogConfig":
        """Create configuration from environment variables."""
        config = cls()
        
        # Parse log level
        # Default to VERBOSE (previously EVENTS) for richer default insight; callers can still override via env
        level_str = os.environ.get("ECONSIM_LOG_LEVEL", "VERBOSE").upper()
        try:
            config.level = LogLevel(level_str)
        except ValueError:
            config.level = LogLevel.EVENTS
            
        # Parse log format
        format_str = os.environ.get("ECONSIM_LOG_FORMAT", "COMPACT").upper()
        try:
            config.format = LogFormat(format_str)
        except ValueError:
            config.format = LogFormat.COMPACT
            
        # Parse category filters
        categories_str = os.environ.get("ECONSIM_LOG_CATEGORIES", "")
        if categories_str:
            config.enabled_categories = set(cat.strip().upper() 
                                          for cat in categories_str.split(",") 
                                          if cat.strip())
            
        # Parse performance threshold
        perf_str = os.environ.get("ECONSIM_LOG_PERF_THRESHOLD", "10.0")
        try:
            config.perf_threshold_percent = float(perf_str)
        except ValueError:
            config.perf_threshold_percent = 10.0
            
        # Parse file size limit
        size_str = os.environ.get("ECONSIM_LOG_MAX_FILE_SIZE", "50.0")
        try:
            config.max_file_size_mb = float(size_str)
        except ValueError:
            config.max_file_size_mb = 50.0
            
        # Parse educational flags
        config.include_explanations = os.environ.get("ECONSIM_LOG_EXPLANATIONS") == "1"
        config.explain_decisions = os.environ.get("ECONSIM_LOG_DECISION_REASONING") == "1"
        
        return config
        
    def should_log_category(self, category: str) -> bool:
        """Check if a specific category should be logged."""
        # Check disabled categories first
        if category in self.disabled_categories:
            return False
            
        # Check enabled categories
        if self.enabled_categories and category not in self.enabled_categories:
            return False
            
        # Apply log level filtering
        if self.level == LogLevel.VERBOSE:
            return True
        elif self.level == LogLevel.PERIODIC:
            return category in {
                "CRITICAL", "ERROR", "WARNING", "PHASE", "TRADE", 
                "UTILITY", "MODE", "PERIODIC_PERF", "PERIODIC_SIM", 
                "PERF", "SIMULATION"
            }
        elif self.level == LogLevel.EVENTS:
            return category in {
                "CRITICAL", "ERROR", "WARNING", "PHASE", "TRADE", 
                "UTILITY", "MODE", "SIMULATION"
            }
        elif self.level == LogLevel.CRITICAL:
            return category in {"CRITICAL", "ERROR", "WARNING", "PHASE"}
            
        return False
        
    def should_log_performance(self, step: int, steps_per_sec: float, 
                             last_steps_per_sec: float) -> bool:
        """Check if performance should be logged based on thresholds."""
        if self.level == LogLevel.VERBOSE:
            return True
            
        # Log every N steps in PERIODIC mode
        if self.level == LogLevel.PERIODIC and step % self.perf_log_interval == 0:
            return True
            
        # Log if significant performance change
        if last_steps_per_sec > 0:
            change_percent = abs(steps_per_sec - last_steps_per_sec) / last_steps_per_sec * 100
            if change_percent >= self.perf_threshold_percent:
                return True
                
        return False
        
    def enable_category(self, category: str) -> None:
        """Enable logging for a specific category."""
        category = category.upper()
        self.enabled_categories.add(category)
        self.disabled_categories.discard(category)
        
    def disable_category(self, category: str) -> None:
        """Disable logging for a specific category."""
        category = category.upper()
        self.disabled_categories.add(category)
        self.enabled_categories.discard(category)
        
    def set_level(self, level: LogLevel) -> None:
        """Set the logging level."""
        self.level = level
        
    def set_format(self, format: LogFormat) -> None:
        """Set the logging format."""
        self.format = format
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            "level": self.level.value if hasattr(self.level, 'value') else str(self.level),
            "format": self.format.value if hasattr(self.format, 'value') else str(self.format),
            "enabled_categories": list(self.enabled_categories),
            "disabled_categories": list(self.disabled_categories),
            "perf_threshold_percent": self.perf_threshold_percent,
            "perf_log_interval": self.perf_log_interval,
            "max_file_size_mb": self.max_file_size_mb,
            "keep_rotated_files": self.keep_rotated_files,
            "include_explanations": self.include_explanations,
            "explain_decisions": self.explain_decisions,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogConfig":
        """Create configuration from dictionary."""
        config = cls()
        
        # Parse level and format
        try:
            config.level = LogLevel(data.get("level", "EVENTS"))
        except ValueError:
            config.level = LogLevel.EVENTS
            
        try:
            config.format = LogFormat(data.get("format", "COMPACT"))
        except ValueError:
            config.format = LogFormat.COMPACT
            
        # Set other fields
        config.enabled_categories = set(data.get("enabled_categories", []))
        config.disabled_categories = set(data.get("disabled_categories", []))
        config.perf_threshold_percent = data.get("perf_threshold_percent", 10.0)
        config.perf_log_interval = data.get("perf_log_interval", 25)
        config.max_file_size_mb = data.get("max_file_size_mb", 50.0)
        config.keep_rotated_files = data.get("keep_rotated_files", 5)
        config.include_explanations = data.get("include_explanations", False)
        config.explain_decisions = data.get("explain_decisions", False)
        
        return config


class LogManager:
    """Manages runtime configuration changes to the logging system."""
    
    def __init__(self):
        self._config = LogConfig.from_environment()
        self._config_file = Path.cwd() / "gui_logs" / "log_config.json"
        
    @property
    def config(self) -> LogConfig:
        """Get current logging configuration."""
        return self._config
        
    def update_config(self, **kwargs: Any) -> None:
        """Update logging configuration with new values."""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                # Handle enum conversions
                if key == 'level' and isinstance(value, str):
                    try:
                        value = LogLevel(value.upper())
                    except ValueError:
                        continue  # Skip invalid values
                elif key == 'format' and isinstance(value, str):
                    try:
                        value = LogFormat(value.upper())
                    except ValueError:
                        continue  # Skip invalid values
                        
                setattr(self._config, key, value)
                
        # Optionally save to file for persistence
        self.save_config()
        
    def save_config(self, path: Optional[Path] = None) -> None:
        """Save current configuration to file."""
        if path is None:
            path = self._config_file
            
        path.parent.mkdir(exist_ok=True)
        
        import json
        with open(path, 'w') as f:
            json.dump(self._config.to_dict(), f, indent=2)
            
    def load_config(self, path: Optional[Path] = None) -> None:
        """Load configuration from file."""
        if path is None:
            path = self._config_file
            
        if not path.exists():
            return
            
        try:
            import json
            with open(path, 'r') as f:
                data = json.load(f)
            self._config = LogConfig.from_dict(data)
        except Exception:
            # Fall back to environment configuration if file is corrupted
            self._config = LogConfig.from_environment()


# Global log manager instance
_log_manager: Optional[LogManager] = None


def get_log_manager() -> LogManager:
    """Get the global log manager instance."""
    global _log_manager
    if _log_manager is None:
        _log_manager = LogManager()
    return _log_manager


def get_log_config() -> LogConfig:
    """Get current logging configuration."""
    return get_log_manager().config


def update_log_config(**kwargs: Any) -> None:
    """Update logging configuration at runtime."""
    get_log_manager().update_config(**kwargs)