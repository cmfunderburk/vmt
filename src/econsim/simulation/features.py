"""Centralized simulation feature flag management.

This module consolidates all simulation behavioral flags into a single
configuration class. Instead of scattered os.environ checks throughout
the simulation code, feature flags are read once at startup and provided
as a structured configuration object.

Feature Flag Design Principles:
- Single source of truth for all simulation behavioral flags
- Immutable configuration objects prevent runtime modification
- Environment variable parsing isolated in factory methods
- Backward compatibility with existing flag semantics

Environment Variables Managed:
- ECONSIM_FORAGE_ENABLED: Enable/disable resource collection
- ECONSIM_TRADE_DRAFT: Enable trading intent enumeration  
- ECONSIM_TRADE_EXEC: Enable trading intent execution

Usage:
    features = SimulationFeatures.from_environment()
    if features.trade_draft_enabled:
        # Enumerate trading intents
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimulationFeatures:
    """Centralized configuration for simulation behavioral features.
    
    Consolidates all feature flags that control simulation behavior into
    a single immutable configuration object. Replaces scattered environment
    variable checks with structured configuration access.
    
    Attributes:
        forage_enabled: Allow agents to collect resources from grid
        trade_draft_enabled: Enable enumeration of trading intents
        trade_execution_enabled: Enable execution of trading intents
    """
    forage_enabled: bool = True
    trade_draft_enabled: bool = False  
    trade_execution_enabled: bool = False

    @classmethod
    def from_environment(cls) -> SimulationFeatures:
        """Create feature configuration from environment variables.
        
        Reads all simulation feature flags from environment variables and
        creates an immutable configuration object. Provides backward
        compatibility with existing flag semantics.
        
        Environment Variable Mappings:
        - ECONSIM_FORAGE_ENABLED=0 -> forage_enabled=False (default: True)
        - ECONSIM_TRADE_DRAFT=1 -> trade_draft_enabled=True
        - ECONSIM_TRADE_EXEC=1 -> trade_execution_enabled=True
        
        Returns:
            SimulationFeatures with settings from environment
        """
        # Decision/unified system is always enabled (legacy random movement removed)
        
        # Resource collection (default enabled, explicit disable with =0)
        forage_enabled = os.environ.get("ECONSIM_FORAGE_ENABLED", "1") != "0"
        
        # Trading intent drafting (default disabled)
        trade_draft_enabled = os.environ.get("ECONSIM_TRADE_DRAFT", "0") == "1"
        
        # Trading intent execution (default disabled, requires draft to be meaningful)
        trade_execution_enabled = os.environ.get("ECONSIM_TRADE_EXEC", "0") == "1"
        
        return cls(
            forage_enabled=forage_enabled,
            trade_draft_enabled=trade_draft_enabled,
            trade_execution_enabled=trade_execution_enabled,
        )

    def is_decision_mode_enabled(self) -> bool:
        """Check if the decision system should be used.
        
        Decision-based agent behavior is now the only system available.
        
        Returns:
            Always True (legacy random movement removed)
        """
        return True

    def is_trading_enabled(self) -> bool:
        """Check if any trading functionality is enabled.
        
        Trading requires at least draft enumeration to be meaningful.
        This is useful for conditional setup of trading-related systems.
        
        Returns:
            True if trading intent drafting or execution is enabled
        """
        return self.trade_draft_enabled or self.trade_execution_enabled

    def validate_configuration(self) -> list[str]:
        """Validate feature flag consistency and return warnings.
        
        Checks for potentially problematic flag combinations that might
        indicate configuration errors or unexpected behavior.
        
        Returns:
            List of warning messages for inconsistent configurations
        """
        warnings = []
        
        # Warn if trade execution is enabled without draft
        if self.trade_execution_enabled and not self.trade_draft_enabled:
            warnings.append(
                "Trade execution enabled without draft enumeration. "
                "No intents will be available for execution."
            )
            
        # Warn if both legacy and modern systems might conflict
        # Legacy random movement removed: no mixed-mode warning needed
            
        return warnings