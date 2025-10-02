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
import os
import time
from typing import List, Dict, Set, Any, Optional, TYPE_CHECKING

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
        
        # Event filtering for performance
        self._event_filters: Dict[str, Set[SimulationObserver]] = {}  # event_type -> observers
        self._global_filters: Set[str] = set()  # Globally filtered event types
        
        # Batch event emission
        self._batch_mode: bool = False
        self._batched_events: List[SimulationEvent] = []
        
        # Debug event logging
        self._debug_logging: bool = os.environ.get("ECONSIM_DEBUG_OBSERVERS", "0") == "1"
        self._debug_stats: Dict[str, Any] = {
            "events_processed": 0,
            "events_filtered": 0,
            "observers_failed": 0,
            "batch_flushes": 0
        }

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
        """Distribute an event to all registered observers with filtering.
        
        Applies event filtering for performance, handles batch mode,
        and provides debug logging when enabled. Calls notify() on each 
        registered observer that should receive this event type.
        
        Args:
            event: Event to distribute to observers
        """
        # Check global event filters first
        if event.event_type in self._global_filters:
            if self._debug_logging:
                logger.debug(f"Event {event.event_type} globally filtered")
            self._debug_stats["events_filtered"] += 1
            return
        
        # Handle batch mode
        if self._batch_mode:
            self._batched_events.append(event)
            return
        
        # Debug logging
        if self._debug_logging:
            logger.debug(f"Processing event {event.event_type} for {len(self._observers)} observers")
            
        # Get filtered observers for this event type
        target_observers = self._get_target_observers(event.event_type)
        
        # Distribute to target observers
        for observer in target_observers:
            try:
                observer.notify(event)
                if self._debug_logging:
                    logger.debug(f"Event {event.event_type} processed by {type(observer).__name__}")
            except Exception as e:
                self._debug_stats["observers_failed"] += 1
                logger.error(
                    f"Observer {type(observer).__name__} failed processing event "
                    f"{type(event).__name__}: {e}", 
                    exc_info=True
                )
        
        self._debug_stats["events_processed"] += 1

    def emit_event(self, event: SimulationEvent) -> None:
        """Alias for notify() method for compatibility with validation framework.
        
        Args:
            event: Event to distribute to observers
        """
        self.notify(event)

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

    # Enhanced functionality for Step 1.2
    
    def _get_target_observers(self, event_type: str) -> List[Any]:
        """Get observers that should receive this event type.
        
        Applies event-specific filtering to determine which observers
        should receive events of the given type.
        
        Args:
            event_type: Type of event being distributed
            
        Returns:
            List of observers that should receive this event type
        """
        # If no specific filters for this event type, send to all observers
        if event_type not in self._event_filters:
            return self._observers[:]  # Return copy
        
        # Return only observers that have not filtered out this event type
        filtered_observers = self._event_filters[event_type]
        return [obs for obs in self._observers if obs not in filtered_observers]
    
    def add_event_filter(self, event_type: str, observer: Optional[Any] = None) -> None:
        """Add event filter to improve performance.
        
        Args:
            event_type: Type of event to filter
            observer: Specific observer to filter (None = global filter)
        """
        if observer is None:
            # Global filter - no observer will receive this event type
            self._global_filters.add(event_type)
            if self._debug_logging:
                logger.debug(f"Added global filter for event type: {event_type}")
        else:
            # Observer-specific filter
            if event_type not in self._event_filters:
                self._event_filters[event_type] = set()
            self._event_filters[event_type].add(observer)
            if self._debug_logging:
                logger.debug(f"Added filter for {type(observer).__name__} on event type: {event_type}")
    
    def remove_event_filter(self, event_type: str, observer: Optional[Any] = None) -> None:
        """Remove event filter.
        
        Args:
            event_type: Type of event to unfilter
            observer: Specific observer to unfilter (None = global filter)
        """
        if observer is None:
            self._global_filters.discard(event_type)
            if self._debug_logging:
                logger.debug(f"Removed global filter for event type: {event_type}")
        else:
            if event_type in self._event_filters:
                self._event_filters[event_type].discard(observer)
                if not self._event_filters[event_type]:  # Clean up empty sets
                    del self._event_filters[event_type]
            if self._debug_logging:
                logger.debug(f"Removed filter for {type(observer).__name__} on event type: {event_type}")
    
    def start_batch_mode(self) -> None:
        """Enable batch event processing.
        
        Events will be collected instead of immediately distributed.
        Call flush_batch() to process collected events.
        """
        self._batch_mode = True
        self._batched_events.clear()
        if self._debug_logging:
            logger.debug("Started batch mode for event processing")
    
    def flush_batch(self) -> int:
        """Process all batched events and return to normal mode.
        
        Returns:
            Number of events processed
        """
        if not self._batch_mode:
            return 0
        
        event_count = len(self._batched_events)
        batch_start = time.perf_counter()
        
        # Temporarily disable batch mode to process events
        self._batch_mode = False
        
        try:
            for event in self._batched_events:
                self.notify(event)
        finally:
            # Re-enable batch mode and clear buffer
            self._batch_mode = True
            self._batched_events.clear()
        
        batch_duration = time.perf_counter() - batch_start
        self._debug_stats["batch_flushes"] += 1
        
        if self._debug_logging:
            logger.debug(f"Processed {event_count} batched events in {batch_duration:.4f}s")
        
        return event_count
    
    def stop_batch_mode(self) -> int:
        """Stop batch mode and process any remaining events.
        
        Returns:
            Number of events processed from final batch
        """
        final_count = self.flush_batch() if self._batch_mode else 0
        self._batch_mode = False
        
        if self._debug_logging:
            logger.debug("Stopped batch mode for event processing")
        
        return final_count
    
    def get_debug_stats(self) -> Dict[str, Any]:
        """Get debug statistics for performance analysis.
        
        Returns:
            Dictionary with processing statistics
        """
        return self._debug_stats.copy()
    
    def reset_debug_stats(self) -> None:
        """Reset debug statistics counters."""
        self._debug_stats = {
            "events_processed": 0,
            "events_filtered": 0,
            "observers_failed": 0,
            "batch_flushes": 0
        }
        if self._debug_logging:
            logger.debug("Reset observer debug statistics")