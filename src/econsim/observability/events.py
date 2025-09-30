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