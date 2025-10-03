"""In-memory observer using raw data architecture for testing and validation purposes.

This module implements the MemoryObserver class that stores events
in memory for testing, validation, and analysis using the new raw data
recording architecture for zero-overhead performance.

Features:
- Zero-overhead raw data recording during simulation
- In-memory event storage with efficient access
- Event history and step-based organization
- Testing utilities and validation helpers  
- Memory usage monitoring and limits
- Event search and filtering capabilities
- Raw data storage with human-readable translation on demand

Architecture:
- Inherits from both BaseObserver (for configuration) and RawDataObserver (for storage)
- Uses standalone analysis formatters for converting raw data to analysis-ready format
- No processing overhead during simulation execution
- Analysis performed only when needed (testing, validation)
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import List, Dict, Any, Optional, Set, Deque, TYPE_CHECKING

from .base_observer import BaseObserver
from ..raw_data.raw_data_observer import RawDataObserver

if TYPE_CHECKING:
    from ..config import ObservabilityConfig
    from ..events import SimulationEvent


class MemoryObserver(BaseObserver, RawDataObserver):
    """In-memory observer using raw data architecture for testing and validation.
    
    Stores simulation events in memory with efficient access patterns
    for testing, analysis, and validation purposes using zero-overhead raw data recording.
    Provides utilities for examining event history and patterns.
    
    Architecture:
    - Inherits from both BaseObserver (for configuration) and RawDataObserver (for storage)
    - Uses standalone analysis formatters for converting raw data to analysis-ready format
    - Zero-overhead recording during simulation, analysis deferred to when needed
    - Raw data storage with analysis formatters in separate analysis module
    """

    def __init__(self, config: ObservabilityConfig, max_events: int = 10000):
        """Initialize the memory observer with raw data architecture.
        
        Args:
            config: Observability configuration
            max_events: Maximum number of events to store in memory (legacy, kept for compatibility)
        """
        # Initialize both parent classes
        BaseObserver.__init__(self, config)
        RawDataObserver.__init__(self)
        
        self._max_events = max_events  # Legacy compatibility
        
        # Legacy event storage (kept for backward compatibility)
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
        self._enabled_event_types = {
            'agent_mode_change',
            'trade_execution', 
            'resource_collection',
            'agent_movement',
            'debug_log',
            'performance_monitor',
            'agent_decision',
            'resource_event',
            'economic_decision'
        }

    def notify(self, event: SimulationEvent) -> None:
        """Handle a simulation event by recording raw data.
        
        This method now uses the raw data recording architecture for zero-overhead
        performance. Events are stored as raw dictionaries with no processing.
        Legacy storage is maintained for backward compatibility.
        
        Args:
            event: The simulation event to log
        """
        if not self.is_enabled(event.event_type):
            return
        
        # Extract raw data from event and record using appropriate method
        step = getattr(event, 'step', 0)
        
        if event.event_type == 'trade_execution':
            self.record_trade(
                step=step,
                seller_id=getattr(event, 'seller_id', -1),
                buyer_id=getattr(event, 'buyer_id', -1),
                give_type=getattr(event, 'give_type', ''),
                take_type=getattr(event, 'take_type', ''),
                delta_u_seller=getattr(event, 'delta_u_seller', 0.0),
                delta_u_buyer=getattr(event, 'delta_u_buyer', 0.0),
                trade_location_x=getattr(event, 'trade_location_x', -1),
                trade_location_y=getattr(event, 'trade_location_y', -1)
            )
        elif event.event_type == 'agent_mode_change':
            self.record_mode_change(
                step=step,
                agent_id=getattr(event, 'agent_id', -1),
                old_mode=getattr(event, 'old_mode', ''),
                new_mode=getattr(event, 'new_mode', ''),
                reason=getattr(event, 'reason', '')
            )
        elif event.event_type == 'resource_collection':
            self.record_resource_collection(
                step=step,
                agent_id=getattr(event, 'agent_id', -1),
                x=getattr(event, 'x', -1),
                y=getattr(event, 'y', -1),
                resource_type=getattr(event, 'resource_type', ''),
                amount_collected=getattr(event, 'amount_collected', 1),
                utility_gained=getattr(event, 'utility_gained', 0.0),
                carrying_after=getattr(event, 'carrying_after', None)
            )
        elif event.event_type == 'agent_decision':
            self.record_agent_decision(
                step=step,
                agent_id=getattr(event, 'agent_id', -1),
                decision_type=getattr(event, 'decision_type', ''),
                decision_details=getattr(event, 'decision_details', ''),
                utility_delta=getattr(event, 'utility_delta', 0.0),
                position_x=getattr(event, 'position_x', -1),
                position_y=getattr(event, 'position_y', -1)
            )
        elif event.event_type == 'debug_log':
            self.record_debug_log(
                step=step,
                category=getattr(event, 'category', ''),
                message=getattr(event, 'message', ''),
                agent_id=getattr(event, 'agent_id', -1)
            )
        elif event.event_type == 'performance_monitor':
            self.record_performance_monitor(
                step=step,
                metric_name=getattr(event, 'metric_name', ''),
                metric_value=getattr(event, 'metric_value', 0.0),
                threshold_exceeded=getattr(event, 'threshold_exceeded', False),
                details=getattr(event, 'details', '')
            )
        elif event.event_type == 'economic_decision':
            self.record_economic_decision(
                step=step,
                agent_id=getattr(event, 'agent_id', -1),
                decision_type=getattr(event, 'decision_type', ''),
                decision_context=getattr(event, 'decision_context', ''),
                utility_before=getattr(event, 'utility_before', 0.0),
                utility_after=getattr(event, 'utility_after', 0.0),
                opportunity_cost=getattr(event, 'opportunity_cost', 0.0),
                alternatives_considered=getattr(event, 'alternatives_considered', 0),
                decision_time_ms=getattr(event, 'decision_time_ms', 0.0),
                position_x=getattr(event, 'position_x', -1),
                position_y=getattr(event, 'position_y', -1)
            )
        elif event.event_type == 'resource_event':
            self.record_resource_event(
                step=step,
                event_type_detail=getattr(event, 'event_type_detail', ''),
                position_x=getattr(event, 'position_x', -1),
                position_y=getattr(event, 'position_y', -1),
                resource_type=getattr(event, 'resource_type', ''),
                amount=getattr(event, 'amount', 1),
                agent_id=getattr(event, 'agent_id', -1)
            )
        else:
            # For unknown event types, record as generic debug log
            self.record_debug_log(
                step=step,
                category='UNKNOWN_EVENT',
                message=f"Unknown event type: {event.event_type}",
                agent_id=-1
            )
        
        # Legacy compatibility - also store in legacy format
        self._total_events_received += 1
        
        # Convert event to dictionary for legacy storage
        event_dict = {
            'step': step,
            'timestamp': getattr(event, 'timestamp', 0),
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
        self._events_by_step[step].append(event_dict)
        self._events_by_type[event.event_type].append(event_dict)
        
        # Update current step
        self._current_step = max(self._current_step, step)

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
        """Handle end-of-step boundary with zero overhead.
        
        In the raw data architecture, no processing is done at step boundaries.
        All data is stored in memory and analysis is performed only when needed.
        
        Args:
            step: The simulation step that just completed
        """
        # Zero overhead - no processing during simulation
        # Raw data is stored in memory and analysis is deferred
        self._current_step = step

    # Query methods for testing and validation

    def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all stored events in chronological order.
        
        Returns:
            List of all event dictionaries (raw data format)
        """
        # Use raw data from RawDataObserver
        return super().get_all_events()

    def get_events_by_step(self, step: int) -> List[Dict[str, Any]]:
        """Get all events for a specific simulation step.
        
        Args:
            step: The simulation step to query
            
        Returns:
            List of event dictionaries for that step (raw data format)
        """
        # Use raw data from RawDataObserver
        return super().get_events_by_step(step)

    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Get all events of a specific type.
        
        Args:
            event_type: The event type to query
            
        Returns:
            List of event dictionaries of that type (raw data format)
        """
        # Use raw data from RawDataObserver
        return super().get_events_by_type(event_type)

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
        raw_data_stats = self.get_statistics()
        
        memory_stats = {
            'observer_type': 'memory',
            'max_events': self._max_events,
            'stored_events': len(self._all_events),
            'total_events_received': self._total_events_received,
            'events_dropped': self._events_dropped,
            'current_step': self._current_step,
            'unique_event_types': len(self._events_by_type),
            'steps_with_events': len(self._events_by_step),
            'memory_utilization': len(self._all_events) / self._max_events if self._max_events > 0 else 0,
            'raw_data_events': raw_data_stats['total_events'],
            'raw_data_types': list(raw_data_stats['event_types']),
            'step_range': raw_data_stats['step_range'],
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
        # Use raw data for assertion
        raw_events = self.get_events_by_type(event_type)
        actual_count = len(raw_events)
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
        # Use raw data for assertion
        step_events = self.get_events_by_step(step)
        assert step_events, f"Step {step} has no events"

    def assert_agent_has_events(self, agent_id: int) -> None:
        """Assert that a specific agent has events.
        
        Args:
            agent_id: The agent ID to check
            
        Raises:
            AssertionError: If the agent has no events
        """
        # Use raw data for assertion
        agent_events = self.get_events_by_agent(agent_id)
        assert agent_events, f"Agent {agent_id} has no events"

    def __repr__(self) -> str:
        """String representation of the memory observer."""
        raw_data_stats = self.get_statistics()
        return (f"MemoryObserver(events={raw_data_stats['total_events']}, "
                f"types={len(raw_data_stats['event_types'])}, "
                f"legacy={len(self._all_events)}/{self._max_events}, closed={self._closed})")

    def __len__(self) -> int:
        """Get number of stored events."""
        return len(self._events)  # Use raw data count