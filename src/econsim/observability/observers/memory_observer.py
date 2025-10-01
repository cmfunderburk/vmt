"""In-memory observer for testing and validation purposes.

This module implements the MemoryObserver class that stores events
in memory for testing, validation, and analysis. It's designed to
be lightweight and provide easy access to collected events.

Features:
- In-memory event storage with efficient access
- Event history and step-based organization
- Testing utilities and validation helpers  
- Memory usage monitoring and limits
- Event search and filtering capabilities
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import List, Dict, Any, Optional, Set, Deque, TYPE_CHECKING

from .base_observer import BaseObserver

if TYPE_CHECKING:
    from ..config import ObservabilityConfig
    from ..events import SimulationEvent


class MemoryObserver(BaseObserver):
    """In-memory observer for testing and validation.
    
    Stores simulation events in memory with efficient access patterns
    for testing, analysis, and validation purposes. Provides utilities
    for examining event history and patterns.
    """

    def __init__(self, config: ObservabilityConfig, max_events: int = 10000):
        """Initialize the memory observer.
        
        Args:
            config: Observability configuration
            max_events: Maximum number of events to store in memory
        """
        super().__init__(config)
        
        self._max_events = max_events
        
        # Event storage
        self._all_events: Deque[Dict[str, Any]] = deque(maxlen=max_events)
        self._events_by_step: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        self._events_by_type: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Statistics
        self._total_events_received = 0
        self._events_dropped = 0
        self._current_step = 0

    def _initialize_event_filtering(self) -> None:
        """Initialize event filtering for memory observer.
        
        MemoryObserver accepts all events by default since it's used
        for testing and validation where comprehensive event history
        is typically desired.
        """
        # Accept all events by default for testing purposes
        self._enabled_event_types = None  # None means accept all

    def notify(self, event: SimulationEvent) -> None:
        """Store a simulation event in memory.
        
        Args:
            event: The simulation event to store
        """
        if not self.is_enabled(event.event_type):
            return
            
        self._total_events_received += 1
        
        # Convert event to dictionary for storage
        event_dict = {
            'step': event.step,
            'timestamp': event.timestamp,
            'event_type': event.event_type,
        }
        
        # Add event-specific fields
        for field_name in ['agent_id', 'old_mode', 'new_mode', 'reason']:
            if hasattr(event, field_name):
                event_dict[field_name] = getattr(event, field_name)
        
        # Check if we're at capacity
        if len(self._all_events) >= self._max_events:
            # Remove oldest events to make room
            oldest_event = self._all_events[0] if self._all_events else None
            if oldest_event:
                self._remove_event_from_indices(oldest_event)
                self._events_dropped += 1
        
        # Store event in all indices
        self._all_events.append(event_dict)
        self._events_by_step[event.step].append(event_dict)
        self._events_by_type[event.event_type].append(event_dict)
        
        # Update current step
        self._current_step = max(self._current_step, event.step)

    def _remove_event_from_indices(self, event_dict: Dict[str, Any]) -> None:
        """Remove an event from secondary indices when evicted.
        
        Args:
            event_dict: Event dictionary to remove from indices
        """
        # Remove from step index
        step = event_dict.get('step')
        if step is not None and step in self._events_by_step:
            try:
                self._events_by_step[step].remove(event_dict)
                if not self._events_by_step[step]:  # Clean up empty lists
                    del self._events_by_step[step]
            except ValueError:
                pass  # Event not found, already removed
        
        # Remove from type index
        event_type = event_dict.get('event_type')
        if event_type and event_type in self._events_by_type:
            try:
                self._events_by_type[event_type].remove(event_dict)
                if not self._events_by_type[event_type]:  # Clean up empty lists
                    del self._events_by_type[event_type]
            except ValueError:
                pass  # Event not found, already removed

    def flush_step(self, step: int) -> None:
        """Handle step boundary (no-op for memory observer).
        
        Args:
            step: The simulation step that just completed
        """
        # Memory observer doesn't need to do anything at step boundaries
        # since events are immediately available in memory
        pass

    # Query methods for testing and validation

    def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all stored events in chronological order.
        
        Returns:
            List of all event dictionaries
        """
        return list(self._all_events)

    def get_events_by_step(self, step: int) -> List[Dict[str, Any]]:
        """Get all events for a specific simulation step.
        
        Args:
            step: The simulation step to query
            
        Returns:
            List of event dictionaries for that step
        """
        return self._events_by_step.get(step, []).copy()

    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Get all events of a specific type.
        
        Args:
            event_type: The event type to query
            
        Returns:
            List of event dictionaries of that type
        """
        return self._events_by_type.get(event_type, []).copy()

    def get_events_by_agent(self, agent_id: int) -> List[Dict[str, Any]]:
        """Get all events involving a specific agent.
        
        Args:
            agent_id: The agent ID to search for
            
        Returns:
            List of event dictionaries involving that agent
        """
        agent_events = []
        for event in self._all_events:
            if event.get('agent_id') == agent_id:
                agent_events.append(event)
        return agent_events

    def get_events_in_range(self, start_step: int, end_step: int) -> List[Dict[str, Any]]:
        """Get all events within a step range.
        
        Args:
            start_step: Starting step (inclusive)
            end_step: Ending step (inclusive)
            
        Returns:
            List of event dictionaries in the step range
        """
        range_events = []
        for event in self._all_events:
            step = event.get('step', -1)
            if start_step <= step <= end_step:
                range_events.append(event)
        return range_events

    def count_events_by_type(self) -> Dict[str, int]:
        """Count events by type.
        
        Returns:
            Dictionary mapping event types to their counts
        """
        return {event_type: len(events) for event_type, events in self._events_by_type.items()}

    def get_steps_with_events(self) -> Set[int]:
        """Get set of all steps that have events.
        
        Returns:
            Set of step numbers that contain events
        """
        return set(self._events_by_step.keys())

    def clear_events(self) -> None:
        """Clear all stored events."""
        self._all_events.clear()
        self._events_by_step.clear()
        self._events_by_type.clear()
        self._total_events_received = 0
        self._events_dropped = 0
        self._current_step = 0

    def close(self) -> None:
        """Close the memory observer."""
        super().close()
        # Memory observer doesn't need special cleanup
        # Events remain accessible even after closing

    def get_observer_stats(self) -> Dict[str, Any]:
        """Get memory observer statistics.
        
        Returns:
            Dictionary containing memory observer metrics
        """
        base_stats = super().get_observer_stats()
        
        memory_stats = {
            'max_events': self._max_events,
            'stored_events': len(self._all_events),
            'total_events_received': self._total_events_received,
            'events_dropped': self._events_dropped,
            'current_step': self._current_step,
            'unique_event_types': len(self._events_by_type),
            'steps_with_events': len(self._events_by_step),
            'memory_utilization': len(self._all_events) / self._max_events if self._max_events > 0 else 0,
        }
        
        return {**base_stats, **memory_stats}

    # Testing utilities

    def assert_event_count(self, event_type: str, expected_count: int) -> None:
        """Assert that a specific number of events of a type were received.
        
        Args:
            event_type: The event type to check
            expected_count: Expected number of events
            
        Raises:
            AssertionError: If the count doesn't match
        """
        actual_count = len(self._events_by_type.get(event_type, []))
        assert actual_count == expected_count, (
            f"Expected {expected_count} {event_type} events, got {actual_count}"
        )

    def assert_step_has_events(self, step: int) -> None:
        """Assert that a specific step has events.
        
        Args:
            step: The step to check
            
        Raises:
            AssertionError: If the step has no events
        """
        assert step in self._events_by_step, f"Step {step} has no events"

    def assert_agent_has_events(self, agent_id: int) -> None:
        """Assert that a specific agent has events.
        
        Args:
            agent_id: The agent ID to check
            
        Raises:
            AssertionError: If the agent has no events
        """
        agent_events = self.get_events_by_agent(agent_id)
        assert agent_events, f"Agent {agent_id} has no events"

    def __repr__(self) -> str:
        """String representation of the memory observer."""
        return (f"MemoryObserver(events={len(self._all_events)}/{self._max_events}, "
                f"types={len(self._events_by_type)}, closed={self._closed})")

    def __len__(self) -> int:
        """Get number of stored events."""
        return len(self._all_events)