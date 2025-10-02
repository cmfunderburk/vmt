"""Step execution results and metrics.

This module defines the result objects returned by step handlers during
simulation execution. Results encapsulate metrics, events, and any
state changes produced by handler execution.

Design Principles:
- Immutable results prevent post-execution modification
- Structured metrics collection for performance monitoring
- Event aggregation for observer notification
- Minimal overhead with efficient data structures
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass(frozen=True, slots=True)
class StepResult:
    """Result returned by step handler execution.
    
    Encapsulates metrics, events, and any state changes produced
    during handler execution. Results are aggregated by the
    StepExecutor for observer notification and metrics collection.
    
    Attributes:
        metrics: Performance and behavioral metrics from handler execution
        events_count: Number of observer events generated
        execution_time_ms: Handler execution time in milliseconds
        handler_name: Name of the handler that produced this result
    """
    metrics: Dict[str, Any] = field(default_factory=dict)
    events_count: int = 0
    execution_time_ms: float = 0.0
    handler_name: str = ""
    
    @classmethod
    def empty(cls, handler_name: str = "") -> 'StepResult':
        """Create an empty result for handlers that perform no work."""
        return cls(handler_name=handler_name)
    
    @classmethod
    def with_metrics(cls, handler_name: str, **metrics: Any) -> 'StepResult':
        """Create a result with specified metrics."""
        return cls(
            metrics=dict(metrics),
            handler_name=handler_name
        )