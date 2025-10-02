"""Educational analytics observer for behavioral insights and learning.

This module implements the EducationalObserver class that preserves and
enhances the educational features from the legacy GUILogger. It provides
comprehensive behavioral analysis, agent insights, and educational metrics
for understanding simulation dynamics.

Features:
- Educational analytics and behavioral insights
- Agent behavior pattern analysis
- System dynamics understanding
- Learning-focused metrics and summaries
- Integration with behavioral aggregation buffers
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List, Any, Set, TYPE_CHECKING

from .base_observer import BaseObserver
from ..buffers import BufferManager, BehavioralAggregationBuffer, CorrelationBuffer

if TYPE_CHECKING:
    from ..config import ObservabilityConfig
    from ..events import SimulationEvent


class EducationalObserver(BaseObserver):
    """Educational analytics observer for learning and insights.
    
    Preserves and enhances educational features from the legacy GUILogger,
    providing comprehensive behavioral analysis and educational metrics
    for understanding agent behavior and simulation dynamics.
    """

    def __init__(self, config: ObservabilityConfig, 
                 behavioral_window: int = 100, 
                 correlation_window: int = 50):
        """Initialize the educational observer.
        
        Args:
            config: Observability configuration
            behavioral_window: Window size for behavioral aggregation
            correlation_window: Window size for correlation analysis
        """
        super().__init__(config)
        
        # Create buffer manager with educational-focused buffers
        self._buffer_manager = BufferManager()
        self._buffer_manager.register_buffer(
            BehavioralAggregationBuffer(window_size=behavioral_window),
            'behavioral'
        )
        self._buffer_manager.register_buffer(
            CorrelationBuffer(correlation_window=correlation_window),
            'correlation'
        )
        
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

    def _initialize_event_filtering(self) -> None:
        """Initialize event filtering for educational analysis.
        
        EducationalObserver focuses on events that provide learning
        insights about agent behavior and system dynamics.
        """
        self._enabled_event_types = {
            'agent_mode_change',      # Core behavioral data
            'behavioral_aggregation', # Behavioral patterns
            'correlation_analysis',   # System relationships
            'trade_execution',        # Economic interactions
            'resource_collection',    # Resource competition
        }

    def notify(self, event: SimulationEvent) -> None:
        """Process a simulation event for educational insights.
        
        Args:
            event: The simulation event to analyze
        """
        if not self.is_enabled(event.event_type):
            return
        
        # Add to buffer system for aggregation and correlation
        self._buffer_manager.add_event(event)
        
        # Perform immediate educational analysis
        self._analyze_event_for_learning(event)

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
        """Generate educational insights at step boundary.
        
        Args:
            step: The simulation step that just completed
        """
        # Flush buffer system and get aggregated data
        buffered_data = self._buffer_manager.flush_step(step)
        
        # Generate educational insights from aggregated data
        if buffered_data:
            insights = self._generate_educational_insights(step, buffered_data)
            if insights:
                self._session_insights[f'step_{step}'] = insights
                self._total_insights_generated += 1
        
        self._last_analysis_step = step

    def _generate_educational_insights(self, step: int, 
                                     buffered_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Generate educational insights from buffered data.
        
        Args:
            step: Current simulation step
            buffered_data: Aggregated data from buffer system
            
        Returns:
            Dictionary containing educational insights
        """
        insights = {
            'step': step,
            'timestamp': time.time(),
            'insight_type': 'educational_analysis',
        }
        
        # Analyze behavioral patterns
        if 'behavioral' in buffered_data:
            behavioral_data = buffered_data['behavioral']
            if behavioral_data:
                insights['behavioral_insights'] = self._extract_behavioral_insights(behavioral_data[0])
        
        # Analyze correlation patterns
        if 'correlation' in buffered_data:
            correlation_data = buffered_data['correlation']
            if correlation_data:
                insights['system_insights'] = self._extract_system_insights(correlation_data[0])
        
        # Generate learning recommendations
        insights['learning_insights'] = self._generate_learning_recommendations()
        
        # Add agent learning profiles
        insights['agent_profiles'] = self._get_agent_learning_summary()
        
        return insights

    def _extract_behavioral_insights(self, behavioral_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract educational insights from behavioral aggregation data.
        
        Args:
            behavioral_data: Behavioral aggregation results
            
        Returns:
            Dictionary of behavioral insights
        """
        insights = {}
        
        summary = behavioral_data.get('summary', {})
        agent_details = behavioral_data.get('agent_details', {})
        
        # Analyze mode diversity
        mode_distribution = summary.get('mode_distribution', {})
        if mode_distribution:
            dominant_mode = max(mode_distribution.items(), key=lambda x: x[1])
            insights['dominant_behavior'] = {
                'mode': dominant_mode[0],
                'frequency': dominant_mode[1],
                'educational_note': f"Most agents are in {dominant_mode[0]} mode, indicating {self._get_mode_explanation(dominant_mode[0])}"
            }
        
        # Analyze agent diversity
        total_agents = summary.get('total_agents', 0)
        if total_agents > 0:
            diverse_agents = sum(1 for agent_data in agent_details.values() 
                               if agent_data.get('mode_diversity', 0) > 2)
            insights['behavioral_diversity'] = {
                'diverse_agents': diverse_agents,
                'diversity_ratio': diverse_agents / total_agents,
                'educational_note': f"{diverse_agents}/{total_agents} agents show diverse behavior patterns"
            }
        
        return insights

    def _extract_system_insights(self, correlation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract educational insights from correlation analysis data.
        
        Args:
            correlation_data: Correlation analysis results
            
        Returns:
            Dictionary of system-level insights
        """
        insights = {}
        
        # Analyze trade relationships
        trade_relationships = correlation_data.get('trade_relationships', {})
        if trade_relationships:
            active_pairs = trade_relationships.get('active_relationships', 0)
            top_pairs = trade_relationships.get('top_trading_pairs', [])
            
            insights['economic_dynamics'] = {
                'active_trading_pairs': active_pairs,
                'cooperation_level': 'high' if active_pairs > 5 else 'moderate' if active_pairs > 2 else 'low',
                'educational_note': f"Economic system shows {active_pairs} active trading relationships"
            }
        
        # Analyze resource competition
        resource_competition = correlation_data.get('resource_competition', {})
        if resource_competition:
            hotspots = resource_competition.get('total_hotspots', 0)
            insights['resource_dynamics'] = {
                'competition_hotspots': hotspots,
                'competition_level': 'high' if hotspots > 3 else 'moderate' if hotspots > 1 else 'low',
                'educational_note': f"Resource competition detected at {hotspots} locations"
            }
        
        return insights

    def _generate_learning_recommendations(self) -> List[str]:
        """Generate educational recommendations based on current patterns.
        
        Returns:
            List of learning-focused recommendations
        """
        recommendations = []
        
        # Analyze system dynamics for recommendations
        if self._system_dynamics['cooperation_events'] > self._system_dynamics['competition_events']:
            recommendations.append(
                "Observe how agents benefit from cooperative trading relationships"
            )
        
        if self._system_dynamics['successful_adaptations'] > 10:
            recommendations.append(
                "Notice how agents adapt their behavior when facing challenges"
            )
        
        # Analyze agent diversity
        mode_diversity = sum(len(profile['modes_explored']) for profile in self._agent_learning_profiles.values())
        if mode_diversity > len(self._agent_learning_profiles) * 2:
            recommendations.append(
                "Examine how different agents explore various behavioral strategies"
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
        return {
            'total_insights_generated': self._total_insights_generated,
            'last_analysis_step': self._last_analysis_step,
            'system_dynamics': self._system_dynamics.copy(),
            'key_learning_points': self._extract_key_learning_points(),
            'agent_learning_profiles': dict(self._agent_learning_profiles),
        }

    def _extract_key_learning_points(self) -> List[str]:
        """Extract key educational learning points from the session.
        
        Returns:
            List of key learning insights
        """
        points = []
        
        # Economic system insights
        total_trades = self._system_dynamics['cooperation_events'] + self._system_dynamics['competition_events']
        if total_trades > 0:
            cooperation_rate = self._system_dynamics['cooperation_events'] / total_trades
            if cooperation_rate > 0.7:
                points.append("High cooperation rate demonstrates mutual benefit in trading")
            elif cooperation_rate < 0.3:
                points.append("Low cooperation suggests competitive resource dynamics")
        
        # Adaptation insights
        if self._system_dynamics['successful_adaptations'] > 0:
            points.append(f"Agents demonstrated {self._system_dynamics['successful_adaptations']} adaptive behaviors")
        
        # Behavioral diversity insights
        if len(self._agent_learning_profiles) > 0:
            avg_modes = sum(len(p['modes_explored']) for p in self._agent_learning_profiles.values()) / len(self._agent_learning_profiles)
            if avg_modes > 2:
                points.append("Agents show diverse behavioral strategies and exploration")
        
        return points

    def close(self) -> None:
        """Close the educational observer."""
        super().close()
        
        # Clear buffer manager
        if self._buffer_manager:
            self._buffer_manager.clear_all_buffers()

    def get_observer_stats(self) -> Dict[str, Any]:
        """Get educational observer statistics.
        
        Returns:
            Dictionary containing educational observer metrics
        """
        base_stats = super().get_observer_stats()
        
        educational_stats = {
            'total_insights_generated': self._total_insights_generated,
            'agents_tracked': len(self._agent_learning_profiles),
            'last_analysis_step': self._last_analysis_step,
            'system_dynamics': self._system_dynamics.copy(),
        }
        
        # Add buffer stats
        if self._buffer_manager:
            educational_stats['buffer_stats'] = self._buffer_manager.get_manager_stats()
        
        return {**base_stats, **educational_stats}

    def __repr__(self) -> str:
        """String representation of the educational observer."""
        return (f"EducationalObserver(insights={self._total_insights_generated}, "
                f"agents={len(self._agent_learning_profiles)}, closed={self._closed})")