"""
Base Event Formatter: Abstract interface for GUI event formatters.

This module defines the abstract base class that all event formatters must implement.
It enforces a consistent interface across all formatters while allowing flexibility
in implementation details.

Key Design Principles:
- Pure presentation logic - no business logic in formatters
- Multiple output formats - display text, analysis data, table rows
- Extensible interface - easy to add new formatting methods
- Type safety - full typing for all methods and return values
- Performance conscious - lightweight operations suitable for GUI

Interface Methods:
- to_display_text() - Human-readable text for GUI display
- to_analysis_data() - Structured data for analysis widgets
- to_table_row() - List format for table displays
- to_detailed_view() - Rich detailed formatting (optional)

Usage:
    class TradeEventFormatter(EventFormatter):
        def to_display_text(self, raw_event: Dict[str, Any]) -> str:
            return f"Agent {raw_event['seller_id']} traded..."
        
        def to_analysis_data(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
            return {'participants': [...], 'utility_gain': ...}
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union


class EventFormatter(ABC):
    """Abstract base class for all event formatters.
    
    This class defines the standard interface that all event formatters must implement.
    Each formatter is responsible for converting raw event dictionaries (from RawDataObserver)
    into human-readable formats suitable for GUI display.
    
    Design Principles:
    1. Pure presentation logic - no business calculations
    2. Stateless operations - no internal state between calls
    3. Fast operations - suitable for real-time GUI updates
    4. Multiple output formats - flexible for different GUI needs
    5. Error tolerant - handle missing or invalid data gracefully
    
    Subclasses must implement all abstract methods and may add formatter-specific
    methods as needed.
    """
    
    @abstractmethod
    def to_display_text(self, raw_event: Dict[str, Any]) -> str:
        """Convert raw event to human-readable display text.
        
        This method produces a concise, human-readable summary suitable for
        event lists, tooltips, or brief descriptions.
        
        Args:
            raw_event: Raw event dictionary from RawDataObserver
            
        Returns:
            Human-readable string suitable for GUI display
            
        Examples:
            "Agent 1 traded wood for food with Agent 2"
            "Agent 3 changed from foraging to trading mode"
            "Agent 5 collected 2 stone at (10, 15)"
        """
        pass
    
    @abstractmethod
    def to_analysis_data(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw event to analysis-friendly structure.
        
        This method produces structured data suitable for analysis widgets,
        charts, statistics, and data processing operations.
        
        Args:
            raw_event: Raw event dictionary from RawDataObserver
            
        Returns:
            Dictionary with analysis-friendly structure and computed fields
            
        Examples:
            {'participants': [1, 2], 'items_exchanged': ['wood', 'food'], 'utility_gain': 3.8}
            {'agent': 3, 'transition': 'forage_to_trade', 'duration_in_mode': 15}
            {'collection_rate': 2, 'location': (10, 15), 'efficiency': 0.8}
        """
        pass
    
    @abstractmethod
    def to_table_row(self, raw_event: Dict[str, Any]) -> List[Union[str, int, float]]:
        """Convert raw event to table row format.
        
        This method produces a list of values suitable for displaying in
        table widgets, CSV export, or tabular analysis.
        
        Args:
            raw_event: Raw event dictionary from RawDataObserver
            
        Returns:
            List of values in a consistent order for table display
            
        Examples:
            [42, "Trade", "Agent 1 → Agent 2", "wood → food", 3.8]
            [43, "Mode Change", "Agent 3", "foraging → trading", "found partner"]
            [44, "Collection", "Agent 5", "2 stone", "(10, 15)"]
        """
        pass
    
    # ============================================================================
    # OPTIONAL METHODS - Subclasses can override for enhanced functionality
    # ============================================================================
    
    def to_detailed_view(self, raw_event: Dict[str, Any]) -> Dict[str, str]:
        """Convert raw event to detailed view format (optional).
        
        This method produces detailed, structured information suitable for
        event detail panels, inspection views, or debugging displays.
        
        Args:
            raw_event: Raw event dictionary from RawDataObserver
            
        Returns:
            Dictionary mapping field names to formatted display values
            
        Note:
            Default implementation provides basic field formatting.
            Subclasses can override for event-specific detailed views.
        """
        detailed = {}
        for key, value in raw_event.items():
            if key == 'type':
                detailed['Event Type'] = str(value).replace('_', ' ').title()
            elif key == 'step':
                detailed['Step'] = str(value)
            elif 'id' in key.lower():
                detailed[self._format_field_name(key)] = f"Agent {value}" if isinstance(value, int) else str(value)
            else:
                detailed[self._format_field_name(key)] = str(value)
        return detailed
    
    def get_table_headers(self) -> List[str]:
        """Get table column headers for this event type (optional).
        
        Returns:
            List of column header strings for table display
            
        Note:
            Default implementation provides generic headers.
            Subclasses should override for event-specific headers.
        """
        return ["Step", "Event Type", "Description", "Details", "Context"]
    
    def format_for_export(self, raw_event: Dict[str, Any], format_type: str = 'json') -> Union[str, Dict]:
        """Format event for export (optional).
        
        Args:
            raw_event: Raw event dictionary from RawDataObserver
            format_type: Export format ('json', 'csv', 'text')
            
        Returns:
            Formatted data suitable for the specified export format
        """
        if format_type == 'json':
            return raw_event.copy()  # Return raw data for JSON export
        elif format_type == 'csv':
            return self.to_table_row(raw_event)
        elif format_type == 'text':
            return self.to_display_text(raw_event)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    # ============================================================================
    # UTILITY METHODS - Common formatting helpers
    # ============================================================================
    
    def _format_field_name(self, field_name: str) -> str:
        """Convert snake_case field name to human-readable format.
        
        Args:
            field_name: Field name in snake_case
            
        Returns:
            Human-readable field name
        """
        return field_name.replace('_', ' ').title()
    
    def _format_agent_id(self, agent_id: int) -> str:
        """Format agent ID for display.
        
        Args:
            agent_id: Numeric agent ID
            
        Returns:
            Formatted agent identifier
        """
        return f"Agent {agent_id}" if agent_id >= 0 else "System"
    
    def _format_location(self, x: int, y: int) -> str:
        """Format coordinate pair for display.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Formatted location string
        """
        return f"({x}, {y})" if x >= 0 and y >= 0 else "Unknown location"
    
    def _format_utility(self, utility: float) -> str:
        """Format utility value for display.
        
        Args:
            utility: Utility value
            
        Returns:
            Formatted utility string with appropriate sign and precision
        """
        if utility == 0.0:
            return "No change"
        elif utility > 0.0:
            return f"+{utility:.2f}"
        else:
            return f"{utility:.2f}"
    
    def _safe_get(self, raw_event: Dict[str, Any], key: str, default: Any = 'Unknown') -> Any:
        """Safely get value from raw event with default fallback.
        
        Args:
            raw_event: Raw event dictionary
            key: Key to retrieve
            default: Default value if key is missing
            
        Returns:
            Value from dictionary or default if key is missing
        """
        return raw_event.get(key, default)
    
    def _validate_event_type(self, raw_event: Dict[str, Any], expected_type: str) -> bool:
        """Validate that raw event is of expected type.
        
        Args:
            raw_event: Raw event dictionary
            expected_type: Expected event type string
            
        Returns:
            True if event type matches, False otherwise
        """
        return raw_event.get('type') == expected_type
    
    # ============================================================================
    # ERROR HANDLING METHODS
    # ============================================================================
    
    def _handle_formatting_error(self, raw_event: Dict[str, Any], error: Exception, context: str) -> str:
        """Handle formatting errors gracefully.
        
        Args:
            raw_event: Raw event that caused the error
            error: Exception that occurred
            context: Context where error occurred (method name)
            
        Returns:
            Safe fallback string for display
        """
        event_type = raw_event.get('type', 'unknown')
        step = raw_event.get('step', '?')
        return f"[Error formatting {event_type} event at step {step}]"
    
    # ============================================================================
    # METADATA METHODS
    # ============================================================================
    
    def get_supported_event_type(self) -> str:
        """Get the event type this formatter supports.
        
        Returns:
            Event type string (e.g., 'trade', 'mode_change')
            
        Note:
            Default implementation derives from class name.
            Subclasses can override if needed.
        """
        class_name = self.__class__.__name__
        if class_name.endswith('EventFormatter'):
            event_type = class_name[:-14]  # Remove 'EventFormatter' suffix
            return event_type.lower().replace('_', '')
        return 'unknown'
    
    def get_formatter_info(self) -> Dict[str, Any]:
        """Get metadata about this formatter.
        
        Returns:
            Dictionary with formatter metadata
        """
        return {
            'formatter_class': self.__class__.__name__,
            'supported_event_type': self.get_supported_event_type(),
            'methods': ['to_display_text', 'to_analysis_data', 'to_table_row'],
            'optional_methods': ['to_detailed_view', 'format_for_export'],
            'version': '1.0.0'
        }
    
    def __repr__(self) -> str:
        """String representation of formatter."""
        return f"{self.__class__.__name__}(type='{self.get_supported_event_type()}')"