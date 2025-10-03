"""
Resource Collection Event Formatter: GUI display formatting for resource collection events.

This module provides specialized formatting for resource collection events, converting
raw collection dictionaries into various GUI-friendly formats while maintaining
complete separation from the raw data storage layer.

Key Features:
- Human-readable collection event summaries
- Resource efficiency and rate analysis
- Inventory tracking and capacity analysis
- Location-based collection pattern analysis
"""

from typing import Dict, List, Any, Union
from .base_formatter import EventFormatter


class ResourceCollectionEventFormatter(EventFormatter):
    """
    Formatter for resource collection events from the simulation.
    
    Handles conversion of raw resource collection dictionaries (from RawDataObserver) 
    into GUI-friendly formats for display, analysis, and resource management tracking.
    
    Raw Resource Collection Event Schema:
    {
        'type': 'resource_collection',
        'step': int,
        'agent_id': int,
        'x': int,
        'y': int,
        'resource_type': str,
        'amount_collected': int,
        'utility_gained': float,
        'carrying_after': dict  # Inventory state after collection
    }
    """
    
    # Resource type display mappings
    RESOURCE_DISPLAY_NAMES = {
        'wood': 'Wood',
        'stone': 'Stone',
        'food': 'Food',
        'water': 'Water',
        'metal': 'Metal',
        'energy': 'Energy'
    }
    
    # Resource units for display
    RESOURCE_UNITS = {
        'wood': 'logs',
        'stone': 'chunks',
        'food': 'units',
        'water': 'liters',
        'metal': 'ore',
        'energy': 'units'
    }
    
    def to_display_text(self, raw_event: Dict[str, Any]) -> str:
        """
        Convert raw resource collection event to human-readable display text.
        
        Args:
            raw_event: Raw resource collection dictionary from RawDataObserver
            
        Returns:
            Concise, human-readable collection summary
            
        Example:
            "Agent 5 collected 2 Wood at (10, 15) (+1.8 utility)"
        """
        try:
            agent_id = self._safe_get(raw_event, 'agent_id', '?')
            resource_type = self._safe_get(raw_event, 'resource_type', 'unknown')
            amount = raw_event.get('amount_collected', 0)
            x = raw_event.get('x', -1)
            y = raw_event.get('y', -1)
            utility_gained = raw_event.get('utility_gained', 0.0)
            
            # Format resource type for display
            resource_display = self._format_resource_type(resource_type)
            
            # Format location
            location_str = self._format_location(x, y)
            
            base_text = f"Agent {agent_id} collected {amount} {resource_display} at {location_str}"
            
            if utility_gained != 0.0:
                utility_str = self._format_utility(utility_gained)
                return f"{base_text} ({utility_str} utility)"
            else:
                return base_text
                
        except Exception as e:
            return self._handle_formatting_error(raw_event, e, 'to_display_text')
    
    def to_analysis_data(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert raw resource collection event to analysis-friendly structure.
        
        Args:
            raw_event: Raw resource collection dictionary from RawDataObserver
            
        Returns:
            Dictionary with enriched analysis data
            
        Example:
            {
                'agent_id': 5,
                'resource': {'type': 'wood', 'amount': 2},
                'location': (10, 15),
                'efficiency': 0.9,
                'utility_per_unit': 0.9,
                'inventory_status': 'moderate',
                'collection_rate': 2.0
            }
        """
        try:
            agent_id = raw_event.get('agent_id', -1)
            resource_type = raw_event.get('resource_type', '')
            amount_collected = raw_event.get('amount_collected', 0)
            utility_gained = raw_event.get('utility_gained', 0.0)
            x = raw_event.get('x', -1)
            y = raw_event.get('y', -1)
            carrying_after = raw_event.get('carrying_after', {})
            step = raw_event.get('step', -1)
            
            # Calculate efficiency metrics
            utility_per_unit = utility_gained / amount_collected if amount_collected > 0 else 0.0
            
            # Analyze inventory status
            inventory_status = self._analyze_inventory_status(carrying_after)
            
            # Estimate collection efficiency (based on amount vs expected)
            efficiency = self._estimate_collection_efficiency(resource_type, amount_collected)
            
            # Location analysis
            location = (x, y) if x >= 0 and y >= 0 else None
            
            return {
                'agent_id': agent_id,
                'resource': {
                    'type': resource_type,
                    'amount': amount_collected,
                    'display_name': self._format_resource_type(resource_type)
                },
                'location': location,
                'step': step,
                'efficiency': round(efficiency, 3),
                'utility_gained': round(utility_gained, 3),
                'utility_per_unit': round(utility_per_unit, 3),
                'inventory_status': inventory_status,
                'carrying_after': carrying_after,
                'collection_rate': float(amount_collected),  # Units per collection event
                'resource_value': self._assess_resource_value(resource_type, utility_per_unit)
            }
            
        except Exception as e:
            return {
                'error': f"Analysis formatting error: {e}",
                'raw_event': raw_event
            }
    
    def to_table_row(self, raw_event: Dict[str, Any]) -> List[Union[str, int, float]]:
        """
        Convert raw resource collection event to table row format.
        
        Args:
            raw_event: Raw resource collection dictionary from RawDataObserver
            
        Returns:
            List of values for table display: [Step, Type, Agent, Resource, Amount, Location, Utility]
            
        Example:
            [44, "Collection", "Agent 5", "Wood", 2, "(10, 15)", 1.8]
        """
        try:
            step = raw_event.get('step', -1)
            agent_id = self._safe_get(raw_event, 'agent_id', '?')
            resource_type = self._safe_get(raw_event, 'resource_type', '?')
            amount = raw_event.get('amount_collected', 0)
            x = raw_event.get('x', -1)
            y = raw_event.get('y', -1)
            utility_gained = raw_event.get('utility_gained', 0.0)
            
            # Format for table display
            resource_display = self._format_resource_type(resource_type)
            location_str = self._format_location(x, y)
            
            return [step, "Collection", f"Agent {agent_id}", resource_display, 
                   amount, location_str, round(utility_gained, 2)]
            
        except Exception as e:
            step = raw_event.get('step', -1)
            return [step, "Collection", "[Error]", "[Error]", 0, "[Error]", 0.0]
    
    def to_detailed_view(self, raw_event: Dict[str, Any]) -> Dict[str, str]:
        """
        Convert raw resource collection event to detailed view format.
        
        Args:
            raw_event: Raw resource collection dictionary from RawDataObserver
            
        Returns:
            Dictionary mapping field names to formatted display values
        """
        try:
            detailed = {}
            
            # Basic event info
            detailed['Event Type'] = 'Resource Collection'
            detailed['Step'] = str(raw_event.get('step', 'Unknown'))
            detailed['Agent'] = self._format_agent_id(raw_event.get('agent_id', -1))
            
            # Resource details
            resource_type = raw_event.get('resource_type', 'Unknown')
            amount_collected = raw_event.get('amount_collected', 0)
            detailed['Resource Type'] = self._format_resource_type(resource_type)
            detailed['Amount Collected'] = f"{amount_collected} {self._get_resource_unit(resource_type)}"
            
            # Location information
            x = raw_event.get('x', -1)
            y = raw_event.get('y', -1)
            detailed['Collection Location'] = self._format_location(x, y)
            
            # Utility analysis
            utility_gained = raw_event.get('utility_gained', 0.0)
            utility_per_unit = utility_gained / amount_collected if amount_collected > 0 else 0.0
            detailed['Utility Gained'] = self._format_utility(utility_gained)
            detailed['Utility Per Unit'] = f"{utility_per_unit:.2f}"
            
            # Efficiency analysis
            efficiency = self._estimate_collection_efficiency(resource_type, amount_collected)
            detailed['Collection Efficiency'] = f"{efficiency:.1%}"
            
            # Inventory analysis
            carrying_after = raw_event.get('carrying_after', {})
            inventory_status = self._analyze_inventory_status(carrying_after)
            detailed['Inventory Status'] = inventory_status.replace('_', ' ').title()
            
            # Show inventory summary
            inventory_summary = self._format_inventory_summary(carrying_after)
            detailed['Current Inventory'] = inventory_summary
            
            # Resource value assessment
            resource_value = self._assess_resource_value(resource_type, utility_per_unit)
            detailed['Resource Value Assessment'] = resource_value.replace('_', ' ').title()
            
            return detailed
            
        except Exception as e:
            return {
                'Event Type': 'Resource Collection',
                'Error': f'Formatting error: {e}',
                'Raw Data': str(raw_event)
            }
    
    def get_table_headers(self) -> List[str]:
        """
        Get table column headers for resource collection events.
        
        Returns:
            List of column header strings
        """
        return ["Step", "Event Type", "Agent", "Resource", "Amount", "Location", "Utility"]
    
    def get_supported_event_type(self) -> str:
        """
        Get the event type this formatter supports.
        
        Returns:
            Event type string: 'resource_collection'
        """
        return 'resource_collection'
    
    # ============================================================================
    # RESOURCE COLLECTION SPECIFIC HELPER METHODS
    # ============================================================================
    
    def _format_resource_type(self, resource_type: str) -> str:
        """
        Format resource type for display.
        
        Args:
            resource_type: Raw resource type string
            
        Returns:
            Human-readable resource type name
        """
        return self.RESOURCE_DISPLAY_NAMES.get(resource_type.lower(), resource_type.capitalize())
    
    def _get_resource_unit(self, resource_type: str) -> str:
        """
        Get the display unit for a resource type.
        
        Args:
            resource_type: Raw resource type string
            
        Returns:
            Unit name for display (e.g., 'logs', 'chunks')
        """
        return self.RESOURCE_UNITS.get(resource_type.lower(), 'units')
    
    def _estimate_collection_efficiency(self, resource_type: str, amount_collected: int) -> float:
        """
        Estimate collection efficiency based on expected amounts.
        
        Args:
            resource_type: Type of resource collected
            amount_collected: Amount actually collected
            
        Returns:
            Efficiency ratio (0.0 to 1.0+)
        """
        # Expected amounts per collection (baseline expectations)
        expected_amounts = {
            'wood': 2,
            'stone': 1,
            'food': 3,
            'water': 5,
            'metal': 1,
            'energy': 2
        }
        
        expected = expected_amounts.get(resource_type.lower(), 2)
        efficiency = amount_collected / expected if expected > 0 else 0.0
        
        # Cap at reasonable maximum
        return min(efficiency, 2.0)
    
    def _analyze_inventory_status(self, carrying_after: Dict[str, Any]) -> str:
        """
        Analyze inventory status after collection.
        
        Args:
            carrying_after: Inventory dictionary after collection
            
        Returns:
            Inventory status string
        """
        if not carrying_after:
            return 'empty'
        
        # Count total items (simplified analysis)
        total_items = 0
        for _, amount in carrying_after.items():
            if isinstance(amount, (int, float)):
                total_items += amount
        
        # Rough capacity analysis (assume ~10 total capacity)
        estimated_capacity = 10
        fill_ratio = total_items / estimated_capacity
        
        if fill_ratio < 0.3:
            return 'low'
        elif fill_ratio < 0.7:
            return 'moderate'
        elif fill_ratio < 0.9:
            return 'high'
        else:
            return 'nearly_full'
    
    def _format_inventory_summary(self, carrying_after: Dict[str, Any]) -> str:
        """
        Format inventory contents for display.
        
        Args:
            carrying_after: Inventory dictionary
            
        Returns:
            Formatted inventory summary string
        """
        if not carrying_after:
            return 'Empty'
        
        items = []
        for resource_type, amount in carrying_after.items():
            if isinstance(amount, (int, float)) and amount > 0:
                resource_name = self._format_resource_type(resource_type)
                items.append(f"{amount} {resource_name}")
        
        if not items:
            return 'Empty'
        elif len(items) <= 3:
            return ', '.join(items)
        else:
            return f"{', '.join(items[:2])}, and {len(items) - 2} more types"
    
    def _assess_resource_value(self, resource_type: str, utility_per_unit: float) -> str:
        """
        Assess the relative value of this resource collection.
        
        Args:
            resource_type: Type of resource
            utility_per_unit: Utility gained per unit collected
            
        Returns:
            Value assessment string
        """
        # Base value expectations (these would ideally come from game balance)
        base_values = {
            'wood': 0.8,
            'stone': 1.0,
            'food': 1.2,
            'water': 0.6,
            'metal': 1.5,
            'energy': 1.0
        }
        
        expected_value = base_values.get(resource_type.lower(), 1.0)
        
        if utility_per_unit >= expected_value * 1.5:
            return 'very_high_value'
        elif utility_per_unit >= expected_value * 1.2:
            return 'high_value'
        elif utility_per_unit >= expected_value * 0.8:
            return 'normal_value'
        elif utility_per_unit >= expected_value * 0.5:
            return 'low_value'
        else:
            return 'very_low_value'
    
    def analyze_collection_patterns(self, raw_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze patterns across multiple resource collection events.
        
        Args:
            raw_events: List of raw resource collection dictionaries
            
        Returns:
            Dictionary with collection pattern analysis
        """
        if not raw_events:
            return {
                'total_collections': 0,
                'unique_collectors': 0,
                'resource_distribution': {},
                'average_efficiency': 0.0
            }
        
        # Track collection patterns
        resource_counts: Dict[str, int] = {}
        location_counts: Dict[str, int] = {}
        collector_activity: Dict[int, int] = {}
        total_utility = 0.0
        total_amount = 0
        
        for event in raw_events:
            agent_id = event.get('agent_id', -1)
            resource_type = event.get('resource_type', '')
            amount = event.get('amount_collected', 0)
            utility = event.get('utility_gained', 0.0)
            x = event.get('x', -1)
            y = event.get('y', -1)
            
            # Track resource distribution
            resource_counts[resource_type] = resource_counts.get(resource_type, 0) + amount
            
            # Track locations
            if x >= 0 and y >= 0:
                location_key = f"({x},{y})"
                location_counts[location_key] = location_counts.get(location_key, 0) + 1
            
            # Track collector activity
            collector_activity[agent_id] = collector_activity.get(agent_id, 0) + 1
            
            total_utility += utility
            total_amount += amount
        
        # Calculate metrics
        avg_utility_per_collection = total_utility / len(raw_events) if raw_events else 0.0
        avg_amount_per_collection = total_amount / len(raw_events) if raw_events else 0.0
        
        # Find most productive locations
        sorted_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)
        top_locations = sorted_locations[:5]
        
        return {
            'total_collections': len(raw_events),
            'unique_collectors': len([agent for agent, _ in collector_activity.items() if agent >= 0]),
            'resource_distribution': resource_counts,
            'top_collection_locations': top_locations,
            'collector_activity': collector_activity,
            'average_utility_per_collection': round(avg_utility_per_collection, 3),
            'average_amount_per_collection': round(avg_amount_per_collection, 2),
            'total_resources_collected': total_amount,
            'total_utility_generated': round(total_utility, 3)
        }