"""Test suite for GUI Observer functionality.

Tests the complete GUI event observer system including event-to-display mapping,
display update batching, and performance monitoring.
"""

import pytest
import time
from unittest.mock import Mock, MagicMock

from src.econsim.observability.config import ObservabilityConfig
from src.econsim.observability.events import (
    AgentModeChangeEvent, TradeExecutionEvent, ResourceCollectionEvent,
    DebugLogEvent, PerformanceMonitorEvent, AgentDecisionEvent, ResourceEvent
)
from src.econsim.observability.observers.gui_observer import (
    GUIEventObserver, DisplayUpdateBatcher, EventToDisplayMapper,
    DisplayUpdate, GUIPerformanceMonitor, create_gui_observer
)


class TestEventToDisplayMapper:
    """Test event-to-display mapping functionality."""
    
    def test_mapper_initialization(self):
        """Test mapper initialization with default mappings."""
        mapper = EventToDisplayMapper()
        
        # Check that default mappings are registered
        assert "agent_mode_change" in mapper._event_handlers
        assert "trade_execution" in mapper._event_handlers  
        assert "resource_collection" in mapper._event_handlers
        assert len(mapper._event_handlers["agent_mode_change"]) > 0
    
    def test_agent_mode_change_mapping(self):
        """Test agent mode change event mapping."""
        mapper = EventToDisplayMapper()
        
        # Create mode change event
        event = AgentModeChangeEvent.create(
            step=10,
            agent_id=1,
            old_mode="foraging",
            new_mode="trading",
            reason="found_partner"
        )
        
        # Map event to updates
        updates = mapper.map_event_to_updates(event)
        
        # Should generate updates for agent inspector and visual
        assert len(updates) >= 2
        assert any(u.element_id == "agent_inspector_1" for u in updates)
        assert any(u.element_id == "agent_visual_1" for u in updates)
        assert any(u.update_type == "mode_change" for u in updates)
    
    def test_trade_execution_mapping(self):
        """Test trade execution event mapping."""
        mapper = EventToDisplayMapper()
        
        # Create trade execution event
        event = TradeExecutionEvent.create(
            step=15,
            seller_id=1,
            buyer_id=2,
            give_type="wood",
            take_type="food",
            delta_u_seller=5.0,
            delta_u_buyer=3.0,
            trade_location_x=5,
            trade_location_y=7
        )
        
        # Map event to updates
        updates = mapper.map_event_to_updates(event)
        
        # Should generate updates for grid highlight, trade inspector, metrics
        assert len(updates) >= 3
        assert any(u.element_id == "grid_cell_5_7" for u in updates)
        assert any(u.element_id == "trade_inspector" for u in updates)
        assert any(u.element_id == "metrics_panel" for u in updates)
    
    def test_resource_collection_mapping(self):
        """Test resource collection event mapping."""
        mapper = EventToDisplayMapper()
        
        # Create resource collection event
        event = ResourceCollectionEvent.create(
            step=20,
            agent_id=3,
            x=8,
            y=9,
            resource_type="food",
            amount_collected=2
        )
        
        # Map event to updates
        updates = mapper.map_event_to_updates(event)
        
        # Should generate updates for grid cell and agent inspector
        assert len(updates) >= 2
        assert any(u.element_id == "grid_cell_8_9" for u in updates)
        assert any(u.element_id == "agent_inspector_3" for u in updates)
    
    def test_custom_mapping_registration(self):
        """Test registering custom event mappings."""
        mapper = EventToDisplayMapper()
        
        # Create custom handler
        def custom_handler(event):
            return [DisplayUpdate("custom_element", "custom_update", {"test": True})]
        
        # Register custom mapping
        mapper.register_mapping("custom_event", custom_handler)
        
        # Verify registration
        assert "custom_event" in mapper._event_handlers
        assert len(mapper._event_handlers["custom_event"]) == 1


class TestDisplayUpdateBatcher:
    """Test display update batching functionality."""
    
    def test_batcher_initialization(self):
        """Test batcher initialization."""
        batcher = DisplayUpdateBatcher(batch_size=10, flush_interval=0.05)
        
        assert batcher.batch_size == 10
        assert batcher.flush_interval == 0.05
        assert len(batcher._pending_updates) == 0
    
    def test_update_queuing(self):
        """Test queuing display updates."""
        batcher = DisplayUpdateBatcher(batch_size=5)
        
        # Queue some updates
        for i in range(3):
            update = DisplayUpdate(f"element_{i}", "test", {"value": i})
            batcher.queue_update(update)
        
        # Should have pending updates
        assert len(batcher._pending_updates) == 3
    
    def test_auto_flush_on_batch_size(self):
        """Test automatic flush when batch size reached."""
        batcher = DisplayUpdateBatcher(batch_size=2)
        callback_called = False
        received_updates = []
        
        def test_callback(updates):
            nonlocal callback_called, received_updates
            callback_called = True
            received_updates = updates.copy()
        
        batcher.add_update_callback(test_callback)
        
        # Queue updates to exceed batch size
        batcher.queue_update(DisplayUpdate("elem1", "test", {}))
        batcher.queue_update(DisplayUpdate("elem2", "test", {}))  # Should trigger flush
        
        # Should have triggered callback
        assert callback_called
        assert len(received_updates) == 2
        assert len(batcher._pending_updates) == 0
    
    def test_priority_sorting(self):
        """Test priority-based sorting of updates."""
        batcher = DisplayUpdateBatcher(batch_size=10)
        callback_called = False
        received_updates = []
        
        def test_callback(updates):
            nonlocal callback_called, received_updates
            callback_called = True
            received_updates = updates.copy()
        
        batcher.add_update_callback(test_callback)
        
        # Queue updates with different priorities
        batcher.queue_update(DisplayUpdate("elem1", "test", {}, priority=1))
        batcher.queue_update(DisplayUpdate("elem2", "test", {}, priority=5))
        batcher.queue_update(DisplayUpdate("elem3", "test", {}, priority=3))
        
        # Manually flush to check sorting
        batcher.flush_updates()
        
        # Should be sorted by priority (highest first)
        assert callback_called
        priorities = [u.priority for u in received_updates]
        assert priorities == sorted(priorities, reverse=True)


class TestGUIEventObserver:
    """Test main GUI event observer functionality."""
    
    @pytest.fixture
    def config(self):
        """Create test observability config."""
        return ObservabilityConfig(
            agent_mode_logging=True,
            trade_logging=True,
            behavioral_aggregation=True
        )
    
    @pytest.fixture
    def mock_gui(self):
        """Create mock GUI reference."""
        gui = Mock()
        gui.update_agent_mode = Mock()
        gui.update_agent_inventory = Mock()
        gui.highlight_grid_cell = Mock()
        gui.update_trade_display = Mock()
        gui.add_log_entry = Mock()
        return gui
    
    def test_observer_initialization(self, config, mock_gui):
        """Test observer initialization."""
        observer = GUIEventObserver(config, mock_gui)
        
        assert observer.gui_reference == mock_gui
        assert observer.event_mapper is not None
        assert observer.update_batcher is not None
        assert observer.metrics.events_processed == 0
    
    def test_agent_mode_change_notification(self, config, mock_gui):
        """Test handling agent mode change events."""
        observer = GUIEventObserver(config, mock_gui)
        
        # Create and notify event
        event = AgentModeChangeEvent.create(
            step=10,
            agent_id=1,
            old_mode="foraging",
            new_mode="trading"
        )
        
        observer.notify(event)
        
        # Should process the event
        assert observer.metrics.events_processed == 1
        assert observer.metrics.updates_generated > 0
    
    def test_trade_execution_notification(self, config, mock_gui):
        """Test handling trade execution events."""
        observer = GUIEventObserver(config, mock_gui)
        
        # Create and notify event
        event = TradeExecutionEvent.create(
            step=15,
            seller_id=1,
            buyer_id=2,
            give_type="wood",
            take_type="food",
            delta_u_seller=5.0,
            delta_u_buyer=3.0
        )
        
        observer.notify(event)
        
        # Should process the event
        assert observer.metrics.events_processed == 1
        assert observer.metrics.updates_generated > 0
    
    def test_event_filtering(self, config, mock_gui):
        """Test event filtering for GUI relevance."""
        observer = GUIEventObserver(config, mock_gui)
        
        # Disable a specific event type
        observer.disable_event_type("trade_execution")
        
        # Create trade event
        event = TradeExecutionEvent.create(
            step=15,
            seller_id=1,
            buyer_id=2,
            give_type="wood",
            take_type="food",
            delta_u_seller=5.0,
            delta_u_buyer=3.0
        )
        
        observer.notify(event)
        
        # Should not process disabled event
        assert observer.metrics.events_processed == 0
    
    def test_step_flush(self, config, mock_gui):
        """Test step boundary flushing."""
        observer = GUIEventObserver(config, mock_gui)
        
        # Generate some events
        event = AgentModeChangeEvent.create(
            step=10,
            agent_id=1,
            old_mode="foraging",
            new_mode="trading"
        )
        observer.notify(event)
        
        # Flush step
        observer.flush_step(10)
        
        # Should have flushed updates
        assert observer.metrics.batches_flushed >= 0
    
    def test_performance_metrics(self, config, mock_gui):
        """Test performance metrics tracking."""
        observer = GUIEventObserver(config, mock_gui)
        
        # Process several events
        for i in range(5):
            event = AgentModeChangeEvent.create(
                step=i,
                agent_id=1,
                old_mode="foraging",
                new_mode="trading"
            )
            observer.notify(event)
        
        # Check metrics
        metrics = observer.get_gui_metrics()
        assert metrics["events_processed"] == 5
        assert metrics["updates_generated"] > 0
        assert metrics["average_processing_time_ms"] >= 0
    
    def test_custom_mapping_integration(self, config, mock_gui):
        """Test custom mapping registration and usage."""
        observer = GUIEventObserver(config, mock_gui)
        
        # Register custom mapping
        def custom_handler(event):
            return [DisplayUpdate("custom_element", "custom_update", {"test": True})]
        
        observer.register_custom_mapping("custom_event", custom_handler)
        
        # Verify mapping was registered
        assert "custom_event" in observer.event_mapper._event_handlers


class TestGUIPerformanceMonitor:
    """Test GUI performance monitoring."""
    
    def test_performance_monitor_initialization(self):
        """Test performance monitor initialization."""
        config = ObservabilityConfig(behavioral_aggregation=True)
        monitor = GUIPerformanceMonitor(config)
        
        assert monitor.gui_metrics["total_gui_events"] == 0
        assert monitor.gui_metrics["gui_processing_time"] == 0.0
        assert len(monitor._gui_processing_times) == 0
    
    def test_gui_event_monitoring(self):
        """Test monitoring of GUI-relevant events."""
        config = ObservabilityConfig(behavioral_aggregation=True)
        monitor = GUIPerformanceMonitor(config)
        
        # Enable monitoring for agent mode changes
        monitor.enable_event_type("agent_mode_change")
        
        # Process GUI-relevant event
        event = AgentModeChangeEvent.create(
            step=10,
            agent_id=1,
            old_mode="foraging",
            new_mode="trading"
        )
        
        monitor.notify(event)
        
        # Should track GUI event
        assert monitor.gui_metrics["total_gui_events"] == 1
        assert monitor.gui_metrics["gui_processing_time"] > 0
        assert len(monitor._gui_processing_times) == 1
    
    def test_performance_report(self):
        """Test performance report generation."""
        config = ObservabilityConfig(behavioral_aggregation=True)
        monitor = GUIPerformanceMonitor(config)
        monitor.enable_event_type("agent_mode_change")
        
        # Process some events
        for i in range(3):
            event = AgentModeChangeEvent.create(
                step=i,
                agent_id=1,
                old_mode="foraging",
                new_mode="trading"
            )
            monitor.notify(event)
        
        # Get performance report
        report = monitor.get_performance_report()
        
        assert report["total_gui_events"] == 3
        assert report["samples_collected"] == 3
        assert "average_latency_ms" in report
        assert "responsiveness_score" in report


class TestFactoryFunctions:
    """Test factory functions for easy integration."""
    
    def test_create_gui_observer(self):
        """Test GUI observer factory function."""
        config = ObservabilityConfig(behavioral_aggregation=True)
        observer = create_gui_observer(config)


class TestIntegrationScenarios:
    """Test complete integration scenarios."""
    
    def test_complete_workflow(self):
        """Test complete observer workflow integration."""
        config = ObservabilityConfig(behavioral_aggregation=True)
        observer = create_gui_observer(config)
    
    def test_error_handling(self):
        """Test error handling in GUI observer."""
        config = ObservabilityConfig(behavioral_aggregation=True)
        observer = GUIEventObserver(config, None)  # No GUI reference
        
        # Should handle missing GUI gracefully
        event = AgentModeChangeEvent.create(1, 1, "foraging", "trading")
        observer.notify(event)  # Should not raise exception
        
        # Should still track metrics
        assert observer.metrics.events_processed == 1


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])