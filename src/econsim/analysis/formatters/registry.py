"""
Formatter Registry: Central registry and factory for event formatters.

This module provides centralized management of event formatters, including
automatic discovery, registration, and factory methods for getting appropriate
formatters by event type.

Key Features:
- Automatic formatter discovery and registration
- Factory methods for getting formatters by event type
- Formatter caching for performance
- Extensible design for adding new formatters
- Error handling for unknown event types

Architecture:
- FormatterRegistry singleton manages all formatters
- Auto-registration discovers formatter classes at import time
- Factory methods provide clean interface for GUI components
- Caching improves performance for repeated formatter requests

Usage:
    # Get registry instance
    registry = FormatterRegistry()
    
    # Get formatter for specific event type
    formatter = registry.get_formatter('trade')
    display_text = formatter.to_display_text(raw_trade_event)
    
    # Register custom formatter
    registry.register_formatter('custom_event', CustomEventFormatter())
    
    # Get all supported event types
    supported_types = registry.get_supported_types()
"""

from __future__ import annotations

import inspect
from typing import Dict, Set, Optional, Type, Any, List
from .base_formatter import EventFormatter


class FormatterRegistry:
    """Central registry for event formatters.
    
    This class manages all available event formatters and provides factory methods
    for getting appropriate formatters by event type. It supports automatic
    discovery of formatter classes and caching for performance.
    
    The registry follows the singleton pattern to ensure consistent formatter
    instances across the application.
    """
    
    _instance: Optional[FormatterRegistry] = None
    
    def __new__(cls) -> FormatterRegistry:
        """Singleton pattern - ensure only one registry instance."""
        if cls._instance is None:
            cls._instance = super(FormatterRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize formatter registry."""
        if self._initialized:
            return
            
        self._formatters: Dict[str, EventFormatter] = {}
        self._formatter_classes: Dict[str, Type[EventFormatter]] = {}
        self._initialized = True
        
        # Auto-discover and register formatters
        self._discover_formatters()
    
    # ============================================================================
    # FORMATTER REGISTRATION METHODS
    # ============================================================================
    
    def register_formatter(self, event_type: str, formatter: EventFormatter) -> None:
        """Register a formatter instance for an event type.
        
        Args:
            event_type: Event type string (e.g., 'trade', 'mode_change')
            formatter: Formatter instance to register
        """
        if not isinstance(formatter, EventFormatter):
            raise ValueError(f"Formatter must be instance of EventFormatter, got {type(formatter)}")
        
        self._formatters[event_type] = formatter
        
    def register_formatter_class(self, event_type: str, formatter_class: Type[EventFormatter]) -> None:
        """Register a formatter class for an event type (lazy instantiation).
        
        Args:
            event_type: Event type string
            formatter_class: Formatter class to register
        """
        if not issubclass(formatter_class, EventFormatter):
            raise ValueError(f"Formatter class must inherit from EventFormatter, got {formatter_class}")
        
        self._formatter_classes[event_type] = formatter_class
    
    def unregister_formatter(self, event_type: str) -> bool:
        """Unregister formatter for an event type.
        
        Args:
            event_type: Event type to unregister
            
        Returns:
            True if formatter was unregistered, False if not found
        """
        removed_instance = self._formatters.pop(event_type, None)
        removed_class = self._formatter_classes.pop(event_type, None)
        return removed_instance is not None or removed_class is not None
    
    # ============================================================================
    # FORMATTER FACTORY METHODS
    # ============================================================================
    
    def get_formatter(self, event_type: str) -> Optional[EventFormatter]:
        """Get formatter instance for an event type.
        
        Args:
            event_type: Event type string
            
        Returns:
            Formatter instance or None if not found
        """
        # Check if formatter instance already exists
        if event_type in self._formatters:
            return self._formatters[event_type]
        
        # Check if formatter class is registered for lazy instantiation
        if event_type in self._formatter_classes:
            formatter_class = self._formatter_classes[event_type]
            formatter_instance = formatter_class()
            self._formatters[event_type] = formatter_instance
            return formatter_instance
        
        return None
    
    def get_formatter_safe(self, event_type: str) -> EventFormatter:
        """Get formatter instance with fallback to default formatter.
        
        Args:
            event_type: Event type string
            
        Returns:
            Formatter instance (never None)
        """
        formatter = self.get_formatter(event_type)
        if formatter is not None:
            return formatter
        
        # Return default formatter for unknown event types
        return self._get_default_formatter()
    
    def has_formatter(self, event_type: str) -> bool:
        """Check if formatter is available for an event type.
        
        Args:
            event_type: Event type string
            
        Returns:
            True if formatter is available, False otherwise
        """
        return (event_type in self._formatters or 
                event_type in self._formatter_classes)
    
    # ============================================================================
    # DISCOVERY AND INTROSPECTION METHODS
    # ============================================================================
    
    def get_supported_types(self) -> Set[str]:
        """Get all supported event types.
        
        Returns:
            Set of event type strings that have registered formatters
        """
        return set(self._formatters.keys()) | set(self._formatter_classes.keys())
    
    def get_formatter_info(self, event_type: str) -> Optional[Dict[str, Any]]:
        """Get information about a registered formatter.
        
        Args:
            event_type: Event type string
            
        Returns:
            Dictionary with formatter information or None if not found
        """
        formatter = self.get_formatter(event_type)
        if formatter is not None:
            info = formatter.get_formatter_info()
            info['registered_as'] = event_type
            return info
        return None
    
    def list_all_formatters(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered formatters.
        
        Returns:
            Dictionary mapping event types to formatter information
        """
        all_formatters = {}
        for event_type in self.get_supported_types():
            formatter_info = self.get_formatter_info(event_type)
            if formatter_info:
                all_formatters[event_type] = formatter_info
        return all_formatters
    
    # ============================================================================
    # AUTOMATIC DISCOVERY METHODS
    # ============================================================================
    
    def _discover_formatters(self) -> None:
        """Automatically discover and register formatter classes.
        
        Scans the formatters package for EventFormatter subclasses and
        registers them based on their supported event types.
        """
        # List of formatter modules to scan
        formatter_modules = [
            'econsim.gui.formatters.trade_formatter',
            'econsim.gui.formatters.mode_change_formatter',
            'econsim.gui.formatters.resource_formatter',
            'econsim.gui.formatters.debug_formatter'
        ]
        
        # Scan each module and register found formatters
        for module_name in formatter_modules:
            formatter_classes = self._scan_module_for_formatters(module_name)
            for formatter_class in formatter_classes:
                # Instantiate to get supported event type
                try:
                    instance = formatter_class()
                    event_type = instance.get_supported_event_type()
                    if event_type and event_type != 'unknown':
                        self.register_formatter_class(event_type, formatter_class)
                except Exception as e:
                    # Log error but continue with other formatters
                    print(f"Warning: Failed to register formatter {formatter_class.__name__}: {e}")
        
        # Also try to import and register individual formatter classes directly
        self._register_known_formatters()
    
    def _register_known_formatters(self) -> None:
        """Register known formatter classes directly by importing them."""
        try:
            # Import and register TradeEventFormatter
            from .trade_formatter import TradeEventFormatter
            self.register_formatter_class('trade', TradeEventFormatter)
        except ImportError:
            pass
        
        try:
            # Import and register ModeChangeEventFormatter
            from .mode_change_formatter import ModeChangeEventFormatter
            self.register_formatter_class('mode_change', ModeChangeEventFormatter)
        except ImportError:
            pass
        
        try:
            # Import and register ResourceCollectionEventFormatter
            from .resource_formatter import ResourceCollectionEventFormatter
            self.register_formatter_class('resource_collection', ResourceCollectionEventFormatter)
        except ImportError:
            pass
        
        try:
            # Import and register DebugLogEventFormatter
            from .debug_formatter import DebugLogEventFormatter
            self.register_formatter_class('debug_log', DebugLogEventFormatter)
        except ImportError:
            pass
        
        try:
            # Import and register PerformanceMonitorEventFormatter
            from .performance_formatter import PerformanceMonitorEventFormatter
            self.register_formatter_class('performance_monitor', PerformanceMonitorEventFormatter)
        except ImportError:
            pass
    
    def _scan_module_for_formatters(self, module_name: str) -> List[Type[EventFormatter]]:
        """Scan a module for EventFormatter subclasses.
        
        Args:
            module_name: Name of module to scan
            
        Returns:
            List of discovered formatter classes
        """
        try:
            module = __import__(module_name, fromlist=[''])
            formatter_classes = []
            
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, EventFormatter) and 
                    obj is not EventFormatter and
                    not inspect.isabstract(obj)):
                    formatter_classes.append(obj)
            
            return formatter_classes
        except ImportError:
            return []
    
    def refresh_formatters(self) -> None:
        """Refresh formatter registry by re-scanning for formatters.
        
        This method can be called to pick up newly added formatter classes
        without restarting the application.
        """
        # Clear existing registrations
        self._formatters.clear()
        self._formatter_classes.clear()
        
        # Re-discover formatters
        self._discover_formatters()
    
    # ============================================================================
    # DEFAULT FORMATTER FOR UNKNOWN EVENT TYPES
    # ============================================================================
    
    def _get_default_formatter(self) -> EventFormatter:
        """Get default formatter for unknown event types.
        
        Returns:
            Default formatter instance
        """
        return DefaultEventFormatter()
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def clear_all_formatters(self) -> None:
        """Clear all registered formatters (useful for testing)."""
        self._formatters.clear()
        self._formatter_classes.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics.
        
        Returns:
            Dictionary with registry statistics
        """
        return {
            'total_formatters': len(self.get_supported_types()),
            'instance_formatters': len(self._formatters),
            'class_formatters': len(self._formatter_classes),
            'supported_types': sorted(self.get_supported_types())
        }
    
    def __len__(self) -> int:
        """Return number of registered formatters."""
        return len(self.get_supported_types())
    
    def __contains__(self, event_type: str) -> bool:
        """Check if event type has registered formatter."""
        return self.has_formatter(event_type)
    
    def __repr__(self) -> str:
        """String representation of registry."""
        stats = self.get_statistics()
        return f"FormatterRegistry(formatters={stats['total_formatters']}, types={stats['supported_types']})"


class DefaultEventFormatter(EventFormatter):
    """Default formatter for unknown event types.
    
    This formatter provides safe fallback formatting for event types
    that don't have specific formatters registered.
    """
    
    def to_display_text(self, raw_event: Dict[str, Any]) -> str:
        """Convert unknown event to basic display text."""
        event_type = raw_event.get('type', 'unknown')
        step = raw_event.get('step', '?')
        return f"[{event_type.replace('_', ' ').title()}] at step {step}"
    
    def to_analysis_data(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert unknown event to basic analysis structure."""
        return {
            'event_type': raw_event.get('type', 'unknown'),
            'step': raw_event.get('step', 0),
            'raw_fields': list(raw_event.keys()),
            'is_unknown_type': True
        }
    
    def to_table_row(self, raw_event: Dict[str, Any]) -> List[Any]:
        """Convert unknown event to basic table row."""
        return [
            raw_event.get('step', '?'),
            raw_event.get('type', 'Unknown').replace('_', ' ').title(),
            'Unknown event type',
            f"{len(raw_event)} fields",
            'No specific formatter'
        ]
    
    def get_supported_event_type(self) -> str:
        """Return supported event type."""
        return 'default'


# Global registry instance
_registry_instance: Optional[FormatterRegistry] = None


def get_registry() -> FormatterRegistry:
    """Get global formatter registry instance.
    
    Returns:
        Global FormatterRegistry instance
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = FormatterRegistry()
    return _registry_instance


def get_formatter(event_type: str) -> Optional[EventFormatter]:
    """Convenience function to get formatter from global registry.
    
    Args:
        event_type: Event type string
        
    Returns:
        Formatter instance or None if not found
    """
    return get_registry().get_formatter(event_type)


def register_formatter(event_type: str, formatter: EventFormatter) -> None:
    """Convenience function to register formatter in global registry.
    
    Args:
        event_type: Event type string
        formatter: Formatter instance to register
    """
    get_registry().register_formatter(event_type, formatter)