"""Basic event buffer implementation for general-purpose event storage.

This module provides a straightforward event buffer that stores events
in chronological order and flushes them at step boundaries. It's designed
for scenarios where simple event logging is needed without complex
aggregation or correlation analysis.

Features:
- Chronological event ordering
- Configurable capacity limits
- Step-based batch flushing
- Memory-efficient circular buffering
- Event metadata preservation
"""

from __future__ import annotations

import time
from collections import deque
from typing import List, Dict, Any, Deque, TYPE_CHECKING

from .base import EventBuffer, BufferOverflowError, BufferStateError

if TYPE_CHECKING:
    from ..events import SimulationEvent


class BasicEventBuffer(EventBuffer):
    """Basic event buffer with chronological storage and batch flushing.
    
    Stores events in order of arrival and flushes them at step boundaries.
    Provides simple, efficient buffering for general-purpose event logging.
    """

    def __init__(self, capacity: int = 10000):
        """Initialize the event buffer.
        
        Args:
            capacity: Maximum number of events to buffer before overflow
        """
        self._capacity = capacity
        self._events: Deque[Dict[str, Any]] = deque(maxlen=capacity)
        self._current_step: int = 0
        self._total_events_processed: int = 0
        self._overflow_count: int = 0
        
    def add_event(self, event: SimulationEvent) -> None:
        """Add an event to the buffer with timestamp.
        
        Args:
            event: The simulation event to buffer
            
        Raises:
            BufferStateError: If event step is before current buffer step
        """
        # Convert event to dictionary format for storage using dataclasses.asdict()
        # This ensures ALL fields from the event are preserved, including trade-specific fields
        from dataclasses import asdict
        event_dict = asdict(event)
        
        # Check for step ordering (events should not go backwards in time)
        if event.step < self._current_step:
            raise BufferStateError(
                f"Event step {event.step} is before current buffer step {self._current_step}"
            )
        
        # Track buffer overflow if we're at capacity
        if len(self._events) >= self._capacity:
            self._overflow_count += 1
            
        # Add to buffer (deque automatically handles capacity limit)
        self._events.append(event_dict)
        self._total_events_processed += 1
        self._current_step = max(self._current_step, event.step)
    
    def flush_step(self, step: int) -> List[Dict[str, Any]]:
        """Flush all events for the completed step.
        
        Returns events in chronological order and clears the buffer.
        
        Args:
            step: The simulation step being completed
            
        Returns:
            List of event dictionaries in chronological order
        """
        # Collect all events for this step and earlier
        events_to_flush = []
        remaining_events = deque()
        
        for event_dict in self._events:
            if event_dict['step'] <= step:
                events_to_flush.append(event_dict)
            else:
                remaining_events.append(event_dict)
        
        # Keep future events in buffer
        self._events = remaining_events
        
        # Sort by timestamp for deterministic output
        events_to_flush.sort(key=lambda e: (e['step'], e['timestamp'], e['event_type']))
        
        return events_to_flush
    
    def clear(self) -> None:
        """Clear all buffered events and reset state."""
        self._events.clear()
        self._current_step = 0
        self._total_events_processed = 0
        self._overflow_count = 0
    
    def get_buffer_stats(self) -> Dict[str, Any]:
        """Get statistics about buffer usage and performance.
        
        Returns:
            Dictionary containing buffer metrics
        """
        return {
            'type': 'BasicEventBuffer',
            'capacity': self._capacity,
            'current_size': len(self._events),
            'utilization': len(self._events) / self._capacity if self._capacity > 0 else 0,
            'total_events_processed': self._total_events_processed,
            'overflow_count': self._overflow_count,
            'current_step': self._current_step,
        }
    
    @property
    def size(self) -> int:
        """Get current number of buffered events."""
        return len(self._events)
    
    @property 
    def capacity(self) -> int:
        """Get buffer capacity."""
        return self._capacity
    
    @property
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return len(self._events) == 0
    
    @property
    def is_full(self) -> bool:
        """Check if buffer is at capacity."""
        return len(self._events) >= self._capacity