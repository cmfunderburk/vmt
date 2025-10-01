"""Abstract base classes for event buffer implementations.

This module defines the core interfaces that all event buffers must implement.
The EventBuffer ABC provides a consistent contract for event storage, 
aggregation, and step-based flushing operations.

Design Principles:
- Abstract interface for pluggable buffer implementations
- Step-based lifecycle with clear flush boundaries
- Type-safe event handling with generic typing
- Memory-efficient operation with configurable limits
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..events import SimulationEvent


class EventBuffer(ABC):
    """Abstract base class for all event buffers.
    
    Defines the core interface that all buffer implementations must provide.
    Buffers are responsible for efficient storage and aggregation of simulation
    events, with step-based flushing for deterministic operation.
    """

    @abstractmethod
    def add_event(self, event: SimulationEvent) -> None:
        """Add a simulation event to the buffer.
        
        Called during simulation execution to store events for later processing.
        Implementations should be efficient as this is called frequently.
        
        Args:
            event: The simulation event to buffer
        """
        ...

    @abstractmethod
    def flush_step(self, step: int) -> List[Dict[str, Any]]:
        """Flush buffered events at step boundary.
        
        Called at the end of each simulation step to retrieve and clear
        buffered events. Returns structured data ready for processing.
        
        Args:
            step: The simulation step number being completed
            
        Returns:
            List of event dictionaries ready for output/analysis
        """
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear all buffered data.
        
        Called to reset buffer state, typically during initialization
        or when switching between simulation runs.
        """
        ...

    def get_buffer_stats(self) -> Dict[str, Any]:
        """Get statistics about current buffer state.
        
        Optional method that buffers can override to provide diagnostic
        information about their internal state and performance.
        
        Returns:
            Dictionary of buffer statistics (default: empty)
        """
        return {}


class BufferError(Exception):
    """Base exception for buffer-related errors."""
    pass


class BufferOverflowError(BufferError):
    """Raised when buffer capacity is exceeded."""
    pass


class BufferStateError(BufferError):
    """Raised when buffer is in invalid state for operation."""
    pass