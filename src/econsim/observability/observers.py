"""Observer protocol and base classes for the observability system.

This module defines the observer interface that allows simulation components to
emit events without depending on specific logging or GUI implementations. The
protocol-based design provides type safety while maintaining flexibility.

Observer Design Principles:
- Protocol-based interface for type safety and flexibility
- Minimal surface area focused on event handling
- Support for both streaming and batch processing patterns
- Graceful resource management with close() method

Observer Lifecycle:
1. Register with ObserverRegistry
2. Receive events via notify() calls during simulation
3. Handle step boundaries via flush_step() calls  
4. Clean up resources via close() when simulation ends
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .events import SimulationEvent


class SimulationObserver(Protocol):
    """Protocol defining the observer interface for simulation events.
    
    All observers must implement these methods to participate in the
    observability system. The protocol approach allows for both simple
    and complex observer implementations without inheritance constraints.
    """

    def notify(self, event: SimulationEvent) -> None:
        """Handle a simulation event.
        
        Called synchronously during simulation execution for each event.
        Implementations should be efficient to avoid impacting performance.
        
        Args:
            event: The simulation event to process
        """
        ...

    def flush_step(self, step: int) -> None:
        """Handle end-of-step boundary.
        
        Called after all events for a simulation step have been emitted.
        Useful for batch processing, aggregation, or triggering periodic
        output like behavioral summaries.
        
        Args:
            step: The simulation step that just completed
        """
        ...

    def close(self) -> None:
        """Clean up observer resources.
        
        Called when the simulation ends or the observer is unregistered.
        Should handle file closing, connection cleanup, etc. gracefully.
        """
        ...


class BaseObserver(ABC):
    """Abstract base class providing common observer functionality.
    
    Provides a default implementation skeleton for observers that want
    to inherit rather than implement the protocol directly. Includes
    common patterns like event filtering and graceful error handling.
    
    Attributes:
        enabled: Whether this observer should process events
    """

    def __init__(self, enabled: bool = True) -> None:
        """Initialize base observer.
        
        Args:
            enabled: Whether to process events (default: True)
        """
        self.enabled = enabled
        self._closed = False

    @abstractmethod  
    def notify(self, event: SimulationEvent) -> None:
        """Handle a simulation event. Must be implemented by subclasses."""
        pass

    def flush_step(self, step: int) -> None:
        """Default step flush implementation (no-op).
        
        Subclasses can override to implement step boundary handling.
        """
        pass

    def close(self) -> None:
        """Default close implementation.
        
        Marks observer as closed. Subclasses should call super().close()
        after their own cleanup logic.
        """
        self._closed = True

    def is_enabled(self, event_type: str | None = None) -> bool:
        """Check if observer should process events.
        
        Args:
            event_type: Optional event type for filtered checking
            
        Returns:
            True if observer should process the event
        """
        return self.enabled and not self._closed