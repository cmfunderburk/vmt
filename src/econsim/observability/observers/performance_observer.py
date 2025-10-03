"""Performance monitoring observer using raw data architecture for optimization and analysis.

This module implements the PerformanceObserver class that tracks
simulation performance metrics, identifies bottlenecks, and provides
optimization insights using the new raw data recording architecture
for zero-overhead performance monitoring.

Features:
- Zero-overhead raw data recording during simulation
- Deferred performance analysis using DataTranslator
- Step execution timing analysis
- Memory usage tracking
- Bottleneck identification
- Performance optimization recommendations
- Raw data storage with human-readable translation on demand

Architecture:
- Inherits from both BaseObserver (for configuration) and RawDataObserver (for storage)
- Uses DataTranslator for converting raw data to analysis-ready format
- No processing overhead during simulation execution
- Performance analysis performed only when needed (GUI display, file output)
"""

from __future__ import annotations

import time
from collections import deque

# Optional psutil import for memory monitoring
try:
    import psutil
except ImportError:
    psutil = None
from typing import Dict, List, Any, Optional, Deque, Union, TYPE_CHECKING

# Type aliases for better type checking
StepMetrics = Dict[str, Union[int, float]]
EventTiming = Dict[str, Union[str, float, int]]
MemorySample = Dict[str, Union[float, int, str]]
PerformanceData = Dict[str, Any]
StepRecord = Dict[str, Union[int, float]]  # For slowest/fastest step records

from .base_observer import BaseObserver
from ..raw_data.raw_data_observer import RawDataObserver
from ..raw_data.data_translator import DataTranslator
from ..raw_data.raw_data_writer import RawDataWriter

if TYPE_CHECKING:
    from ..config import ObservabilityConfig
    from ..events import SimulationEvent


class PerformanceObserver(BaseObserver, RawDataObserver):
    """Performance monitoring observer using raw data architecture for optimization insights.
    
    Tracks simulation performance metrics including timing, memory usage,
    and execution patterns to identify optimization opportunities and
    ensure efficient simulation execution using zero-overhead raw data recording.
    
    Architecture:
    - Inherits from both BaseObserver (for configuration) and RawDataObserver (for storage)
    - Uses DataTranslator for converting raw data to analysis-ready format
    - Zero-overhead recording during simulation, analysis deferred to when needed
    - Raw data storage with human-readable translation on demand
    """

    def __init__(self, config: ObservabilityConfig, 
                 history_size: int = 1000, 
                 enable_profiling: bool = True,
                 output_dir: str = None):
        """Initialize the performance observer with raw data architecture.
        
        Args:
            config: Observability configuration
            history_size: Number of performance samples to keep in memory (legacy, kept for compatibility)
            enable_profiling: Whether to enable detailed profiling (legacy, kept for compatibility)
            output_dir: Optional output directory for performance analysis files
        """
        # Initialize both parent classes
        BaseObserver.__init__(self, config)
        RawDataObserver.__init__(self)
        
        self._history_size = history_size  # Legacy compatibility
        self._enable_profiling = enable_profiling  # Legacy compatibility
        self.output_dir = output_dir
        
        # Performance metrics storage (legacy compatibility - will be replaced by raw data analysis)
        self._step_timings: Deque[Dict[str, Any]] = deque(maxlen=history_size)
        self._event_timings: Deque[Dict[str, Any]] = deque(maxlen=history_size)
        self._memory_samples: Deque[Dict[str, Any]] = deque(maxlen=history_size)
        
        # Current step tracking
        self._current_step = 0
        self._step_start_time = 0.0
        self._events_this_step = 0
        self._step_event_start_time = 0.0
        
        # Cumulative statistics
        self._total_events_processed = 0
        self._total_processing_time = 0.0
        self._peak_memory_usage = 0.0
        self._slowest_step: StepRecord = {'step': 0, 'duration': 0.0}
        self._fastest_step: StepRecord = {'step': 0, 'duration': float('inf')}
        
        # Performance thresholds for warnings
        self._slow_step_threshold = 0.1  # 100ms per step
        self._high_memory_threshold = 1024 * 1024 * 1024  # 1GB
        
        # Process handle for memory monitoring
        self._process = psutil.Process() if psutil else None
        
        # Initialize data translator for analysis
        self._data_translator = DataTranslator()
        
        # Initialize raw data writer for disk persistence
        self._raw_data_writer = RawDataWriter(
            compress=True,
            compression_level=6,
            max_file_size_mb=100,
            enable_rotation=True,
            atomic_writes=True
        )

    def _initialize_event_filtering(self) -> None:
        """Initialize event filtering for performance monitoring.
        
        PerformanceObserver accepts all events to monitor comprehensive
        performance across all simulation activities.
        """
        # Monitor all events for comprehensive performance analysis
        self._enabled_event_types = {
            'agent_mode_change',
            'trade_execution', 
            'resource_collection',
            'agent_movement',
            'debug_log',
            'performance_monitor',
            'agent_decision',
            'resource_event',
            'economic_decision',
            'gui_display'
        }

    def notify(self, event: SimulationEvent) -> None:
        """Handle a simulation event by recording raw data.
        
        This method now uses the raw data recording architecture for zero-overhead
        performance. Events are stored as raw dictionaries with no processing.
        Performance analysis is deferred to when data is actually needed.
        
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
        elif event.event_type == 'gui_display':
            self.record_gui_display(
                step=step,
                display_type=getattr(event, 'display_type', ''),
                element_id=getattr(event, 'element_id', ''),
                data=getattr(event, 'data', None)
            )
        else:
            # For unknown event types, record as generic debug log
            self.record_debug_log(
                step=step,
                category='UNKNOWN_EVENT',
                message=f"Unknown event type: {event.event_type}",
                agent_id=-1
            )

    def _start_new_step(self, step: int) -> None:
        """Start tracking metrics for a new simulation step.
        
        Args:
            step: The new simulation step number
        """
        self._current_step = step
        self._step_start_time = time.perf_counter()
        self._events_this_step = 0
        
        # Sample memory usage at step start
        self._sample_memory_usage(step, 'step_start')

    def _finalize_step_metrics(self) -> None:
        """Finalize and record metrics for the completed step."""
        if self._step_start_time == 0:
            return  # No step in progress
        
        # Calculate step timing
        step_duration = time.perf_counter() - self._step_start_time
        self._total_processing_time += step_duration
        
        # Record step metrics
        step_metrics: StepMetrics = {
            'step': self._current_step,
            'duration': step_duration,
            'events_processed': self._events_this_step,
            'events_per_second': self._events_this_step / step_duration if step_duration > 0 else 0,
            'timestamp': time.time(),
        }
        
        self._step_timings.append(step_metrics)
        
        # Update performance extremes
        if step_duration > self._slowest_step['duration']:
            self._slowest_step = {'step': self._current_step, 'duration': step_duration}
        if step_duration < self._fastest_step['duration']:
            self._fastest_step = {'step': self._current_step, 'duration': step_duration}
        
        # Check for performance warnings
        if step_duration > self._slow_step_threshold:
            self._record_performance_warning('slow_step', step_metrics)
        
        # Sample memory usage at step end
        self._sample_memory_usage(self._current_step, 'step_end')

    def _record_event_timing(self, event: SimulationEvent, processing_time: float) -> None:
        """Record timing information for an individual event.
        
        Args:
            event: The processed event
            processing_time: Time taken to process the event
        """
        event_timing: EventTiming = {
            'step': event.step,
            'event_type': event.event_type,
            'processing_time': processing_time,
            'timestamp': time.time(),
        }
        
        self._event_timings.append(event_timing)

    def _sample_memory_usage(self, step: int, phase: str) -> None:
        """Sample current memory usage.
        
        Args:
            step: Current simulation step
            phase: Phase identifier ('step_start', 'step_end', etc.)
        """
        if not self._process:
            return
        
        try:
            memory_info = self._process.memory_info()
            memory_usage = memory_info.rss  # Resident Set Size
            
            memory_sample: MemorySample = {
                'step': step,
                'phase': phase,
                'memory_rss': memory_usage,
                'memory_vms': memory_info.vms,  # Virtual Memory Size
                'timestamp': time.time(),
            }
            
            self._memory_samples.append(memory_sample)
            
            # Update peak memory usage
            if memory_usage > self._peak_memory_usage:
                self._peak_memory_usage = memory_usage
            
            # Check for high memory usage
            if memory_usage > self._high_memory_threshold:
                self._record_performance_warning('high_memory', memory_sample)
                
        except Exception:
            # Memory sampling failed, continue without it
            pass

    def _record_performance_warning(self, warning_type: str, data: Dict[str, Any]) -> None:
        """Record a performance warning.
        
        Args:
            warning_type: Type of performance warning
            data: Associated performance data
        """
        # In a full implementation, this would log warnings
        # For now, we just track that warnings occurred
        pass

    def flush_step(self, step: int) -> None:
        """Handle end-of-step boundary with zero overhead.
        
        In the raw data architecture, no processing is done at step boundaries.
        All data is stored in memory and performance analysis is performed only when needed.
        
        Args:
            step: The simulation step that just completed
        """
        # Zero overhead - no processing during simulation
        # Raw data is stored in memory and analysis is deferred
        self._current_step = step

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary from raw data.
        
        Returns:
            Dictionary containing performance analysis and metrics
        """
        # Get all raw events
        all_events = self.get_all_events()
        
        if not all_events:
            return {'status': 'no_data', 'message': 'No performance data available'}
        
        # Generate performance analysis from raw data
        performance_analysis = self._generate_performance_analysis_from_raw_data()
        
        return performance_analysis

    def _generate_performance_analysis_from_raw_data(self) -> Dict[str, Any]:
        """Generate comprehensive performance analysis from raw data using DataTranslator.
        
        Returns:
            Dictionary containing comprehensive performance analysis
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
                elif event['type'] == 'performance_monitor':
                    translated_events.append(self._data_translator.translate_performance_monitor_event(event))
                elif event['type'] == 'economic_decision':
                    translated_events.append(self._data_translator.translate_economic_decision_event(event))
                else:
                    # Keep raw event for unknown types
                    translated_events.append(event)
            except Exception as e:
                # Keep raw event if translation fails
                translated_events.append(event)
        
        # Generate comprehensive performance analysis
        analysis = {
            "total_events": len(all_events),
            "event_types": self.get_event_type_counts(),
            "step_range": self.get_statistics()['step_range'],
            "translated_events": translated_events,
            "performance_metrics": self._calculate_performance_metrics_from_raw_data(),
            "event_distribution_analysis": self._analyze_event_distribution_from_raw_data(),
            "step_performance_analysis": self._analyze_step_performance_from_raw_data(),
            "memory_usage_analysis": self._analyze_memory_usage_from_raw_data(),
            "performance_assessment": self._assess_performance_from_raw_data(),
        }
        
        return analysis
    
    def _calculate_performance_metrics_from_raw_data(self) -> Dict[str, Any]:
        """Calculate performance metrics from raw data."""
        all_events = self.get_all_events()
        
        if not all_events:
            return {}
        
        # Calculate basic metrics
        total_events = len(all_events)
        event_types = self.get_event_type_counts()
        
        # Calculate step distribution
        step_counts = self.get_step_event_counts()
        total_steps = len(step_counts)
        
        # Calculate events per step
        events_per_step = total_events / total_steps if total_steps > 0 else 0
        
        # Calculate performance monitor events
        performance_events = self.get_events_by_type('performance_monitor')
        performance_metrics = {}
        
        for event in performance_events:
            metric_name = event.get('metric_name', 'unknown')
            metric_value = event.get('metric_value', 0.0)
            threshold_exceeded = event.get('threshold_exceeded', False)
            
            if metric_name not in performance_metrics:
                performance_metrics[metric_name] = {
                    'values': [],
                    'threshold_exceeded_count': 0,
                    'avg_value': 0.0,
                    'max_value': 0.0,
                    'min_value': float('inf')
                }
            
            performance_metrics[metric_name]['values'].append(metric_value)
            if threshold_exceeded:
                performance_metrics[metric_name]['threshold_exceeded_count'] += 1
            
            # Update min/max
            if metric_value > performance_metrics[metric_name]['max_value']:
                performance_metrics[metric_name]['max_value'] = metric_value
            if metric_value < performance_metrics[metric_name]['min_value']:
                performance_metrics[metric_name]['min_value'] = metric_value
        
        # Calculate averages
        for metric_name, data in performance_metrics.items():
            if data['values']:
                data['avg_value'] = sum(data['values']) / len(data['values'])
                if data['min_value'] == float('inf'):
                    data['min_value'] = 0.0
        
        return {
            "total_events": total_events,
            "total_steps": total_steps,
            "events_per_step": events_per_step,
            "event_type_distribution": event_types,
            "step_distribution": step_counts,
            "performance_metrics": performance_metrics,
        }
    
    def _analyze_event_distribution_from_raw_data(self) -> Dict[str, Any]:
        """Analyze event distribution patterns from raw data."""
        all_events = self.get_all_events()
        
        if not all_events:
            return {}
        
        # Analyze event distribution by type
        event_types = self.get_event_type_counts()
        total_events = len(all_events)
        
        # Calculate percentages
        event_percentages = {}
        for event_type, count in event_types.items():
            event_percentages[event_type] = (count / total_events) * 100
        
        # Find most common event types
        most_common_events = sorted(event_types.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Analyze event distribution by step
        step_counts = self.get_step_event_counts()
        if step_counts:
            avg_events_per_step = sum(step_counts.values()) / len(step_counts)
            max_events_in_step = max(step_counts.values())
            min_events_in_step = min(step_counts.values())
        else:
            avg_events_per_step = 0
            max_events_in_step = 0
            min_events_in_step = 0
        
        return {
            "total_events": total_events,
            "event_type_counts": event_types,
            "event_type_percentages": event_percentages,
            "most_common_events": most_common_events,
            "step_distribution": {
                "avg_events_per_step": avg_events_per_step,
                "max_events_in_step": max_events_in_step,
                "min_events_in_step": min_events_in_step,
                "total_steps_with_events": len(step_counts)
            }
        }
    
    def _analyze_step_performance_from_raw_data(self) -> Dict[str, Any]:
        """Analyze step performance patterns from raw data."""
        step_counts = self.get_step_event_counts()
        
        if not step_counts:
            return {}
        
        # Analyze step performance
        steps = list(step_counts.keys())
        event_counts = list(step_counts.values())
        
        # Calculate performance statistics
        avg_events_per_step = sum(event_counts) / len(event_counts)
        max_events_per_step = max(event_counts)
        min_events_per_step = min(event_counts)
        
        # Find steps with highest and lowest event counts
        max_step = max(step_counts.items(), key=lambda x: x[1])
        min_step = min(step_counts.items(), key=lambda x: x[1])
        
        # Analyze performance trends
        if len(steps) > 1:
            # Simple trend analysis
            first_half = steps[:len(steps)//2]
            second_half = steps[len(steps)//2:]
            
            first_half_avg = sum(step_counts[step] for step in first_half) / len(first_half)
            second_half_avg = sum(step_counts[step] for step in second_half) / len(second_half)
            
            if second_half_avg > first_half_avg * 1.1:
                trend = "increasing"
            elif second_half_avg < first_half_avg * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "total_steps": len(steps),
            "step_range": (min(steps), max(steps)),
            "avg_events_per_step": avg_events_per_step,
            "max_events_per_step": max_events_per_step,
            "min_events_per_step": min_events_per_step,
            "max_event_step": max_step,
            "min_event_step": min_step,
            "performance_trend": trend,
            "step_distribution": step_counts
        }
    
    def _analyze_memory_usage_from_raw_data(self) -> Dict[str, Any]:
        """Analyze memory usage patterns from raw data."""
        # For now, return basic memory analysis
        # In a full implementation, this would analyze memory-related events
        return {
            "memory_analysis": "Memory usage analysis not yet implemented in raw data architecture",
            "note": "Memory monitoring would be implemented through performance_monitor events"
        }
    
    def _assess_performance_from_raw_data(self) -> Dict[str, Any]:
        """Assess overall performance from raw data and provide recommendations."""
        all_events = self.get_all_events()
        
        if not all_events:
            return {
                'overall_rating': 'no_data',
                'bottlenecks': [],
                'recommendations': ['No performance data available for analysis']
            }
        
        assessment = {
            'overall_rating': 'good',
            'bottlenecks': [],
            'recommendations': [],
        }
        
        # Analyze event distribution
        event_types = self.get_event_type_counts()
        total_events = len(all_events)
        
        # Check for performance monitor events with threshold exceeded
        performance_events = self.get_events_by_type('performance_monitor')
        threshold_exceeded_count = 0
        
        for event in performance_events:
            if event.get('threshold_exceeded', False):
                threshold_exceeded_count += 1
        
        if threshold_exceeded_count > 0:
            assessment['overall_rating'] = 'poor'
            assessment['bottlenecks'].append('performance_thresholds_exceeded')
            assessment['recommendations'].append(f'{threshold_exceeded_count} performance thresholds exceeded - investigate bottlenecks')
        
        # Check for high event density
        step_counts = self.get_step_event_counts()
        if step_counts:
            avg_events_per_step = sum(step_counts.values()) / len(step_counts)
            if avg_events_per_step > 100:  # High event density threshold
                assessment['bottlenecks'].append('high_event_density')
                assessment['recommendations'].append('High event density detected - consider optimizing event generation')
        
        # Check for unbalanced event distribution
        if event_types:
            most_common_count = max(event_types.values())
            if most_common_count > total_events * 0.8:  # 80% of events are one type
                assessment['bottlenecks'].append('unbalanced_event_distribution')
                assessment['recommendations'].append('Unbalanced event distribution - consider diversifying simulation activities')
        
        return assessment

    def _assess_performance(self) -> Dict[str, Any]:
        """Assess overall performance and provide recommendations.
        
        Returns:
            Performance assessment and recommendations
        """
        assessment = {
            'overall_rating': 'good',
            'bottlenecks': [],
            'recommendations': [],
        }
        
        # Check step timing performance
        if self._step_timings:
            avg_duration = sum(s['duration'] for s in self._step_timings) / len(self._step_timings)
            if avg_duration > self._slow_step_threshold:
                assessment['overall_rating'] = 'poor'
                assessment['bottlenecks'].append('slow_step_processing')
                assessment['recommendations'].append('Consider optimizing step handlers or reducing simulation complexity')
        
        # Check memory usage
        if self._peak_memory_usage > self._high_memory_threshold:
            assessment['bottlenecks'].append('high_memory_usage')
            assessment['recommendations'].append('Monitor memory usage and consider optimizing data structures')
        
        # Check event processing efficiency
        if self._event_timings:
            avg_event_time = sum(e['processing_time'] for e in self._event_timings) / len(self._event_timings)
            if avg_event_time > 0.001:  # 1ms per event threshold
                assessment['bottlenecks'].append('slow_event_processing')
                assessment['recommendations'].append('Optimize observer event processing for better performance')
        
        return assessment

    def get_recent_performance(self, steps: int = 10) -> Dict[str, Any]:
        """Get performance data for recent steps.
        
        Args:
            steps: Number of recent steps to analyze
            
        Returns:
            Recent performance metrics
        """
        if not self._step_timings:
            return {}
        
        recent_steps = list(self._step_timings)[-steps:] if len(self._step_timings) >= steps else list(self._step_timings)
        
        if not recent_steps:
            return {}
        
        recent_durations = [step['duration'] for step in recent_steps]
        recent_events = [step['events_processed'] for step in recent_steps]
        
        return {
            'steps_analyzed': len(recent_steps),
            'avg_duration': sum(recent_durations) / len(recent_durations),
            'total_events': sum(recent_events),
            'avg_events_per_step': sum(recent_events) / len(recent_events),
            'performance_trend': self._calculate_performance_trend(recent_steps),
        }

    def _calculate_performance_trend(self, recent_steps: List[Dict[str, Any]]) -> str:
        """Calculate performance trend from recent steps.
        
        Args:
            recent_steps: List of recent step metrics
            
        Returns:
            Performance trend description
        """
        if len(recent_steps) < 3:
            return 'insufficient_data'
        
        # Simple trend analysis based on duration
        first_half = recent_steps[:len(recent_steps)//2]
        second_half = recent_steps[len(recent_steps)//2:]
        
        first_avg = sum(s['duration'] for s in first_half) / len(first_half)
        second_avg = sum(s['duration'] for s in second_half) / len(second_half)
        
        if second_avg < first_avg * 0.9:
            return 'improving'
        elif second_avg > first_avg * 1.1:
            return 'degrading'
        else:
            return 'stable'

    def close(self) -> None:
        """Close the performance observer and write final results."""
        # Write final performance analysis if output directory is specified
        if self.output_dir and len(self._events) > 0:
            try:
                import json
                from pathlib import Path
                
                output_path = Path(self.output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                
                # Generate final performance analysis
                performance_analysis = self._generate_performance_analysis_from_raw_data()
                
                # Write performance analysis file
                analysis_file = output_path / f"performance_analysis_final.json"
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    json.dump(performance_analysis, f, indent=2)
                
                # Write raw data using RawDataWriter
                raw_data_file = output_path / f"performance_raw_data_final.jsonl.gz"
                write_result = self._raw_data_writer.flush_to_disk(
                    events=self.get_all_events(),
                    filepath=raw_data_file,
                    append=False
                )
                
                print(f"PerformanceObserver closed. Wrote {write_result['events_written']} events "
                      f"({write_result['bytes_written']} bytes) to {raw_data_file}")
                
            except Exception as e:
                print(f"Warning: Failed to write final performance data: {e}")
        
        # Call parent close method
        super().close()
        
        # Clear raw data from memory after writing
        self.clear_events()

    def get_observer_stats(self) -> Dict[str, Any]:
        """Get performance observer statistics.
        
        Returns:
            Dictionary containing performance observer metrics
        """
        base_stats = super().get_observer_stats()
        raw_data_stats = self.get_statistics()
        
        performance_stats = {
            'observer_type': 'performance',
            'total_events_processed': self._total_events_processed,
            'total_processing_time': self._total_processing_time,
            'step_samples': len(self._step_timings),
            'event_samples': len(self._event_timings),
            'memory_samples': len(self._memory_samples),
            'peak_memory_mb': self._peak_memory_usage / (1024 * 1024),
            'profiling_enabled': self._enable_profiling,
            'output_dir': self.output_dir,
            'raw_data_events': raw_data_stats['total_events'],
            'raw_data_types': list(raw_data_stats['event_types']),
            'step_range': raw_data_stats['step_range'],
        }
        
        return {**base_stats, **performance_stats}

    def __repr__(self) -> str:
        """String representation of the performance observer."""
        raw_data_stats = self.get_statistics()
        return (f"PerformanceObserver(events={raw_data_stats['total_events']}, "
                f"types={len(raw_data_stats['event_types'])}, "
                f"steps={raw_data_stats['step_range']}, "
                f"profiling={self._enable_profiling}, closed={self._closed})")