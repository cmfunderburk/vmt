"""Correlation buffer for tracking event relationships and patterns.

This module implements event correlation tracking to identify patterns
and relationships between different simulation events. It's designed
for advanced analytics and educational insights about system behavior.

Features:
- Temporal event correlation analysis
- Agent interaction pattern detection
- Resource competition tracking
- Trade relationship identification
- Educational pattern analysis
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import List, Dict, Any, DefaultDict, Set, Tuple, TYPE_CHECKING

from .base import EventBuffer

if TYPE_CHECKING:
    from ..events import SimulationEvent


class CorrelationBuffer(EventBuffer):
    """Tracks correlations and relationships between simulation events.
    
    Analyzes temporal patterns, agent interactions, and system behaviors
    to provide insights into simulation dynamics and agent relationships.
    """

    def __init__(self, correlation_window: int = 50, max_correlations: int = 1000):
        """Initialize the correlation buffer.
        
        Args:
            correlation_window: Number of steps to look back for correlations
            max_correlations: Maximum number of correlations to track
        """
        self._correlation_window = correlation_window
        self._max_correlations = max_correlations
        
        # Event sequence tracking for temporal correlation
        self._event_sequence: deque = deque(maxlen=correlation_window * 10)
        
        # Agent interaction tracking
        self._agent_interactions: DefaultDict[Tuple[int, int], List[Dict[str, Any]]] = defaultdict(list)
        
        # Resource competition tracking
        self._resource_competition: DefaultDict[Tuple[int, int], int] = defaultdict(int)  # (x, y) -> competition_count
        
        # Trade relationship tracking
        self._trade_relationships: DefaultDict[Tuple[int, int], Dict[str, Any]] = defaultdict(lambda: {
            'trade_count': 0,
            'last_trade_step': 0,
            'mutual_benefit_count': 0,
        })
        
        # Temporal pattern detection
        self._temporal_patterns: List[Dict[str, Any]] = []
        
        # Current step tracking
        self._current_step = 0
        
        # Statistics
        self._total_correlations_found = 0
        self._active_agents = set()

    def add_event(self, event: SimulationEvent) -> None:
        """Add an event and analyze it for correlations.
        
        Args:
            event: The simulation event to analyze for correlations
        """
        self._current_step = max(self._current_step, event.step)
        
        # Create event record for correlation analysis
        event_record = {
            'step': event.step,
            'timestamp': event.timestamp,
            'event_type': event.event_type,
        }
        
        # Extract relevant event data
        if hasattr(event, 'agent_id'):
            event_record['agent_id'] = event.agent_id
            self._active_agents.add(event.agent_id)
            
        # Add event-specific fields for correlation analysis
        self._extract_event_fields(event, event_record)
        
        # Add to sequence for temporal analysis
        self._event_sequence.append(event_record)
        
        # Analyze correlations based on event type
        self._analyze_event_correlations(event_record)
        
        # Cleanup old correlation data
        self._cleanup_old_correlations(event.step)

    def _extract_event_fields(self, event: SimulationEvent, event_record: Dict[str, Any]) -> None:
        """Extract event-specific fields for correlation analysis.
        
        Args:
            event: Source simulation event
            event_record: Target event record dictionary
        """
        # Common fields for correlation
        fields_to_extract = [
            'agent_id', 'old_mode', 'new_mode', 'reason',  # Mode changes
            'resource_x', 'resource_y', 'resource_type',   # Resource events  
            'partner_id', 'trade_value', 'utility_gain',   # Trade events
            'from_x', 'from_y', 'to_x', 'to_y',           # Movement events
        ]
        
        for field in fields_to_extract:
            if hasattr(event, field):
                event_record[field] = getattr(event, field)

    def _analyze_event_correlations(self, event_record: Dict[str, Any]) -> None:
        """Analyze the current event for correlations with recent events.
        
        Args:
            event_record: Event record to analyze
        """
        event_type = event_record['event_type']
        current_step = event_record['step']
        
        # Analyze different types of correlations
        if event_type == 'agent_mode_change':
            self._analyze_mode_change_correlations(event_record)
        elif event_type == 'trade_execution':
            self._analyze_trade_correlations(event_record)
        elif event_type == 'resource_collection':
            self._analyze_resource_correlations(event_record)
        elif event_type == 'agent_movement':
            self._analyze_movement_correlations(event_record)
    
    def _analyze_mode_change_correlations(self, event_record: Dict[str, Any]) -> None:
        """Analyze correlations for agent mode change events.
        
        Args:
            event_record: Mode change event record
        """
        agent_id = event_record.get('agent_id')
        if not agent_id:
            return
            
        current_step = event_record['step']
        window_start = max(0, current_step - self._correlation_window)
        
        # Look for recent mode changes by other agents
        related_events = []
        for event in self._event_sequence:
            if (event['step'] >= window_start and 
                event['event_type'] == 'agent_mode_change' and
                event.get('agent_id') != agent_id):
                related_events.append(event)
        
        # If we find clustering of mode changes, record it as a correlation
        if len(related_events) >= 2:  # Threshold for "clustering"
            correlation = {
                'type': 'mode_change_cluster',
                'trigger_agent': agent_id,
                'trigger_step': current_step,
                'related_agents': [e.get('agent_id') for e in related_events],
                'cluster_size': len(related_events) + 1,
                'time_window': current_step - min(e['step'] for e in related_events),
            }
            self._temporal_patterns.append(correlation)
            self._total_correlations_found += 1

    def _analyze_trade_correlations(self, event_record: Dict[str, Any]) -> None:
        """Analyze correlations for trade execution events.
        
        Args:
            event_record: Trade event record
        """
        agent_id = event_record.get('agent_id')
        partner_id = event_record.get('partner_id')
        
        if not (agent_id and partner_id):
            return
            
        # Create bidirectional relationship key
        relationship_key = tuple(sorted([agent_id, partner_id]))
        
        # Update trade relationship tracking
        trade_data = self._trade_relationships[relationship_key]
        trade_data['trade_count'] += 1
        trade_data['last_trade_step'] = event_record['step']
        
        # Check for mutual benefit (both agents gain utility)
        if event_record.get('utility_gain', 0) > 0:
            trade_data['mutual_benefit_count'] += 1

    def _analyze_resource_correlations(self, event_record: Dict[str, Any]) -> None:
        """Analyze correlations for resource collection events.
        
        Args:
            event_record: Resource collection event record
        """
        resource_x = event_record.get('resource_x')
        resource_y = event_record.get('resource_y')
        
        if resource_x is None or resource_y is None:
            return
            
        resource_pos = (resource_x, resource_y)
        current_step = event_record['step']
        window_start = max(0, current_step - self._correlation_window)
        
        # Look for other agents collecting from same location recently
        competitors = []
        for event in self._event_sequence:
            if (event['step'] >= window_start and
                event['event_type'] == 'resource_collection' and
                event.get('resource_x') == resource_x and
                event.get('resource_y') == resource_y and
                event.get('agent_id') != event_record.get('agent_id')):
                competitors.append(event)
        
        # Track resource competition
        if competitors:
            self._resource_competition[resource_pos] += 1

    def _analyze_movement_correlations(self, event_record: Dict[str, Any]) -> None:
        """Analyze correlations for agent movement events.
        
        Args:
            event_record: Movement event record
        """
        # Could implement flocking behavior detection, following patterns, etc.
        # For now, just track the movement for future analysis
        pass

    def _cleanup_old_correlations(self, current_step: int) -> None:
        """Remove correlation data outside the analysis window.
        
        Args:
            current_step: Current simulation step
        """
        # Limit temporal patterns to prevent unbounded growth
        if len(self._temporal_patterns) > self._max_correlations:
            # Keep most recent patterns
            self._temporal_patterns = self._temporal_patterns[-self._max_correlations:]

    def flush_step(self, step: int) -> List[Dict[str, Any]]:
        """Flush correlation analysis at step boundary.
        
        Args:
            step: The simulation step being completed
            
        Returns:
            List containing correlation analysis results
        """
        if not self._temporal_patterns and not self._trade_relationships and not self._resource_competition:
            return []

        # Generate correlation summary
        correlation_summary = {
            'event_type': 'correlation_analysis',
            'step': step,
            'timestamp': step,  # Use step as timestamp fallback
            'analysis_window': self._correlation_window,
            'correlations_found': self._total_correlations_found,
            'patterns': self._get_pattern_summary(),
            'trade_relationships': self._get_trade_relationship_summary(),
            'resource_competition': self._get_resource_competition_summary(),
            'active_agents': len(self._active_agents),
        }

        return [correlation_summary]

    def _get_pattern_summary(self) -> Dict[str, Any]:
        """Generate summary of detected patterns.
        
        Returns:
            Dictionary containing pattern analysis
        """
        if not self._temporal_patterns:
            return {'total_patterns': 0}

        # Analyze pattern types
        pattern_types = defaultdict(int)
        for pattern in self._temporal_patterns:
            pattern_types[pattern['type']] += 1

        return {
            'total_patterns': len(self._temporal_patterns),
            'pattern_types': dict(pattern_types),
            'recent_patterns': self._temporal_patterns[-10:],  # Last 10 patterns
        }

    def _get_trade_relationship_summary(self) -> Dict[str, Any]:
        """Generate summary of trade relationships.
        
        Returns:
            Dictionary containing trade relationship analysis
        """
        if not self._trade_relationships:
            return {'total_relationships': 0}

        # Find most active trading pairs
        active_relationships = [
            {
                'agents': list(agents),
                'trade_count': data['trade_count'],
                'last_trade_step': data['last_trade_step'],
                'mutual_benefit_rate': (
                    data['mutual_benefit_count'] / data['trade_count'] 
                    if data['trade_count'] > 0 else 0
                ),
            }
            for agents, data in self._trade_relationships.items()
            if data['trade_count'] > 0
        ]

        # Sort by trade frequency
        active_relationships.sort(key=lambda x: x['trade_count'], reverse=True)

        return {
            'total_relationships': len(self._trade_relationships),
            'active_relationships': len(active_relationships),
            'top_trading_pairs': active_relationships[:10],  # Top 10 pairs
        }

    def _get_resource_competition_summary(self) -> Dict[str, Any]:
        """Generate summary of resource competition.
        
        Returns:
            Dictionary containing resource competition analysis
        """
        if not self._resource_competition:
            return {'total_hotspots': 0}

        # Find most contested resource locations
        hotspots = [
            {'position': list(pos), 'competition_level': count}
            for pos, count in self._resource_competition.items()
            if count > 1  # Only locations with actual competition
        ]

        hotspots.sort(key=lambda x: x['competition_level'], reverse=True)

        return {
            'total_hotspots': len(hotspots),
            'top_contested_locations': hotspots[:10],  # Top 10 contested spots
            'average_competition': (
                sum(self._resource_competition.values()) / len(self._resource_competition)
                if self._resource_competition else 0
            ),
        }

    def clear(self) -> None:
        """Clear all correlation data."""
        self._event_sequence.clear()
        self._agent_interactions.clear()
        self._resource_competition.clear()
        self._trade_relationships.clear()
        self._temporal_patterns.clear()
        self._active_agents.clear()
        self._current_step = 0
        self._total_correlations_found = 0

    def get_buffer_stats(self) -> Dict[str, Any]:
        """Get statistics about correlation buffer state.
        
        Returns:
            Dictionary containing buffer metrics
        """
        return {
            'type': 'CorrelationBuffer',
            'correlation_window': self._correlation_window,
            'max_correlations': self._max_correlations,
            'events_in_sequence': len(self._event_sequence),
            'correlations_found': self._total_correlations_found,
            'active_agents': len(self._active_agents),
            'trade_relationships': len(self._trade_relationships),
            'resource_hotspots': len(self._resource_competition),
            'current_step': self._current_step,
        }