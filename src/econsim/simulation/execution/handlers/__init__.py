"""Step handler protocol and base classes.

This module defines the protocol interface for all simulation step handlers
and provides base implementations for common functionality. Handlers are
responsible for specific aspects of simulation step processing.

Design Principles:
- Protocol-based interfaces for type safety and testability
- Single responsibility: each handler focuses on one concern
- Deterministic execution with explicit RNG management
- Observer pattern integration for event notification
- Performance monitoring with execution time tracking
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from ..context import StepContext
from ..result import StepResult


@runtime_checkable
class StepHandler(Protocol):
    """Protocol interface for simulation step handlers.
    
    All step handlers must implement this protocol to participate
    in the step execution framework. Handlers receive immutable
    context and return structured results.
    
    Methods:
        execute: Process one aspect of the simulation step
    """
    
    def execute(self, context: StepContext) -> StepResult:
        """Execute handler logic for the current simulation step.
        
        Args:
            context: Immutable step context with simulation state and config
            
        Returns:
            StepResult with metrics and event counts from handler execution
        """
        ...


class BaseStepHandler(ABC):
    """Abstract base class for step handlers with common functionality.
    
    Provides performance monitoring, error handling, and observer integration
    for concrete handler implementations. Handlers should inherit from this
    class unless they have specific requirements.
    
    Attributes:
        handler_name: Identifier for metrics and debugging
    """
    
    def __init__(self, handler_name: str):
        self.handler_name = handler_name
    
    def execute(self, context: StepContext) -> StepResult:
        """Execute handler with performance monitoring and error handling."""
        start_time = time.perf_counter()
        
        try:
            result = self._execute_impl(context)
            
            # Add execution timing to result
            execution_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
            
            return StepResult(
                metrics=result.metrics,
                events_count=result.events_count,
                execution_time_ms=execution_time,
                handler_name=self.handler_name
            )
            
        except Exception as e:
            # Log error and return empty result to prevent step failure
            execution_time = (time.perf_counter() - start_time) * 1000
            
            # TODO: Use observer system for error logging
            print(f"Handler {self.handler_name} failed: {e}")
            
            return StepResult(
                metrics={"error": str(e)},
                execution_time_ms=execution_time,
                handler_name=self.handler_name
            )
    
    @abstractmethod
    def _execute_impl(self, context: StepContext) -> StepResult:
        """Concrete handler implementation.
        
        Subclasses implement this method with their specific logic.
        Base class handles timing, error handling, and result formatting.
        
        Args:
            context: Immutable step context
            
        Returns:
            StepResult with handler-specific metrics
        """
        pass
