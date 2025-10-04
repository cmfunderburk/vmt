"""Tests for FileObserver functionality."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock

# Add src to Python path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))

from econsim.observability.observers.file_observer import FileObserver
from econsim.observability.config import ObservabilityConfig


class TestFileObserver:
    """Test FileObserver recording and output format."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock config
        self.config = Mock(spec=ObservabilityConfig)
        self.config.behavioral_aggregation = False
        self.config.correlation_tracking = False
        
        # Create temporary directory for test output
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = Path(self.temp_dir) / "test_events.jsonl"
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_file_observer_initialization(self):
        """Test that FileObserver initializes correctly."""
        observer = FileObserver(
            config=self.config,
            output_path=self.output_path
        )
        
        assert observer is not None
        assert observer.output_path == self.output_path
        assert observer._format == 'jsonl'
        assert not observer._closed
    
    def test_file_observer_records_trade_events(self):
        """Test that FileObserver captures trade events."""
        observer = FileObserver(
            config=self.config,
            output_path=self.output_path
        )
        
        # Record trade events using actual method names from audit
        observer.record_trade(
            step=1,
            seller_id=0,
            buyer_id=1,
            give_type="wood",
            take_type="stone",
            delta_u_seller=5.0,
            delta_u_buyer=3.0,
            trade_location_x=10,
            trade_location_y=15
        )
        
        observer.record_trade(
            step=2,
            seller_id=1,
            buyer_id=2,
            give_type="stone",
            take_type="wood"
        )
        
        # Verify events were recorded in memory
        events = observer.get_all_events()
        assert len(events) == 2
        
        # Verify first event
        event1 = events[0]
        assert event1["type"] == "trade"
        assert event1["step"] == 1
        assert event1["seller_id"] == 0
        assert event1["buyer_id"] == 1
        assert event1["give_type"] == "wood"
        assert event1["take_type"] == "stone"
        assert event1["delta_u_seller"] == 5.0
        assert event1["delta_u_buyer"] == 3.0
        assert event1["trade_location_x"] == 10
        assert event1["trade_location_y"] == 15
        
        # Verify second event
        event2 = events[1]
        assert event2["type"] == "trade"
        assert event2["step"] == 2
        assert event2["seller_id"] == 1
        assert event2["buyer_id"] == 2
        assert event2["give_type"] == "stone"
        assert event2["take_type"] == "wood"
    
    def test_file_observer_records_mode_change_events(self):
        """Test that FileObserver captures mode change events."""
        observer = FileObserver(
            config=self.config,
            output_path=self.output_path
        )
        
        # Record mode change events
        observer.record_mode_change(
            step=10,
            agent_id=0,
            old_mode="foraging",
            new_mode="trading",
            reason="found partner"
        )
        
        observer.record_mode_change(
            step=11,
            agent_id=1,
            old_mode="trading",
            new_mode="foraging",
            reason="no more resources"
        )
        
        # Verify events were recorded
        events = observer.get_all_events()
        assert len(events) == 2
        
        # Verify first event
        event1 = events[0]
        assert event1["type"] == "mode_change"
        assert event1["step"] == 10
        assert event1["agent_id"] == 0
        assert event1["old_mode"] == "foraging"
        assert event1["new_mode"] == "trading"
        assert event1["reason"] == "found partner"
        
        # Verify second event
        event2 = events[1]
        assert event2["type"] == "mode_change"
        assert event2["step"] == 11
        assert event2["agent_id"] == 1
        assert event2["old_mode"] == "trading"
        assert event2["new_mode"] == "foraging"
        assert event2["reason"] == "no more resources"
    
    def test_file_observer_records_resource_collection_events(self):
        """Test that FileObserver captures resource collection events."""
        observer = FileObserver(
            config=self.config,
            output_path=self.output_path
        )
        
        # Record resource collection events
        observer.record_resource_collection(
            step=5,
            agent_id=0,
            x=10,
            y=15,
            resource_type="wood",
            amount_collected=2,
            utility_gained=4.0,
            carrying_after={"wood": 3, "stone": 1}
        )
        
        observer.record_resource_collection(
            step=6,
            agent_id=1,
            x=20,
            y=25,
            resource_type="stone"
        )
        
        # Verify events were recorded
        events = observer.get_all_events()
        assert len(events) == 2
        
        # Verify first event
        event1 = events[0]
        assert event1["type"] == "resource_collection"
        assert event1["step"] == 5
        assert event1["agent_id"] == 0
        assert event1["x"] == 10
        assert event1["y"] == 15
        assert event1["resource_type"] == "wood"
        assert event1["amount_collected"] == 2
        assert event1["utility_gained"] == 4.0
        assert event1["carrying_after"] == {"wood": 3, "stone": 1}
        
        # Verify second event
        event2 = events[1]
        assert event2["type"] == "resource_collection"
        assert event2["step"] == 6
        assert event2["agent_id"] == 1
        assert event2["x"] == 20
        assert event2["y"] == 25
        assert event2["resource_type"] == "stone"
        assert event2["amount_collected"] == 1  # default value
    
    def test_file_observer_records_debug_log_events(self):
        """Test that FileObserver captures debug log events."""
        observer = FileObserver(
            config=self.config,
            output_path=self.output_path
        )
        
        # Record debug log events
        observer.record_debug_log(
            step=1,
            category="MOVEMENT",
            message="Agent 0 moved from (10,10) to (11,10)",
            agent_id=0
        )
        
        observer.record_debug_log(
            step=2,
            category="TRADE",
            message="Trade initiated between agents 0 and 1"
        )
        
        # Verify events were recorded
        events = observer.get_all_events()
        assert len(events) == 2
        
        # Verify first event
        event1 = events[0]
        assert event1["type"] == "debug_log"
        assert event1["step"] == 1
        assert event1["category"] == "MOVEMENT"
        assert event1["message"] == "Agent 0 moved from (10,10) to (11,10)"
        assert event1["agent_id"] == 0
        
        # Verify second event
        event2 = events[1]
        assert event2["type"] == "debug_log"
        assert event2["step"] == 2
        assert event2["category"] == "TRADE"
        assert event2["message"] == "Trade initiated between agents 0 and 1"
        assert event2["agent_id"] == -1  # default value
    
    def test_file_observer_records_all_event_types(self):
        """Test that FileObserver can record all event types from audit."""
        observer = FileObserver(
            config=self.config,
            output_path=self.output_path
        )
        
        # Record one event of each type
        observer.record_trade(step=1, seller_id=0, buyer_id=1, give_type="wood", take_type="stone")
        observer.record_mode_change(step=2, agent_id=0, old_mode="foraging", new_mode="trading")
        observer.record_resource_collection(step=3, agent_id=0, x=10, y=15, resource_type="wood")
        observer.record_debug_log(step=4, category="TEST", message="Debug message")
        observer.record_performance_monitor(step=5, metric_name="step_time", metric_value=1.5)
        observer.record_agent_decision(step=6, agent_id=0, decision_type="movement", decision_details="Moving to resource")
        observer.record_resource_event(step=7, event_type_detail="spawn", position_x=20, position_y=25, resource_type="stone")
        observer.record_economic_decision(step=8, agent_id=0, decision_type="resource_selection", decision_context="Choosing resource")
        
        # Verify all events were recorded
        events = observer.get_all_events()
        assert len(events) == 8
        
        # Verify event types
        event_types = {event["type"] for event in events}
        expected_types = {
            "trade", "mode_change", "resource_collection", "debug_log",
            "performance_monitor", "agent_decision", "resource_event", "economic_decision"
        }
        assert event_types == expected_types
    
    def test_file_observer_output_format_matches_schema(self):
        """Test that output format matches schema."""
        observer = FileObserver(
            config=self.config,
            output_path=self.output_path
        )
        
        # Record a trade event
        observer.record_trade(
            step=100,
            seller_id=1,
            buyer_id=2,
            give_type="wood",
            take_type="stone",
            delta_u_seller=5.0,
            delta_u_buyer=3.0,
            trade_location_x=15,
            trade_location_y=20
        )
        
        # Get the recorded event
        events = observer.get_all_events()
        assert len(events) == 1
        
        event = events[0]
        
        # Verify schema compliance
        from econsim.observability.event_schema import validate_event, get_required_fields
        
        # Should validate against schema
        assert validate_event(event)
        
        # Should have all required fields
        required_fields = get_required_fields("trade")
        for field in required_fields:
            assert field in event
        
        # Should have correct types
        assert isinstance(event["step"], int)
        assert isinstance(event["seller_id"], int)
        assert isinstance(event["buyer_id"], int)
        assert isinstance(event["give_type"], str)
        assert isinstance(event["take_type"], str)
        assert isinstance(event["delta_u_seller"], float)
        assert isinstance(event["delta_u_buyer"], float)
        assert isinstance(event["trade_location_x"], int)
        assert isinstance(event["trade_location_y"], int)
    
    def test_file_observer_event_filtering(self):
        """Test that FileObserver respects event filtering."""
        observer = FileObserver(
            config=self.config,
            output_path=self.output_path
        )
        
        # Check that enabled event types are set
        assert observer.is_enabled("trade_execution")
        assert observer.is_enabled("agent_mode_change")
        assert observer.is_enabled("resource_collection")
        assert observer.is_enabled("debug_log")
        assert observer.is_enabled("performance_monitor")
        assert observer.is_enabled("agent_decision")
        assert observer.is_enabled("resource_event")
        assert observer.is_enabled("economic_decision")
    
    def test_file_observer_statistics(self):
        """Test that FileObserver provides accurate statistics."""
        observer = FileObserver(
            config=self.config,
            output_path=self.output_path
        )
        
        # Record some events
        for i in range(10):
            observer.record_debug_log(step=i, category="TEST", message=f"Message {i}")
        
        # Get statistics
        stats = observer.get_statistics()
        
        assert stats["total_events"] == 10
        assert "debug_log" in stats["event_types"]
        assert stats["step_range"] == (0, 9)
        assert stats["events_per_second"] >= 0.0
    
    def test_file_observer_close_and_write(self):
        """Test that FileObserver writes events to disk when closed."""
        observer = FileObserver(
            config=self.config,
            output_path=self.output_path
        )
        
        # Record some events
        observer.record_trade(step=1, seller_id=0, buyer_id=1, give_type="wood", take_type="stone")
        observer.record_mode_change(step=2, agent_id=0, old_mode="foraging", new_mode="trading")
        
        # Close observer (this should write to disk)
        observer.close()
        
        # Verify file was created
        assert self.output_path.exists()
        
        # Verify file contains data
        assert self.output_path.stat().st_size > 0
    
    def test_file_observer_memory_usage_estimate(self):
        """Test memory usage estimation."""
        observer = FileObserver(
            config=self.config,
            output_path=self.output_path
        )
        
        # Record some events
        for i in range(100):
            observer.record_debug_log(step=i, category="TEST", message=f"Message {i}")
        
        # Get memory usage estimate
        memory_stats = observer.get_memory_usage_estimate()
        
        assert memory_stats["events_count"] == 100
        assert memory_stats["total_bytes"] > 0
        assert memory_stats["bytes_per_event"] > 0
        assert memory_stats["bytes_per_event"] < 1000  # Should be reasonable


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
