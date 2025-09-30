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
        
        Handlers are executed in the order provided during initialization.
        Results are aggregated and returned for metrics collection.
        
        Args:
            context: Immutable step context with simulation state
            
        Returns:
            Aggregated metrics from all handler executions
        """
        step_start = time.perf_counter()
        aggregated_metrics = {}
        total_events = 0
        handler_timings = {}
        
        for handler in self.handlers:
            try:
                result = handler.execute(context)
                
                # Aggregate handler metrics
                if result.metrics:
                    handler_metrics = {f"{result.handler_name}_{k}": v 
                                     for k, v in result.metrics.items()}
                    aggregated_metrics.update(handler_metrics)
                
                # Track handler performance
                handler_timings[result.handler_name] = result.execution_time_ms
                total_events += result.events_count
                
            except Exception as e:
                # Isolate handler failures - log error but continue execution
                handler_name = getattr(handler, 'handler_name', handler.__class__.__name__)
                print(f"Handler {handler_name} failed during step {context.step_number}: {e}")
                
                # Record failure in metrics
                aggregated_metrics[f"{handler_name}_error"] = str(e)
        
        # Add overall step timing
        total_step_time = (time.perf_counter() - step_start) * 1000
        
        return {
            **aggregated_metrics,
            "total_step_time_ms": total_step_time,
            "total_events_generated": total_events,
            "handler_timings": handler_timings,
            "handlers_executed": len(self.handlers)
        }
    
    def get_handler_names(self) -> List[str]:
        """Get names of all registered handlers for debugging."""
        return [getattr(h, 'handler_name', h.__class__.__name__) for h in self.handlers]
