"""Centralized observability configuration management.

This module provides configuration classes for managing observability settings
without scattered environment variable checks throughout the codebase. The
configuration classes read from environment variables once and provide
structured access to settings.

Configuration Design Principles:
- Single source of truth for observability settings
- Environment variable parsing isolated in factory methods  
- Immutable dataclass configuration objects
- Sensible defaults with explicit override capability

Environment Variables:
- ECONSIM_DEBUG_AGENT_MODES: Enable agent mode change logging
- ECONSIM_LOG_LEVEL: Set logging verbosity
- ECONSIM_LOG_CATEGORIES: Enable specific log categories
- ECONSIM_LOG_EXPLANATIONS: Enable detailed explanations in logs
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ObservabilityConfig:
    """Configuration for simulation observability and logging.
    
    Centralizes all observability-related settings to avoid scattered
    environment variable checks. Immutable configuration object created
    from environment state at startup.
    
    Attributes:
        agent_mode_logging: Enable agent behavioral mode change tracking
        trade_logging: Enable trade event logging  
        behavioral_aggregation: Enable behavioral summary generation
        log_level: Minimum log level for output
        enabled_categories: Set of enabled log categories
        detailed_explanations: Include detailed explanations in logs
    """
    agent_mode_logging: bool = False
    trade_logging: bool = False  
    behavioral_aggregation: bool = False
    log_level: str = "INFO"
    enabled_categories: frozenset[str] = frozenset()
    detailed_explanations: bool = False

    @classmethod
    def from_environment(cls) -> ObservabilityConfig:
        """Create configuration from environment variables.
        
        Reads all relevant environment variables and creates an immutable
        configuration object. Provides sensible defaults for missing vars.
        
        Returns:
            ObservabilityConfig with settings from environment
        """
        # Agent mode logging (ECONSIM_DEBUG_AGENT_MODES)
        agent_mode_logging = os.environ.get("ECONSIM_DEBUG_AGENT_MODES", "0") == "1"
        
        # Trade logging (derived from trade flags)
        trade_draft = os.environ.get("ECONSIM_TRADE_DRAFT", "0") == "1"
        trade_exec = os.environ.get("ECONSIM_TRADE_EXEC", "0") == "1"
        trade_logging = trade_draft or trade_exec
        
        # Behavioral aggregation (default enabled for comprehensive logging)
        behavioral_aggregation = True
        
        # Log level
        log_level = os.environ.get("ECONSIM_LOG_LEVEL", "INFO").upper()
        
        # Log categories (comma-separated)
        categories_str = os.environ.get("ECONSIM_LOG_CATEGORIES", "")
        enabled_categories = frozenset(
            cat.strip() for cat in categories_str.split(",") 
            if cat.strip()
        )
        
        # Detailed explanations
        detailed_explanations = os.environ.get("ECONSIM_LOG_EXPLANATIONS", "0") == "1"
        
        return cls(
            agent_mode_logging=agent_mode_logging,
            trade_logging=trade_logging,
            behavioral_aggregation=behavioral_aggregation,  
            log_level=log_level,
            enabled_categories=enabled_categories,
            detailed_explanations=detailed_explanations,
        )

    def is_category_enabled(self, category: str) -> bool:
        """Check if a log category is enabled.
        
        Args:
            category: Category name to check
            
        Returns:
            True if category is enabled or no categories are specified
        """
        if not self.enabled_categories:
            return True  # If no categories specified, enable all
        return category in self.enabled_categories

    def should_log_event_type(self, event_type: str) -> bool:
        """Check if an event type should be logged.
        
        Args:
            event_type: Event type identifier
            
        Returns:
            True if event type should be logged based on configuration
        """
        if event_type == "agent_mode_change":
            return self.agent_mode_logging
        elif event_type.startswith("trade_"):
            return self.trade_logging
        else:
            return True  # Log unknown event types by default