"""Event buffering system for deferred observer notification.

Provides batched event processing similar to the debug logging solution,
collecting events during simulation steps and processing them afterwards
to eliminate per-event overhead.

Design Pattern:
- Events are queued during step execution (minimal overhead)
- Observer notification is batched at step boundaries  
- Single timestamp and system call per step instead of per event
- Preserves all event information without loss

Performance Benefits:
- Reduces O(events × observers) to O(1) during step execution
- Eliminates high-frequency system calls (time.time())
- Reduces object allocation pressure during performance-critical simulation
- Maintains full observability without simulation impact
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .registry import ObserverRegistry


@dataclass
class PendingModeChange:
    """Lightweight mode change record for batching."""
    agent_id: int
    old_mode: str
    new_mode: str
    reason: str


@dataclass
class PendingResourceCollection:
    """Lightweight resource collection record for batching."""
    agent_id: int
    x: int
    y: int
    resource_type: str
    amount: int


class EventBuffer:
    """Event buffer for deferred observer notification.
    
    Collects events during simulation steps and processes them in batches
    to minimize performance impact on the simulation loop.
    
    Usage Pattern:
        # During step execution (minimal overhead):
        buffer.queue_mode_change(agent_id, old_mode, new_mode, reason)
        buffer.queue_resource_collection(agent_id, x, y, resource_type, amount)
        
        # At step boundary (batch processing):
        buffer.flush_step(step_number, observer_registry)
    """
    
    def __init__(self):
        """Initialize empty event buffer."""
        self._pending_mode_changes: List[PendingModeChange] = []
        self._pending_collections: List[PendingResourceCollection] = []
        self._current_step: Optional[int] = None
        self._step_start_time: Optional[float] = None
        
    def start_step(self, step_number: int) -> None:
        """Mark the beginning of a new simulation step.
        
        Records step start time to be used for all events in this step,
        eliminating per-event time.time() system calls.
        
        Args:
            step_number: Current simulation step number
        """
        self._current_step = step_number
        self._step_start_time = time.time()  # Single system call per step
        
    def queue_mode_change(self, agent_id: int, old_mode: str, new_mode: str, reason: str = "") -> None:
        """Queue an agent mode change for batch processing.
        
        Minimal overhead - just appends to list without object allocation
        or observer notification.
        
        Args:
            agent_id: Agent that changed modes
            old_mode: Previous mode string
            new_mode: New mode string  
            reason: Optional reason for change
        """
        if old_mode != new_mode:  # Skip no-op changes
            self._pending_mode_changes.append(
                PendingModeChange(agent_id, old_mode, new_mode, reason)
            )
    
    def queue_resource_collection(self, agent_id: int, x: int, y: int, 
                                resource_type: str, amount: int = 1) -> None:
        """Queue a resource collection for batch processing.
        
        Args:
            agent_id: Agent that collected resource
            x: Grid x coordinate
            y: Grid y coordinate
            resource_type: Type of resource collected
            amount: Amount collected (default 1)
        """
        self._pending_collections.append(
            PendingResourceCollection(agent_id, x, y, resource_type, amount)
        )
    
    def flush_step(self, observer_registry: ObserverRegistry) -> int:
        """Process all queued events and notify observers.
        
        Creates event objects and notifies observers in batch,
        using the step start timestamp for all events to maintain
        temporal consistency.
        
        Args:
            observer_registry: Registry to notify with events
            
        Returns:
            Number of events processed
        """
        if not observer_registry.has_observers():
            # Clear buffers but skip event creation if no observers
            event_count = len(self._pending_mode_changes) + len(self._pending_collections)
            self._clear_buffers()
            return event_count
            
        if self._current_step is None or self._step_start_time is None:
            return 0
            
        events_created = 0
        
        # Process mode change events
        if self._pending_mode_changes:
            from .events import AgentModeChangeEvent
            
            for change in self._pending_mode_changes:
                event = AgentModeChangeEvent(
                    step=self._current_step,
                    timestamp=self._step_start_time,  # Shared timestamp
                    event_type="agent_mode_change",
                    agent_id=change.agent_id,
                    old_mode=change.old_mode,
                    new_mode=change.new_mode,
                    reason=change.reason
                )
                observer_registry.notify(event)
                events_created += 1
        
        # Process resource collection events  
        if self._pending_collections:
            from .events import ResourceCollectionEvent
            
            for collection in self._pending_collections:
                event = ResourceCollectionEvent(
                    step=self._current_step,
                    timestamp=self._step_start_time,  # Shared timestamp
                    event_type="resource_collection",
                    agent_id=collection.agent_id,
                    x=collection.x,
                    y=collection.y,
                    resource_type=collection.resource_type,
                    amount_collected=collection.amount
                )
                observer_registry.notify(event)
                events_created += 1
        
        self._clear_buffers()
        return events_created
    
    def _clear_buffers(self) -> None:
        """Clear all pending events."""
        self._pending_mode_changes.clear()
        self._pending_collections.clear()
        self._current_step = None
        self._step_start_time = None
        
    def get_pending_count(self) -> int:
        """Get the number of events pending flush.
        
        Returns:
            Total number of queued events
        """
        return len(self._pending_mode_changes) + len(self._pending_collections)
    
    def is_empty(self) -> bool:
        """Check if buffer has no pending events.
        
        Returns:
            True if no events are queued
        """
        return len(self._pending_mode_changes) == 0 and len(self._pending_collections) == 0


class StepEventBuffer:
    """Step-aware event buffer that integrates with simulation execution.
    
    Provides a higher-level interface that automatically manages step
    boundaries and integrates with the existing simulation step execution.
    """
    
    def __init__(self):
        """Initialize step-aware event buffer."""
        self._buffer = EventBuffer()
        self._last_step: Optional[int] = None
        
    def begin_step(self, step_number: int) -> None:
        """Begin a new simulation step.
        
        Args:
            step_number: Current step number
        """
        self._buffer.start_step(step_number)
        self._last_step = step_number
        
    def end_step(self, observer_registry: ObserverRegistry) -> int:
        """End current step and process events.
        
        Args:
            observer_registry: Registry to notify
            
        Returns:
            Number of events processed
        """
        return self._buffer.flush_step(observer_registry)
        
    def queue_mode_change(self, agent_id: int, old_mode: str, new_mode: str, reason: str = "") -> None:
        """Queue mode change event (delegate to buffer)."""
        self._buffer.queue_mode_change(agent_id, old_mode, new_mode, reason)
        
    def queue_resource_collection(self, agent_id: int, x: int, y: int, 
                                resource_type: str, amount: int = 1) -> None:
        """Queue resource collection event (delegate to buffer)."""
        self._buffer.queue_resource_collection(agent_id, x, y, resource_type, amount)
        
    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics.
        
        Returns:
            Dictionary with buffer status information
        """
        return {
            'pending_events': self._buffer.get_pending_count(),
            'current_step': self._last_step,
            'is_empty': self._buffer.is_empty()
        }