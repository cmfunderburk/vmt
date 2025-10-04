"""Centralized event emission for agent actions."""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

# Observer system removed - comprehensive delta system handles recording

class AgentEventEmitter:
    """Handles all agent event emission with consistent error handling."""
    
    def __init__(self, agent_id: int):
        self.agent_id = agent_id
    
    def emit_mode_change(
        self,
        old_mode: str,
        new_mode: str,
        reason: str,
        step_number: int
    ) -> None:
        """Emit agent mode change event - observer system removed."""
        # Observer system removed - comprehensive delta system handles recording
        pass
    
    def emit_resource_collection(
        self,
        x: int,
        y: int,
        resource_type: str,
        step: int
    ) -> None:
        """Emit resource collection event - observer system removed."""
        # Observer system removed - comprehensive delta system handles recording
        pass
