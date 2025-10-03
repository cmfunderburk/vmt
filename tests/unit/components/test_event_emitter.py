"""Unit tests for AgentEventEmitter component."""

import pytest
from unittest.mock import Mock, patch
from econsim.simulation.components.event_emitter import AgentEventEmitter


class TestAgentEventEmitter:
    def test_init(self):
        """Test AgentEventEmitter initialization."""
        emitter = AgentEventEmitter(agent_id=42)
        assert emitter.agent_id == 42
    
    def test_emit_mode_change_with_event_buffer(self):
        """Test mode change emission via event buffer."""
        emitter = AgentEventEmitter(agent_id=1)
        event_buffer = Mock()
        
        emitter.emit_mode_change(
            old_mode="forage",
            new_mode="return_home", 
            reason="collected_resource",
            step_number=5,
            event_buffer=event_buffer
        )
        
        event_buffer.queue_mode_change.assert_called_once_with(
            1, "forage", "return_home", "collected_resource"
        )
    
    def test_emit_mode_change_with_observer_registry(self):
        """Test mode change emission via observer registry using raw data architecture."""
        emitter = AgentEventEmitter(agent_id=2)
        
        # Mock observer with record_mode_change method
        mock_observer = Mock()
        mock_observer.record_mode_change = Mock()
        
        # Mock observer registry
        observer_registry = Mock()
        observer_registry._observers = [mock_observer]
        
        emitter.emit_mode_change(
            old_mode="idle",
            new_mode="forage",
            reason="target_found",
            step_number=10,
            observer_registry=observer_registry
        )
        
        # Verify raw data recording was called correctly
        mock_observer.record_mode_change.assert_called_once_with(
            step=10,
            agent_id=2,
            old_mode="idle",
            new_mode="forage",
            reason="target_found"
        )
    
    def test_emit_mode_change_no_observers(self):
        """Test mode change emission with no observers (graceful degradation)."""
        emitter = AgentEventEmitter(agent_id=3)
        
        # Should not raise any exceptions
        emitter.emit_mode_change(
            old_mode="forage",
            new_mode="idle",
            reason="no_targets",
            step_number=15
        )
    
    def test_emit_resource_collection_with_observer_registry(self):
        """Test resource collection emission via observer registry using raw data architecture."""
        emitter = AgentEventEmitter(agent_id=4)
        
        # Mock observer with record_resource_collection method
        mock_observer = Mock()
        mock_observer.record_resource_collection = Mock()
        
        # Mock observer registry
        observer_registry = Mock()
        observer_registry._observers = [mock_observer]
        
        emitter.emit_resource_collection(
            x=5,
            y=7,
            resource_type="A",
            step=20,
            observer_registry=observer_registry
        )
        
        # Verify raw data recording was called correctly
        mock_observer.record_resource_collection.assert_called_once_with(
            step=20,
            agent_id=4,
            x=5,
            y=7,
            resource_type="A",
            amount_collected=1
        )
    
    def test_emit_resource_collection_no_observers(self):
        """Test resource collection emission with no observers (graceful degradation)."""
        emitter = AgentEventEmitter(agent_id=5)
        
        # Should not raise any exceptions
        emitter.emit_resource_collection(
            x=3,
            y=4,
            resource_type="B",
            step=25
        )
    
    def test_event_buffer_priority_over_observer_registry(self):
        """Test that event buffer takes priority over observer registry."""
        emitter = AgentEventEmitter(agent_id=6)
        event_buffer = Mock()
        observer_registry = Mock()
        
        emitter.emit_mode_change(
            old_mode="idle",
            new_mode="move_to_partner",
            reason="partner_found",
            step_number=30,
            observer_registry=observer_registry,
            event_buffer=event_buffer
        )
        
        # Event buffer should be used
        event_buffer.queue_mode_change.assert_called_once_with(
            6, "idle", "move_to_partner", "partner_found"
        )
        # Observer registry should NOT be used
        observer_registry.notify.assert_not_called()
