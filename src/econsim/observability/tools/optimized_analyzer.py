"""Analysis tools for optimized log format.

This module provides comprehensive analysis capabilities for optimized log files,
including performance metrics, behavioral analysis, and format validation.

Features:
- Optimized log format parsing and analysis
- Performance metrics calculation
- Behavioral pattern analysis
- Event frequency and timing analysis
- Format validation and integrity checking
- Export capabilities for further analysis

Usage:
    from econsim.observability.tools.optimized_analyzer import OptimizedLogAnalyzer
    
    analyzer = OptimizedLogAnalyzer()
    results = analyzer.analyze_log_file("optimized_log.jsonl")
    analyzer.export_analysis(results, "analysis_report.json")
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass

from ..serializers import OptimizedEventSerializer


@dataclass
class EventMetrics:
    """Metrics for a specific event type."""
    event_type: str
    total_count: int
    unique_agents: set
    step_range: Tuple[int, int]
    time_range: Tuple[float, float]
    frequency_per_step: Dict[int, int]
    average_step_frequency: float


@dataclass
class AgentMetrics:
    """Metrics for a specific agent."""
    agent_id: int
    total_events: int
    mode_transitions: List[Dict[str, Any]]
    event_types: Counter
    step_range: Tuple[int, int]
    activity_patterns: Dict[str, Any]


@dataclass
class LogAnalysisResults:
    """Comprehensive analysis results for an optimized log file."""
    file_path: str
    analysis_timestamp: float
    total_events: int
    total_steps: int
    unique_agents: set
    time_range: Tuple[float, float]
    file_size_bytes: int
    compression_ratio: float
    event_metrics: Dict[str, EventMetrics]
    agent_metrics: Dict[int, AgentMetrics]
    step_analysis: Dict[int, Dict[str, Any]]
    performance_summary: Dict[str, Any]


class OptimizedLogAnalyzer:
    """Comprehensive analyzer for optimized log format files.
    
    Provides detailed analysis of optimized log files including performance
    metrics, behavioral patterns, and format validation.
    """
    
    def __init__(self):
        """Initialize the optimized log analyzer."""
        self.serializer = OptimizedEventSerializer()
    
    def analyze_log_file(self, log_path: Path, 
                        detailed_analysis: bool = True) -> LogAnalysisResults:
        """Perform comprehensive analysis of an optimized log file.
        
        Args:
            log_path: Path to the optimized log file
            detailed_analysis: Whether to perform detailed step-by-step analysis
            
        Returns:
            LogAnalysisResults with comprehensive analysis data
        """
        log_path = Path(log_path)
        
        if not log_path.exists():
            raise FileNotFoundError(f"Log file not found: {log_path}")
        
        # Initialize analysis data structures
        event_counts = defaultdict(int)
        agent_events = defaultdict(list)
        step_events = defaultdict(list)
        event_times = []
        agent_mode_transitions = defaultdict(list)
        step_timestamps = {}
        
        # Parse the optimized log file
        with open(log_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    event_data = json.loads(line)
                    self._process_event_data(
                        event_data, line_num, event_counts, agent_events,
                        step_events, event_times, agent_mode_transitions,
                        step_timestamps
                    )
                except json.JSONDecodeError as e:
                    print(f"Warning: Invalid JSON on line {line_num}: {e}")
                    continue
                except Exception as e:
                    print(f"Warning: Error processing line {line_num}: {e}")
                    continue
        
        # Calculate comprehensive metrics
        return self._calculate_analysis_results(
            log_path, event_counts, agent_events, step_events,
            event_times, agent_mode_transitions, step_timestamps,
            detailed_analysis
        )
    
    def _process_event_data(self, event_data: Dict[str, Any], line_num: int,
                           event_counts: Dict[str, int], agent_events: Dict[int, List],
                           step_events: Dict[int, List], event_times: List[float],
                           agent_mode_transitions: Dict[int, List],
                           step_timestamps: Dict[int, float]) -> None:
        """Process a single event data structure.
        
        Args:
            event_data: Event data dictionary
            line_num: Line number for error reporting
            event_counts: Counter for event types
            agent_events: List of events per agent
            step_events: List of events per step
            event_times: List of all event timestamps
            agent_mode_transitions: Mode transitions per agent
            step_timestamps: Timestamp for each step
        """
        # Handle step headers with batched events
        if 'events' in event_data:
            # This is a step header
            step = event_data.get('s', 0)
            step_timestamp = event_data.get('t0', 0)
            step_timestamps[step] = step_timestamp
            
            # Process each event in the batch
            for event in event_data['events']:
                self._process_single_event(
                    event, step, step_timestamp, event_counts, agent_events,
                    step_events, event_times, agent_mode_transitions
                )
        else:
            # Single event
            step = event_data.get('s', 0)
            step_timestamp = step_timestamps.get(step, 0)
            self._process_single_event(
                event_data, step, step_timestamp, event_counts, agent_events,
                step_events, event_times, agent_mode_transitions
            )
    
    def _process_single_event(self, event: Dict[str, Any], step: int,
                             step_timestamp: float, event_counts: Dict[str, int],
                             agent_events: Dict[int, List], step_events: Dict[int, List],
                             event_times: List[float],
                             agent_mode_transitions: Dict[int, List]) -> None:
        """Process a single event.
        
        Args:
            event: Single event dictionary
            step: Step number
            step_timestamp: Base timestamp for the step
            event_counts: Counter for event types
            agent_events: List of events per agent
            step_events: List of events per step
            event_times: List of all event timestamps
            agent_mode_transitions: Mode transitions per agent
        """
        # Calculate absolute timestamp
        relative_time = event.get('t', 0)
        absolute_time = step_timestamp + relative_time
        event_times.append(absolute_time)
        
        # Get event type
        event_type_code = event.get('e', '')
        event_type_map = {v: k for k, v in OptimizedEventSerializer.EVENT_TYPE_CODES.items()}
        event_type = event_type_map.get(event_type_code, event_type_code)
        
        # Count event type
        event_counts[event_type] += 1
        
        # Track events per step
        step_events[step].append(event)
        
        # Track agent-specific events
        if 'a' in event:
            agent_id = event['a']
            agent_events[agent_id].append({
                'step': step,
                'timestamp': absolute_time,
                'event_type': event_type,
                'event_data': event
            })
            
            # Track mode transitions
            if event_type_code == 'mode' and 'trans' in event:
                mode_transition = {
                    'step': step,
                    'timestamp': absolute_time,
                    'transition': event['trans'],
                    'reason': event.get('r', '')
                }
                agent_mode_transitions[agent_id].append(mode_transition)
    
    def _calculate_analysis_results(self, log_path: Path,
                                   event_counts: Dict[str, int],
                                   agent_events: Dict[int, List],
                                   step_events: Dict[int, List],
                                   event_times: List[float],
                                   agent_mode_transitions: Dict[int, List],
                                   step_timestamps: Dict[int, float],
                                   detailed_analysis: bool) -> LogAnalysisResults:
        """Calculate comprehensive analysis results.
        
        Args:
            log_path: Path to the log file
            event_counts: Counter for event types
            agent_events: List of events per agent
            step_events: List of events per step
            event_times: List of all event timestamps
            agent_mode_transitions: Mode transitions per agent
            step_timestamps: Timestamp for each step
            detailed_analysis: Whether to perform detailed analysis
            
        Returns:
            LogAnalysisResults with comprehensive analysis data
        """
        # Basic statistics
        total_events = sum(event_counts.values())
        total_steps = len(step_events)
        unique_agents = set(agent_events.keys())
        file_size = log_path.stat().st_size
        
        # Time range
        time_range = (min(event_times), max(event_times)) if event_times else (0, 0)
        
        # Calculate event metrics
        event_metrics = {}
        for event_type, count in event_counts.items():
            # Find events of this type to calculate metrics
            type_events = []
            for step, events in step_events.items():
                for event in events:
                    event_type_code = event.get('e', '')
                    event_type_map = {v: k for k, v in OptimizedEventSerializer.EVENT_TYPE_CODES.items()}
                    if event_type_map.get(event_type_code, event_type_code) == event_type:
                        type_events.append((step, event))
            
            if type_events:
                steps_with_events = [step for step, _ in type_events]
                step_range = (min(steps_with_events), max(steps_with_events))
                
                # Calculate frequency per step
                step_frequency = Counter(steps_with_events)
                average_frequency = count / len(step_frequency) if step_frequency else 0
                
                event_metrics[event_type] = EventMetrics(
                    event_type=event_type,
                    total_count=count,
                    unique_agents=set(),
                    step_range=step_range,
                    time_range=time_range,
                    frequency_per_step=dict(step_frequency),
                    average_step_frequency=average_frequency
                )
        
        # Calculate agent metrics
        agent_metrics = {}
        for agent_id, events in agent_events.items():
            if not events:
                continue
            
            event_types = Counter(event['event_type'] for event in events)
            steps = [event['step'] for event in events]
            step_range = (min(steps), max(steps))
            
            agent_metrics[agent_id] = AgentMetrics(
                agent_id=agent_id,
                total_events=len(events),
                mode_transitions=agent_mode_transitions.get(agent_id, []),
                event_types=event_types,
                step_range=step_range,
                activity_patterns={}
            )
        
        # Step analysis (if detailed analysis requested)
        step_analysis = {}
        if detailed_analysis:
            for step, events in step_events.items():
                step_analysis[step] = {
                    'event_count': len(events),
                    'timestamp': step_timestamps.get(step, 0),
                    'event_types': Counter(event.get('e', '') for event in events),
                    'agents': list(set(event.get('a', -1) for event in events if 'a' in event))
                }
        
        # Performance summary
        performance_summary = {
            'events_per_step': total_events / max(total_steps, 1),
            'events_per_second': total_events / max(time_range[1] - time_range[0], 1),
            'average_events_per_agent': total_events / max(len(unique_agents), 1),
            'file_size_bytes': file_size,
            'bytes_per_event': file_size / max(total_events, 1),
            'compression_ratio': 1.0,  # Would need original size to calculate
        }
        
        return LogAnalysisResults(
            file_path=str(log_path),
            analysis_timestamp=time.time(),
            total_events=total_events,
            total_steps=total_steps,
            unique_agents=unique_agents,
            time_range=time_range,
            file_size_bytes=file_size,
            compression_ratio=performance_summary['compression_ratio'],
            event_metrics=event_metrics,
            agent_metrics=agent_metrics,
            step_analysis=step_analysis,
            performance_summary=performance_summary
        )
    
    def export_analysis(self, results: LogAnalysisResults, 
                       output_path: Path, format: str = 'json') -> None:
        """Export analysis results to a file.
        
        Args:
            results: Analysis results to export
            output_path: Path for the output file
            format: Output format ('json', 'csv', 'txt')
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'json':
            self._export_json(results, output_path)
        elif format == 'txt':
            self._export_text(results, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_json(self, results: LogAnalysisResults, output_path: Path) -> None:
        """Export results as JSON.
        
        Args:
            results: Analysis results
            output_path: Output file path
        """
        # Convert dataclasses to dictionaries for JSON serialization
        export_data = {
            'file_path': results.file_path,
            'analysis_timestamp': results.analysis_timestamp,
            'total_events': results.total_events,
            'total_steps': results.total_steps,
            'unique_agents': list(results.unique_agents),
            'time_range': results.time_range,
            'file_size_bytes': results.file_size_bytes,
            'compression_ratio': results.compression_ratio,
            'event_metrics': {
                event_type: {
                    'event_type': metrics.event_type,
                    'total_count': metrics.total_count,
                    'unique_agents': list(metrics.unique_agents),
                    'step_range': metrics.step_range,
                    'time_range': metrics.time_range,
                    'frequency_per_step': metrics.frequency_per_step,
                    'average_step_frequency': metrics.average_step_frequency
                }
                for event_type, metrics in results.event_metrics.items()
            },
            'agent_metrics': {
                agent_id: {
                    'agent_id': metrics.agent_id,
                    'total_events': metrics.total_events,
                    'mode_transitions': metrics.mode_transitions,
                    'event_types': dict(metrics.event_types),
                    'step_range': metrics.step_range,
                    'activity_patterns': metrics.activity_patterns
                }
                for agent_id, metrics in results.agent_metrics.items()
            },
            'step_analysis': {
                str(step): {
                    'event_count': data['event_count'],
                    'timestamp': data['timestamp'],
                    'event_types': dict(data['event_types']),
                    'agents': data['agents']
                }
                for step, data in results.step_analysis.items()
            },
            'performance_summary': results.performance_summary
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
    
    def _export_text(self, results: LogAnalysisResults, output_path: Path) -> None:
        """Export results as human-readable text.
        
        Args:
            results: Analysis results
            output_path: Output file path
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== Optimized Log Analysis Report ===\n\n")
            
            f.write(f"File: {results.file_path}\n")
            f.write(f"Analysis timestamp: {time.ctime(results.analysis_timestamp)}\n")
            f.write(f"Total events: {results.total_events:,}\n")
            f.write(f"Total steps: {results.total_steps:,}\n")
            f.write(f"Unique agents: {len(results.unique_agents)}\n")
            f.write(f"Time range: {results.time_range[0]:.3f} - {results.time_range[1]:.3f}\n")
            f.write(f"File size: {results.file_size_bytes:,} bytes\n\n")
            
            f.write("=== Event Metrics ===\n")
            for event_type, metrics in results.event_metrics.items():
                f.write(f"\n{event_type}:\n")
                f.write(f"  Total count: {metrics.total_count:,}\n")
                f.write(f"  Step range: {metrics.step_range[0]} - {metrics.step_range[1]}\n")
                f.write(f"  Average per step: {metrics.average_step_frequency:.2f}\n")
            
            f.write("\n=== Agent Metrics ===\n")
            for agent_id, metrics in results.agent_metrics.items():
                f.write(f"\nAgent {agent_id}:\n")
                f.write(f"  Total events: {metrics.total_events:,}\n")
                f.write(f"  Step range: {metrics.step_range[0]} - {metrics.step_range[1]}\n")
                f.write(f"  Mode transitions: {len(metrics.mode_transitions)}\n")
                f.write(f"  Event types: {dict(metrics.event_types)}\n")
            
            f.write("\n=== Performance Summary ===\n")
            for key, value in results.performance_summary.items():
                if isinstance(value, float):
                    f.write(f"{key}: {value:.3f}\n")
                else:
                    f.write(f"{key}: {value:,}\n")


def analyze_optimized_log(log_path: Path, output_path: Optional[Path] = None,
                         export_format: str = 'json') -> LogAnalysisResults:
    """Convenience function to analyze an optimized log file.
    
    Args:
        log_path: Path to the optimized log file
        output_path: Optional path to export analysis results
        export_format: Export format ('json', 'txt')
        
    Returns:
        LogAnalysisResults with comprehensive analysis data
    """
    analyzer = OptimizedLogAnalyzer()
    results = analyzer.analyze_log_file(log_path)
    
    if output_path:
        analyzer.export_analysis(results, output_path, export_format)
    
    return results
