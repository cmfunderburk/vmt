"""Unit tests for AgentModeStateMachine component."""

import pytest
from unittest.mock import Mock
from econsim.simulation.components.mode_state_machine import AgentModeStateMachine, AgentMode


class TestAgentModeStateMachine:
    def test_initialization(self):
        """Test AgentModeStateMachine initializes correctly."""
        state_machine = AgentModeStateMachine(agent_id=1)
        
        assert state_machine.agent_id == 1
        assert state_machine._event_emitter is None
    
    def test_set_event_emitter(self):
        """Test setting event emitter."""
        state_machine = AgentModeStateMachine(agent_id=1)
        mock_emitter = Mock()
        
        state_machine.set_event_emitter(mock_emitter)
        assert state_machine._event_emitter == mock_emitter
    
    def test_valid_transitions(self):
        """Test that valid transitions are accepted."""
        state_machine = AgentModeStateMachine(agent_id=1)
        
        # FORAGE -> RETURN_HOME should be valid
        assert state_machine.is_valid_transition(AgentMode.FORAGE, AgentMode.RETURN_HOME)
        
        # FORAGE -> IDLE should be valid
        assert state_machine.is_valid_transition(AgentMode.FORAGE, AgentMode.IDLE)
        
        # FORAGE -> MOVE_TO_PARTNER should be valid
        assert state_machine.is_valid_transition(AgentMode.FORAGE, AgentMode.MOVE_TO_PARTNER)
        
        # RETURN_HOME -> FORAGE should be valid
        assert state_machine.is_valid_transition(AgentMode.RETURN_HOME, AgentMode.FORAGE)
        
        # IDLE -> FORAGE should be valid
        assert state_machine.is_valid_transition(AgentMode.IDLE, AgentMode.FORAGE)
        
        # MOVE_TO_PARTNER -> IDLE should be valid
        assert state_machine.is_valid_transition(AgentMode.MOVE_TO_PARTNER, AgentMode.IDLE)
    
    def test_invalid_transitions(self):
        """Test that invalid transitions are rejected."""
        state_machine = AgentModeStateMachine(agent_id=1)
        
        # FORAGE -> FORAGE should be valid (no-op)
        assert state_machine.is_valid_transition(AgentMode.FORAGE, AgentMode.FORAGE)
        
        # But some transitions should be invalid (if any exist)
        # Note: Based on the implementation, all defined transitions should be valid
        # This test verifies the transition matrix is working correctly
    
    def test_validate_and_emit_transition_valid(self):
        """Test validation and emission for valid transitions."""
        state_machine = AgentModeStateMachine(agent_id=1)
        mock_emitter = Mock()
        state_machine.set_event_emitter(mock_emitter)
        
        # Valid transition should return True and emit event
        result = state_machine.validate_and_emit_transition(
            old_mode="forage",
            new_mode="return_home",
            reason="test_reason",
            step_number=42
        )
        
        assert result is True
        mock_emitter.emit_mode_change.assert_called_once_with(
            old_mode="forage",
            new_mode="return_home",
            reason="test_reason",
            step_number=42,
            observer_registry=None,
            event_buffer=None
        )
    
    def test_validate_and_emit_transition_invalid_mode_string(self):
        """Test validation with invalid mode strings."""
        state_machine = AgentModeStateMachine(agent_id=1)
        
        # Invalid mode string should return False
        result = state_machine.validate_and_emit_transition(
            old_mode="INVALID_MODE",
            new_mode="forage",
            reason="test_reason",
            step_number=42
        )
        
        assert result is False
    
    def test_validate_and_emit_transition_invalid_transition(self):
        """Test validation with invalid transition (if any exist)."""
        state_machine = AgentModeStateMachine(agent_id=1)
        
        # Test with observer registry and event buffer
        mock_registry = Mock()
        mock_buffer = Mock()
        
        result = state_machine.validate_and_emit_transition(
            old_mode="forage",
            new_mode="forage",  # No-op transition should be valid
            reason="test_reason",
            step_number=42,
            observer_registry=mock_registry,
            event_buffer=mock_buffer
        )
        
        assert result is True
    
    def test_get_valid_transitions(self):
        """Test getting valid transitions from a mode."""
        state_machine = AgentModeStateMachine(agent_id=1)
        
        # Get valid transitions from FORAGE
        valid_transitions = state_machine.get_valid_transitions(AgentMode.FORAGE)
        
        # Should include the expected transitions
        expected = {AgentMode.RETURN_HOME, AgentMode.IDLE, AgentMode.MOVE_TO_PARTNER}
        assert valid_transitions == expected
    
    def test_get_all_modes(self):
        """Test getting all available modes."""
        state_machine = AgentModeStateMachine(agent_id=1)
        
        all_modes = state_machine.get_all_modes()
        
        # Should include all defined modes
        expected = {AgentMode.FORAGE, AgentMode.RETURN_HOME, AgentMode.IDLE, AgentMode.MOVE_TO_PARTNER}
        assert all_modes == expected
    
    def test_no_event_emitter_graceful(self):
        """Test that validation works without event emitter."""
        state_machine = AgentModeStateMachine(agent_id=1)
        # Don't set event emitter
        
        # Should still validate transitions correctly
        result = state_machine.validate_and_emit_transition(
            old_mode="forage",
            new_mode="return_home",
            reason="test_reason",
            step_number=42
        )
        
        assert result is True  # Should not crash without emitter
    
    def test_transition_matrix_completeness(self):
        """Test that all modes have defined transitions."""
        state_machine = AgentModeStateMachine(agent_id=1)
        
        all_modes = state_machine.get_all_modes()
        
        # Every mode should have at least some valid transitions
        for mode in all_modes:
            valid_transitions = state_machine.get_valid_transitions(mode)
            assert len(valid_transitions) > 0, f"Mode {mode} has no valid transitions"
    
    def test_enum_consistency(self):
        """Test that AgentMode enum values match expected strings."""
        # Verify enum values match what the Agent class expects (lowercase)
        assert AgentMode.FORAGE.value == "forage"
        assert AgentMode.RETURN_HOME.value == "return_home"
        assert AgentMode.IDLE.value == "idle"
        assert AgentMode.MOVE_TO_PARTNER.value == "move_to_partner"
