"""Semantic analyzer for Phase 4E context-aware compression.

This module provides semantic analysis capabilities for understanding event context
and applying intelligent compression based on behavioral patterns and semantic similarity.
"""

from __future__ import annotations

import json
from collections import defaultdict, Counter
from typing import Dict, Any, List, Union, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from .optimized_serializer import OptimizedEventSerializer, LogFormatVersion


@dataclass
class SemanticPattern:
    """Represents a semantic pattern in event data."""
    pattern_type: str
    frequency: int
    compression_ratio: float
    context_indicators: List[str]
    semantic_group: str


@dataclass
class CompressionContext:
    """Represents the compression context for semantic analysis."""
    step_number: int
    timestamp: float
    event_types: List[str]
    agent_count: int
    pattern_frequency: Dict[str, int]
    semantic_similarity: float


class SemanticAnalyzer:
    """Analyzes event data for semantic patterns and compression opportunities.
    
    Provides context-aware compression by understanding behavioral patterns,
    temporal relationships, and semantic similarity between events.
    """
    
    def __init__(self):
        """Initialize the semantic analyzer."""
        self.pattern_cache: Dict[str, SemanticPattern] = {}
        self.context_history: List[CompressionContext] = []
        self.semantic_groups: Dict[str, List[str]] = defaultdict(list)
        
        # Initialize semantic groups based on behavioral patterns
        self._initialize_semantic_groups()
    
    def _initialize_semantic_groups(self) -> None:
        """Initialize semantic groups for context-aware compression."""
        # Collection semantic groups
        self.semantic_groups['collection'] = [
            'resource_collection',
            'resource_claimed_fallback',
            'collected_resource'
        ]
        
        # Mode transition semantic groups
        self.semantic_groups['mode_transition'] = [
            'agent_mode_change',
            'forage',
            'return_home',
            'idle'
        ]
        
        # Trading semantic groups
        self.semantic_groups['trading'] = [
            'trade_execution',
            'trade_completed',
            'trade_failed'
        ]
        
        # Movement semantic groups
        self.semantic_groups['movement'] = [
            'agent_movement',
            'target_reached',
            'resource_selection'
        ]
    
    def analyze_step_semantics(self, step_data: Dict[str, Any]) -> CompressionContext:
        """Analyze semantic patterns in a single step.
        
        Args:
            step_data: Step data dictionary
            
        Returns:
            CompressionContext with semantic analysis results
        """
        # Extract basic context
        step_number = step_data.get('s', 0)
        timestamp = step_data.get('t0', 0.0)
        
        # Analyze event types
        event_types = []
        agent_count = 0
        
        # Analyze collection events
        if 'c' in step_data:
            event_types.append('collection')
            agent_count += self._count_agents_in_events(step_data['c'])
        
        # Analyze mode events
        if 'm' in step_data:
            event_types.append('mode_change')
            agent_count += self._count_agents_in_events(step_data['m'])
        
        # Analyze other events
        if 'o' in step_data:
            event_types.append('other')
            agent_count += self._count_agents_in_events(step_data['o'])
        
        # Analyze pattern frequency
        pattern_frequency = self._analyze_pattern_frequency(step_data)
        
        # Calculate semantic similarity
        semantic_similarity = self._calculate_semantic_similarity(step_data)
        
        # Create compression context
        context = CompressionContext(
            step_number=step_number,
            timestamp=timestamp,
            event_types=event_types,
            agent_count=agent_count,
            pattern_frequency=pattern_frequency,
            semantic_similarity=semantic_similarity
        )
        
        # Cache context for future analysis
        self.context_history.append(context)
        
        return context
    
    def _count_agents_in_events(self, events: Union[str, List]) -> int:
        """Count total number of agents in events.
        
        Args:
            events: Events data (string or list)
            
        Returns:
            Total agent count
        """
        if isinstance(events, str):
            # Parse string format like "t0,1-5,7,9-12"
            return self._count_agents_in_string(events)
        
        if not isinstance(events, list):
            return 0
        
        total_count = 0
        for event in events:
            if isinstance(event, str):
                total_count += self._count_agents_in_string(event)
            elif isinstance(event, list):
                total_count += self._count_agents_in_list(event)
        
        return total_count
    
    def _count_agents_in_string(self, event_string: str) -> int:
        """Count agents in string format event.
        
        Args:
            event_string: Event string like "t0,1-5,7,9-12"
            
        Returns:
            Agent count
        """
        # Skip timestamp part (first element)
        parts = event_string.split(',')
        if len(parts) <= 1:
            return 0
        
        # Count agents in remaining parts
        agent_count = 0
        for part in parts[1:]:
            part = part.strip()
            if '-' in part:
                # Range: "1-5"
                start, end = map(int, part.split('-'))
                agent_count += (end - start + 1)
            else:
                # Single: "7"
                agent_count += 1
        
        return agent_count
    
    def _count_agents_in_list(self, event_list: List) -> int:
        """Count agents in list format event.
        
        Args:
            event_list: Event list
            
        Returns:
            Agent count
        """
        if not event_list:
            return 0
        
        # Look for agent data in the list
        for item in event_list:
            if isinstance(item, (list, str)):
                if isinstance(item, str) and ('-' in item or ',' in item):
                    return self._count_agents_in_string(item)
                elif isinstance(item, list):
                    return self._count_agents_in_list(item)
            elif isinstance(item, int):
                return 1  # Single agent
        
        return 0
    
    def _analyze_pattern_frequency(self, step_data: Dict[str, Any]) -> Dict[str, int]:
        """Analyze pattern frequency in step data.
        
        Args:
            step_data: Step data dictionary
            
        Returns:
            Dictionary of pattern frequencies
        """
        pattern_freq = Counter()
        
        # Analyze mode events for patterns
        if 'm' in step_data:
            mode_events = step_data['m']
            if isinstance(mode_events, str):
                # String format: "1,t0,1-5"
                parts = mode_events.split(',')
                if parts:
                    pattern_freq[parts[0]] += 1
            elif isinstance(mode_events, list):
                for event in mode_events:
                    if isinstance(event, str):
                        parts = event.split(',')
                        if parts:
                            pattern_freq[parts[0]] += 1
                    elif isinstance(event, list) and event:
                        pattern_freq[str(event[0])] += 1
        
        return dict(pattern_freq)
    
    def _calculate_semantic_similarity(self, step_data: Dict[str, Any]) -> float:
        """Calculate semantic similarity score for the step.
        
        Args:
            step_data: Step data dictionary
            
        Returns:
            Semantic similarity score (0.0 to 1.0)
        """
        # Analyze event type diversity
        event_types = []
        if 'c' in step_data:
            event_types.append('collection')
        if 'm' in step_data:
            event_types.append('mode_change')
        if 'o' in step_data:
            event_types.append('other')
        
        # Calculate similarity based on event type patterns
        if len(event_types) == 1:
            # Single event type - high similarity
            return 0.9
        elif len(event_types) == 2:
            # Two event types - medium similarity
            return 0.6
        else:
            # Multiple event types - low similarity
            return 0.3
    
    def suggest_compression_strategy(self, context: CompressionContext) -> Dict[str, Any]:
        """Suggest optimal compression strategy based on semantic analysis.
        
        Args:
            context: Compression context from semantic analysis
            
        Returns:
            Dictionary with compression strategy recommendations
        """
        strategy = {
            'use_semantic_compression': True,
            'compression_level': 'standard',
            'group_by_similarity': True,
            'merge_agent_lists': False,
            'infer_context': True
        }
        
        # Adjust strategy based on context
        if context.semantic_similarity > 0.8:
            # High similarity - use aggressive compression
            strategy['compression_level'] = 'aggressive'
            strategy['merge_agent_lists'] = True
        elif context.semantic_similarity < 0.4:
            # Low similarity - use conservative compression
            strategy['compression_level'] = 'conservative'
            strategy['group_by_similarity'] = False
        
        # Adjust based on agent count
        if context.agent_count > 20:
            # Large agent count - prioritize list compression
            strategy['merge_agent_lists'] = True
        elif context.agent_count < 5:
            # Small agent count - prioritize readability
            strategy['compression_level'] = 'conservative'
        
        # Adjust based on pattern frequency
        if context.pattern_frequency:
            most_common_pattern = max(context.pattern_frequency.items(), key=lambda x: x[1])
            if most_common_pattern[1] > 5:
                # High pattern frequency - use pattern-based compression
                strategy['use_pattern_compression'] = True
                strategy['primary_pattern'] = most_common_pattern[0]
        
        return strategy
    
    def analyze_log_file_semantics(self, log_path: Path) -> Dict[str, Any]:
        """Analyze semantic patterns in an entire log file.
        
        Args:
            log_path: Path to log file
            
        Returns:
            Dictionary with semantic analysis results
        """
        analysis_results = {
            'total_steps': 0,
            'semantic_patterns': [],
            'compression_opportunities': [],
            'average_similarity': 0.0,
            'pattern_frequency': Counter(),
            'recommendations': []
        }
        
        try:
            with open(log_path, 'r', encoding='utf-8') as file:
                similarities = []
                
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        step_data = json.loads(line)
                        context = self.analyze_step_semantics(step_data)
                        
                        analysis_results['total_steps'] += 1
                        similarities.append(context.semantic_similarity)
                        
                        # Update pattern frequency
                        for pattern, freq in context.pattern_frequency.items():
                            analysis_results['pattern_frequency'][pattern] += freq
                        
                        # Identify compression opportunities
                        if context.semantic_similarity > 0.7:
                            analysis_results['compression_opportunities'].append({
                                'step': context.step_number,
                                'similarity': context.semantic_similarity,
                                'agent_count': context.agent_count,
                                'event_types': context.event_types
                            })
                    
                    except json.JSONDecodeError:
                        continue  # Skip invalid JSON lines
                
                # Calculate average similarity
                if similarities:
                    analysis_results['average_similarity'] = sum(similarities) / len(similarities)
                
                # Generate recommendations
                analysis_results['recommendations'] = self._generate_recommendations(analysis_results)
        
        except FileNotFoundError:
            analysis_results['error'] = f"Log file not found: {log_path}"
        
        return analysis_results
    
    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate compression recommendations based on analysis.
        
        Args:
            analysis_results: Analysis results dictionary
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Similarity-based recommendations
        avg_similarity = analysis_results['average_similarity']
        if avg_similarity > 0.8:
            recommendations.append("High semantic similarity detected - use aggressive semantic compression")
        elif avg_similarity < 0.4:
            recommendations.append("Low semantic similarity - use conservative compression with pattern grouping")
        
        # Pattern frequency recommendations
        pattern_freq = analysis_results['pattern_frequency']
        if pattern_freq:
            most_common = max(pattern_freq.items(), key=lambda x: x[1])
            if most_common[1] > 50:
                recommendations.append(f"High frequency pattern '{most_common[0]}' - prioritize pattern-based compression")
        
        # Compression opportunities
        opportunities = analysis_results['compression_opportunities']
        if len(opportunities) > analysis_results['total_steps'] * 0.7:
            recommendations.append("Many compression opportunities - enable semantic grouping and agent list merging")
        
        return recommendations
    
    def export_semantic_analysis(self, output_path: Path, analysis_results: Dict[str, Any]) -> None:
        """Export semantic analysis results to a file.
        
        Args:
            output_path: Path to output file
            analysis_results: Analysis results dictionary
        """
        # Convert Counter to regular dict for JSON serialization
        export_data = analysis_results.copy()
        export_data['pattern_frequency'] = dict(export_data['pattern_frequency'])
        
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(export_data, file, indent=2, ensure_ascii=False)


def create_semantic_analyzer() -> SemanticAnalyzer:
    """Factory function to create a semantic analyzer.
    
    Returns:
        Configured SemanticAnalyzer instance
    """
    return SemanticAnalyzer()
