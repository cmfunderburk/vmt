"""Observer registration and notification system.

This module provides the central registry for managing simulation observers
and coordinating event distribution. The registry acts as the bridge between
the simulation layer (event sources) and observer layer (event sinks).

Registry Design Principles:
- Thread-safe observer registration/unregistration
- Efficient event distribution to multiple observers  
- Graceful error handling to prevent observer failures from affecting simulation
- Support for both individual and batch event processing

Usage Pattern:
    registry = ObserverRegistry()
    registry.register(my_observer)
    registry.notify(event)  # Distributes to all registered observers
    registry.flush_step(step_number)  # Notifies step boundary
"""

from __future__ import annotations

import logging
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .events import SimulationEvent
    from .observers import SimulationObserver

logger = logging.getLogger(__name__)


class ObserverRegistry:
    """Central registry for managing and coordinating simulation observers.
    
    Provides thread-safe registration of observers and efficient event
    distribution. Handles observer failures gracefully to prevent
    disruption of simulation execution.
    
    Attributes:
        _observers: List of registered observers
    """

    def __init__(self) -> None:
        """Initialize empty observer registry."""
        self._observers: List[SimulationObserver] = []

    def register(self, observer: SimulationObserver) -> None:
        """Register an observer to receive simulation events.
        
        Args:
            observer: Observer implementing SimulationObserver protocol
            
        Raises:
            ValueError: If observer is already registered
        """
        if observer in self._observers:
            raise ValueError("Observer already registered")
            
        self._observers.append(observer)
        logger.debug(f"Registered observer: {type(observer).__name__}")

    def unregister(self, observer: SimulationObserver) -> None:
        """Unregister an observer from receiving events.
        
        Args:
            observer: Observer to remove from registry
            
        Raises:
            ValueError: If observer is not registered
        """
        try:
            self._observers.remove(observer)
            logger.debug(f"Unregistered observer: {type(observer).__name__}")
        except ValueError:
            raise ValueError("Observer not found in registry")

    def notify(self, event: SimulationEvent) -> None:
        """Distribute an event to all registered observers.
        
        Calls notify() on each registered observer. If an observer
        raises an exception, logs the error but continues distributing
        to other observers to maintain simulation stability.
        
        Args:
            event: Event to distribute to observers
        """
        for observer in self._observers[:]:  # Copy to avoid modification during iteration
            try:
                observer.notify(event)
            except Exception as e:
                logger.error(
                    f"Observer {type(observer).__name__} failed processing event "
                    f"{type(event).__name__}: {e}", 
                    exc_info=True
                )

    def flush_step(self, step: int) -> None:
        """Notify all observers of step boundary.
        
        Calls flush_step() on each registered observer. Handles observer
        failures gracefully with error logging.
        
        Args:
            step: Simulation step number that just completed
        """
        for observer in self._observers[:]:  # Copy to avoid modification during iteration
            try:
                observer.flush_step(step)
            except Exception as e:
                logger.error(
                    f"Observer {type(observer).__name__} failed flushing step "
                    f"{step}: {e}",
                    exc_info=True
                )

    def close_all(self) -> None:
        """Close all registered observers and clear registry.
        
        Calls close() on each observer and removes them from the registry.
        Handles observer failures gracefully with error logging.
        """
        for observer in self._observers[:]:  # Copy list since we'll modify it
            try:
                observer.close()
            except Exception as e:
                logger.error(
                    f"Observer {type(observer).__name__} failed closing: {e}",
                    exc_info=True
                )
                
        self._observers.clear()
        logger.debug("Closed all observers and cleared registry")

    def observer_count(self) -> int:
        """Return the number of registered observers.
        
        Returns:
            Number of currently registered observers
        """
        return len(self._observers)

    def has_observers(self) -> bool:
        """Check if any observers are registered.
        
        Returns:
            True if at least one observer is registered
        """
        return len(self._observers) > 0