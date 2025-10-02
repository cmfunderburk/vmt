"""Buffer manager for coordinated management of multiple event buffers.

This module provides the BufferManager class that orchestrates multiple
buffer types, handles buffer lifecycle, and provides a unified interface
for event distribution and data collection across all buffers.

Features:
- Multi-buffer coordination and management
- Efficient event distribution to relevant buffers
- Unified data collection and aggregation
- Buffer lifecycle management
- Performance optimization through selective routing
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional, Set, TYPE_CHECKING

from .base import EventBuffer, BufferError

if TYPE_CHECKING:
    from ..events import SimulationEvent


class BufferManager:
    """Manages multiple event buffers with coordinated lifecycle and routing.
    
    Provides a unified interface for managing multiple buffer types,
    handling event distribution, and collecting aggregated results
    from all managed buffers.
    """

    def __init__(self, buffer_size: Optional[int] = None):
        """Initialize the buffer manager.
        
        Args:
            buffer_size: Default buffer size for managed buffers (optional)
        """
        self._buffers: List[EventBuffer] = []
        self._buffer_registry: Dict[str, EventBuffer] = {}
        self._default_buffer_size = buffer_size or 10000
        
        # Event type routing for performance optimization
        self._event_type_routing: Dict[str, Set[str]] = {
            'agent_mode_change': {'behavioral', 'correlation', 'basic'},
            'trade_execution': {'correlation', 'basic'},
            'resource_collection': {'correlation', 'basic'},
            'agent_movement': {'correlation', 'basic'},
        }
        
        # Buffer statistics
        self._total_events_processed = 0
        self._events_by_type: Dict[str, int] = {}
        self._last_flush_step = 0

    def register_buffer(self, buffer: EventBuffer, name: str) -> None:
        """Register a buffer with the manager.
        
        Args:
            buffer: The event buffer to register
            name: Unique name for the buffer
            
        Raises:
            BufferError: If buffer name is already registered
        """
        if name in self._buffer_registry:
            raise BufferError(f"Buffer '{name}' is already registered")
            
        self._buffers.append(buffer)
        self._buffer_registry[name] = buffer

    def unregister_buffer(self, name: str) -> Optional[EventBuffer]:
        """Unregister a buffer from the manager.
        
        Args:
            name: Name of the buffer to unregister
            
        Returns:
            The unregistered buffer, or None if not found
        """
        if name not in self._buffer_registry:
            return None
            
        buffer = self._buffer_registry.pop(name)
        self._buffers.remove(buffer)
        return buffer

    def get_buffer(self, name: str) -> Optional[EventBuffer]:
        """Get a registered buffer by name.
        
        Args:
            name: Name of the buffer to retrieve
            
        Returns:
            The buffer, or None if not found
        """
        return self._buffer_registry.get(name)

    def add_event(self, event: SimulationEvent) -> None:
        """Distribute an event to appropriate buffers.
        
        Routes events to buffers based on event type and buffer capabilities
        for optimal performance.
        
        Args:
            event: The simulation event to distribute
        """
        self._total_events_processed += 1
        
        # Update event type statistics
        event_type = event.event_type
        self._events_by_type[event_type] = self._events_by_type.get(event_type, 0) + 1
        
        # Route event to appropriate buffers
        target_buffer_types = self._event_type_routing.get(event_type, set())
        
        # If no specific routing, send to all buffers
        if not target_buffer_types:
            target_buffers = self._buffers
        else:
            # Send to buffers matching the routing criteria
            target_buffers = []
            for buffer_name, buffer in self._buffer_registry.items():
                # Check if buffer type matches routing
                buffer_type = self._get_buffer_type(buffer)
                if buffer_type in target_buffer_types or 'basic' in target_buffer_types:
                    target_buffers.append(buffer)
        
        # Distribute event to target buffers with error isolation
        for buffer in target_buffers:
            try:
                buffer.add_event(event)
            except Exception as e:
                # Log error but continue processing other buffers
                # In production, this might use proper logging
                print(f"Warning: Buffer error processing event {event_type}: {e}")

    def _get_buffer_type(self, buffer: EventBuffer) -> str:
        """Determine buffer type from buffer class name.
        
        Args:
            buffer: Buffer to analyze
            
        Returns:
            Buffer type identifier
        """
        class_name = buffer.__class__.__name__.lower()
        
        if 'behavioral' in class_name:
            return 'behavioral'
        elif 'correlation' in class_name:
            return 'correlation'
        elif 'basic' in class_name or 'event' in class_name:
            return 'basic'
        else:
            return 'unknown'

    def flush_step(self, step: int) -> Dict[str, List[Dict[str, Any]]]:
        """Flush all buffers at step boundary and collect results.
        
        Args:
            step: The simulation step being completed
            
        Returns:
            Dictionary mapping buffer names to their flushed data
        """
        self._last_flush_step = step
        results = {}
        
        # Flush each registered buffer and collect results
        for buffer_name, buffer in self._buffer_registry.items():
            try:
                buffer_results = buffer.flush_step(step)
                if buffer_results:  # Only include non-empty results
                    results[buffer_name] = buffer_results
            except Exception as e:
                # Log error but continue with other buffers
                print(f"Warning: Error flushing buffer '{buffer_name}' at step {step}: {e}")
                results[buffer_name] = []  # Provide empty results for failed buffer
        
        return results

    def clear_all_buffers(self) -> None:
        """Clear all managed buffers."""
        for buffer in self._buffers:
            try:
                buffer.clear()
            except Exception as e:
                print(f"Warning: Error clearing buffer: {e}")
        
        # Reset manager statistics
        self._total_events_processed = 0
        self._events_by_type.clear()
        self._last_flush_step = 0

    def get_manager_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about buffer manager state.
        
        Returns:
            Dictionary containing manager and buffer statistics
        """
        # Collect stats from all buffers
        buffer_stats = {}
        total_buffer_size = 0
        
        for name, buffer in self._buffer_registry.items():
            try:
                stats = buffer.get_buffer_stats()
                buffer_stats[name] = stats
                
                # Aggregate size if available
                if 'current_size' in stats:
                    total_buffer_size += stats['current_size']
            except Exception as e:
                buffer_stats[name] = {'error': str(e)}
        
        return {
            'manager_type': 'BufferManager',
            'registered_buffers': len(self._buffer_registry),
            'total_events_processed': self._total_events_processed,
            'events_by_type': dict(self._events_by_type),
            'last_flush_step': self._last_flush_step,
            'total_buffer_size': total_buffer_size,
            'buffer_details': buffer_stats,
            'event_routing': dict(self._event_type_routing),
        }

    def get_buffer_names(self) -> List[str]:
        """Get list of all registered buffer names.
        
        Returns:
            List of buffer names
        """
        return list(self._buffer_registry.keys())

    def is_empty(self) -> bool:
        """Check if all buffers are empty.
        
        Returns:
            True if all buffers report as empty, False otherwise
        """
        for buffer in self._buffers:
            # Check if buffer has is_empty property/method
            if hasattr(buffer, 'is_empty'):
                if not buffer.is_empty:
                    return False
            elif hasattr(buffer, 'size'):
                if buffer.size > 0:
                    return False
        
        return True

    def add_event_type_routing(self, event_type: str, buffer_types: Set[str]) -> None:
        """Add or update event type routing configuration.
        
        Args:
            event_type: The event type to configure
            buffer_types: Set of buffer types that should receive this event type
        """
        self._event_type_routing[event_type] = buffer_types.copy()

    def remove_event_type_routing(self, event_type: str) -> bool:
        """Remove event type routing configuration.
        
        Args:
            event_type: The event type to remove from routing
            
        Returns:
            True if routing was removed, False if not found
        """
        if event_type in self._event_type_routing:
            del self._event_type_routing[event_type]
            return True
        return False

    def __len__(self) -> int:
        """Get number of registered buffers."""
        return len(self._buffers)

    def __contains__(self, name: str) -> bool:
        """Check if a buffer name is registered."""
        return name in self._buffer_registry

    def __iter__(self):
        """Iterate over registered buffer names."""
        return iter(self._buffer_registry.keys())