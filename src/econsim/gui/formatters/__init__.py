"""
GUI Event Formatters Package

This package contains GUI formatting classes that convert raw simulation data
to human-readable format for display purposes. This implements clean separation
between business logic (raw data) and presentation logic (GUI formatting).

Key Features:
- Pure GUI formatting logic - no business logic
- On-demand formatting - zero overhead during simulation
- Extensible design - easy to add new event types
- Lazy formatting support - format only when displaying
- Multiple output formats - display text, analysis data, table rows

Architecture:
- Raw data stored in RawDataObserver as pure dictionaries
- Formatters convert raw data to display format when requested by GUI
- No formatting during simulation - all formatting deferred to GUI layer
- Clean separation allows independent testing and modification

Usage:
    from econsim.gui.formatters import TradeEventFormatter
    
    formatter = TradeEventFormatter()
    raw_trade = {'type': 'trade', 'seller_id': 1, 'buyer_id': 2, ...}
    display_text = formatter.to_display_text(raw_trade)
    analysis_data = formatter.to_analysis_data(raw_trade)

Available Formatters:
- TradeEventFormatter - Trade execution formatting
- ModeChangeEventFormatter - Agent mode transition formatting  
- ResourceCollectionEventFormatter - Resource collection formatting
- DebugLogEventFormatter - Debug log formatting
- PerformanceMonitorEventFormatter - Performance metric formatting

Registry:
- FormatterRegistry - Central registry for all formatters
- Auto-discovery and registration of formatter classes
- Factory methods for getting appropriate formatter by event type
"""

from .base_formatter import EventFormatter
from .registry import FormatterRegistry, get_registry, get_formatter, register_formatter

# Import individual formatters
from .trade_formatter import TradeEventFormatter
from .mode_change_formatter import ModeChangeEventFormatter
from .resource_formatter import ResourceCollectionEventFormatter
from .debug_formatter import DebugLogEventFormatter
from .performance_formatter import PerformanceMonitorEventFormatter

__all__ = [
    # Base classes
    'EventFormatter',
    'FormatterRegistry',
    
    # Registry convenience functions
    'get_registry',
    'get_formatter', 
    'register_formatter',
    
    # Individual formatters
    'TradeEventFormatter',
    'ModeChangeEventFormatter', 
    'ResourceCollectionEventFormatter',
    'DebugLogEventFormatter',
    'PerformanceMonitorEventFormatter'
]

# Package metadata
__version__ = '1.0.0'
__author__ = 'VMT Development Team'
__description__ = 'GUI formatting layer for VMT simulation events'