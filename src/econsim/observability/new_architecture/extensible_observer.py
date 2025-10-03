"""
Extensible observer base class with direct emission methods.

This module implements the ExtensibleObserver base class that provides direct
emission methods with hardcoded compression for maximum performance and clarity.
This replaces the complex 6-layer serialization pipeline with simple, explicit
methods that are easy to understand, debug, and extend.

Key Features:
- Direct emission methods for each event type
- Hardcoded compression for maximum performance
- Fail-fast validation with clear error messages
- Context manager support for automatic resource cleanup
- Thread-safe operations
- Minimal memory overhead with no intermediate transformations

Architecture Benefits:
- Eliminates ~1500 lines of complex serialization code
- Reduces pipeline complexity from 6 layers to 2
- Single responsibility: observers compress, GUI translates
- Extensibility: Add new fields in 2-3 minutes, new event types in ~10 minutes
"""

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, TYPE_CHECKING

from .log_writer import ExtensibleLogWriter

if TYPE_CHECKING:
    from ..config import ObservabilityConfig


class ExtensibleObserver(ABC):
    """Base observer with direct emission methods for maximum clarity and maintainability.
    
    Provides direct emission methods with hardcoded compression for each event type.
    This approach eliminates the complex serialization pipeline while maintaining
    high performance and clear, debuggable code.
    
    Key Design Principles:
    - Direct methods: No magic, no generation, clear explicit methods
    - Hardcoded compression: Maximum performance, minimal runtime overhead
    - Fail-fast validation: Clear error messages with context
    - Single responsibility: Compression only, no translation logic
    - Extensibility: Easy to add new fields and event types
    """
    
    def __init__(self, config: 'ObservabilityConfig', output_path: Optional[Path] = None):
        """Initialize the extensible observer.
        
        Args:
            config: Observability configuration
            output_path: Optional output path for log files
        """
        self._config = config
        self._output_path = output_path
        self._log_writer: Optional[ExtensibleLogWriter] = None
        self._simulation_start_time: Optional[float] = None
        self._closed = False
        
        # Initialize log writer if output path provided
        if self._output_path:
            self._log_writer = ExtensibleLogWriter(self._output_path)
    
    def set_simulation_start_time(self, start_time: float) -> None:
        """Set the simulation start time for relative timestamp calculation.
        
        Args:
            start_time: Absolute timestamp when simulation started
        """
        self._simulation_start_time = start_time
    
    def _get_delta_time(self) -> float:
        """Calculate delta time since simulation start.
        
        Returns:
            Delta time in seconds since simulation start, or 0.0 if not set
        """
        if self._simulation_start_time is None:
            return 0.0
        return time.time() - self._simulation_start_time
    
    def _write_log_entry(self, entry_dict: Dict[str, Any]) -> None:
        """Write a log entry using the log writer.
        
        Args:
            entry_dict: Dictionary to write as JSON log entry
        """
        if self._log_writer and not self._closed:
            self._log_writer.write_entry(entry_dict)
    
    # ========================================================================
    # DIRECT EMISSION METHODS WITH HARDCODED COMPRESSION
    # ========================================================================
    
    def emit_trade_execution(self, step: int, seller_id: int, buyer_id: int, 
                           give_type: str, take_type: str, delta_u_seller: float, 
                           delta_u_buyer: float, **optional) -> None:
        """Emit trade execution event with required and optional fields.
        
        Args:
            step: Simulation step number
            seller_id: Agent giving the resource
            buyer_id: Agent receiving the resource
            give_type: Resource type being given
            take_type: Resource type being received
            delta_u_seller: Utility change for seller
            delta_u_buyer: Utility change for buyer
            **optional: Optional fields (trade_location_x, trade_location_y, etc.)
        """
        # Fail-fast validation with clear error messages
        assert seller_id is not None, f"seller_id required for trade execution at step {step}"
        assert buyer_id is not None, f"buyer_id required for trade execution at step {step}"
        assert give_type is not None, f"give_type required for trade execution at step {step}"
        assert take_type is not None, f"take_type required for trade execution at step {step}"
        assert isinstance(seller_id, int), f"seller_id must be integer, got {type(seller_id)} at step {step}"
        assert isinstance(buyer_id, int), f"buyer_id must be integer, got {type(buyer_id)} at step {step}"
        assert seller_id != buyer_id, f"seller_id and buyer_id must be different at step {step}"
        assert give_type != take_type, f"give_type and take_type must be different at step {step}"
        
        # Direct compression with hardcoded field mapping
        compressed = f"sid:{seller_id},bid:{buyer_id},gt:{give_type},tt:{take_type},dus:{delta_u_seller},dub:{delta_u_buyer}"
        
        # Optional fields with explicit mapping
        optional_mapping = {
            'trade_location_x': 'tx',
            'trade_location_y': 'ty',
            'trade_volume': 'vol',
            'market_price': 'price',
            'trade_efficiency': 'eff'
        }
        
        for field, value in optional.items():
            if field in optional_mapping and value is not None:
                code = optional_mapping[field]
                compressed += f",{code}:{value}"
        
        self._write_log_entry({
            "s": step, 
            "dt": self._get_delta_time(), 
            "e": "trade", 
            "d": compressed
        })
    
    def emit_agent_mode_change(self, step: int, agent_id: int, old_mode: str, 
                             new_mode: str, reason: str, **optional) -> None:
        """Emit agent mode change event.
        
        Args:
            step: Simulation step number
            agent_id: Unique agent identifier
            old_mode: Previous behavioral mode
            new_mode: New behavioral mode
            reason: Reason for mode change
            **optional: Optional fields (transition_duration, decision_confidence, etc.)
        """
        # Clear validation
        assert agent_id is not None, f"agent_id required for mode change at step {step}"
        assert old_mode is not None, f"old_mode required for mode change at step {step}"
        assert new_mode is not None, f"new_mode required for mode change at step {step}"
        assert reason is not None, f"reason required for mode change at step {step}"
        assert isinstance(agent_id, int), f"agent_id must be integer, got {type(agent_id)} at step {step}"
        assert agent_id >= 0, f"agent_id must be non-negative, got {agent_id} at step {step}"
        
        # Direct compression
        compressed = f"aid:{agent_id},om:{old_mode},nm:{new_mode},r:{reason}"
        
        # Optional fields
        optional_mapping = {
            'transition_duration': 'dur',
            'decision_confidence': 'conf'
        }
        
        for field, value in optional.items():
            if field in optional_mapping and value is not None:
                code = optional_mapping[field]
                compressed += f",{code}:{value}"
        
        self._write_log_entry({
            "s": step, 
            "dt": self._get_delta_time(), 
            "e": "mode", 
            "d": compressed
        })
    
    def emit_resource_collection(self, step: int, agent_id: int, x: int, y: int,
                               resource_type: str, amount_collected: int = 1,
                               utility_gained: float = 0.0, **optional) -> None:
        """Emit resource collection event.
        
        Args:
            step: Simulation step number
            agent_id: Agent collecting the resource
            x: X coordinate of resource
            y: Y coordinate of resource
            resource_type: Type of resource collected
            amount_collected: Amount of resource collected
            utility_gained: Utility gained from collection
            **optional: Optional fields (carrying_after, etc.)
        """
        # Clear validation
        assert agent_id is not None, f"agent_id required for resource collection at step {step}"
        assert x is not None, f"x coordinate required for resource collection at step {step}"
        assert y is not None, f"y coordinate required for resource collection at step {step}"
        assert resource_type is not None, f"resource_type required for resource collection at step {step}"
        assert isinstance(agent_id, int), f"agent_id must be integer, got {type(agent_id)} at step {step}"
        assert isinstance(x, int), f"x must be integer, got {type(x)} at step {step}"
        assert isinstance(y, int), f"y must be integer, got {type(y)} at step {step}"
        assert isinstance(amount_collected, int), f"amount_collected must be integer, got {type(amount_collected)} at step {step}"
        assert amount_collected > 0, f"amount_collected must be positive, got {amount_collected} at step {step}"
        
        # Direct compression
        compressed = f"aid:{agent_id},x:{x},y:{y},rt:{resource_type},amt:{amount_collected},ug:{utility_gained}"
        
        # Optional fields
        optional_mapping = {
            'carrying_after': 'ca'
        }
        
        for field, value in optional.items():
            if field in optional_mapping and value is not None:
                code = optional_mapping[field]
                # Handle dict values specially
                if isinstance(value, dict):
                    # Convert dict to string representation
                    dict_str = ",".join(f"{k}:{v}" for k, v in value.items())
                    compressed += f",{code}:{dict_str}"
                else:
                    compressed += f",{code}:{value}"
        
        self._write_log_entry({
            "s": step, 
            "dt": self._get_delta_time(), 
            "e": "collect", 
            "d": compressed
        })
    
    def emit_debug_log(self, step: int, category: str, message: str, 
                      agent_id: int = -1, **optional) -> None:
        """Emit debug log event.
        
        Args:
            step: Simulation step number
            category: Log category (TRADE, MODE, ECON, etc.)
            message: Debug message text
            agent_id: Optional agent context
            **optional: Optional fields
        """
        # Clear validation
        assert category is not None, f"category required for debug log at step {step}"
        assert message is not None, f"message required for debug log at step {step}"
        assert isinstance(agent_id, int), f"agent_id must be integer, got {type(agent_id)} at step {step}"
        
        # Direct compression
        compressed = f"cat:{category},msg:{message}"
        
        # Add agent_id if provided
        if agent_id >= 0:
            compressed += f",aid:{agent_id}"
        
        # Optional fields (none currently defined for debug log)
        for field, value in optional.items():
            if value is not None:
                compressed += f",{field}:{value}"
        
        self._write_log_entry({
            "s": step, 
            "dt": self._get_delta_time(), 
            "e": "debug", 
            "d": compressed
        })
    
    def emit_performance_monitor(self, step: int, metric_name: str, metric_value: float,
                               threshold_exceeded: bool = False, details: str = "", **optional) -> None:
        """Emit performance monitor event.
        
        Args:
            step: Simulation step number
            metric_name: Name of performance metric
            metric_value: Numeric value of metric
            threshold_exceeded: Whether threshold was exceeded
            details: Additional context or details
            **optional: Optional fields
        """
        # Clear validation
        assert metric_name is not None, f"metric_name required for performance monitor at step {step}"
        assert isinstance(metric_value, (int, float)), f"metric_value must be numeric, got {type(metric_value)} at step {step}"
        assert isinstance(threshold_exceeded, bool), f"threshold_exceeded must be boolean, got {type(threshold_exceeded)} at step {step}"
        
        # Direct compression
        compressed = f"mn:{metric_name},mv:{metric_value}"
        
        # Add optional fields if provided
        if threshold_exceeded:
            compressed += f",te:{threshold_exceeded}"
        if details:
            compressed += f",det:{details}"
        
        # Additional optional fields
        for field, value in optional.items():
            if value is not None:
                compressed += f",{field}:{value}"
        
        self._write_log_entry({
            "s": step, 
            "dt": self._get_delta_time(), 
            "e": "perf", 
            "d": compressed
        })
    
    def emit_agent_decision(self, step: int, agent_id: int, decision_type: str,
                          decision_details: str, utility_delta: float = 0.0,
                          position_x: int = -1, position_y: int = -1, **optional) -> None:
        """Emit agent decision event.
        
        Args:
            step: Simulation step number
            agent_id: ID of agent making decision
            decision_type: Type of decision (movement, collection, etc.)
            decision_details: Detailed description of decision
            utility_delta: Utility change from decision
            position_x: X coordinate context
            position_y: Y coordinate context
            **optional: Optional fields
        """
        # Clear validation
        assert agent_id is not None, f"agent_id required for agent decision at step {step}"
        assert decision_type is not None, f"decision_type required for agent decision at step {step}"
        assert decision_details is not None, f"decision_details required for agent decision at step {step}"
        assert isinstance(agent_id, int), f"agent_id must be integer, got {type(agent_id)} at step {step}"
        assert agent_id >= 0, f"agent_id must be non-negative, got {agent_id} at step {step}"
        
        # Direct compression
        compressed = f"aid:{agent_id},dt:{decision_type},dd:{decision_details}"
        
        # Add optional fields if provided
        if utility_delta != 0.0:
            compressed += f",ud:{utility_delta}"
        if position_x >= 0:
            compressed += f",px:{position_x}"
        if position_y >= 0:
            compressed += f",py:{position_y}"
        
        # Additional optional fields
        for field, value in optional.items():
            if value is not None:
                compressed += f",{field}:{value}"
        
        self._write_log_entry({
            "s": step, 
            "dt": self._get_delta_time(), 
            "e": "decision", 
            "d": compressed
        })
    
    def emit_resource_event(self, step: int, event_type_detail: str, position_x: int,
                          position_y: int, resource_type: str, amount: int = 1,
                          agent_id: int = -1, **optional) -> None:
        """Emit resource event.
        
        Args:
            step: Simulation step number
            event_type_detail: Specific type of resource event
            position_x: X coordinate of resource
            position_y: Y coordinate of resource
            resource_type: Type of resource
            amount: Amount of resource
            agent_id: Optional agent context
            **optional: Optional fields
        """
        # Clear validation
        assert event_type_detail is not None, f"event_type_detail required for resource event at step {step}"
        assert position_x is not None, f"position_x required for resource event at step {step}"
        assert position_y is not None, f"position_y required for resource event at step {step}"
        assert resource_type is not None, f"resource_type required for resource event at step {step}"
        assert isinstance(position_x, int), f"position_x must be integer, got {type(position_x)} at step {step}"
        assert isinstance(position_y, int), f"position_y must be integer, got {type(position_y)} at step {step}"
        assert isinstance(amount, int), f"amount must be integer, got {type(amount)} at step {step}"
        assert amount > 0, f"amount must be positive, got {amount} at step {step}"
        
        # Direct compression
        compressed = f"etd:{event_type_detail},px:{position_x},py:{position_y},rt:{resource_type},amt:{amount}"
        
        # Add agent_id if provided
        if agent_id >= 0:
            compressed += f",aid:{agent_id}"
        
        # Additional optional fields
        for field, value in optional.items():
            if value is not None:
                compressed += f",{field}:{value}"
        
        self._write_log_entry({
            "s": step, 
            "dt": self._get_delta_time(), 
            "e": "resource", 
            "d": compressed
        })
    
    def emit_economic_decision(self, step: int, agent_id: int, decision_type: str,
                             decision_context: str, utility_before: float = 0.0,
                             utility_after: float = 0.0, opportunity_cost: float = 0.0,
                             alternatives_considered: int = 0, decision_time_ms: float = 0.0,
                             position_x: int = -1, position_y: int = -1, **optional) -> None:
        """Emit economic decision event.
        
        Args:
            step: Simulation step number
            agent_id: ID of agent making economic decision
            decision_type: Type of economic decision
            decision_context: Detailed context of decision
            utility_before: Agent utility before decision
            utility_after: Agent utility after decision
            opportunity_cost: Cost of not choosing alternatives
            alternatives_considered: Number of alternatives evaluated
            decision_time_ms: Time taken to make decision
            position_x: X coordinate context
            position_y: Y coordinate context
            **optional: Optional fields
        """
        # Clear validation
        assert agent_id is not None, f"agent_id required for economic decision at step {step}"
        assert decision_type is not None, f"decision_type required for economic decision at step {step}"
        assert decision_context is not None, f"decision_context required for economic decision at step {step}"
        assert isinstance(agent_id, int), f"agent_id must be integer, got {type(agent_id)} at step {step}"
        assert agent_id >= 0, f"agent_id must be non-negative, got {agent_id} at step {step}"
        assert isinstance(alternatives_considered, int), f"alternatives_considered must be integer, got {type(alternatives_considered)} at step {step}"
        assert alternatives_considered >= 0, f"alternatives_considered must be non-negative, got {alternatives_considered} at step {step}"
        assert isinstance(decision_time_ms, (int, float)), f"decision_time_ms must be numeric, got {type(decision_time_ms)} at step {step}"
        assert decision_time_ms >= 0, f"decision_time_ms must be non-negative, got {decision_time_ms} at step {step}"
        
        # Direct compression
        compressed = f"aid:{agent_id},dt:{decision_type},dc:{decision_context}"
        
        # Add optional fields if provided
        if utility_before != 0.0:
            compressed += f",ub:{utility_before}"
        if utility_after != 0.0:
            compressed += f",ua:{utility_after}"
        if opportunity_cost != 0.0:
            compressed += f",oc:{opportunity_cost}"
        if alternatives_considered > 0:
            compressed += f",ac:{alternatives_considered}"
        if decision_time_ms > 0.0:
            compressed += f",dtm:{decision_time_ms}"
        if position_x >= 0:
            compressed += f",px:{position_x}"
        if position_y >= 0:
            compressed += f",py:{position_y}"
        
        # Additional optional fields
        for field, value in optional.items():
            if value is not None:
                compressed += f",{field}:{value}"
        
        self._write_log_entry({
            "s": step, 
            "dt": self._get_delta_time(), 
            "e": "econ", 
            "d": compressed
        })
    
    def emit_gui_display(self, step: int, display_type: str, element_id: str,
                        data: Optional[Dict[str, Any]] = None, **optional) -> None:
        """Emit GUI display event (optional).
        
        Args:
            step: Simulation step number
            display_type: Type of display update
            element_id: GUI element identifier
            data: Optional data payload for display
            **optional: Optional fields
        """
        # Clear validation
        assert display_type is not None, f"display_type required for GUI display at step {step}"
        assert element_id is not None, f"element_id required for GUI display at step {step}"
        
        # Direct compression
        compressed = f"dt:{display_type},eid:{element_id}"
        
        # Add data if provided
        if data:
            # Convert dict to string representation
            data_str = ",".join(f"{k}:{v}" for k, v in data.items())
            compressed += f",data:{data_str}"
        
        # Additional optional fields
        for field, value in optional.items():
            if value is not None:
                compressed += f",{field}:{value}"
        
        self._write_log_entry({
            "s": step, 
            "dt": self._get_delta_time(), 
            "e": "gui", 
            "d": compressed
        })
    
    # ========================================================================
    # LIFECYCLE METHODS
    # ========================================================================
    
    def flush_step(self, step: int) -> None:
        """Handle end-of-step boundary.
        
        Args:
            step: The simulation step that just completed
        """
        if self._log_writer and not self._closed:
            self._log_writer.flush()
    
    def close(self) -> None:
        """Close the observer and release resources."""
        if self._log_writer and not self._closed:
            self._log_writer.close()
        self._closed = True
    
    def __enter__(self) -> 'ExtensibleObserver':
        """Context manager entry."""
        if self._log_writer:
            self._log_writer.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        if self._log_writer:
            self._log_writer.__exit__(exc_type, exc_val, exc_tb)
        self.close()
    
    @property
    def is_closed(self) -> bool:
        """Check if the observer has been closed."""
        return self._closed
    
    def get_observer_stats(self) -> Dict[str, Any]:
        """Get statistics about observer state and performance.
        
        Returns:
            Dictionary containing observer metrics and statistics
        """
        stats = {
            'observer_type': self.__class__.__name__,
            'is_closed': self._closed,
            'has_log_writer': self._log_writer is not None,
            'output_path': str(self._output_path) if self._output_path else None,
        }
        
        if self._log_writer:
            stats.update(self._log_writer.get_statistics())
        
        return stats
