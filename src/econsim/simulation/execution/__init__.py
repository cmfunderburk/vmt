"""Public API for simulation step execution framework.

This module exports the core classes and protocols needed to implement
and use the step execution framework. The framework decomposes the
monolithic Simulation.step() method into focused, testable handlers.

Exported Classes:
- StepExecutor: Coordinates handler execution during simulation steps
- StepContext: Immutable context passed between handlers  
- StepResult: Results and metrics returned by handlers
- StepHandler: Protocol interface for handler implementation
- BaseStepHandler: Abstract base class with common functionality

Usage:
    from econsim.simulation.execution import StepExecutor, StepContext
    
    # Create handlers for specific concerns
    handlers = [MovementHandler(), CollectionHandler(), TradingHandler()]
    
    # Initialize executor with handler sequence
    executor = StepExecutor(handlers)
    
    # Execute step with immutable context
    context = StepContext(simulation=sim, step_number=1, ...)
    metrics = executor.execute_step(context)
"""

from .context import StepContext
from .result import StepResult
from .step_executor import StepExecutor
from .handlers import StepHandler, BaseStepHandler

__all__ = [
    'StepExecutor',
    'StepContext', 
    'StepResult',
    'StepHandler',
    'BaseStepHandler'
]
