"""Agent mode management utilities for observer integration.

Provides centralized agent mode change functionality that ensures
all mode transitions go through the observer system for consistent
event emission and logging.

Design Principles:
- Single point of truth for mode changes
- Consistent observer event emission  
- Backward compatibility with direct assignments
- Structured logging integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..agent import Agent
    from ..constants import AgentMode
    from ...observability.registry import ObserverRegistry


def set_agent_mode(agent: 'Agent', new_mode: 'AgentMode', reason: str = "", 
                   step: int = 0, observer_registry: 'ObserverRegistry' = None) -> None:
    """Set agent mode with observer event emission.
    
    Centralized method for changing agent modes that ensures observer
    events are emitted for all mode transitions.
    
    Args:
        agent: Agent to modify
        new_mode: New mode to set
        reason: Reason for mode change (for logging)
        step: Current step number
        observer_registry: Observer registry for event emission (optional)
    """
    # Use the agent's centralized _set_mode() helper to ensure consistent event emission
    agent._set_mode(new_mode, reason, observer_registry, step)