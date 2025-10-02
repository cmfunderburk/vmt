"""Simulation event data models for the observability system.

This module defines the event hierarchy used to communicate simulation state changes
without creating circular dependencies. Events are immutable dataclasses that capture
the essential information needed for logging, debugging, and educational analytics.

Event Design Principles:
- Frozen dataclasses for immutability and performance
- Minimal data payload focused on observational needs  
- Timestamp and step tracking for temporal analysis
- Type-safe event_type field for filtering and routing

Event Hierarchy:
- SimulationEvent: Base class with common fields
- AgentModeChangeEvent: Agent behavior state transitions
- Future: ResourceCollectionEvent, TradeExecutionEvent, etc.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class SimulationEvent:
    """Base class for all simulation events.
    
    Provides common fields for temporal tracking and event identification.
    All concrete event types should inherit from this class.
    
    Attributes:
        step: Simulation step number when event occurred
        timestamp: Wall clock time (time.time()) when event was created
        event_type: String identifier for event type (for filtering/routing)
    """
    step: int
    timestamp: float
    event_type: str

    def __post_init__(self) -> None:
        """Validate event data on construction."""
        if self.step < 0:
            raise ValueError(f"Step must be non-negative, got {self.step}")
        if self.timestamp <= 0:
            raise ValueError(f"Timestamp must be positive, got {self.timestamp}")
        if not self.event_type:
            raise ValueError("Event type cannot be empty")


@dataclass(frozen=True, slots=True)  
class AgentModeChangeEvent(SimulationEvent):
    """Event emitted when an agent changes behavioral mode.
    
    Captures agent state transitions for behavioral analysis and debugging.
    Essential for understanding agent decision patterns in educational scenarios.
    
    Attributes:
        agent_id: Unique agent identifier  
        old_mode: Previous behavioral mode string
        new_mode: New behavioral mode string
        reason: Optional explanation for the mode change
    """
    agent_id: int
    old_mode: str
    new_mode: str 
    reason: str = ""

    def __post_init__(self) -> None:
        """Validate agent event data."""
        # Validate parent fields
        if self.step < 0:
            raise ValueError(f"Step must be non-negative, got {self.step}")
        if self.timestamp <= 0:
            raise ValueError(f"Timestamp must be positive, got {self.timestamp}")
        if not self.event_type:
            raise ValueError("Event type cannot be empty")
        
        # Validate agent-specific fields  
        if self.agent_id < 0:
            raise ValueError(f"Agent ID must be non-negative, got {self.agent_id}")
        if not self.old_mode or not self.new_mode:
            raise ValueError("Mode strings cannot be empty")

    @classmethod
    def create(cls, step: int, agent_id: int, old_mode: str, new_mode: str, reason: str = "") -> AgentModeChangeEvent:
        """Factory method for creating agent mode change events.
        
        Args:
            step: Current simulation step
            agent_id: Agent identifier
            old_mode: Previous mode
            new_mode: New mode  
            reason: Optional reason for change
            
        Returns:
            AgentModeChangeEvent with current timestamp
        """
        return cls(
            step=step,
            timestamp=time.time(),
            event_type="agent_mode_change",
            agent_id=agent_id,
            old_mode=old_mode,
            new_mode=new_mode,
            reason=reason
        )

    def to_dict(self) -> dict[str, int | str]:
        """Convert event to dictionary for serialization."""
        return {
            'type': 'agent_mode_change',
            'step': self.step,
            'agent_id': self.agent_id,
            'old_mode': self.old_mode,
            'new_mode': self.new_mode,
            'reason': self.reason
        }


@dataclass(frozen=True, slots=True)
class ResourceCollectionEvent(SimulationEvent):
    """Event fired when an agent collects a resource.
    
    Provides detailed information about resource collection activities
    for educational analytics and debugging.
    """
    
    agent_id: int
    x: int
    y: int
    resource_type: str
    amount_collected: int = 1
    
    def __post_init__(self) -> None:
        """Validate resource collection event data."""
        # Validate parent fields
        if self.step < 0:
            raise ValueError(f"Step must be non-negative, got {self.step}")
        if self.timestamp <= 0:
            raise ValueError(f"Timestamp must be positive, got {self.timestamp}")
        if not self.event_type:
            raise ValueError("Event type cannot be empty")
        
        # Validate collection-specific fields  
        if self.agent_id < 0:
            raise ValueError(f"Agent ID must be non-negative, got {self.agent_id}")
        if not self.resource_type:
            raise ValueError("Resource type cannot be empty")
        if self.amount_collected <= 0:
            raise ValueError(f"Amount collected must be positive, got {self.amount_collected}")

    @classmethod
    def create(cls, step: int, agent_id: int, x: int, y: int, resource_type: str, amount_collected: int = 1) -> ResourceCollectionEvent:
        """Factory method for creating resource collection events.
        
        Args:
            step: Current simulation step
            agent_id: Agent identifier
            x: X coordinate of resource
            y: Y coordinate of resource
            resource_type: Type of resource collected
            amount_collected: Amount collected (default 1)
            
        Returns:
            ResourceCollectionEvent with current timestamp
        """
        return cls(
            step=step,
            timestamp=time.time(),
            event_type="resource_collection",
            agent_id=agent_id,
            x=x,
            y=y,
            resource_type=resource_type,
            amount_collected=amount_collected
        )
    
    def to_dict(self) -> dict[str, int | str]:
        """Convert event to dictionary for serialization."""
        return {
            'type': 'resource_collection',
            'step': self.step,
            'agent_id': self.agent_id,
            'x': self.x,
            'y': self.y,
            'resource_type': self.resource_type
        }


@dataclass(frozen=True, slots=True)
class TradeExecutionEvent(SimulationEvent):
    """Event fired when a trade is successfully executed between two agents.
    
    Captures trade details for economic analysis and educational purposes.
    Only emitted when a trade actually occurs, not for trade intents.
    """
    
    seller_id: int
    buyer_id: int
    give_type: str
    take_type: str
    delta_u_seller: float
    delta_u_buyer: float
    trade_location_x: int = -1  # Optional meeting point
    trade_location_y: int = -1  # Optional meeting point
    
    def __post_init__(self) -> None:
        """Validate trade execution event data."""
        # Validate parent fields
        if self.step < 0:
            raise ValueError(f"Step must be non-negative, got {self.step}")
        if self.timestamp <= 0:
            raise ValueError(f"Timestamp must be positive, got {self.timestamp}")
        if not self.event_type:
            raise ValueError("Event type cannot be empty")
        
        # Validate trade-specific fields  
        if self.seller_id < 0:
            raise ValueError(f"Seller ID must be non-negative, got {self.seller_id}")
        if self.buyer_id < 0:
            raise ValueError(f"Buyer ID must be non-negative, got {self.buyer_id}")
        if self.seller_id == self.buyer_id:
            raise ValueError("Seller and buyer must be different agents")
        if not self.give_type or not self.take_type:
            raise ValueError("Give and take types cannot be empty")
        if self.give_type == self.take_type:
            raise ValueError("Give and take types must be different")

    @classmethod
    def create(cls, step: int, seller_id: int, buyer_id: int, give_type: str, take_type: str, 
               delta_u_seller: float, delta_u_buyer: float, 
               trade_location_x: int = -1, trade_location_y: int = -1) -> TradeExecutionEvent:
        """Factory method for creating trade execution events.
        
        Args:
            step: Current simulation step
            seller_id: Agent giving the resource
            buyer_id: Agent receiving the resource
            give_type: Resource type being given
            take_type: Resource type being received
            delta_u_seller: Utility change for seller
            delta_u_buyer: Utility change for buyer
            trade_location_x: Optional X coordinate of trade
            trade_location_y: Optional Y coordinate of trade
            
        Returns:
            TradeExecutionEvent with current timestamp
        """
        return cls(
            step=step,
            timestamp=time.time(),
            event_type="trade_execution",
            seller_id=seller_id,
            buyer_id=buyer_id,
            give_type=give_type,
            take_type=take_type,
            delta_u_seller=delta_u_seller,
            delta_u_buyer=delta_u_buyer,
            trade_location_x=trade_location_x,
            trade_location_y=trade_location_y
        )


@dataclass(frozen=True, slots=True) 
class DebugLogEvent(SimulationEvent):
    """Event for debug/categorical logging messages.
    
    Provides categorical logging (simulation, trade, etc.)
    with structured observer events that can be filtered by category and 
    environment variables.
    """
    
    category: str  # "TRADE", "MODE", "ECON", "SPATIAL", "UTILITY", "SIMULATION", etc.
    message: str
    agent_id: int = -1  # Optional agent context
    
    def __post_init__(self) -> None:
        """Validate debug log event data."""
        # Validate parent fields
        if self.step < 0:
            raise ValueError(f"Step must be non-negative, got {self.step}")
        if self.timestamp <= 0:
            raise ValueError(f"Timestamp must be positive, got {self.timestamp}")
        if not self.event_type:
            raise ValueError("Event type cannot be empty")
        
        # Validate debug-specific fields
        if not self.category:
            raise ValueError("Category cannot be empty")
        if not self.message:
            raise ValueError("Message cannot be empty")
    
    @classmethod
    def create(cls, step: int, category: str, message: str, agent_id: int = -1) -> DebugLogEvent:
        """Factory method for creating debug log events.
        
        Args:
            step: Current simulation step
            category: Log category (TRADE, MODE, ECON, etc.)
            message: Debug message text
            agent_id: Optional agent context
            
        Returns:
            DebugLogEvent with current timestamp
        """
        return cls(
            step=step,
            timestamp=time.time(),
            event_type="debug_log",
            category=category,
            message=message,
            agent_id=agent_id
        )


@dataclass(frozen=True, slots=True)
class PerformanceMonitorEvent(SimulationEvent):
    """Event for performance monitoring and metrics.
    
    Captures performance data like steps/sec, frame timing, memory usage,
    and other optimization-relevant metrics from the simulation.
    """
    
    metric_name: str  # "steps_per_sec", "frame_time", "memory_usage", etc.
    metric_value: float
    threshold_exceeded: bool = False
    details: str = ""
    
    def __post_init__(self) -> None:
        """Validate performance monitor event data.""" 
        # Validate parent fields
        if self.step < 0:
            raise ValueError(f"Step must be non-negative, got {self.step}")
        if self.timestamp <= 0:
            raise ValueError(f"Timestamp must be positive, got {self.timestamp}")
        if not self.event_type:
            raise ValueError("Event type cannot be empty")
        
        # Validate performance-specific fields
        if not self.metric_name:
            raise ValueError("Metric name cannot be empty")
    
    @classmethod
    def create(cls, step: int, metric_name: str, metric_value: float, 
               threshold_exceeded: bool = False, details: str = "") -> PerformanceMonitorEvent:
        """Factory method for creating performance monitor events.
        
        Args:
            step: Current simulation step
            metric_name: Name of the performance metric
            metric_value: Numeric value of the metric
            threshold_exceeded: Whether metric exceeded a threshold
            details: Additional context or details
            
        Returns:
            PerformanceMonitorEvent with current timestamp
        """
        return cls(
            step=step,
            timestamp=time.time(),
            event_type="performance_monitor",
            metric_name=metric_name,
            metric_value=metric_value,
            threshold_exceeded=threshold_exceeded,
            details=details
        )


@dataclass(frozen=True, slots=True)
class AgentDecisionEvent(SimulationEvent):
    """Event for agent decision-making processes.
    
    Captures detailed information about agent decision logic for educational
    analytics and behavioral analysis.
    """
    
    agent_id: int
    decision_type: str  # "movement", "collection", "trade_intent", etc.
    decision_details: str
    utility_delta: float = 0.0
    position_x: int = -1
    position_y: int = -1
    
    def __post_init__(self) -> None:
        """Validate agent decision event data."""
        # Validate parent fields
        if self.step < 0:
            raise ValueError(f"Step must be non-negative, got {self.step}")
        if self.timestamp <= 0:
            raise ValueError(f"Timestamp must be positive, got {self.timestamp}")
        if not self.event_type:
            raise ValueError("Event type cannot be empty")
        
        # Validate decision-specific fields
        if self.agent_id < 0:
            raise ValueError(f"Agent ID must be non-negative, got {self.agent_id}")
        if not self.decision_type:
            raise ValueError("Decision type cannot be empty")
        if not self.decision_details:
            raise ValueError("Decision details cannot be empty")
    
    @classmethod
    def create(cls, step: int, agent_id: int, decision_type: str, decision_details: str,
               utility_delta: float = 0.0, position_x: int = -1, position_y: int = -1) -> AgentDecisionEvent:
        """Factory method for creating agent decision events.
        
        Args:
            step: Current simulation step
            agent_id: ID of the agent making the decision
            decision_type: Type of decision being made
            decision_details: Detailed description of the decision
            utility_delta: Utility change associated with decision
            position_x: Optional X coordinate context
            position_y: Optional Y coordinate context
            
        Returns:
            AgentDecisionEvent with current timestamp
        """
        return cls(
            step=step,
            timestamp=time.time(),
            event_type="agent_decision",
            agent_id=agent_id,
            decision_type=decision_type,
            decision_details=decision_details,
            utility_delta=utility_delta,
            position_x=position_x,
            position_y=position_y
        )


@dataclass(frozen=True, slots=True)
class ResourceEvent(SimulationEvent):
    """Event for resource-related activities beyond collection.
    
    Captures resource spawning, despawning, and other resource lifecycle
    events for comprehensive resource tracking.
    """
    
    event_type_detail: str  # "spawn", "despawn", "move", "transform", etc.
    position_x: int
    position_y: int
    resource_type: str
    amount: int = 1
    agent_id: int = -1  # Optional agent context (for pickup/deposit events)
    
    def __post_init__(self) -> None:
        """Validate resource event data."""
        # Validate parent fields
        if self.step < 0:
            raise ValueError(f"Step must be non-negative, got {self.step}")
        if self.timestamp <= 0:
            raise ValueError(f"Timestamp must be positive, got {self.timestamp}")
        if not self.event_type:
            raise ValueError("Event type cannot be empty")
        
        # Validate resource-specific fields
        if not self.event_type_detail:
            raise ValueError("Event type detail cannot be empty")
        if not self.resource_type:
            raise ValueError("Resource type cannot be empty")
        if self.amount <= 0:
            raise ValueError(f"Amount must be positive, got {self.amount}")
    
    @classmethod
    def create(cls, step: int, event_type_detail: str, position_x: int, position_y: int,
               resource_type: str, amount: int = 1, agent_id: int = -1) -> ResourceEvent:
        """Factory method for creating resource events.
        
        Args:
            step: Current simulation step
            event_type_detail: Specific type of resource event
            position_x: X coordinate of resource
            position_y: Y coordinate of resource
            resource_type: Type of resource
            amount: Amount of resource
            agent_id: Optional agent context
            
        Returns:
            ResourceEvent with current timestamp
        """
        return cls(
            step=step,
            timestamp=time.time(),
            event_type="resource_event",
            event_type_detail=event_type_detail,
            position_x=position_x,
            position_y=position_y,
            resource_type=resource_type,
            amount=amount,
            agent_id=agent_id
        )


@dataclass(frozen=True, slots=True)
class GUIDisplayEvent(SimulationEvent):
    """Event for GUI display updates and visual feedback.
    
    Captures information needed for GUI rendering and user interface
    updates without creating circular dependencies.
    """
    
    display_type: str  # "highlight", "overlay", "panel_update", etc.
    element_id: str  # Identifier for the GUI element
    data: dict[str, Any] = field(default_factory=dict)  # Flexible data payload for display info
    
    def __post_init__(self) -> None:
        """Validate GUI display event data."""
        # Validate parent fields
        if self.step < 0:
            raise ValueError(f"Step must be non-negative, got {self.step}")
        if self.timestamp <= 0:
            raise ValueError(f"Timestamp must be positive, got {self.timestamp}")
        if not self.event_type:
            raise ValueError("Event type cannot be empty")
        
        # Validate display-specific fields
        if not self.display_type:
            raise ValueError("Display type cannot be empty")
        if not self.element_id:
            raise ValueError("Element ID cannot be empty")
    
    @classmethod
    def create(cls, step: int, display_type: str, element_id: str, 
               data: dict[str, Any] | None = None) -> GUIDisplayEvent:
        """Factory method for creating GUI display events.
        
        Args:
            step: Current simulation step
            display_type: Type of display update
            element_id: GUI element identifier
            data: Optional data payload for display
            
        Returns:
            GUIDisplayEvent with current timestamp
        """
        return cls(
            step=step,
            timestamp=time.time(),
            event_type="gui_display",
            display_type=display_type,
            element_id=element_id,
            data=data or {}
        )