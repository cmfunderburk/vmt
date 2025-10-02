"""Centralized event emission for agent actions."""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...observability.registry import ObserverRegistry
    from ...observability.event_buffer import StepEventBuffer

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
        observer_registry: Optional['ObserverRegistry'] = None,
        event_buffer: Optional['StepEventBuffer'] = None
    ) -> None:
        """Emit agent mode change event."""
        if event_buffer is not None:
            event_buffer.queue_mode_change(self.agent_id, old_mode, new_mode, reason)
        elif observer_registry:
            from econsim.observability.events import AgentModeChangeEvent
            event = AgentModeChangeEvent.create(
                step=step_number,
                agent_id=self.agent_id,
                old_mode=old_mode,
                new_mode=new_mode,
                reason=reason
            )
            observer_registry.notify(event)
    
    def emit_resource_collection(
        self,
        x: int,
        y: int,
        resource_type: str,
        step: int,
        observer_registry: Optional['ObserverRegistry'] = None
    ) -> None:
        """Emit resource collection event."""
        if observer_registry:
            from econsim.observability.events import ResourceCollectionEvent
            event = ResourceCollectionEvent.create(
                step=step,
                agent_id=self.agent_id,
                x=x,
                y=y,
                resource_type=resource_type,
                amount_collected=1
            )
            observer_registry.notify(event)
