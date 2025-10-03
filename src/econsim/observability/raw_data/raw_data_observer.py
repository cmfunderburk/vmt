"""
Raw Data Observer: Zero-overhead data storage for simulation events.

This module implements a zero-overhead logging system that stores raw simulation data
as primitive types (dictionaries) with no processing overhead during simulation.

Key Features:
- Zero processing overhead - direct dictionary append operations
- No event object creation - raw data stored as-is
- No JSON serialization during simulation - deferred to disk write
- No string formatting - primitive types only
- No validation - trust simulation data

Performance Targets:
- <0.0001ms per event recording (100x faster than current system)
- >1,000,000 events/second recording speed
- Zero per-frame allocations during simulation
- 33% memory reduction (raw dicts vs compressed JSON)

Usage:
    observer = RawDataObserver()
    observer.record_trade(step=100, seller_id=1, buyer_id=2, give_type="wood", take_type="stone")
    observer.record_mode_change(step=101, agent_id=1, old_mode="foraging", new_mode="trading", reason="found partner")
    
    # Get events for analysis
    trade_events = observer.get_events_by_type("trade")
    step_events = observer.get_events_by_step(100)
    all_events = observer.get_all_events()
"""

from __future__ import annotations

import time
from typing import Dict, List, Any, Optional, Set, Tuple


class RawDataObserver:
    """Zero-overhead observer storing raw simulation data as dictionaries.
    
    This observer stores events as simple dictionaries in memory with zero
    processing overhead. All translation to human-readable format is deferred
    to when the data is actually needed (GUI display, analysis, etc.).
    
    Architecture:
    - Single list of event dictionaries in chronological order
    - Direct dictionary append operations (zero processing)
    - Optional fields supported via **kwargs pattern
    - Type field in each event for filtering and analysis
    """
    
    def __init__(self) -> None:
        """Initialize raw data observer with empty event storage."""
        self._events: List[Dict[str, Any]] = []  # Single list of event dictionaries
        self._step_count: int = 0
        self._start_time: float = time.time()
    
    # ============================================================================
    # CORE RECORDING METHODS - Zero Overhead Event Storage
    # ============================================================================
    
    def record_trade(self, step: int, seller_id: int, buyer_id: int, give_type: str, 
                    take_type: str, delta_u_seller: float = 0.0, delta_u_buyer: float = 0.0,
                    trade_location_x: int = -1, trade_location_y: int = -1, **optional) -> None:
        """Record trade execution data - zero processing overhead.
        
        Args:
            step: Simulation step number
            seller_id: ID of agent giving resource
            buyer_id: ID of agent receiving resource
            give_type: Resource type being given
            take_type: Resource type being received
            delta_u_seller: Utility change for seller (optional)
            delta_u_buyer: Utility change for buyer (optional)
            trade_location_x: X coordinate of trade location (optional)
            trade_location_y: Y coordinate of trade location (optional)
            **optional: Additional optional fields
        """
        event = {
            'type': 'trade',
            'step': step,
            'seller_id': seller_id,
            'buyer_id': buyer_id,
            'give_type': give_type,
            'take_type': take_type,
            'delta_u_seller': delta_u_seller,
            'delta_u_buyer': delta_u_buyer,
            'trade_location_x': trade_location_x,
            'trade_location_y': trade_location_y
        }
        # Add optional fields if provided
        event.update(optional)
        self._events.append(event)  # Just append - zero processing
    
    def record_mode_change(self, step: int, agent_id: int, old_mode: str, new_mode: str, 
                          reason: str = "", **optional) -> None:
        """Record agent mode change data - zero processing overhead.
        
        Args:
            step: Simulation step number
            agent_id: ID of agent changing mode
            old_mode: Previous behavioral mode
            new_mode: New behavioral mode
            reason: Optional explanation for mode change
            **optional: Additional optional fields
        """
        event = {
            'type': 'mode_change',
            'step': step,
            'agent_id': agent_id,
            'old_mode': old_mode,
            'new_mode': new_mode,
            'reason': reason
        }
        event.update(optional)
        self._events.append(event)  # Just append - zero processing
    
    def record_resource_collection(self, step: int, agent_id: int, x: int, y: int, 
                                 resource_type: str, amount_collected: int = 1,
                                 utility_gained: float = 0.0, 
                                 carrying_after: Optional[Dict[str, int]] = None, **optional) -> None:
        """Record resource collection data - zero processing overhead.
        
        Args:
            step: Simulation step number
            agent_id: ID of agent collecting resource
            x: X coordinate of resource
            y: Y coordinate of resource
            resource_type: Type of resource collected
            amount_collected: Amount collected (default 1)
            utility_gained: Utility gained from collection (default 0.0)
            carrying_after: Agent's inventory after collection (optional)
            **optional: Additional optional fields
        """
        event = {
            'type': 'resource_collection',
            'step': step,
            'agent_id': agent_id,
            'x': x,
            'y': y,
            'resource_type': resource_type,
            'amount_collected': amount_collected,
            'utility_gained': utility_gained,
            'carrying_after': carrying_after or {}
        }
        event.update(optional)
        self._events.append(event)  # Just append - zero processing
    
    def record_debug_log(self, step: int, category: str, message: str, 
                        agent_id: int = -1, **optional) -> None:
        """Record debug log data - zero processing overhead.
        
        Args:
            step: Simulation step number
            category: Log category (TRADE, MODE, ECON, etc.)
            message: Debug message text
            agent_id: Optional agent context (default -1)
            **optional: Additional optional fields
        """
        event = {
            'type': 'debug_log',
            'step': step,
            'category': category,
            'message': message,
            'agent_id': agent_id
        }
        event.update(optional)
        self._events.append(event)  # Just append - zero processing
    
    def record_performance_monitor(self, step: int, metric_name: str, metric_value: float,
                                 threshold_exceeded: bool = False, details: str = "", **optional) -> None:
        """Record performance monitor data - zero processing overhead.
        
        Args:
            step: Simulation step number
            metric_name: Name of performance metric
            metric_value: Numeric value of metric
            threshold_exceeded: Whether metric exceeded threshold (default False)
            details: Additional context or details (default "")
            **optional: Additional optional fields
        """
        event = {
            'type': 'performance_monitor',
            'step': step,
            'metric_name': metric_name,
            'metric_value': metric_value,
            'threshold_exceeded': threshold_exceeded,
            'details': details
        }
        event.update(optional)
        self._events.append(event)  # Just append - zero processing
    
    def record_agent_decision(self, step: int, agent_id: int, decision_type: str, 
                            decision_details: str, utility_delta: float = 0.0,
                            position_x: int = -1, position_y: int = -1, **optional) -> None:
        """Record agent decision data - zero processing overhead.
        
        Args:
            step: Simulation step number
            agent_id: ID of agent making decision
            decision_type: Type of decision (movement, collection, trade_intent, etc.)
            decision_details: Detailed description of decision
            utility_delta: Utility change associated with decision (default 0.0)
            position_x: Optional X coordinate context (default -1)
            position_y: Optional Y coordinate context (default -1)
            **optional: Additional optional fields
        """
        event = {
            'type': 'agent_decision',
            'step': step,
            'agent_id': agent_id,
            'decision_type': decision_type,
            'decision_details': decision_details,
            'utility_delta': utility_delta,
            'position_x': position_x,
            'position_y': position_y
        }
        event.update(optional)
        self._events.append(event)  # Just append - zero processing
    
    def record_resource_event(self, step: int, event_type_detail: str, position_x: int, 
                            position_y: int, resource_type: str, amount: int = 1,
                            agent_id: int = -1, **optional) -> None:
        """Record resource event data - zero processing overhead.
        
        Args:
            step: Simulation step number
            event_type_detail: Specific type of resource event (spawn, despawn, move, etc.)
            position_x: X coordinate of resource
            position_y: Y coordinate of resource
            resource_type: Type of resource
            amount: Amount of resource (default 1)
            agent_id: Optional agent context (default -1)
            **optional: Additional optional fields
        """
        event = {
            'type': 'resource_event',
            'step': step,
            'event_type_detail': event_type_detail,
            'position_x': position_x,
            'position_y': position_y,
            'resource_type': resource_type,
            'amount': amount,
            'agent_id': agent_id
        }
        event.update(optional)
        self._events.append(event)  # Just append - zero processing
    
    def record_economic_decision(self, step: int, agent_id: int, decision_type: str,
                               decision_context: str, utility_before: float = 0.0,
                               utility_after: float = 0.0, opportunity_cost: float = 0.0,
                               alternatives_considered: int = 0, decision_time_ms: float = 0.0,
                               position_x: int = -1, position_y: int = -1, **optional) -> None:
        """Record economic decision data - zero processing overhead.
        
        Args:
            step: Simulation step number
            agent_id: ID of agent making economic decision
            decision_type: Type of economic decision (resource_selection, trade_proposal, etc.)
            decision_context: Detailed context of decision
            utility_before: Agent's utility before decision (default 0.0)
            utility_after: Agent's utility after decision (default 0.0)
            opportunity_cost: Cost of not choosing alternatives (default 0.0)
            alternatives_considered: Number of alternatives evaluated (default 0)
            decision_time_ms: Time taken to make decision (default 0.0)
            position_x: Optional X coordinate context (default -1)
            position_y: Optional Y coordinate context (default -1)
            **optional: Additional optional fields
        """
        event = {
            'type': 'economic_decision',
            'step': step,
            'agent_id': agent_id,
            'decision_type': decision_type,
            'decision_context': decision_context,
            'utility_before': utility_before,
            'utility_after': utility_after,
            'utility_delta': utility_after - utility_before,
            'opportunity_cost': opportunity_cost,
            'alternatives_considered': alternatives_considered,
            'decision_time_ms': decision_time_ms,
            'position_x': position_x,
            'position_y': position_y
        }
        event.update(optional)
        self._events.append(event)  # Just append - zero processing
    
    # ============================================================================
    # DATA ACCESS METHODS - Event Filtering and Analysis
    # ============================================================================
    
    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Get all events of a specific type.
        
        Args:
            event_type: Type of events to filter (e.g., 'trade', 'mode_change')
            
        Returns:
            List of event dictionaries matching the specified type
        """
        return [event for event in self._events if event.get('type') == event_type]
    
    def get_events_by_step(self, step: int) -> List[Dict[str, Any]]:
        """Get all events from a specific simulation step.
        
        Args:
            step: Simulation step number
            
        Returns:
            List of event dictionaries from the specified step
        """
        return [event for event in self._events if event.get('step') == step]
    
    def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all events in chronological order.
        
        Returns:
            List of all event dictionaries in chronological order
        """
        return self._events.copy()  # Return copy to prevent external modification
    
    def get_events_by_agent(self, agent_id: int) -> List[Dict[str, Any]]:
        """Get all events related to a specific agent.
        
        Args:
            agent_id: ID of agent to filter events for
            
        Returns:
            List of event dictionaries related to the specified agent
        """
        related_events = []
        for event in self._events:
            # Check direct agent_id field
            if event.get('agent_id') == agent_id:
                related_events.append(event)
            # Check trade events where agent is seller or buyer
            elif event.get('type') == 'trade':
                if event.get('seller_id') == agent_id or event.get('buyer_id') == agent_id:
                    related_events.append(event)
        return related_events
    
    def get_events_in_range(self, start_step: int, end_step: int) -> List[Dict[str, Any]]:
        """Get all events within a step range (inclusive).
        
        Args:
            start_step: Starting step number (inclusive)
            end_step: Ending step number (inclusive)
            
        Returns:
            List of event dictionaries within the specified step range
        """
        return [event for event in self._events 
                if start_step <= event.get('step', 0) <= end_step]
    
    # ============================================================================
    # STATISTICS AND METADATA METHODS
    # ============================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get observer statistics and metadata.
        
        Returns:
            Dictionary containing observer statistics including:
            - total_events: Total number of events recorded
            - event_types: Set of all event types recorded
            - step_range: Tuple of (min_step, max_step) if events exist
            - recording_duration: Time since observer creation
            - events_per_second: Average recording rate
        """
        if not self._events:
            return {
                'total_events': 0,
                'event_types': set(),
                'step_range': (0, 0),
                'recording_duration': time.time() - self._start_time,
                'events_per_second': 0.0
            }
        
        steps = [event.get('step', 0) for event in self._events]
        event_types = set(event.get('type', 'unknown') for event in self._events)
        duration = time.time() - self._start_time
        
        return {
            'total_events': len(self._events),
            'event_types': event_types,
            'step_range': (min(steps), max(steps)),
            'recording_duration': duration,
            'events_per_second': len(self._events) / duration if duration > 0 else 0.0
        }
    
    def get_event_type_counts(self) -> Dict[str, int]:
        """Get count of events by type.
        
        Returns:
            Dictionary mapping event types to their counts
        """
        counts: Dict[str, int] = {}
        for event in self._events:
            event_type = event.get('type', 'unknown')
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts
    
    def get_step_event_counts(self) -> Dict[int, int]:
        """Get count of events by step.
        
        Returns:
            Dictionary mapping step numbers to their event counts
        """
        counts: Dict[int, int] = {}
        for event in self._events:
            step = event.get('step', 0)
            counts[step] = counts.get(step, 0) + 1
        return counts
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def clear_events(self) -> None:
        """Clear all recorded events. Useful for testing or reset scenarios."""
        self._events.clear()
        self._start_time = time.time()
    
    def get_memory_usage_estimate(self) -> Dict[str, Any]:
        """Get estimated memory usage of stored events.
        
        Returns:
            Dictionary with memory usage estimates in bytes
        """
        if not self._events:
            return {
                'total_bytes': 0,
                'events_count': 0,
                'bytes_per_event': 0
            }
        
        # Rough estimate: each event dict is ~100-200 bytes on average
        estimated_bytes = len(self._events) * 150  # Conservative estimate
        
        return {
            'total_bytes': estimated_bytes,
            'events_count': len(self._events),
            'bytes_per_event': estimated_bytes / len(self._events)
        }
    
    def __len__(self) -> int:
        """Return number of recorded events."""
        return len(self._events)
    
    def __repr__(self) -> str:
        """String representation of observer state."""
        stats = self.get_statistics()
        return (f"RawDataObserver(events={stats['total_events']}, "
                f"types={len(stats['event_types'])}, "
                f"steps={stats['step_range']})")
