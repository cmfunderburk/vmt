"""Educational analytics observer using raw data architecture for behavioral insights and learning.

This module implements the EducationalObserver class that preserves and
provides educational features using the new
raw data recording architecture for zero-overhead performance.

Features:
- Zero-overhead raw data recording during simulation
- Deferred educational analysis using standalone analysis formatters
- Educational analytics and behavioral insights
- Agent behavior pattern analysis
- System dynamics understanding
- Learning-focused metrics and summaries
- Raw data storage with analysis formatters in separate analysis module

Architecture:
- Inherits from both BaseObserver (for configuration) and RawDataObserver (for storage)
- Uses standalone analysis formatters for converting raw data to analysis-ready format
- No processing overhead during simulation execution
- Educational analysis performed only when needed using analysis module formatters
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List, Any, Set, TYPE_CHECKING

from .base_observer import BaseObserver
from ..raw_data.raw_data_observer import RawDataObserver
from ..raw_data.raw_data_writer import RawDataWriter

if TYPE_CHECKING:
    from ..config import ObservabilityConfig
    from ..events import SimulationEvent


class EducationalObserver(BaseObserver, RawDataObserver):
    """Educational analytics observer using raw data architecture for learning and insights.
    
    Provides educational features for learning and analysis,
    providing comprehensive behavioral analysis and educational metrics
    for understanding agent behavior and simulation dynamics using zero-overhead raw data recording.
    
    Architecture:
    - Inherits from both BaseObserver (for configuration) and RawDataObserver (for storage)
    - Uses standalone analysis formatters for converting raw data to analysis-ready format
    - Zero-overhead recording during simulation, analysis deferred to when needed
    - Raw data storage with analysis formatters in separate analysis module
    """

    def __init__(self, config: ObservabilityConfig, 
                 behavioral_window: int = 100, 
                 correlation_window: int = 50,
                 output_dir: str = None):
        """Initialize the educational observer with raw data architecture.
        
        Args:
            config: Observability configuration
            behavioral_window: Window size for behavioral aggregation
            correlation_window: Window size for correlation analysis
            output_dir: Optional output directory for educational analysis files
        """
        # Initialize both parent classes
        BaseObserver.__init__(self, config)
        RawDataObserver.__init__(self)
        
        self.output_dir = output_dir
        
        # Legacy compatibility - kept for backward compatibility
        self._behavioral_window = behavioral_window
        self._correlation_window = correlation_window
        
        # Educational analytics state
        self._session_insights: Dict[str, Any] = {}
        self._learning_objectives: List[str] = []
        self._key_patterns: List[Dict[str, Any]] = []
        
        # Agent tracking for educational insights
        self._agent_learning_profiles: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
            'modes_explored': set(),
            'adaptation_events': [],
            'learning_score': 0.0,
        })
        
        # System-level educational metrics
        self._system_dynamics: Dict[str, Any] = {
            'cooperation_events': 0,
            'competition_events': 0,
            'resource_conflicts': 0,
            'successful_adaptations': 0,
        }
        
        # Statistics for reporting
        self._total_insights_generated = 0
        self._last_analysis_step = 0
        
        # Initialize raw data writer for disk persistence
        self._raw_data_writer = RawDataWriter(
            compress=True,
            compression_level=6,
            max_file_size_mb=100,
            enable_rotation=True,
            atomic_writes=True
        )

    def _initialize_event_filtering(self) -> None:
        """Initialize event filtering for educational analysis.
        
        EducationalObserver focuses on events that provide learning
        insights about agent behavior and system dynamics.
        """
        self._enabled_event_types = {
            'agent_mode_change',      # Core behavioral data
            'trade_execution',        # Economic interactions
            'resource_collection',    # Resource competition
            'agent_decision',         # Decision-making patterns
            'economic_decision',      # Economic decision-making
            'debug_log',              # Educational debug information
            'performance_monitor',    # Performance insights
            'resource_event',         # Resource dynamics
        }

    def notify(self, event: SimulationEvent) -> None:
        """Handle a simulation event by recording raw data.
        
        This method now uses the raw data recording architecture for zero-overhead
        performance. Events are stored as raw dictionaries with no processing.
        Educational analysis is deferred to when data is actually needed.
        
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

    def _analyze_event_for_learning(self, event: SimulationEvent) -> None:
        """Analyze an individual event for educational insights.
        
        Args:
            event: The simulation event to analyze
        """
        event_type = event.event_type
        
        if event_type == 'agent_mode_change':
            self._analyze_mode_change_learning(event)
        elif event_type == 'trade_execution':
            self._analyze_trade_learning(event)
        elif event_type == 'resource_collection':
            self._analyze_resource_learning(event)

    def _analyze_mode_change_learning(self, event: SimulationEvent) -> None:
        """Analyze mode changes for learning insights.
        
        Args:
            event: Agent mode change event
        """
        if not hasattr(event, 'agent_id'):
            return
            
        agent_id = event.agent_id
        profile = self._agent_learning_profiles[agent_id]
        
        # Track mode exploration
        if hasattr(event, 'new_mode'):
            profile['modes_explored'].add(event.new_mode)
        
        # Analyze adaptation patterns
        if hasattr(event, 'reason'):
            reason = event.reason
            if 'stagnation' in reason.lower() or 'retarget' in reason.lower():
                profile['adaptation_events'].append({
                    'step': event.step,
                    'reason': reason,
                    'adaptive_behavior': True,
                })
                self._system_dynamics['successful_adaptations'] += 1

    def _analyze_trade_learning(self, event: SimulationEvent) -> None:
        """Analyze trade events for economic learning insights.
        
        Args:
            event: Trade execution event
        """
        # Track cooperation vs competition patterns
        if hasattr(event, 'utility_gain'):
            utility_gain = getattr(event, 'utility_gain', 0)
            if utility_gain > 0:
                self._system_dynamics['cooperation_events'] += 1
            else:
                self._system_dynamics['competition_events'] += 1

    def _analyze_resource_learning(self, event: SimulationEvent) -> None:
        """Analyze resource collection for resource dynamics learning.
        
        Args:
            event: Resource collection event
        """
        # Track resource competition (simplified analysis)
        self._system_dynamics['resource_conflicts'] += 1

    def flush_step(self, step: int) -> None:
        """Handle end-of-step boundary with zero overhead.
        
        In the raw data architecture, no processing is done at step boundaries.
        All data is stored in memory and educational analysis is performed only when needed.
        
        Args:
            step: The simulation step that just completed
        """
        # Zero overhead - no processing during simulation
        # Raw data is stored in memory and analysis is deferred
        self._last_analysis_step = step

    def _generate_educational_insights_from_raw_data(self) -> Dict[str, Any]:
        """Generate educational insights from raw data.
        
        Returns:
            Dictionary containing comprehensive educational insights
        """
        # Get all raw events
        all_events = self.get_all_events()
        
        # Translate events to human-readable format
        translated_events = []
        for event in all_events:
            try:
                if event['type'] == 'trade':
                    translated_events.append(self._data_translator.translate_trade_event(event))
                elif event['type'] == 'mode_change':
                    translated_events.append(self._data_translator.translate_mode_change_event(event))
                elif event['type'] == 'resource_collection':
                    translated_events.append(self._data_translator.translate_resource_collection_event(event))
                elif event['type'] == 'agent_decision':
                    translated_events.append(self._data_translator.translate_agent_decision_event(event))
                elif event['type'] == 'economic_decision':
                    translated_events.append(self._data_translator.translate_economic_decision_event(event))
                else:
                    # Keep raw event for unknown types
                    translated_events.append(event)
            except Exception as e:
                # Keep raw event if translation fails
                translated_events.append(event)
        
        # Generate comprehensive educational analysis
        insights = {
            "total_events": len(all_events),
            "event_types": self.get_event_type_counts(),
            "step_range": self.get_statistics()['step_range'],
            "translated_events": translated_events,
            "behavioral_insights": self._analyze_behavioral_patterns_from_raw_data(),
            "system_dynamics_insights": self._analyze_system_dynamics_from_raw_data(),
            "agent_learning_insights": self._analyze_agent_learning_from_raw_data(),
            "educational_recommendations": self._generate_educational_recommendations_from_raw_data(),
        }
        
        return insights

    def _analyze_behavioral_patterns_from_raw_data(self) -> Dict[str, Any]:
        """Analyze behavioral patterns from raw data for educational insights."""
        mode_change_events = self.get_events_by_type('mode_change')
        agent_decision_events = self.get_events_by_type('agent_decision')
        
        # Analyze mode distribution
        mode_distribution = {}
        agent_mode_transitions = {}
        
        for event in mode_change_events:
            new_mode = event.get('new_mode', 'unknown')
            mode_distribution[new_mode] = mode_distribution.get(new_mode, 0) + 1
            
            # Track agent mode transitions
            agent_id = event.get('agent_id', -1)
            if agent_id >= 0:
                if agent_id not in agent_mode_transitions:
                    agent_mode_transitions[agent_id] = []
                transition = f"{event.get('old_mode', '?')} → {new_mode}"
                agent_mode_transitions[agent_id].append(transition)
        
        # Find dominant behavior
        dominant_behavior = None
        if mode_distribution:
            dominant_mode = max(mode_distribution.items(), key=lambda x: x[1])
            dominant_behavior = {
                'mode': dominant_mode[0],
                'frequency': dominant_mode[1],
                'educational_note': f"Most agents are in {dominant_mode[0]} mode, indicating {self._get_mode_explanation(dominant_mode[0])}"
            }
        
        # Analyze behavioral diversity
        total_agents = len(agent_mode_transitions)
        diverse_agents = sum(1 for transitions in agent_mode_transitions.values() if len(transitions) > 2)
        
        return {
            'mode_distribution': mode_distribution,
            'dominant_behavior': dominant_behavior,
            'behavioral_diversity': {
                'diverse_agents': diverse_agents,
                'diversity_ratio': diverse_agents / total_agents if total_agents > 0 else 0,
                'educational_note': f"{diverse_agents}/{total_agents} agents show diverse behavior patterns"
            },
            'agent_mode_transitions': agent_mode_transitions,
            'total_mode_changes': len(mode_change_events),
            'total_agent_decisions': len(agent_decision_events)
        }

    def _analyze_system_dynamics_from_raw_data(self) -> Dict[str, Any]:
        """Analyze system dynamics from raw data for educational insights."""
        trade_events = self.get_events_by_type('trade')
        resource_collection_events = self.get_events_by_type('resource_collection')
        resource_events = self.get_events_by_type('resource_event')
        
        # Analyze trade relationships
        trade_pairs = {}
        cooperation_events = 0
        competition_events = 0
        
        for event in trade_events:
            seller_id = event.get('seller_id', -1)
            buyer_id = event.get('buyer_id', -1)
            delta_u_seller = event.get('delta_u_seller', 0.0)
            delta_u_buyer = event.get('delta_u_buyer', 0.0)
            
            if seller_id >= 0 and buyer_id >= 0:
                pair_key = f"{min(seller_id, buyer_id)}-{max(seller_id, buyer_id)}"
                trade_pairs[pair_key] = trade_pairs.get(pair_key, 0) + 1
                
                # Analyze cooperation vs competition
                if delta_u_seller > 0 and delta_u_buyer > 0:
                    cooperation_events += 1
                else:
                    competition_events += 1
        
        # Analyze resource competition
        resource_locations = {}
        for event in resource_collection_events:
            x = event.get('x', -1)
            y = event.get('y', -1)
            if x >= 0 and y >= 0:
                location_key = f"{x},{y}"
                resource_locations[location_key] = resource_locations.get(location_key, 0) + 1
        
        # Find competition hotspots (locations with multiple collections)
        competition_hotspots = sum(1 for count in resource_locations.values() if count > 1)
        
        return {
            'economic_dynamics': {
                'active_trading_pairs': len(trade_pairs),
                'cooperation_events': cooperation_events,
                'competition_events': competition_events,
                'cooperation_level': 'high' if cooperation_events > competition_events * 2 else 'moderate' if cooperation_events > competition_events else 'low',
                'educational_note': f"Economic system shows {len(trade_pairs)} active trading relationships with {cooperation_events} cooperative and {competition_events} competitive interactions"
            },
            'resource_dynamics': {
                'competition_hotspots': competition_hotspots,
                'total_resource_locations': len(resource_locations),
                'competition_level': 'high' if competition_hotspots > 3 else 'moderate' if competition_hotspots > 1 else 'low',
                'educational_note': f"Resource competition detected at {competition_hotspots} locations out of {len(resource_locations)} total locations"
            },
            'trade_relationships': trade_pairs,
            'resource_locations': resource_locations
        }

    def _analyze_agent_learning_from_raw_data(self) -> Dict[str, Any]:
        """Analyze agent learning patterns from raw data for educational insights."""
        mode_change_events = self.get_events_by_type('mode_change')
        agent_decision_events = self.get_events_by_type('agent_decision')
        economic_decision_events = self.get_events_by_type('economic_decision')
        
        # Track agent learning profiles
        agent_profiles = {}
        
        for event in mode_change_events:
            agent_id = event.get('agent_id', -1)
            if agent_id >= 0:
                if agent_id not in agent_profiles:
                    agent_profiles[agent_id] = {
                        'modes_explored': set(),
                        'adaptation_events': [],
                        'learning_score': 0.0,
                        'decisions_made': 0,
                        'economic_decisions': 0
                    }
                
                new_mode = event.get('new_mode', '')
                agent_profiles[agent_id]['modes_explored'].add(new_mode)
                
                # Track adaptation events
                reason = event.get('reason', '')
                if 'stagnation' in reason.lower() or 'retarget' in reason.lower():
                    agent_profiles[agent_id]['adaptation_events'].append({
                        'step': event.get('step', 0),
                        'reason': reason,
                        'adaptive_behavior': True,
                    })
        
        # Count decisions per agent
        for event in agent_decision_events:
            agent_id = event.get('agent_id', -1)
            if agent_id >= 0:
                if agent_id not in agent_profiles:
                    agent_profiles[agent_id] = {
                        'modes_explored': set(),
                        'adaptation_events': [],
                        'learning_score': 0.0,
                        'decisions_made': 0,
                        'economic_decisions': 0
                    }
                agent_profiles[agent_id]['decisions_made'] += 1
        
        for event in economic_decision_events:
            agent_id = event.get('agent_id', -1)
            if agent_id >= 0:
                if agent_id not in agent_profiles:
                    agent_profiles[agent_id] = {
                        'modes_explored': set(),
                        'adaptation_events': [],
                        'learning_score': 0.0,
                        'decisions_made': 0,
                        'economic_decisions': 0
                    }
                agent_profiles[agent_id]['economic_decisions'] += 1
        
        # Calculate learning scores
        for agent_id, profile in agent_profiles.items():
            mode_diversity = len(profile['modes_explored'])
            adaptation_count = len(profile['adaptation_events'])
            total_decisions = profile['decisions_made'] + profile['economic_decisions']
            profile['learning_score'] = mode_diversity + (adaptation_count * 0.5) + (total_decisions * 0.1)
        
        # Find most adaptive agents
        sorted_agents = sorted(
            agent_profiles.items(),
            key=lambda x: x[1]['learning_score'],
            reverse=True
        )
        
        # Convert sets to lists for JSON serialization
        serializable_agent_profiles = {}
        for agent_id, profile in agent_profiles.items():
            serializable_agent_profiles[agent_id] = {
                'modes_explored': list(profile['modes_explored']),  # Convert set to list
                'adaptation_events': profile['adaptation_events'],
                'learning_score': profile['learning_score'],
                'decisions_made': profile['decisions_made'],
                'economic_decisions': profile['economic_decisions']
            }
        
        return {
            'total_agents_tracked': len(agent_profiles),
            'most_adaptive_agents': [
                {
                    'agent_id': agent_id,
                    'learning_score': profile['learning_score'],
                    'modes_explored': len(profile['modes_explored']),
                    'adaptations': len(profile['adaptation_events']),
                    'decisions_made': profile['decisions_made'],
                    'economic_decisions': profile['economic_decisions']
                }
                for agent_id, profile in sorted_agents[:5]  # Top 5
            ],
            'average_learning_score': sum(p['learning_score'] for p in agent_profiles.values()) / len(agent_profiles) if agent_profiles else 0,
            'agent_profiles': serializable_agent_profiles
        }
    
    def _generate_educational_recommendations_from_raw_data(self) -> List[str]:
        """Generate educational recommendations based on raw data analysis."""
        recommendations = []
        
        # Get system dynamics analysis
        system_dynamics = self._analyze_system_dynamics_from_raw_data()
        behavioral_patterns = self._analyze_behavioral_patterns_from_raw_data()
        agent_learning = self._analyze_agent_learning_from_raw_data()
        
        # Analyze cooperation vs competition
        economic_dynamics = system_dynamics.get('economic_dynamics', {})
        cooperation_events = economic_dynamics.get('cooperation_events', 0)
        competition_events = economic_dynamics.get('competition_events', 0)
        
        if cooperation_events > competition_events:
            recommendations.append(
                "Observe how agents benefit from cooperative trading relationships"
            )
        elif competition_events > cooperation_events:
            recommendations.append(
                "Notice how competitive interactions affect agent behavior and outcomes"
            )
        
        # Analyze adaptation patterns
        total_adaptations = sum(len(profile['adaptation_events']) for profile in agent_learning.get('agent_profiles', {}).values())
        if total_adaptations > 10:
            recommendations.append(
                "Notice how agents adapt their behavior when facing challenges"
            )
        
        # Analyze behavioral diversity
        behavioral_diversity = behavioral_patterns.get('behavioral_diversity', {})
        diversity_ratio = behavioral_diversity.get('diversity_ratio', 0)
        if diversity_ratio > 0.5:
            recommendations.append(
                "Examine how different agents explore various behavioral strategies"
            )
        
        # Analyze resource competition
        resource_dynamics = system_dynamics.get('resource_dynamics', {})
        competition_hotspots = resource_dynamics.get('competition_hotspots', 0)
        if competition_hotspots > 0:
            recommendations.append(
                f"Study how resource competition at {competition_hotspots} locations affects agent strategies"
            )
        
        return recommendations

    def _get_agent_learning_summary(self) -> Dict[str, Any]:
        """Get summary of agent learning patterns.
        
        Returns:
            Dictionary summarizing agent learning behaviors
        """
        if not self._agent_learning_profiles:
            return {}
        
        # Calculate learning scores
        for agent_id, profile in self._agent_learning_profiles.items():
            mode_diversity = len(profile['modes_explored'])
            adaptation_count = len(profile['adaptation_events'])
            profile['learning_score'] = mode_diversity + (adaptation_count * 0.5)
        
        # Find most adaptive agents
        sorted_agents = sorted(
            self._agent_learning_profiles.items(),
            key=lambda x: x[1]['learning_score'],
            reverse=True
        )
        
        return {
            'total_agents_tracked': len(self._agent_learning_profiles),
            'most_adaptive_agents': [
                {
                    'agent_id': agent_id,
                    'learning_score': profile['learning_score'],
                    'modes_explored': len(profile['modes_explored']),
                    'adaptations': len(profile['adaptation_events']),
                }
                for agent_id, profile in sorted_agents[:5]  # Top 5
            ],
            'average_learning_score': sum(p['learning_score'] for p in self._agent_learning_profiles.values()) / len(self._agent_learning_profiles),
        }

    def _get_mode_explanation(self, mode: str) -> str:
        """Get educational explanation for a behavioral mode.
        
        Args:
            mode: The behavioral mode to explain
            
        Returns:
            Educational explanation string
        """
        explanations = {
            'IDLE': 'agents are waiting or deciding on their next action',
            'FORAGE': 'active resource seeking and exploration behavior',
            'RETURN_HOME': 'agents are returning to deposit resources',
            'TRADE': 'economic exchange and cooperation behavior',
        }
        return explanations.get(mode, f'agents are in {mode} behavioral state')

    # Public methods for accessing educational insights

    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary for educational review.
        
        Returns:
            Educational summary of the entire simulation session
        """
        # Generate educational insights from raw data
        educational_insights = self._generate_educational_insights_from_raw_data()
        
        return {
            'total_insights_generated': self._total_insights_generated,
            'last_analysis_step': self._last_analysis_step,
            'total_events': len(self.get_all_events()),
            'event_types': self.get_event_type_counts(),
            'step_range': self.get_statistics()['step_range'],
            'educational_insights': educational_insights,
            'key_learning_points': self._extract_key_learning_points_from_raw_data(),
        }

    def _extract_key_learning_points_from_raw_data(self) -> List[str]:
        """Extract key educational learning points from raw data analysis.
        
        Returns:
            List of key learning insights
        """
        points = []
        
        # Get system dynamics analysis
        system_dynamics = self._analyze_system_dynamics_from_raw_data()
        behavioral_patterns = self._analyze_behavioral_patterns_from_raw_data()
        agent_learning = self._analyze_agent_learning_from_raw_data()
        
        # Economic system insights
        economic_dynamics = system_dynamics.get('economic_dynamics', {})
        cooperation_events = economic_dynamics.get('cooperation_events', 0)
        competition_events = economic_dynamics.get('competition_events', 0)
        total_trades = cooperation_events + competition_events
        
        if total_trades > 0:
            cooperation_rate = cooperation_events / total_trades
            if cooperation_rate > 0.7:
                points.append("High cooperation rate demonstrates mutual benefit in trading")
            elif cooperation_rate < 0.3:
                points.append("Low cooperation suggests competitive resource dynamics")
        
        # Adaptation insights
        total_adaptations = sum(len(profile['adaptation_events']) for profile in agent_learning.get('agent_profiles', {}).values())
        if total_adaptations > 0:
            points.append(f"Agents demonstrated {total_adaptations} adaptive behaviors")
        
        # Behavioral diversity insights
        agent_profiles = agent_learning.get('agent_profiles', {})
        if agent_profiles:
            avg_modes = sum(len(p['modes_explored']) for p in agent_profiles.values()) / len(agent_profiles)
            if avg_modes > 2:
                points.append("Agents show diverse behavioral strategies and exploration")
        
        # Resource competition insights
        resource_dynamics = system_dynamics.get('resource_dynamics', {})
        competition_hotspots = resource_dynamics.get('competition_hotspots', 0)
        if competition_hotspots > 0:
            points.append(f"Resource competition at {competition_hotspots} locations shows spatial dynamics")
        
        return points

    def close(self) -> None:
        """Close the educational observer and write final results."""
        # Write final educational analysis if output directory is specified
        if self.output_dir and len(self._events) > 0:
            try:
                import json
                from pathlib import Path
                
                output_path = Path(self.output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                
                # Generate final educational analysis
                educational_analysis = self._generate_educational_insights_from_raw_data()
                
                # Write educational analysis file
                analysis_file = output_path / f"educational_analysis_final.json"
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    json.dump(educational_analysis, f, indent=2)
                
                # Write raw data using RawDataWriter
                raw_data_file = output_path / f"educational_raw_data_final.jsonl.gz"
                write_result = self._raw_data_writer.flush_to_disk(
                    events=self.get_all_events(),
                    filepath=raw_data_file,
                    append=False
                )
                
                print(f"EducationalObserver closed. Wrote {write_result['events_written']} events "
                      f"({write_result['bytes_written']} bytes) to {raw_data_file}")
                
            except Exception as e:
                print(f"Warning: Failed to write final educational data: {e}")
        
        # Call parent close method
        super().close()
        
        # Clear raw data from memory after writing
        self.clear_events()

    def get_observer_stats(self) -> Dict[str, Any]:
        """Get educational observer statistics.
        
        Returns:
            Dictionary containing educational observer metrics
        """
        base_stats = super().get_observer_stats()
        raw_data_stats = self.get_statistics()
        
        educational_stats = {
            'observer_type': 'educational',
            'total_insights_generated': self._total_insights_generated,
            'agents_tracked': len(self._agent_learning_profiles),
            'last_analysis_step': self._last_analysis_step,
            'system_dynamics': self._system_dynamics.copy(),
            'output_dir': self.output_dir,
            'raw_data_events': raw_data_stats['total_events'],
            'raw_data_types': list(raw_data_stats['event_types']),
            'step_range': raw_data_stats['step_range'],
        }
        
        return {**base_stats, **educational_stats}

    def __repr__(self) -> str:
        """String representation of the educational observer."""
        raw_data_stats = self.get_statistics()
        return (f"EducationalObserver(events={raw_data_stats['total_events']}, "
                f"types={len(raw_data_stats['event_types'])}, "
                f"insights={self._total_insights_generated}, "
                f"agents={len(self._agent_learning_profiles)}, closed={self._closed})")