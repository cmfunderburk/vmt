"""Performance monitoring observer for optimization and analysis.

This module implements the PerformanceObserver class that tracks
simulation performance metrics, identifies bottlenecks, and provides
optimization insights for maintaining efficient execution.

Features:
- Performance monitoring and profiling
- Step execution timing analysis
- Memory usage tracking
- Bottleneck identification
- Performance optimization recommendations
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

if TYPE_CHECKING:
    from ..config import ObservabilityConfig
    from ..events import SimulationEvent


class PerformanceObserver(BaseObserver):
    """Performance monitoring observer for optimization insights.
    
    Tracks simulation performance metrics including timing, memory usage,
    and execution patterns to identify optimization opportunities and
    ensure efficient simulation execution.
    """

    def __init__(self, config: ObservabilityConfig, 
                 history_size: int = 1000, 
                 enable_profiling: bool = True):
        """Initialize the performance observer.
        
        Args:
            config: Observability configuration
            history_size: Number of performance samples to keep in memory
            enable_profiling: Whether to enable detailed profiling
        """
        super().__init__(config)
        
        self._history_size = history_size
        self._enable_profiling = enable_profiling
        
        # Performance metrics storage
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

    def _initialize_event_filtering(self) -> None:
        """Initialize event filtering for performance monitoring.
        
        PerformanceObserver accepts all events to monitor comprehensive
        performance across all simulation activities.
        """
        # Monitor all events for comprehensive performance analysis
        self._enabled_event_types = None  # Accept all events

    def notify(self, event: SimulationEvent) -> None:
        """Process an event and track performance metrics.
        
        Args:
            event: The simulation event to process
        """
        if not self.is_enabled(event.event_type):
            return
        
        # Track event processing performance
        start_time = time.perf_counter() if self._enable_profiling else 0.0
        
        # Update event counts
        self._total_events_processed += 1
        self._events_this_step += 1
        
        # Track step boundary changes
        if event.step != self._current_step:
            self._finalize_step_metrics()
            self._start_new_step(event.step)
        
        # Record event timing if profiling enabled
        if self._enable_profiling:
            processing_time = time.perf_counter() - start_time
            self._record_event_timing(event, processing_time)

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
        """Finalize performance metrics for the completed step.
        
        Args:
            step: The simulation step that just completed
        """
        # Finalize current step if it matches
        if step == self._current_step and self._step_start_time > 0:
            self._finalize_step_metrics()

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary.
        
        Returns:
            Dictionary containing performance analysis and metrics
        """
        if not self._step_timings:
            return {'status': 'no_data', 'message': 'No performance data available'}
        
        # Calculate timing statistics
        step_durations = [metrics['duration'] for metrics in self._step_timings]
        avg_step_duration = sum(step_durations) / len(step_durations)
        
        # Calculate throughput
        total_steps = len(self._step_timings)
        steps_per_second = total_steps / self._total_processing_time if self._total_processing_time > 0 else 0
        
        # Memory statistics
        memory_stats = {}
        if self._memory_samples:
            memory_values = [sample['memory_rss'] for sample in self._memory_samples]
            memory_stats = {
                'peak_memory_mb': self._peak_memory_usage / (1024 * 1024),
                'avg_memory_mb': sum(memory_values) / len(memory_values) / (1024 * 1024),
                'current_memory_mb': memory_values[-1] / (1024 * 1024) if memory_values else 0,
            }
        
        return {
            'timing_stats': {
                'total_steps': total_steps,
                'total_processing_time': self._total_processing_time,
                'avg_step_duration': avg_step_duration,
                'steps_per_second': steps_per_second,
                'slowest_step': self._slowest_step,
                'fastest_step': self._fastest_step if self._fastest_step['duration'] != float('inf') else None,
            },
            'event_stats': {
                'total_events_processed': self._total_events_processed,
                'events_per_step': self._total_events_processed / total_steps if total_steps > 0 else 0,
                'avg_events_per_second': self._total_events_processed / self._total_processing_time if self._total_processing_time > 0 else 0,
            },
            'memory_stats': memory_stats,
            'performance_assessment': self._assess_performance(),
        }

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
        """Close the performance observer."""
        # Finalize any ongoing step
        if self._step_start_time > 0:
            self._finalize_step_metrics()
        
        super().close()

    def get_observer_stats(self) -> Dict[str, Any]:
        """Get performance observer statistics.
        
        Returns:
            Dictionary containing performance observer metrics
        """
        base_stats = super().get_observer_stats()
        
        performance_stats = {
            'total_events_processed': self._total_events_processed,
            'total_processing_time': self._total_processing_time,
            'step_samples': len(self._step_timings),
            'event_samples': len(self._event_timings),
            'memory_samples': len(self._memory_samples),
            'peak_memory_mb': self._peak_memory_usage / (1024 * 1024),
            'profiling_enabled': self._enable_profiling,
        }
        
        return {**base_stats, **performance_stats}

    def __repr__(self) -> str:
        """String representation of the performance observer."""
        return (f"PerformanceObserver(events={self._total_events_processed}, "
                f"steps={len(self._step_timings)}, profiling={self._enable_profiling}, "
                f"closed={self._closed})")