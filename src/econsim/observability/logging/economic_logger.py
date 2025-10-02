"""Economic logging utilities and helpers.

This module provides utility functions and helpers for economic logging,
including configuration helpers and integration with the observer system.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .config import EconomicLoggingConfig
from .file_manager import EconomicLogFileManager


def create_economic_logging_config_from_environment() -> EconomicLoggingConfig:
    """Create economic logging configuration from environment variables.
    
    Reads economic logging configuration from environment variables
    and creates a configuration object with appropriate defaults.
    
    Returns:
        EconomicLoggingConfig with settings from environment
    """
    # Economic logging configuration
    enabled = os.environ.get("ECONSIM_ECONOMIC_LOGGING", "1") == "1"
    log_level = os.environ.get("ECONSIM_ECONOMIC_LOG_LEVEL", "INFO")
    categories = os.environ.get("ECONSIM_ECONOMIC_LOG_CATEGORIES", "ALL").split(",")
    output_dir = os.environ.get("ECONSIM_ECONOMIC_LOG_OUTPUT_DIR")
    format_type = os.environ.get("ECONSIM_ECONOMIC_LOG_FORMAT", "optimized")
    buffer_size = int(os.environ.get("ECONSIM_ECONOMIC_LOG_BUFFER_SIZE", "1000"))
    
    # Optimized format configuration (73%+ size reduction)
    use_optimized = os.environ.get("ECONSIM_ECONOMIC_USE_OPTIMIZED", "1") == "1"
    batch_size = int(os.environ.get("ECONSIM_ECONOMIC_BATCH_SIZE", "5"))
    relative_timestamps = os.environ.get("ECONSIM_ECONOMIC_RELATIVE_TIMESTAMPS", "1") == "1"
    
    return EconomicLoggingConfig(
        enabled=enabled,
        log_level=log_level,
        categories=categories,
        output_dir=Path(output_dir) if output_dir else None,
        format=format_type,
        buffer_size=buffer_size,
        auto_rotate=True,
        max_file_size=10 * 1024 * 1024,  # 10MB
        use_optimized_format=use_optimized,
        batch_size=batch_size,
        enable_relative_timestamps=relative_timestamps,
    )


def create_economic_log_file_manager(
    config: Optional[EconomicLoggingConfig] = None,
    base_dir: Optional[Path] = None
) -> Optional[EconomicLogFileManager]:
    """Create an economic log file manager with appropriate configuration.
    
    Args:
        config: Economic logging configuration (creates from environment if None)
        base_dir: Base directory for log files (uses current directory if None)
        
    Returns:
        EconomicLogFileManager instance or None if logging is disabled
    """
    if config is None:
        config = create_economic_logging_config_from_environment()
    
    if not config.enabled:
        return None
    
    return EconomicLogFileManager(config, base_dir)


def get_economic_log_directory() -> Path:
    """Get the default economic log directory.
    
    Returns:
        Path to the default economic log directory
    """
    output_dir = os.environ.get("ECONSIM_ECONOMIC_LOG_OUTPUT_DIR")
    if output_dir:
        return Path(output_dir)
    
    return Path("logs") / "economic"


def is_economic_logging_enabled() -> bool:
    """Check if economic logging is enabled via environment variables.
    
    Returns:
        True if economic logging is enabled
    """
    return os.environ.get("ECONSIM_ECONOMIC_LOGGING", "1") == "1"


def get_economic_log_level() -> str:
    """Get the economic logging level from environment variables.
    
    Returns:
        Logging level string (DEBUG, INFO, WARN, ERROR)
    """
    return os.environ.get("ECONSIM_ECONOMIC_LOG_LEVEL", "INFO")


def get_economic_log_categories() -> list[str]:
    """Get the economic logging categories from environment variables.
    
    Returns:
        List of event categories to log
    """
    categories_str = os.environ.get("ECONSIM_ECONOMIC_LOG_CATEGORIES", "ALL")
    return categories_str.split(",")


def should_log_economic_event(event_type: str, categories: list[str]) -> bool:
    """Check if an economic event should be logged based on categories.
    
    Args:
        event_type: Type of the economic event
        categories: List of categories to log
        
    Returns:
        True if the event should be logged
    """
    if "ALL" in categories:
        return True
    
    # Map event types to categories
    event_category_map = {
        "agent_mode_change": "MODE",
        "resource_collection": "RESOURCE",
        "trade_execution": "TRADE",
        "agent_decision": "DECISION",
        "debug_log": "DEBUG",
        "performance_monitor": "PERFORMANCE",
    }
    
    event_category = event_category_map.get(event_type, "OTHER")
    return event_category in categories
