"""
Trade Event Formatter: GUI display formatting for trade events.

This module provides specialized formatting for trade events, converting raw trade
dictionaries into various GUI-friendly formats while maintaining complete separation
from the raw data storage layer.

Key Features:
- Human-readable trade summaries for display widgets
- Analysis-friendly structures for reporting and statistics
- Table row formatting for grid displays
- Detailed view formatting for inspection panels
- Utility calculation and efficiency metrics
"""

from typing import Dict, List, Any, Union
from .base_formatter import EventFormatter


class TradeEventFormatter(EventFormatter):
    """
    Formatter for trade events from the simulation.
    
    Handles conversion of raw trade dictionaries (from RawDataObserver) into
    GUI-friendly formats for display, analysis, and reporting.
    
    Raw Trade Event Schema:
    {
        'type': 'trade',
        'step': int,
        'seller_id': int,
        'buyer_id': int,
        'give_type': str,
        'take_type': str,
        'delta_u_seller': float,
        'delta_u_buyer': float,
        'trade_location_x': int,
        'trade_location_y': int
    }
    """
    
    def to_display_text(self, raw_event: Dict[str, Any]) -> str:
        """
        Convert raw trade event to human-readable display text.
        
        Args:
            raw_event: Raw trade dictionary from RawDataObserver
            
        Returns:
            Concise, human-readable trade summary
            
        Example:
            "Agent 1 traded wood for food with Agent 2 (+3.8 utility)"
        """
        try:
            seller_id = self._safe_get(raw_event, 'seller_id', '?')
            buyer_id = self._safe_get(raw_event, 'buyer_id', '?')
            give_type = self._safe_get(raw_event, 'give_type', '?')
            take_type = self._safe_get(raw_event, 'take_type', '?')
            
            # Calculate total utility gain
            delta_u_seller = raw_event.get('delta_u_seller', 0.0)
            delta_u_buyer = raw_event.get('delta_u_buyer', 0.0)
            total_utility = delta_u_seller + delta_u_buyer
            
            base_text = f"Agent {seller_id} traded {give_type} for {take_type} with Agent {buyer_id}"
            
            if total_utility != 0.0:
                utility_text = self._format_utility(total_utility)
                return f"{base_text} ({utility_text} total utility)"
            else:
                return base_text
                
        except Exception as e:
            return self._handle_formatting_error(raw_event, e, 'to_display_text')
    
    def to_analysis_data(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert raw trade event to analysis-friendly structure.
        
        Args:
            raw_event: Raw trade dictionary from RawDataObserver
            
        Returns:
            Dictionary with enriched analysis data
            
        Example:
            {
                'participants': [1, 2],
                'items_exchanged': ['wood', 'food'],
                'total_utility_gain': 3.8,
                'trade_efficiency': 0.95,
                'location': (10, 15),
                'step': 42,
                'utility_distribution': {'seller': 1.5, 'buyer': 2.3},
                'trade_type': 'bilateral_exchange'
            }
        """
        try:
            # Extract core trade data
            seller_id = raw_event.get('seller_id', -1)
            buyer_id = raw_event.get('buyer_id', -1)
            give_type = raw_event.get('give_type', '')
            take_type = raw_event.get('take_type', '')
            delta_u_seller = raw_event.get('delta_u_seller', 0.0)
            delta_u_buyer = raw_event.get('delta_u_buyer', 0.0)
            
            # Calculate derived metrics
            total_utility = delta_u_seller + delta_u_buyer
            
            # Trade efficiency (how close to optimal utility distribution)
            if total_utility > 0:
                max_individual = max(abs(delta_u_seller), abs(delta_u_buyer))
                efficiency = min(delta_u_seller, delta_u_buyer) / max_individual if max_individual > 0 else 1.0
                efficiency = max(0.0, min(1.0, efficiency))  # Clamp to [0,1]
            else:
                efficiency = 0.0
            
            # Location data
            location_x = raw_event.get('trade_location_x', -1)
            location_y = raw_event.get('trade_location_y', -1)
            location = (location_x, location_y) if location_x >= 0 and location_y >= 0 else None
            
            # Classify trade type
            trade_type = self._classify_trade_type(give_type, take_type, delta_u_seller, delta_u_buyer)
            
            return {
                'participants': [seller_id, buyer_id],
                'items_exchanged': [give_type, take_type],
                'total_utility_gain': round(total_utility, 3),
                'trade_efficiency': round(efficiency, 3),
                'location': location,
                'step': raw_event.get('step', -1),
                'utility_distribution': {
                    'seller': round(delta_u_seller, 3),
                    'buyer': round(delta_u_buyer, 3)
                },
                'trade_type': trade_type,
                'mutual_benefit': delta_u_seller > 0 and delta_u_buyer > 0
            }
            
        except Exception as e:
            return {
                'error': f"Analysis formatting error: {e}",
                'raw_event': raw_event
            }
    
    def to_table_row(self, raw_event: Dict[str, Any]) -> List[Union[str, int, float]]:
        """
        Convert raw trade event to table row format.
        
        Args:
            raw_event: Raw trade dictionary from RawDataObserver
            
        Returns:
            List of values for table display: [Step, Type, Participants, Exchange, Utility]
            
        Example:
            [42, "Trade", "Agent 1 ↔ Agent 2", "wood → food", 3.8]
        """
        try:
            step = raw_event.get('step', -1)
            seller_id = self._safe_get(raw_event, 'seller_id', '?')
            buyer_id = self._safe_get(raw_event, 'buyer_id', '?')
            give_type = self._safe_get(raw_event, 'give_type', '?')
            take_type = self._safe_get(raw_event, 'take_type', '?')
            
            # Calculate total utility
            delta_u_seller = raw_event.get('delta_u_seller', 0.0)
            delta_u_buyer = raw_event.get('delta_u_buyer', 0.0)
            total_utility = round(delta_u_seller + delta_u_buyer, 2)
            
            participants = f"Agent {seller_id} ↔ Agent {buyer_id}"
            exchange = f"{give_type} → {take_type}"
            
            return [step, "Trade", participants, exchange, total_utility]
            
        except Exception as e:
            step = raw_event.get('step', -1)
            return [step, "Trade", "[Error]", "[Error]", 0.0]
    
    def to_detailed_view(self, raw_event: Dict[str, Any]) -> Dict[str, str]:
        """
        Convert raw trade event to detailed view format.
        
        Args:
            raw_event: Raw trade dictionary from RawDataObserver
            
        Returns:
            Dictionary mapping field names to formatted display values
        """
        try:
            detailed = {}
            
            # Basic event info
            detailed['Event Type'] = 'Trade Execution'
            detailed['Step'] = str(raw_event.get('step', 'Unknown'))
            
            # Participants
            seller_id = raw_event.get('seller_id', -1)
            buyer_id = raw_event.get('buyer_id', -1)
            detailed['Seller'] = self._format_agent_id(seller_id)
            detailed['Buyer'] = self._format_agent_id(buyer_id)
            
            # Items exchanged
            give_type = raw_event.get('give_type', 'Unknown')
            take_type = raw_event.get('take_type', 'Unknown')
            detailed['Items Given'] = give_type.capitalize()
            detailed['Items Received'] = take_type.capitalize()
            
            # Utility analysis
            delta_u_seller = raw_event.get('delta_u_seller', 0.0)
            delta_u_buyer = raw_event.get('delta_u_buyer', 0.0)
            total_utility = delta_u_seller + delta_u_buyer
            
            detailed['Seller Utility Change'] = self._format_utility(delta_u_seller)
            detailed['Buyer Utility Change'] = self._format_utility(delta_u_buyer)
            detailed['Total Utility Generated'] = self._format_utility(total_utility)
            
            # Location
            location_x = raw_event.get('trade_location_x', -1)
            location_y = raw_event.get('trade_location_y', -1)
            detailed['Trade Location'] = self._format_location(location_x, location_y)
            
            # Analysis
            trade_type = self._classify_trade_type(give_type, take_type, delta_u_seller, delta_u_buyer)
            detailed['Trade Classification'] = trade_type.replace('_', ' ').title()
            
            mutual_benefit = delta_u_seller > 0 and delta_u_buyer > 0
            detailed['Mutual Benefit'] = 'Yes' if mutual_benefit else 'No'
            
            return detailed
            
        except Exception as e:
            return {
                'Event Type': 'Trade Execution',
                'Error': f'Formatting error: {e}',
                'Raw Data': str(raw_event)
            }
    
    def get_table_headers(self) -> List[str]:
        """
        Get table column headers for trade events.
        
        Returns:
            List of column header strings
        """
        return ["Step", "Event Type", "Participants", "Exchange", "Total Utility"]
    
    def get_supported_event_type(self) -> str:
        """
        Get the event type this formatter supports.
        
        Returns:
            Event type string: 'trade'
        """
        return 'trade'
    
    # ============================================================================
    # TRADE-SPECIFIC HELPER METHODS
    # ============================================================================
    
    def _classify_trade_type(self, give_type: str, take_type: str, 
                           delta_u_seller: float, delta_u_buyer: float) -> str:
        """
        Classify the type of trade based on items and utility changes.
        
        Args:
            give_type: Resource type given by seller
            take_type: Resource type received by seller
            delta_u_seller: Utility change for seller
            delta_u_buyer: Utility change for buyer
            
        Returns:
            Trade classification string
        """
        # Check for mutual benefit
        if delta_u_seller > 0 and delta_u_buyer > 0:
            if abs(delta_u_seller - delta_u_buyer) < 0.1:
                return 'balanced_mutual_benefit'
            elif delta_u_seller > delta_u_buyer:
                return 'seller_favored_trade'
            else:
                return 'buyer_favored_trade'
        elif delta_u_seller > 0 and delta_u_buyer <= 0:
            return 'seller_advantage_trade'
        elif delta_u_seller <= 0 and delta_u_buyer > 0:
            return 'buyer_advantage_trade'
        else:
            return 'zero_sum_trade'
    
    def calculate_trade_metrics(self, raw_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate aggregate metrics across multiple trade events.
        
        Args:
            raw_events: List of raw trade dictionaries
            
        Returns:
            Dictionary with aggregate trade metrics
        """
        if not raw_events:
            return {
                'total_trades': 0,
                'total_utility_generated': 0.0,
                'average_utility_per_trade': 0.0,
                'unique_participants': 0,
                'trade_efficiency': 0.0
            }
        
        total_utility = 0.0
        participants = set()
        efficiency_sum = 0.0
        
        for event in raw_events:
            # Utility calculation
            delta_u_seller = event.get('delta_u_seller', 0.0)
            delta_u_buyer = event.get('delta_u_buyer', 0.0)
            total_utility += delta_u_seller + delta_u_buyer
            
            # Participants tracking
            participants.add(event.get('seller_id', -1))
            participants.add(event.get('buyer_id', -1))
            
            # Efficiency calculation
            total_individual = abs(delta_u_seller) + abs(delta_u_buyer)
            if total_individual > 0:
                mutual_benefit = min(delta_u_seller, delta_u_buyer) if delta_u_seller > 0 and delta_u_buyer > 0 else 0
                efficiency_sum += mutual_benefit / total_individual
        
        # Remove invalid participant IDs
        participants.discard(-1)
        
        return {
            'total_trades': len(raw_events),
            'total_utility_generated': round(total_utility, 3),
            'average_utility_per_trade': round(total_utility / len(raw_events), 3),
            'unique_participants': len(participants),
            'average_efficiency': round(efficiency_sum / len(raw_events), 3) if raw_events else 0.0,
            'participants_list': sorted(list(participants))
        }