"""Agent state machine with explicit transitions and validation."""

from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .event_emitter import AgentEventEmitter

# Import AgentMode from constants to avoid circular dependency
from ..constants import AgentMode


class AgentModeStateMachine:
    """Validates mode transitions and emits events; does NOT own mode state.
    
    This component provides centralized mode transition validation and event emission.
    The actual mode state remains in the Agent class for backward compatibility.
    
    CRITICAL INVARIANT: This component does NOT store mode state. It only validates
    transitions and emits events. The Agent.mode property remains authoritative.
    """
    
    # Valid transitions map - defines allowed mode changes
    VALID_TRANSITIONS = {
        AgentMode.FORAGE: {AgentMode.RETURN_HOME, AgentMode.IDLE, AgentMode.MOVE_TO_PARTNER},
        AgentMode.RETURN_HOME: {AgentMode.FORAGE, AgentMode.IDLE},
        AgentMode.IDLE: {AgentMode.FORAGE, AgentMode.MOVE_TO_PARTNER, AgentMode.RETURN_HOME},
        AgentMode.MOVE_TO_PARTNER: {AgentMode.IDLE, AgentMode.FORAGE, AgentMode.RETURN_HOME}
    }
    
    def __init__(self, agent_id: int):
        self.agent_id = agent_id
        self._event_emitter: Optional[AgentEventEmitter] = None
    
    def set_event_emitter(self, event_emitter: AgentEventEmitter) -> None:
        """Set the event emitter for mode change events."""
        self._event_emitter = event_emitter
    
    def is_valid_transition(self, from_mode: AgentMode, to_mode: AgentMode) -> bool:
        """Check if transition is valid (non-destructive check).
        
        Args:
            from_mode: Current mode
            to_mode: Desired new mode
            
        Returns:
            True if transition is allowed, False otherwise
        """
        if from_mode == to_mode:
            return True  # No-op transitions are always valid
        return to_mode in self.VALID_TRANSITIONS.get(from_mode, set())
    
    def validate_and_emit_transition(
        self,
        old_mode: str,
        new_mode: str,
        reason: str,
        step_number: int
    ) -> bool:
        """Validate transition.
        
        Args:
            old_mode: Current mode (string)
            new_mode: Desired new mode (string)
            reason: Reason for mode change
            step_number: Current simulation step
            
        Returns:
            True if transition is valid, False otherwise
        """
        # Convert string modes to enum for validation
        try:
            from_enum = AgentMode(old_mode)
            to_enum = AgentMode(new_mode)
        except ValueError as e:
            # Invalid mode strings - transition not valid
            logging.warning(
                f"Agent {self.agent_id}: Invalid mode string in transition from '{old_mode}' to '{new_mode}': {e}"
            )
            return False
        
        # Validate transition
        if not self.is_valid_transition(from_enum, to_enum):
            return False
        
        # Observer system removed - comprehensive delta system handles recording
        
        return True
    
    def get_valid_transitions(self, current_mode: AgentMode) -> set[AgentMode]:
        """Get all valid transitions from current mode.
        
        Args:
            current_mode: Current agent mode
            
        Returns:
            Set of valid target modes
        """
        return self.VALID_TRANSITIONS.get(current_mode, set())
    
    def get_all_modes(self) -> set[AgentMode]:
        """Get all available agent modes.
        
        Returns:
            Set of all defined agent modes
        """
        return set(AgentMode)
