"""
Unit tests for the new extensible observer base class.

Tests the ExtensibleObserver class including all emission methods,
validation, compression, and lifecycle management.
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.econsim.observability.new_architecture.extensible_observer import ExtensibleObserver


class MockConfig:
    """Mock configuration for testing."""
    pass


class MockExtensibleObserver(ExtensibleObserver):
    """Test implementation of ExtensibleObserver."""
    
    def __init__(self, config, output_path=None):
        super().__init__(config, output_path)
        self._events_emitted = []
    
    def notify(self, event):
        """Mock notify method."""
        pass
    
    def _write_log_entry(self, entry_dict):
        """Override to capture entries for testing."""
        self._events_emitted.append(entry_dict)
        super()._write_log_entry(entry_dict)


class TestExtensibleObserverClass:
    """Test suite for ExtensibleObserver."""
    
    def test_initialization_with_output_path(self):
        """Test observer initialization with output path."""
        config = MockConfig()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.log"
            observer = MockExtensibleObserver(config, output_path)
            
            assert observer._config == config
            assert observer._output_path == output_path
            assert observer._log_writer is not None
            assert not observer._closed
            assert observer._simulation_start_time is None
    
    def test_initialization_without_output_path(self):
        """Test observer initialization without output path."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        assert observer._config == config
        assert observer._output_path is None
        assert observer._log_writer is None
        assert not observer._closed
    
    def test_set_simulation_start_time(self):
        """Test setting simulation start time."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        start_time = time.time()
        observer.set_simulation_start_time(start_time)
        
        assert observer._simulation_start_time == start_time
    
    def test_get_delta_time_with_start_time(self):
        """Test delta time calculation with start time set."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        start_time = time.time() - 1.0  # 1 second ago
        observer.set_simulation_start_time(start_time)
        
        delta = observer._get_delta_time()
        assert delta >= 1.0  # Should be at least 1 second
    
    def test_get_delta_time_without_start_time(self):
        """Test delta time calculation without start time set."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        delta = observer._get_delta_time()
        assert delta == 0.0
    
    def test_emit_trade_execution_basic(self):
        """Test basic trade execution emission."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        observer.emit_trade_execution(
            step=42,
            seller_id=1,
            buyer_id=2,
            give_type="good1",
            take_type="good2",
            delta_u_seller=0.5,
            delta_u_buyer=0.3
        )
        
        assert len(observer._events_emitted) == 1
        event = observer._events_emitted[0]
        
        assert event["s"] == 42
        assert event["e"] == "trade"
        assert "sid:1,bid:2,gt:good1,tt:good2,dus:0.5,dub:0.3" in event["d"]
    
    def test_emit_trade_execution_with_optional_fields(self):
        """Test trade execution emission with optional fields."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        observer.emit_trade_execution(
            step=42,
            seller_id=1,
            buyer_id=2,
            give_type="good1",
            take_type="good2",
            delta_u_seller=0.5,
            delta_u_buyer=0.3,
            trade_location_x=5,
            trade_location_y=7,
            trade_volume=10.0
        )
        
        assert len(observer._events_emitted) == 1
        event = observer._events_emitted[0]
        
        compressed_data = event["d"]
        assert "sid:1,bid:2,gt:good1,tt:good2,dus:0.5,dub:0.3" in compressed_data
        assert "tx:5" in compressed_data
        assert "ty:7" in compressed_data
        assert "vol:10.0" in compressed_data
    
    def test_emit_trade_execution_validation_errors(self):
        """Test trade execution emission validation errors."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        # Test None values
        with pytest.raises(AssertionError, match="seller_id required"):
            observer.emit_trade_execution(42, None, 2, "good1", "good2", 0.5, 0.3)
        
        with pytest.raises(AssertionError, match="buyer_id required"):
            observer.emit_trade_execution(42, 1, None, "good1", "good2", 0.5, 0.3)
        
        with pytest.raises(AssertionError, match="give_type required"):
            observer.emit_trade_execution(42, 1, 2, None, "good2", 0.5, 0.3)
        
        with pytest.raises(AssertionError, match="take_type required"):
            observer.emit_trade_execution(42, 1, 2, "good1", None, 0.5, 0.3)
        
        # Test type errors
        with pytest.raises(AssertionError, match="seller_id must be integer"):
            observer.emit_trade_execution(42, "1", 2, "good1", "good2", 0.5, 0.3)
        
        with pytest.raises(AssertionError, match="buyer_id must be integer"):
            observer.emit_trade_execution(42, 1, "2", "good1", "good2", 0.5, 0.3)
        
        # Test same seller and buyer
        with pytest.raises(AssertionError, match="seller_id and buyer_id must be different"):
            observer.emit_trade_execution(42, 1, 1, "good1", "good2", 0.5, 0.3)
        
        # Test same give and take types
        with pytest.raises(AssertionError, match="give_type and take_type must be different"):
            observer.emit_trade_execution(42, 1, 2, "good1", "good1", 0.5, 0.3)
    
    def test_emit_agent_mode_change_basic(self):
        """Test basic agent mode change emission."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        observer.emit_agent_mode_change(
            step=42,
            agent_id=1,
            old_mode="forage",
            new_mode="trade",
            reason="found_partner"
        )
        
        assert len(observer._events_emitted) == 1
        event = observer._events_emitted[0]
        
        assert event["s"] == 42
        assert event["e"] == "mode"
        assert "aid:1,om:forage,nm:trade,r:found_partner" in event["d"]
    
    def test_emit_agent_mode_change_with_optional_fields(self):
        """Test agent mode change emission with optional fields."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        observer.emit_agent_mode_change(
            step=42,
            agent_id=1,
            old_mode="forage",
            new_mode="trade",
            reason="found_partner",
            transition_duration=0.1,
            decision_confidence=0.8
        )
        
        assert len(observer._events_emitted) == 1
        event = observer._events_emitted[0]
        
        compressed_data = event["d"]
        assert "aid:1,om:forage,nm:trade,r:found_partner" in compressed_data
        assert "dur:0.1" in compressed_data
        assert "conf:0.8" in compressed_data
    
    def test_emit_agent_mode_change_validation_errors(self):
        """Test agent mode change emission validation errors."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        # Test None values
        with pytest.raises(AssertionError, match="agent_id required"):
            observer.emit_agent_mode_change(42, None, "forage", "trade", "reason")
        
        with pytest.raises(AssertionError, match="old_mode required"):
            observer.emit_agent_mode_change(42, 1, None, "trade", "reason")
        
        with pytest.raises(AssertionError, match="new_mode required"):
            observer.emit_agent_mode_change(42, 1, "forage", None, "reason")
        
        with pytest.raises(AssertionError, match="reason required"):
            observer.emit_agent_mode_change(42, 1, "forage", "trade", None)
        
        # Test type errors
        with pytest.raises(AssertionError, match="agent_id must be integer"):
            observer.emit_agent_mode_change(42, "1", "forage", "trade", "reason")
        
        # Test negative agent_id
        with pytest.raises(AssertionError, match="agent_id must be non-negative"):
            observer.emit_agent_mode_change(42, -1, "forage", "trade", "reason")
    
    def test_emit_resource_collection_basic(self):
        """Test basic resource collection emission."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        observer.emit_resource_collection(
            step=42,
            agent_id=1,
            x=5,
            y=7,
            resource_type="good1",
            amount_collected=2,
            utility_gained=1.5
        )
        
        assert len(observer._events_emitted) == 1
        event = observer._events_emitted[0]
        
        assert event["s"] == 42
        assert event["e"] == "collect"
        assert "aid:1,x:5,y:7,rt:good1,amt:2,ug:1.5" in event["d"]
    
    def test_emit_resource_collection_with_optional_fields(self):
        """Test resource collection emission with optional fields."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        carrying_after = {"good1": 3, "good2": 1}
        observer.emit_resource_collection(
            step=42,
            agent_id=1,
            x=5,
            y=7,
            resource_type="good1",
            amount_collected=2,
            utility_gained=1.5,
            carrying_after=carrying_after
        )
        
        assert len(observer._events_emitted) == 1
        event = observer._events_emitted[0]
        
        compressed_data = event["d"]
        assert "aid:1,x:5,y:7,rt:good1,amt:2,ug:1.5" in compressed_data
        assert "ca:good1:3,good2:1" in compressed_data
    
    def test_emit_resource_collection_validation_errors(self):
        """Test resource collection emission validation errors."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        # Test None values
        with pytest.raises(AssertionError, match="agent_id required"):
            observer.emit_resource_collection(42, None, 5, 7, "good1")
        
        with pytest.raises(AssertionError, match="x coordinate required"):
            observer.emit_resource_collection(42, 1, None, 7, "good1")
        
        with pytest.raises(AssertionError, match="y coordinate required"):
            observer.emit_resource_collection(42, 1, 5, None, "good1")
        
        with pytest.raises(AssertionError, match="resource_type required"):
            observer.emit_resource_collection(42, 1, 5, 7, None)
        
        # Test type errors
        with pytest.raises(AssertionError, match="agent_id must be integer"):
            observer.emit_resource_collection(42, "1", 5, 7, "good1")
        
        with pytest.raises(AssertionError, match="x must be integer"):
            observer.emit_resource_collection(42, 1, "5", 7, "good1")
        
        with pytest.raises(AssertionError, match="y must be integer"):
            observer.emit_resource_collection(42, 1, 5, "7", "good1")
        
        with pytest.raises(AssertionError, match="amount_collected must be integer"):
            observer.emit_resource_collection(42, 1, 5, 7, "good1", amount_collected="2")
        
        # Test invalid amount
        with pytest.raises(AssertionError, match="amount_collected must be positive"):
            observer.emit_resource_collection(42, 1, 5, 7, "good1", amount_collected=0)
    
    def test_emit_debug_log_basic(self):
        """Test basic debug log emission."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        observer.emit_debug_log(
            step=42,
            category="TRADE",
            message="Trade executed successfully"
        )
        
        assert len(observer._events_emitted) == 1
        event = observer._events_emitted[0]
        
        assert event["s"] == 42
        assert event["e"] == "debug"
        assert "cat:TRADE,msg:Trade executed successfully" in event["d"]
    
    def test_emit_debug_log_with_agent_id(self):
        """Test debug log emission with agent ID."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        observer.emit_debug_log(
            step=42,
            category="MODE",
            message="Agent changed mode",
            agent_id=1
        )
        
        assert len(observer._events_emitted) == 1
        event = observer._events_emitted[0]
        
        compressed_data = event["d"]
        assert "cat:MODE,msg:Agent changed mode" in compressed_data
        assert "aid:1" in compressed_data
    
    def test_emit_debug_log_validation_errors(self):
        """Test debug log emission validation errors."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        # Test None values
        with pytest.raises(AssertionError, match="category required"):
            observer.emit_debug_log(42, None, "message")
        
        with pytest.raises(AssertionError, match="message required"):
            observer.emit_debug_log(42, "CATEGORY", None)
        
        # Test type errors
        with pytest.raises(AssertionError, match="agent_id must be integer"):
            observer.emit_debug_log(42, "CATEGORY", "message", agent_id="1")
    
    def test_emit_performance_monitor_basic(self):
        """Test basic performance monitor emission."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        observer.emit_performance_monitor(
            step=42,
            metric_name="steps_per_sec",
            metric_value=60.0
        )
        
        assert len(observer._events_emitted) == 1
        event = observer._events_emitted[0]
        
        assert event["s"] == 42
        assert event["e"] == "perf"
        assert "mn:steps_per_sec,mv:60.0" in event["d"]
    
    def test_emit_performance_monitor_with_optional_fields(self):
        """Test performance monitor emission with optional fields."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        observer.emit_performance_monitor(
            step=42,
            metric_name="frame_time",
            metric_value=16.67,
            threshold_exceeded=True,
            details="Frame time exceeded 16ms threshold"
        )
        
        assert len(observer._events_emitted) == 1
        event = observer._events_emitted[0]
        
        compressed_data = event["d"]
        assert "mn:frame_time,mv:16.67" in compressed_data
        assert "te:True" in compressed_data
        assert "det:Frame time exceeded 16ms threshold" in compressed_data
    
    def test_emit_performance_monitor_validation_errors(self):
        """Test performance monitor emission validation errors."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        # Test None values
        with pytest.raises(AssertionError, match="metric_name required"):
            observer.emit_performance_monitor(42, None, 60.0)
        
        # Test type errors
        with pytest.raises(AssertionError, match="metric_value must be numeric"):
            observer.emit_performance_monitor(42, "metric", "60.0")
        
        with pytest.raises(AssertionError, match="threshold_exceeded must be boolean"):
            observer.emit_performance_monitor(42, "metric", 60.0, threshold_exceeded="True")
    
    def test_emit_agent_decision_basic(self):
        """Test basic agent decision emission."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        observer.emit_agent_decision(
            step=42,
            agent_id=1,
            decision_type="movement",
            decision_details="Moved to resource location"
        )
        
        assert len(observer._events_emitted) == 1
        event = observer._events_emitted[0]
        
        assert event["s"] == 42
        assert event["e"] == "decision"
        assert "aid:1,dt:movement,dd:Moved to resource location" in event["d"]
    
    def test_emit_agent_decision_with_optional_fields(self):
        """Test agent decision emission with optional fields."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        observer.emit_agent_decision(
            step=42,
            agent_id=1,
            decision_type="collection",
            decision_details="Collected resource",
            utility_delta=1.5,
            position_x=5,
            position_y=7
        )
        
        assert len(observer._events_emitted) == 1
        event = observer._events_emitted[0]
        
        compressed_data = event["d"]
        assert "aid:1,dt:collection,dd:Collected resource" in compressed_data
        assert "ud:1.5" in compressed_data
        assert "px:5" in compressed_data
        assert "py:7" in compressed_data
    
    def test_emit_agent_decision_validation_errors(self):
        """Test agent decision emission validation errors."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        # Test None values
        with pytest.raises(AssertionError, match="agent_id required"):
            observer.emit_agent_decision(42, None, "type", "details")
        
        with pytest.raises(AssertionError, match="decision_type required"):
            observer.emit_agent_decision(42, 1, None, "details")
        
        with pytest.raises(AssertionError, match="decision_details required"):
            observer.emit_agent_decision(42, 1, "type", None)
        
        # Test type errors
        with pytest.raises(AssertionError, match="agent_id must be integer"):
            observer.emit_agent_decision(42, "1", "type", "details")
        
        # Test negative agent_id
        with pytest.raises(AssertionError, match="agent_id must be non-negative"):
            observer.emit_agent_decision(42, -1, "type", "details")
    
    def test_emit_resource_event_basic(self):
        """Test basic resource event emission."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        observer.emit_resource_event(
            step=42,
            event_type_detail="spawn",
            position_x=5,
            position_y=7,
            resource_type="good1",
            amount=3
        )
        
        assert len(observer._events_emitted) == 1
        event = observer._events_emitted[0]
        
        assert event["s"] == 42
        assert event["e"] == "resource"
        assert "etd:spawn,px:5,py:7,rt:good1,amt:3" in event["d"]
    
    def test_emit_resource_event_with_agent_id(self):
        """Test resource event emission with agent ID."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        observer.emit_resource_event(
            step=42,
            event_type_detail="pickup",
            position_x=5,
            position_y=7,
            resource_type="good1",
            amount=1,
            agent_id=2
        )
        
        assert len(observer._events_emitted) == 1
        event = observer._events_emitted[0]
        
        compressed_data = event["d"]
        assert "etd:pickup,px:5,py:7,rt:good1,amt:1" in compressed_data
        assert "aid:2" in compressed_data
    
    def test_emit_resource_event_validation_errors(self):
        """Test resource event emission validation errors."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        # Test None values
        with pytest.raises(AssertionError, match="event_type_detail required"):
            observer.emit_resource_event(42, None, 5, 7, "good1")
        
        with pytest.raises(AssertionError, match="position_x required"):
            observer.emit_resource_event(42, "spawn", None, 7, "good1")
        
        with pytest.raises(AssertionError, match="position_y required"):
            observer.emit_resource_event(42, "spawn", 5, None, "good1")
        
        with pytest.raises(AssertionError, match="resource_type required"):
            observer.emit_resource_event(42, "spawn", 5, 7, None)
        
        # Test type errors
        with pytest.raises(AssertionError, match="position_x must be integer"):
            observer.emit_resource_event(42, "spawn", "5", 7, "good1")
        
        with pytest.raises(AssertionError, match="position_y must be integer"):
            observer.emit_resource_event(42, "spawn", 5, "7", "good1")
        
        with pytest.raises(AssertionError, match="amount must be integer"):
            observer.emit_resource_event(42, "spawn", 5, 7, "good1", amount="1")
        
        # Test invalid amount
        with pytest.raises(AssertionError, match="amount must be positive"):
            observer.emit_resource_event(42, "spawn", 5, 7, "good1", amount=0)
    
    def test_emit_economic_decision_basic(self):
        """Test basic economic decision emission."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        observer.emit_economic_decision(
            step=42,
            agent_id=1,
            decision_type="resource_selection",
            decision_context="Chose resource with highest utility"
        )
        
        assert len(observer._events_emitted) == 1
        event = observer._events_emitted[0]
        
        assert event["s"] == 42
        assert event["e"] == "econ"
        assert "aid:1,dt:resource_selection,dc:Chose resource with highest utility" in event["d"]
    
    def test_emit_economic_decision_with_optional_fields(self):
        """Test economic decision emission with optional fields."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        observer.emit_economic_decision(
            step=42,
            agent_id=1,
            decision_type="trade_proposal",
            decision_context="Proposed trade with agent 2",
            utility_before=5.0,
            utility_after=6.5,
            opportunity_cost=0.5,
            alternatives_considered=3,
            decision_time_ms=15.2,
            position_x=5,
            position_y=7
        )
        
        assert len(observer._events_emitted) == 1
        event = observer._events_emitted[0]
        
        compressed_data = event["d"]
        assert "aid:1,dt:trade_proposal,dc:Proposed trade with agent 2" in compressed_data
        assert "ub:5.0" in compressed_data
        assert "ua:6.5" in compressed_data
        assert "oc:0.5" in compressed_data
        assert "ac:3" in compressed_data
        assert "dtm:15.2" in compressed_data
        assert "px:5" in compressed_data
        assert "py:7" in compressed_data
    
    def test_emit_economic_decision_validation_errors(self):
        """Test economic decision emission validation errors."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        # Test None values
        with pytest.raises(AssertionError, match="agent_id required"):
            observer.emit_economic_decision(42, None, "type", "context")
        
        with pytest.raises(AssertionError, match="decision_type required"):
            observer.emit_economic_decision(42, 1, None, "context")
        
        with pytest.raises(AssertionError, match="decision_context required"):
            observer.emit_economic_decision(42, 1, "type", None)
        
        # Test type errors
        with pytest.raises(AssertionError, match="agent_id must be integer"):
            observer.emit_economic_decision(42, "1", "type", "context")
        
        # Test negative agent_id
        with pytest.raises(AssertionError, match="agent_id must be non-negative"):
            observer.emit_economic_decision(42, -1, "type", "context")
        
        # Test negative alternatives_considered
        with pytest.raises(AssertionError, match="alternatives_considered must be non-negative"):
            observer.emit_economic_decision(42, 1, "type", "context", alternatives_considered=-1)
        
        # Test negative decision_time_ms
        with pytest.raises(AssertionError, match="decision_time_ms must be non-negative"):
            observer.emit_economic_decision(42, 1, "type", "context", decision_time_ms=-1.0)
    
    def test_emit_gui_display_basic(self):
        """Test basic GUI display emission."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        observer.emit_gui_display(
            step=42,
            display_type="highlight",
            element_id="agent_1"
        )
        
        assert len(observer._events_emitted) == 1
        event = observer._events_emitted[0]
        
        assert event["s"] == 42
        assert event["e"] == "gui"
        assert "dt:highlight,eid:agent_1" in event["d"]
    
    def test_emit_gui_display_with_data(self):
        """Test GUI display emission with data."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        data = {"color": "red", "duration": 2.0}
        observer.emit_gui_display(
            step=42,
            display_type="overlay",
            element_id="trade_panel",
            data=data
        )
        
        assert len(observer._events_emitted) == 1
        event = observer._events_emitted[0]
        
        compressed_data = event["d"]
        assert "dt:overlay,eid:trade_panel" in compressed_data
        assert "data:color:red,duration:2.0" in compressed_data
    
    def test_emit_gui_display_validation_errors(self):
        """Test GUI display emission validation errors."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        # Test None values
        with pytest.raises(AssertionError, match="display_type required"):
            observer.emit_gui_display(42, None, "element_id")
        
        with pytest.raises(AssertionError, match="element_id required"):
            observer.emit_gui_display(42, "type", None)
    
    def test_flush_step(self):
        """Test flush_step method."""
        config = MockConfig()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.log"
            
            with MockExtensibleObserver(config, output_path) as observer:
                # Emit some events
                observer.emit_trade_execution(42, 1, 2, "good1", "good2", 0.5, 0.3)
                observer.emit_agent_mode_change(42, 1, "forage", "trade", "reason")
                
                # Flush step
                observer.flush_step(42)
            
            # Verify events were written to file
            with open(output_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 2
    
    def test_close(self):
        """Test close method."""
        config = MockConfig()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.log"
            observer = MockExtensibleObserver(config, output_path)
            
            assert not observer._closed
            
            observer.close()
            
            assert observer._closed
    
    def test_context_manager(self):
        """Test context manager functionality."""
        config = MockConfig()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.log"
            
            with MockExtensibleObserver(config, output_path) as observer:
                assert not observer._closed
                observer.emit_trade_execution(42, 1, 2, "good1", "good2", 0.5, 0.3)
            
            # Observer should be closed after context exit
            assert observer._closed
            
            # Verify events were written to file
            with open(output_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 1
    
    def test_get_observer_stats(self):
        """Test get_observer_stats method."""
        config = MockConfig()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.log"
            observer = MockExtensibleObserver(config, output_path)
            
            stats = observer.get_observer_stats()
            
            assert stats['observer_type'] == 'MockExtensibleObserver'
            assert stats['is_closed'] == False
            assert stats['has_log_writer'] == True
            assert stats['output_path'] == str(output_path)
            assert 'entries_written' in stats
            assert 'bytes_written' in stats
            assert 'flush_count' in stats
    
    def test_is_closed_property(self):
        """Test is_closed property."""
        config = MockConfig()
        observer = MockExtensibleObserver(config)
        
        assert not observer.is_closed
        
        observer.close()
        
        assert observer.is_closed
