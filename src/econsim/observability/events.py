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
from dataclasses import dataclass


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