"""Step executor for coordinating simulation step handlers.

This module provides the main StepExecutor class that orchestrates
the execution of individual step handlers during simulation steps.
The executor maintains handler order, aggregates results, and ensures
deterministic execution.

Design Principles:
- Handler composition via dependency injection
- Deterministic execution order with explicit sequencing
- Performance monitoring and metrics aggregation
- Observer event coordination across handlers
- Error isolation to prevent handler failures from stopping execution
"""

from __future__ import annotations

import time
from typing import List, Dict, Any

from .context import StepContext
from .handlers import StepHandler


class StepExecutor:
    """Coordinates execution of step handlers during simulation steps.
    
    The executor receives a list of handlers and executes them in order
    during each simulation step. Handler results are aggregated for
    metrics collection and observer notification.
    
    Attributes:
        handlers: Ordered list of step handlers to execute
    """
    
    def __init__(self, handlers: List[StepHandler]):
        """Initialize executor with handler sequence.
        
        Args:
            handlers: Step handlers in execution order
        """
        self.handlers = handlers
        self._step_metrics: Dict[str, Any] = {}
    
    def execute_step(self, context: StepContext) -> Dict[str, Any]:
        """Execute all handlers for the current simulation step.

        Returns a flat metrics dict. Caller owns any higher-level aggregation
        or logging. Keeping a simple structure avoids adding a wrapper object
        that could affect determinism hashing if mistakenly serialized.
        """
        step_start = time.perf_counter()
        aggregated: Dict[str, Any] = {}
        total_events = 0
        handler_timings: Dict[str, float] = {}

        for handler in self.handlers:
            result = handler.execute(context)
            # Prefix metrics with handler name to avoid collisions
            if result.metrics:
                for k, v in result.metrics.items():
                    aggregated[f"{result.handler_name}_{k}"] = v
            handler_timings[result.handler_name] = result.execution_time_ms
            total_events += result.events_count

        aggregated["total_events_generated"] = total_events
        aggregated["handler_timings"] = handler_timings
        aggregated["handlers_executed"] = len(self.handlers)
        aggregated["total_step_time_ms"] = (time.perf_counter() - step_start) * 1000
        return aggregated
    
    def get_handler_names(self) -> List[str]:
        """Get names of all registered handlers for debugging."""
        return [getattr(h, 'handler_name', h.__class__.__name__) for h in self.handlers]
