"""Centralized event emission for agent actions."""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...observability.registry import ObserverRegistry

class AgentEventEmitter:
    """Handles all agent event emission with consistent error handling."""
    
    def __init__(self, agent_id: int):
        self.agent_id = agent_id
    
    def emit_mode_change(
        self,
        old_mode: str,
        new_mode: str,
        reason: str,
        step_number: int,
        observer_registry: Optional['ObserverRegistry'] = None
    ) -> None:
        """Emit agent mode change event using raw data architecture."""
        if observer_registry:
            # Record mode change using raw data architecture
            # Call record_mode_change() on all observers that support raw data recording
            for observer in observer_registry._observers:
                if hasattr(observer, 'record_mode_change'):
                    observer.record_mode_change(
                        step=step_number,
                        agent_id=self.agent_id,
                        old_mode=old_mode,
                        new_mode=new_mode,
                        reason=reason
                    )
    
    def emit_resource_collection(
        self,
        x: int,
        y: int,
        resource_type: str,
        step: int,
        observer_registry: Optional['ObserverRegistry'] = None
    ) -> None:
        """Emit resource collection event using raw data architecture."""
        if observer_registry:
            # Record resource collection using raw data architecture
            # Call record_resource_collection() on all observers that support raw data recording
            for observer in observer_registry._observers:
                if hasattr(observer, 'record_resource_collection'):
                    observer.record_resource_collection(
                        step=step,
                        agent_id=self.agent_id,
                        x=x,
                        y=y,
                        resource_type=resource_type,
                        amount_collected=1
                    )
