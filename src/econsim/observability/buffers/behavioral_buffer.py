"""Behavioral aggregation buffer for agent activity analysis.

This module implements the BehavioralAggregationBuffer as specified in the
UNIFIED_REFACTOR_PLAN. It aggregates agent behavioral data over configurable
time windows to provide insights into agent activity patterns, mode changes,
and behavioral trends.

Features:
- Configurable sliding window aggregation
- Per-agent activity tracking
- Mode change frequency analysis
- Behavioral pattern detection
- Educational analytics support
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import List, Dict, Any, DefaultDict, TYPE_CHECKING

from .base import EventBuffer

if TYPE_CHECKING:
    from ..events import SimulationEvent, AgentModeChangeEvent


class BehavioralAggregationBuffer(EventBuffer):
    """Aggregates agent behavioral data over configurable windows.
    
    Tracks agent activities, mode changes, and behavioral patterns
    within sliding time windows for educational and analytical purposes.
    """

    def __init__(self, window_size: int = 100):
        """Initialize the behavioral aggregation buffer.
        
        Args:
            window_size: Number of steps to aggregate behavior over
        """
        self._window_size = window_size
        
        # Per-agent activity tracking
        self._agent_activities: DefaultDict[int, DefaultDict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Mode change tracking with timestamps
        self._mode_changes: List[Dict[str, Any]] = []
        
        # Step-based event queues for sliding window
        self._event_window: deque = deque(maxlen=window_size)
        
        # Current step tracking
        self._current_step = 0
        
        # Aggregated statistics
        self._total_mode_changes = 0
        self._agents_tracked = set()
    
    def add_event(self, event: SimulationEvent) -> None:
        """Add an event to the behavioral aggregation buffer.
        
        Processes simulation events to extract behavioral patterns,
        focusing on agent mode changes and activity tracking.
        
        Args:
            event: The simulation event to process
        """
        # Update current step tracking
        self._current_step = max(self._current_step, event.step)
        
        # Process agent mode change events
        if event.event_type == "agent_mode_change":
            self._process_mode_change_event(event)
        
        # Add to sliding window for temporal analysis
        event_data = {
            'step': event.step,
            'timestamp': event.timestamp,
            'event_type': event.event_type,
        }
        
        # Extract event-specific data
        if hasattr(event, 'agent_id'):
            event_data['agent_id'] = event.agent_id
            self._agents_tracked.add(event.agent_id)
            
        if hasattr(event, 'old_mode'):
            event_data['old_mode'] = event.old_mode
            
        if hasattr(event, 'new_mode'):
            event_data['new_mode'] = event.new_mode
            
        if hasattr(event, 'reason'):
            event_data['reason'] = event.reason
            
        self._event_window.append(event_data)
    
    def _process_mode_change_event(self, event: SimulationEvent) -> None:
        """Process agent mode change events for behavioral analysis.
        
        Args:
            event: Agent mode change event
        """
        if not hasattr(event, 'agent_id') or not hasattr(event, 'new_mode'):
            return
            
        agent_id = event.agent_id
        new_mode = event.new_mode
        
        # Track mode frequencies per agent
        self._agent_activities[agent_id][new_mode] += 1
        
        # Record mode change with context
        mode_change_record = {
            'step': event.step,
            'timestamp': event.timestamp,
            'agent_id': agent_id,
            'old_mode': getattr(event, 'old_mode', 'unknown'),
            'new_mode': new_mode,
            'reason': getattr(event, 'reason', ''),
        }
        
        self._mode_changes.append(mode_change_record)
        self._total_mode_changes += 1
    
    def flush_step(self, step: int) -> List[Dict[str, Any]]:
        """Flush behavioral aggregation data at step boundary.
        
        Generates comprehensive behavioral analysis including:
        - Agent activity summaries
        - Mode change patterns
        - Behavioral statistics
        - Educational insights
        
        Args:
            step: The simulation step being completed
            
        Returns:
            List containing behavioral analysis data
        """
        if not self._agent_activities and not self._mode_changes:
            return []
        
        # Generate aggregated behavioral summary
        behavioral_summary = {
            'event_type': 'behavioral_aggregation',
            'step': step,
            'timestamp': getattr(self, '_last_timestamp', step),  # Use step if no timestamp available
            'window_size': self._window_size,
            'step_range': {
                'start': max(0, step - self._window_size + 1),
                'end': step,
            },
            'summary': self._generate_behavioral_summary(),
            'agent_details': self._generate_agent_details(),
            'mode_changes': self._get_recent_mode_changes(step),
        }
        
        # Clear old data outside window
        self._cleanup_old_data(step)
        
        return [behavioral_summary]
    
    def _generate_behavioral_summary(self) -> Dict[str, Any]:
        """Generate high-level behavioral summary statistics.
        
        Returns:
            Dictionary containing summary statistics
        """
        if not self._agents_tracked:
            return {
                'total_agents': 0,
                'total_mode_changes': 0,
                'most_active_agents': [],
                'mode_distribution': {},
            }
        
        # Calculate mode distribution across all agents
        mode_totals = defaultdict(int)
        for agent_activities in self._agent_activities.values():
            for mode, count in agent_activities.items():
                mode_totals[mode] += count
        
        # Find most active agents (by mode change frequency)
        agent_activity_scores = {
            agent_id: sum(activities.values())
            for agent_id, activities in self._agent_activities.items()
        }
        
        most_active = sorted(
            agent_activity_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]  # Top 10 most active agents
        
        return {
            'total_agents': len(self._agents_tracked),
            'total_mode_changes': self._total_mode_changes,
            'most_active_agents': [
                {'agent_id': agent_id, 'activity_score': score}
                for agent_id, score in most_active
            ],
            'mode_distribution': dict(mode_totals),
        }
    
    def _generate_agent_details(self) -> Dict[int, Dict[str, Any]]:
        """Generate detailed per-agent behavioral analysis.
        
        Returns:
            Dictionary mapping agent IDs to their behavioral details
        """
        agent_details = {}
        
        for agent_id in self._agents_tracked:
            activities = self._agent_activities[agent_id]
            
            if activities:
                # Calculate agent-specific metrics
                total_activity = sum(activities.values())
                most_common_mode = max(activities.items(), key=lambda x: x[1])
                
                agent_details[agent_id] = {
                    'total_mode_changes': total_activity,
                    'mode_frequencies': dict(activities),
                    'most_common_mode': {
                        'mode': most_common_mode[0],
                        'frequency': most_common_mode[1],
                        'percentage': (most_common_mode[1] / total_activity * 100) if total_activity > 0 else 0,
                    },
                    'mode_diversity': len(activities),  # Number of different modes used
                }
        
        return agent_details
    
    def _get_recent_mode_changes(self, step: int) -> List[Dict[str, Any]]:
        """Get recent mode changes within the current window.
        
        Args:
            step: Current step for window calculation
            
        Returns:
            List of recent mode change records
        """
        window_start = max(0, step - self._window_size + 1)
        
        recent_changes = [
            change for change in self._mode_changes
            if change['step'] >= window_start
        ]
        
        return recent_changes
    
    def _cleanup_old_data(self, step: int) -> None:
        """Clean up data outside the sliding window.
        
        Args:
            step: Current step for determining cleanup boundary
        """
        window_start = max(0, step - self._window_size + 1)
        
        # Remove old mode changes
        self._mode_changes = [
            change for change in self._mode_changes
            if change['step'] >= window_start
        ]
        
        # Note: We keep agent activity counters as cumulative for the session
        # but could implement sliding window counts here if needed
    
    def clear(self) -> None:
        """Clear all behavioral aggregation data."""
        self._agent_activities.clear()
        self._mode_changes.clear()
        self._event_window.clear()
        self._agents_tracked.clear()
        self._current_step = 0
        self._total_mode_changes = 0
    
    def get_buffer_stats(self) -> Dict[str, Any]:
        """Get statistics about behavioral buffer state.
        
        Returns:
            Dictionary containing buffer metrics
        """
        return {
            'type': 'BehavioralAggregationBuffer',
            'window_size': self._window_size,
            'agents_tracked': len(self._agents_tracked),
            'total_mode_changes': self._total_mode_changes,
            'events_in_window': len(self._event_window),
            'current_step': self._current_step,
        }