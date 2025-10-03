"""
Data Translator: GUI translation layer for raw simulation data.

This module converts raw simulation data (dictionaries) to human-readable format
for GUI consumption. Translation is performed only when needed, not during simulation.

Key Features:
- Converts raw event dictionaries to human-readable format
- Provides structured descriptions for GUI display
- Supports filtering and analysis of translated events
- Maintains performance by translating only when requested
- Extensible design for new event types

Usage:
    translator = DataTranslator()
    raw_events = observer.get_all_events()
    translated_events = [translator.translate_event(event) for event in raw_events]
    
    # Or translate specific event types
    trade_events = observer.get_events_by_type("trade")
    human_readable = [translator.translate_trade_event(event) for event in trade_events]
"""

from __future__ import annotations

import time
from typing import Dict, List, Any, Optional, Union


class DataTranslator:
    """Translates raw simulation data to human-readable format for GUI consumption.
    
    This translator converts raw event dictionaries (from RawDataObserver) into
    human-readable format with structured descriptions, formatted text, and
    analysis-friendly data structures.
    
    Architecture:
    - Input: Raw event dictionaries from RawDataObserver
    - Output: Human-readable dictionaries with descriptions and formatted data
    - Performance: Translation only when needed (GUI display, analysis)
    - Extensibility: Easy to add new event types and translation formats
    """
    
    def __init__(self) -> None:
        """Initialize data translator."""
        self._translation_cache: Dict[str, Dict[str, Any]] = {}  # Optional caching
        self._cache_enabled: bool = False  # Disabled by default for simplicity
    
    # ============================================================================
    # SPECIFIC EVENT TRANSLATION METHODS
    # ============================================================================
    
    def translate_trade_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw trade data to human-readable format.
        
        Args:
            raw_event: Raw trade event dictionary from RawDataObserver
            
        Returns:
            Human-readable trade event dictionary with descriptions and formatted data
        """
        return {
            'event_type': 'Trade Execution',
            'step': raw_event.get('step', 0),
            'seller_id': raw_event.get('seller_id', -1),
            'buyer_id': raw_event.get('buyer_id', -1),
            'give_type': raw_event.get('give_type', 'unknown'),
            'take_type': raw_event.get('take_type', 'unknown'),
            'delta_u_seller': raw_event.get('delta_u_seller', 0.0),
            'delta_u_buyer': raw_event.get('delta_u_buyer', 0.0),
            'trade_location_x': raw_event.get('trade_location_x', -1),
            'trade_location_y': raw_event.get('trade_location_y', -1),
            'description': self._format_trade_description(raw_event),
            'summary': f"Agent {raw_event.get('seller_id', '?')} traded {raw_event.get('give_type', '?')} for {raw_event.get('take_type', '?')} with Agent {raw_event.get('buyer_id', '?')}",
            'utility_summary': self._format_trade_utility_summary(raw_event),
            'location_summary': self._format_trade_location_summary(raw_event),
            'raw_data': raw_event  # Keep original for debugging
        }
    
    def translate_mode_change_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw mode change data to human-readable format.
        
        Args:
            raw_event: Raw mode change event dictionary from RawDataObserver
            
        Returns:
            Human-readable mode change event dictionary with descriptions and formatted data
        """
        return {
            'event_type': 'Agent Mode Change',
            'step': raw_event.get('step', 0),
            'agent_id': raw_event.get('agent_id', -1),
            'old_mode': raw_event.get('old_mode', 'unknown'),
            'new_mode': raw_event.get('new_mode', 'unknown'),
            'reason': raw_event.get('reason', ''),
            'description': self._format_mode_change_description(raw_event),
            'summary': f"Agent {raw_event.get('agent_id', '?')} changed from {raw_event.get('old_mode', '?')} to {raw_event.get('new_mode', '?')}",
            'reason_summary': self._format_mode_change_reason_summary(raw_event),
            'transition_type': self._classify_mode_transition(raw_event),
            'raw_data': raw_event  # Keep original for debugging
        }
    
    def translate_resource_collection_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw resource collection data to human-readable format.
        
        Args:
            raw_event: Raw resource collection event dictionary from RawDataObserver
            
        Returns:
            Human-readable resource collection event dictionary with descriptions and formatted data
        """
        return {
            'event_type': 'Resource Collection',
            'step': raw_event.get('step', 0),
            'agent_id': raw_event.get('agent_id', -1),
            'x': raw_event.get('x', -1),
            'y': raw_event.get('y', -1),
            'resource_type': raw_event.get('resource_type', 'unknown'),
            'amount_collected': raw_event.get('amount_collected', 1),
            'utility_gained': raw_event.get('utility_gained', 0.0),
            'carrying_after': raw_event.get('carrying_after', {}),
            'description': self._format_resource_collection_description(raw_event),
            'summary': f"Agent {raw_event.get('agent_id', '?')} collected {raw_event.get('amount_collected', 1)} {raw_event.get('resource_type', '?')} at ({raw_event.get('x', '?')}, {raw_event.get('y', '?')})",
            'location_summary': f"Position: ({raw_event.get('x', '?')}, {raw_event.get('y', '?')})",
            'inventory_summary': self._format_inventory_summary(raw_event.get('carrying_after', {})),
            'utility_summary': self._format_utility_summary(raw_event.get('utility_gained', 0.0)),
            'raw_data': raw_event  # Keep original for debugging
        }
    
    def translate_debug_log_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw debug log data to human-readable format.
        
        Args:
            raw_event: Raw debug log event dictionary from RawDataObserver
            
        Returns:
            Human-readable debug log event dictionary with descriptions and formatted data
        """
        return {
            'event_type': 'Debug Log',
            'step': raw_event.get('step', 0),
            'category': raw_event.get('category', 'UNKNOWN'),
            'message': raw_event.get('message', ''),
            'agent_id': raw_event.get('agent_id', -1),
            'description': self._format_debug_log_description(raw_event),
            'summary': f"[{raw_event.get('category', '?')}] {raw_event.get('message', '')}",
            'category_summary': self._format_debug_category_summary(raw_event.get('category', 'UNKNOWN')),
            'agent_context': self._format_agent_context_summary(raw_event.get('agent_id', -1)),
            'severity': self._classify_debug_severity(raw_event.get('category', 'UNKNOWN')),
            'raw_data': raw_event  # Keep original for debugging
        }
    
    def translate_performance_monitor_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw performance monitor data to human-readable format.
        
        Args:
            raw_event: Raw performance monitor event dictionary from RawDataObserver
            
        Returns:
            Human-readable performance monitor event dictionary with descriptions and formatted data
        """
        return {
            'event_type': 'Performance Monitor',
            'step': raw_event.get('step', 0),
            'metric_name': raw_event.get('metric_name', 'unknown'),
            'metric_value': raw_event.get('metric_value', 0.0),
            'threshold_exceeded': raw_event.get('threshold_exceeded', False),
            'details': raw_event.get('details', ''),
            'description': self._format_performance_monitor_description(raw_event),
            'summary': f"{raw_event.get('metric_name', '?')}: {raw_event.get('metric_value', 0.0):.2f}",
            'status_summary': self._format_performance_status_summary(raw_event),
            'value_summary': self._format_performance_value_summary(raw_event),
            'threshold_summary': self._format_threshold_summary(raw_event),
            'raw_data': raw_event  # Keep original for debugging
        }
    
    def translate_agent_decision_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw agent decision data to human-readable format.
        
        Args:
            raw_event: Raw agent decision event dictionary from RawDataObserver
            
        Returns:
            Human-readable agent decision event dictionary with descriptions and formatted data
        """
        return {
            'event_type': 'Agent Decision',
            'step': raw_event.get('step', 0),
            'agent_id': raw_event.get('agent_id', -1),
            'decision_type': raw_event.get('decision_type', 'unknown'),
            'decision_details': raw_event.get('decision_details', ''),
            'utility_delta': raw_event.get('utility_delta', 0.0),
            'position_x': raw_event.get('position_x', -1),
            'position_y': raw_event.get('position_y', -1),
            'description': self._format_agent_decision_description(raw_event),
            'summary': f"Agent {raw_event.get('agent_id', '?')} made {raw_event.get('decision_type', '?')} decision",
            'decision_summary': self._format_decision_summary(raw_event),
            'utility_summary': self._format_utility_summary(raw_event.get('utility_delta', 0.0)),
            'position_summary': self._format_position_summary(raw_event.get('position_x', -1), raw_event.get('position_y', -1)),
            'raw_data': raw_event  # Keep original for debugging
        }
    
    def translate_resource_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw resource event data to human-readable format.
        
        Args:
            raw_event: Raw resource event dictionary from RawDataObserver
            
        Returns:
            Human-readable resource event dictionary with descriptions and formatted data
        """
        return {
            'event_type': 'Resource Event',
            'step': raw_event.get('step', 0),
            'event_type_detail': raw_event.get('event_type_detail', 'unknown'),
            'position_x': raw_event.get('position_x', -1),
            'position_y': raw_event.get('position_y', -1),
            'resource_type': raw_event.get('resource_type', 'unknown'),
            'amount': raw_event.get('amount', 1),
            'agent_id': raw_event.get('agent_id', -1),
            'description': self._format_resource_event_description(raw_event),
            'summary': f"{raw_event.get('event_type_detail', '?')} {raw_event.get('amount', 1)} {raw_event.get('resource_type', '?')} at ({raw_event.get('position_x', '?')}, {raw_event.get('position_y', '?')})",
            'event_summary': self._format_resource_event_summary(raw_event),
            'location_summary': self._format_position_summary(raw_event.get('position_x', -1), raw_event.get('position_y', -1)),
            'agent_context': self._format_agent_context_summary(raw_event.get('agent_id', -1)),
            'raw_data': raw_event  # Keep original for debugging
        }
    
    def translate_economic_decision_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw economic decision data to human-readable format.
        
        Args:
            raw_event: Raw economic decision event dictionary from RawDataObserver
            
        Returns:
            Human-readable economic decision event dictionary with descriptions and formatted data
        """
        return {
            'event_type': 'Economic Decision',
            'step': raw_event.get('step', 0),
            'agent_id': raw_event.get('agent_id', -1),
            'decision_type': raw_event.get('decision_type', 'unknown'),
            'decision_context': raw_event.get('decision_context', ''),
            'utility_before': raw_event.get('utility_before', 0.0),
            'utility_after': raw_event.get('utility_after', 0.0),
            'utility_delta': raw_event.get('utility_delta', 0.0),
            'opportunity_cost': raw_event.get('opportunity_cost', 0.0),
            'alternatives_considered': raw_event.get('alternatives_considered', 0),
            'decision_time_ms': raw_event.get('decision_time_ms', 0.0),
            'position_x': raw_event.get('position_x', -1),
            'position_y': raw_event.get('position_y', -1),
            'description': self._format_economic_decision_description(raw_event),
            'summary': f"Agent {raw_event.get('agent_id', '?')} made {raw_event.get('decision_type', '?')} economic decision",
            'utility_analysis': self._format_economic_utility_analysis(raw_event),
            'decision_analysis': self._format_economic_decision_analysis(raw_event),
            'performance_analysis': self._format_economic_performance_analysis(raw_event),
            'raw_data': raw_event  # Keep original for debugging
        }
    
    def translate_gui_display_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw GUI display data to human-readable format.
        
        Args:
            raw_event: Raw GUI display event dictionary from RawDataObserver
            
        Returns:
            Human-readable GUI display event dictionary with descriptions and formatted data
        """
        return {
            'event_type': 'GUI Display',
            'step': raw_event.get('step', 0),
            'display_type': raw_event.get('display_type', 'unknown'),
            'element_id': raw_event.get('element_id', ''),
            'data': raw_event.get('data', {}),
            'description': self._format_gui_display_description(raw_event),
            'summary': f"GUI {raw_event.get('display_type', '?')} update for {raw_event.get('element_id', '?')}",
            'display_summary': self._format_gui_display_summary(raw_event),
            'data_summary': self._format_gui_data_summary(raw_event.get('data', {})),
            'raw_data': raw_event  # Keep original for debugging
        }
    
    # ============================================================================
    # GENERIC TRANSLATION METHOD
    # ============================================================================
    
    def translate_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Generic method to translate any event type to human-readable format.
        
        Args:
            raw_event: Raw event dictionary from RawDataObserver
            
        Returns:
            Human-readable event dictionary with descriptions and formatted data
        """
        event_type = raw_event.get('type', 'unknown')
        
        # Route to specific translation method based on event type
        translation_methods = {
            'trade': self.translate_trade_event,
            'mode_change': self.translate_mode_change_event,
            'resource_collection': self.translate_resource_collection_event,
            'debug_log': self.translate_debug_log_event,
            'performance_monitor': self.translate_performance_monitor_event,
            'agent_decision': self.translate_agent_decision_event,
            'resource_event': self.translate_resource_event,
            'economic_decision': self.translate_economic_decision_event,
            'gui_display': self.translate_gui_display_event
        }
        
        # Get appropriate translation method
        translate_method = translation_methods.get(event_type)
        if translate_method:
            return translate_method(raw_event)
        else:
            # Fallback for unknown event types
            return self._translate_unknown_event(raw_event)
    
    # ============================================================================
    # BATCH TRANSLATION METHODS
    # ============================================================================
    
    def translate_events(self, raw_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Translate a list of raw events to human-readable format.
        
        Args:
            raw_events: List of raw event dictionaries from RawDataObserver
            
        Returns:
            List of human-readable event dictionaries
        """
        return [self.translate_event(event) for event in raw_events]
    
    def translate_events_by_type(self, raw_events: List[Dict[str, Any]], event_type: str) -> List[Dict[str, Any]]:
        """Translate events of a specific type to human-readable format.
        
        Args:
            raw_events: List of raw event dictionaries from RawDataObserver
            event_type: Type of events to translate (e.g., 'trade', 'mode_change')
            
        Returns:
            List of human-readable event dictionaries of the specified type
        """
        filtered_events = [event for event in raw_events if event.get('type') == event_type]
        return [self.translate_event(event) for event in filtered_events]
    
    def translate_events_by_step(self, raw_events: List[Dict[str, Any]], step: int) -> List[Dict[str, Any]]:
        """Translate events from a specific step to human-readable format.
        
        Args:
            raw_events: List of raw event dictionaries from RawDataObserver
            step: Simulation step number
            
        Returns:
            List of human-readable event dictionaries from the specified step
        """
        filtered_events = [event for event in raw_events if event.get('step') == step]
        return [self.translate_event(event) for event in filtered_events]
    
    # ============================================================================
    # HUMAN-READABLE DESCRIPTION METHODS
    # ============================================================================
    
    def get_human_readable_description(self, raw_event: Dict[str, Any]) -> str:
        """Get a human-readable description of an event for GUI display.
        
        Args:
            raw_event: Raw event dictionary from RawDataObserver
            
        Returns:
            Human-readable description string suitable for GUI display
        """
        translated_event = self.translate_event(raw_event)
        return translated_event.get('description', 'Unknown event')
    
    def get_human_readable_summary(self, raw_event: Dict[str, Any]) -> str:
        """Get a concise human-readable summary of an event.
        
        Args:
            raw_event: Raw event dictionary from RawDataObserver
            
        Returns:
            Concise human-readable summary string
        """
        translated_event = self.translate_event(raw_event)
        return translated_event.get('summary', 'Unknown event')
    
    def get_human_readable_descriptions(self, raw_events: List[Dict[str, Any]]) -> List[str]:
        """Get human-readable descriptions for a list of events.
        
        Args:
            raw_events: List of raw event dictionaries from RawDataObserver
            
        Returns:
            List of human-readable description strings
        """
        return [self.get_human_readable_description(event) for event in raw_events]
    
    # ============================================================================
    # FORMATTING HELPER METHODS
    # ============================================================================
    
    def _format_trade_description(self, raw_event: Dict[str, Any]) -> str:
        """Format detailed trade description."""
        seller_id = raw_event.get('seller_id', '?')
        buyer_id = raw_event.get('buyer_id', '?')
        give_type = raw_event.get('give_type', '?')
        take_type = raw_event.get('take_type', '?')
        delta_u_seller = raw_event.get('delta_u_seller', 0.0)
        delta_u_buyer = raw_event.get('delta_u_buyer', 0.0)
        
        description = f"Agent {seller_id} traded {give_type} for {take_type} with Agent {buyer_id}"
        
        if delta_u_seller != 0.0 or delta_u_buyer != 0.0:
            description += f" (Seller utility: {delta_u_seller:+.2f}, Buyer utility: {delta_u_buyer:+.2f})"
        
        trade_x = raw_event.get('trade_location_x', -1)
        trade_y = raw_event.get('trade_location_y', -1)
        if trade_x != -1 and trade_y != -1:
            description += f" at location ({trade_x}, {trade_y})"
        
        return description
    
    def _format_trade_utility_summary(self, raw_event: Dict[str, Any]) -> str:
        """Format trade utility summary."""
        delta_u_seller = raw_event.get('delta_u_seller', 0.0)
        delta_u_buyer = raw_event.get('delta_u_buyer', 0.0)
        
        if delta_u_seller == 0.0 and delta_u_buyer == 0.0:
            return "No utility change recorded"
        
        return f"Seller: {delta_u_seller:+.2f}, Buyer: {delta_u_buyer:+.2f}"
    
    def _format_trade_location_summary(self, raw_event: Dict[str, Any]) -> str:
        """Format trade location summary."""
        trade_x = raw_event.get('trade_location_x', -1)
        trade_y = raw_event.get('trade_location_y', -1)
        
        if trade_x == -1 or trade_y == -1:
            return "Location not recorded"
        
        return f"Trade location: ({trade_x}, {trade_y})"
    
    def _format_mode_change_description(self, raw_event: Dict[str, Any]) -> str:
        """Format detailed mode change description."""
        agent_id = raw_event.get('agent_id', '?')
        old_mode = raw_event.get('old_mode', '?')
        new_mode = raw_event.get('new_mode', '?')
        reason = raw_event.get('reason', '')
        
        description = f"Agent {agent_id} changed from {old_mode} to {new_mode}"
        
        if reason:
            description += f": {reason}"
        
        return description
    
    def _format_mode_change_reason_summary(self, raw_event: Dict[str, Any]) -> str:
        """Format mode change reason summary."""
        reason = raw_event.get('reason', '')
        
        if not reason:
            return "No reason provided"
        
        return f"Reason: {reason}"
    
    def _classify_mode_transition(self, raw_event: Dict[str, Any]) -> str:
        """Classify the type of mode transition."""
        old_mode = raw_event.get('old_mode', '').lower()
        new_mode = raw_event.get('new_mode', '').lower()
        
        # Common transitions
        if old_mode == 'foraging' and new_mode == 'trading':
            return 'Forage to Trade'
        elif old_mode == 'trading' and new_mode == 'foraging':
            return 'Trade to Forage'
        elif old_mode == 'idle' and new_mode in ['foraging', 'trading']:
            return 'Activation'
        elif new_mode == 'idle':
            return 'Deactivation'
        else:
            return f'{old_mode.title()} to {new_mode.title()}'
    
    def _format_resource_collection_description(self, raw_event: Dict[str, Any]) -> str:
        """Format detailed resource collection description."""
        agent_id = raw_event.get('agent_id', '?')
        resource_type = raw_event.get('resource_type', '?')
        amount = raw_event.get('amount_collected', 1)
        x = raw_event.get('x', '?')
        y = raw_event.get('y', '?')
        utility_gained = raw_event.get('utility_gained', 0.0)
        
        description = f"Agent {agent_id} collected {amount} {resource_type} at ({x}, {y})"
        
        if utility_gained != 0.0:
            description += f" (utility gained: {utility_gained:+.2f})"
        
        return description
    
    def _format_inventory_summary(self, carrying_after: Dict[str, int]) -> str:
        """Format inventory summary."""
        if not carrying_after:
            return "Empty inventory"
        
        items = [f"{amount} {resource_type}" for resource_type, amount in carrying_after.items()]
        return f"Inventory: {', '.join(items)}"
    
    def _format_utility_summary(self, utility: float) -> str:
        """Format utility summary."""
        if utility == 0.0:
            return "No utility change"
        elif utility > 0.0:
            return f"Utility gained: {utility:+.2f}"
        else:
            return f"Utility lost: {utility:+.2f}"
    
    def _format_debug_log_description(self, raw_event: Dict[str, Any]) -> str:
        """Format detailed debug log description."""
        category = raw_event.get('category', 'UNKNOWN')
        message = raw_event.get('message', '')
        agent_id = raw_event.get('agent_id', -1)
        
        description = f"[{category}] {message}"
        
        if agent_id != -1:
            description += f" (Agent {agent_id})"
        
        return description
    
    def _format_debug_category_summary(self, category: str) -> str:
        """Format debug category summary."""
        category_descriptions = {
            'TRADE': 'Trading activities',
            'MODE': 'Agent mode changes',
            'ECON': 'Economic decisions',
            'SPATIAL': 'Spatial/movement decisions',
            'UTILITY': 'Utility calculations',
            'SIMULATION': 'Simulation state',
            'PERFORMANCE': 'Performance metrics',
            'DEBUG': 'General debugging'
        }
        
        return category_descriptions.get(category, f'Category: {category}')
    
    def _format_agent_context_summary(self, agent_id: int) -> str:
        """Format agent context summary."""
        if agent_id == -1:
            return "No agent context"
        return f"Agent {agent_id}"
    
    def _classify_debug_severity(self, category: str) -> str:
        """Classify debug message severity."""
        high_severity = ['ERROR', 'WARNING', 'CRITICAL']
        medium_severity = ['TRADE', 'MODE', 'ECON']
        low_severity = ['DEBUG', 'INFO', 'VERBOSE']
        
        if category in high_severity:
            return 'High'
        elif category in medium_severity:
            return 'Medium'
        elif category in low_severity:
            return 'Low'
        else:
            return 'Unknown'
    
    def _format_performance_monitor_description(self, raw_event: Dict[str, Any]) -> str:
        """Format detailed performance monitor description."""
        metric_name = raw_event.get('metric_name', 'unknown')
        metric_value = raw_event.get('metric_value', 0.0)
        threshold_exceeded = raw_event.get('threshold_exceeded', False)
        details = raw_event.get('details', '')
        
        description = f"Performance metric {metric_name}: {metric_value:.2f}"
        
        if threshold_exceeded:
            description += " (THRESHOLD EXCEEDED)"
        
        if details:
            description += f" - {details}"
        
        return description
    
    def _format_performance_status_summary(self, raw_event: Dict[str, Any]) -> str:
        """Format performance status summary."""
        threshold_exceeded = raw_event.get('threshold_exceeded', False)
        
        if threshold_exceeded:
            return "⚠️ Threshold exceeded"
        else:
            return "✅ Within normal range"
    
    def _format_performance_value_summary(self, raw_event: Dict[str, Any]) -> str:
        """Format performance value summary."""
        metric_name = raw_event.get('metric_name', 'unknown')
        metric_value = raw_event.get('metric_value', 0.0)
        
        return f"{metric_name}: {metric_value:.2f}"
    
    def _format_threshold_summary(self, raw_event: Dict[str, Any]) -> str:
        """Format threshold summary."""
        threshold_exceeded = raw_event.get('threshold_exceeded', False)
        details = raw_event.get('details', '')
        
        if threshold_exceeded:
            return f"Threshold exceeded: {details}" if details else "Threshold exceeded"
        else:
            return "Within threshold"
    
    def _format_agent_decision_description(self, raw_event: Dict[str, Any]) -> str:
        """Format detailed agent decision description."""
        agent_id = raw_event.get('agent_id', '?')
        decision_type = raw_event.get('decision_type', 'unknown')
        decision_details = raw_event.get('decision_details', '')
        utility_delta = raw_event.get('utility_delta', 0.0)
        
        description = f"Agent {agent_id} made {decision_type} decision"
        
        if decision_details:
            description += f": {decision_details}"
        
        if utility_delta != 0.0:
            description += f" (utility change: {utility_delta:+.2f})"
        
        return description
    
    def _format_decision_summary(self, raw_event: Dict[str, Any]) -> str:
        """Format decision summary."""
        decision_type = raw_event.get('decision_type', 'unknown')
        decision_details = raw_event.get('decision_details', '')
        
        if decision_details:
            return f"{decision_type}: {decision_details}"
        else:
            return f"{decision_type} decision"
    
    def _format_position_summary(self, x: int, y: int) -> str:
        """Format position summary."""
        if x == -1 or y == -1:
            return "Position not recorded"
        return f"Position: ({x}, {y})"
    
    def _format_resource_event_description(self, raw_event: Dict[str, Any]) -> str:
        """Format detailed resource event description."""
        event_type_detail = raw_event.get('event_type_detail', 'unknown')
        resource_type = raw_event.get('resource_type', 'unknown')
        amount = raw_event.get('amount', 1)
        x = raw_event.get('position_x', '?')
        y = raw_event.get('position_y', '?')
        agent_id = raw_event.get('agent_id', -1)
        
        description = f"{event_type_detail.title()} {amount} {resource_type} at ({x}, {y})"
        
        if agent_id != -1:
            description += f" (Agent {agent_id})"
        
        return description
    
    def _format_resource_event_summary(self, raw_event: Dict[str, Any]) -> str:
        """Format resource event summary."""
        event_type_detail = raw_event.get('event_type_detail', 'unknown')
        resource_type = raw_event.get('resource_type', 'unknown')
        amount = raw_event.get('amount', 1)
        
        return f"{event_type_detail.title()} {amount} {resource_type}"
    
    def _format_economic_decision_description(self, raw_event: Dict[str, Any]) -> str:
        """Format detailed economic decision description."""
        agent_id = raw_event.get('agent_id', '?')
        decision_type = raw_event.get('decision_type', 'unknown')
        decision_context = raw_event.get('decision_context', '')
        utility_delta = raw_event.get('utility_delta', 0.0)
        alternatives_considered = raw_event.get('alternatives_considered', 0)
        
        description = f"Agent {agent_id} made {decision_type} economic decision"
        
        if decision_context:
            description += f": {decision_context}"
        
        if utility_delta != 0.0:
            description += f" (utility change: {utility_delta:+.2f})"
        
        if alternatives_considered > 0:
            description += f" (considered {alternatives_considered} alternatives)"
        
        return description
    
    def _format_economic_utility_analysis(self, raw_event: Dict[str, Any]) -> str:
        """Format economic utility analysis."""
        utility_before = raw_event.get('utility_before', 0.0)
        utility_after = raw_event.get('utility_after', 0.0)
        utility_delta = raw_event.get('utility_delta', 0.0)
        opportunity_cost = raw_event.get('opportunity_cost', 0.0)
        
        analysis = f"Utility: {utility_before:.2f} → {utility_after:.2f} (Δ{utility_delta:+.2f})"
        
        if opportunity_cost > 0.0:
            analysis += f", Opportunity cost: {opportunity_cost:.2f}"
        
        return analysis
    
    def _format_economic_decision_analysis(self, raw_event: Dict[str, Any]) -> str:
        """Format economic decision analysis."""
        decision_type = raw_event.get('decision_type', 'unknown')
        alternatives_considered = raw_event.get('alternatives_considered', 0)
        
        analysis = f"Decision type: {decision_type}"
        
        if alternatives_considered > 0:
            analysis += f", Alternatives considered: {alternatives_considered}"
        
        return analysis
    
    def _format_economic_performance_analysis(self, raw_event: Dict[str, Any]) -> str:
        """Format economic performance analysis."""
        decision_time_ms = raw_event.get('decision_time_ms', 0.0)
        
        if decision_time_ms > 0.0:
            return f"Decision time: {decision_time_ms:.2f}ms"
        else:
            return "Decision time not recorded"
    
    def _format_gui_display_description(self, raw_event: Dict[str, Any]) -> str:
        """Format detailed GUI display description."""
        display_type = raw_event.get('display_type', 'unknown')
        element_id = raw_event.get('element_id', '')
        data = raw_event.get('data', {})
        
        description = f"GUI {display_type} update for {element_id}"
        
        if data:
            description += f" with {len(data)} data fields"
        
        return description
    
    def _format_gui_display_summary(self, raw_event: Dict[str, Any]) -> str:
        """Format GUI display summary."""
        display_type = raw_event.get('display_type', 'unknown')
        element_id = raw_event.get('element_id', '')
        
        return f"{display_type.title()} for {element_id}"
    
    def _format_gui_data_summary(self, data: Dict[str, Any]) -> str:
        """Format GUI data summary."""
        if not data:
            return "No data"
        
        return f"Data fields: {', '.join(data.keys())}"
    
    def _translate_unknown_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback translation for unknown event types."""
        return {
            'event_type': 'Unknown Event',
            'step': raw_event.get('step', 0),
            'description': f"Unknown event type: {raw_event.get('type', 'unknown')}",
            'summary': f"Unknown event at step {raw_event.get('step', 0)}",
            'raw_data': raw_event
        }
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def clear_cache(self) -> None:
        """Clear translation cache if enabled."""
        if self._cache_enabled:
            self._translation_cache.clear()
    
    def enable_cache(self, enabled: bool = True) -> None:
        """Enable or disable translation caching."""
        self._cache_enabled = enabled
        if not enabled:
            self.clear_cache()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get translation cache statistics."""
        return {
            'cache_enabled': self._cache_enabled,
            'cache_size': len(self._translation_cache),
            'cache_hit_rate': 0.0  # Would need hit/miss tracking for real stats
        }
    
    def __repr__(self) -> str:
        """String representation of translator state."""
        cache_stats = self.get_cache_stats()
        return (f"DataTranslator(cache_enabled={cache_stats['cache_enabled']}, "
                f"cache_size={cache_stats['cache_size']})")
