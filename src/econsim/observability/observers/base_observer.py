"""Base observer class providing common functionality for all observers.

This module defines the BaseObserver abstract class that provides shared
functionality for all concrete observer implementations. It handles common
concerns like configuration management, event filtering, and lifecycle.

Design Principles:
- Abstract base class enforcing observer contract
- Common configuration and filtering logic
- Event type enable/disable functionality
- Lifecycle management (initialize, close)
- Performance optimization hooks
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Set, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import ObservabilityConfig
    from ..events import SimulationEvent


class BaseObserver(ABC):
    """Abstract base class for all simulation observers.
    
    Provides common functionality including configuration management,
    event filtering, and lifecycle hooks while enforcing the observer
    contract through abstract methods.
    """

    def __init__(self, config: ObservabilityConfig):
        """Initialize the base observer with configuration.
        
        Args:
            config: Observability configuration settings
        """
        self._config = config
        self._enabled_event_types: Optional[Set[str]] = None
        self._closed = False
        
        # Initialize event type filtering
        self._initialize_event_filtering()

    def _initialize_event_filtering(self) -> None:
        """Initialize event type filtering based on configuration.
        
        Subclasses can override this to customize which event types
        they want to receive based on their specific purpose.
        """
        # By default, accept all event types
        # Subclasses should override to be more selective
        self._enabled_event_types = None  # None means accept all

    def is_enabled(self, event_type: str) -> bool:
        """Check if an event type is enabled for this observer.
        
        Args:
            event_type: The type of event to check
            
        Returns:
            True if the event type should be processed, False otherwise
        """
        if self._closed:
            return False
            
        # If no filtering is set, accept all events
        if self._enabled_event_types is None:
            return True
            
        # Check if this event type is in the enabled set
        return event_type in self._enabled_event_types

    def enable_event_type(self, event_type: str) -> None:
        """Enable processing for a specific event type.
        
        Args:
            event_type: The event type to enable
        """
        if self._enabled_event_types is None:
            self._enabled_event_types = set()
        self._enabled_event_types.add(event_type)

    def disable_event_type(self, event_type: str) -> None:
        """Disable processing for a specific event type.
        
        Args:
            event_type: The event type to disable
        """
        if self._enabled_event_types is not None:
            self._enabled_event_types.discard(event_type)

    @property
    def config(self) -> ObservabilityConfig:
        """Get the observer configuration."""
        return self._config

    @property
    def is_closed(self) -> bool:
        """Check if the observer has been closed."""
        return self._closed

    # Abstract methods that subclasses must implement

    @abstractmethod
    def notify(self, event: SimulationEvent) -> None:
        """Handle a simulation event.
        
        Called for each event during simulation execution. Implementations
        should be efficient to avoid impacting simulation performance.
        
        Args:
            event: The simulation event to process
        """
        ...

    @abstractmethod
    def flush_step(self, step: int) -> None:
        """Handle end-of-step boundary.
        
        Called at the end of each simulation step to allow observers
        to perform batch processing, file writing, or other step-boundary
        operations.
        
        Args:
            step: The simulation step that just completed
        """
        ...

    def close(self) -> None:
        """Close the observer and release resources.
        
        Default implementation sets the closed flag. Subclasses should
        override to perform cleanup like closing files, connections, etc.
        """
        self._closed = True

    # Optional hook methods that subclasses can override

    def on_simulation_start(self) -> None:
        """Called when simulation starts.
        
        Optional hook for observers that need to perform initialization
        when a simulation begins.
        """
        pass

    def on_simulation_end(self) -> None:
        """Called when simulation ends.
        
        Optional hook for observers that need to perform cleanup or
        final processing when a simulation completes.
        """
        pass

    def get_observer_stats(self) -> dict[str, any]:
        """Get statistics about observer state and performance.
        
        Returns:
            Dictionary containing observer metrics and statistics
        """
        return {
            'observer_type': self.__class__.__name__,
            'enabled_event_types': (
                list(self._enabled_event_types) if self._enabled_event_types is not None 
                else 'all'
            ),
            'is_closed': self._closed,
        }

    def __repr__(self) -> str:
        """String representation of the observer."""
        return f"{self.__class__.__name__}(closed={self._closed})"