"""Buffer system for efficient event aggregation and processing.

This module provides a comprehensive buffering system for simulation events,
enabling efficient storage, aggregation, and batch processing of event data.
The system supports multiple buffer types for different use cases.

Buffer Types:
- EventBuffer: Basic event storage with step-based flushing
- BehavioralAggregationBuffer: Agent behavior analysis over time windows
- CorrelationBuffer: Event correlation tracking for analytics
- BufferManager: Coordinated management of multiple buffers

Design Principles:
- Efficient memory usage with configurable windows
- Step-based flushing for deterministic boundaries
- Pluggable buffer types via abstract base classes
- Thread-safe operation for concurrent access
"""

from .base import EventBuffer
from .event_buffer import BasicEventBuffer
from .behavioral_buffer import BehavioralAggregationBuffer
from .correlation_buffer import CorrelationBuffer
from .buffer_manager import BufferManager

__all__ = [
    'EventBuffer',
    'BasicEventBuffer', 
    'BehavioralAggregationBuffer',
    'CorrelationBuffer',
    'BufferManager',
]