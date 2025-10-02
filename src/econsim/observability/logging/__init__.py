"""Economic logging infrastructure.

This module provides the core infrastructure for economic behavior logging,
including file management, configuration, and specialized observers.
"""

from .file_manager import EconomicLogFileManager
from .config import EconomicLoggingConfig

__all__ = ["EconomicLogFileManager", "EconomicLoggingConfig"]
