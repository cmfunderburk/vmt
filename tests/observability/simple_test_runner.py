"""Simple test runner for FileObserver without pytest dependency."""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))

from econsim.observability.observers.file_observer import FileObserver
from econsim.observability.config import ObservabilityConfig


def run_test(test_name, test_func):
    """Run a single test and report results."""
    try:
        test_func()
        print(f"✓ {test_name}")
        return True
    except Exception as e:
        print(f"✗ {test_name}: {e}")
        return False


def test_file_observer_initialization():
    """Test that FileObserver initializes correctly."""
    # Create a mock config
    config = Mock(spec=ObservabilityConfig)
    config.behavioral_aggregation = False
    config.correlation_tracking = False
    
    # Create temporary directory for test output
    temp_dir = tempfile.mkdtemp()
    output_path = Path(temp_dir) / "test_events.jsonl"
    
    try:
        observer = FileObserver(
            config=config,
            output_path=output_path
        )
        
        assert observer is not None
        assert observer.output_path == output_path
        assert observer._format == 'jsonl'
        assert not observer._closed
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_file_observer_records_events():
    """Test that FileObserver captures events."""
    # Create a mock config
    config = Mock(spec=ObservabilityConfig)
    config.behavioral_aggregation = False
    config.correlation_tracking = False
    
    # Create temporary directory for test output
    temp_dir = tempfile.mkdtemp()
    output_path = Path(temp_dir) / "test_events.jsonl"
    
    try:
        observer = FileObserver(
            config=config,
            output_path=output_path
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
        
        observer.record_mode_change(
            step=2,
            agent_id=0,
            old_mode="foraging",
            new_mode="trading",
            reason="found partner"
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
        
        # Verify second event
        event2 = events[1]
        assert event2["type"] == "mode_change"
        assert event2["step"] == 2
        assert event2["agent_id"] == 0
        assert event2["old_mode"] == "foraging"
        assert event2["new_mode"] == "trading"
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_file_observer_schema_compliance():
    """Test that recorded events comply with schema."""
    # Create a mock config
    config = Mock(spec=ObservabilityConfig)
    config.behavioral_aggregation = False
    config.correlation_tracking = False
    
    # Create temporary directory for test output
    temp_dir = tempfile.mkdtemp()
    output_path = Path(temp_dir) / "test_events.jsonl"
    
    try:
        observer = FileObserver(
            config=config,
            output_path=output_path
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
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_file_observer_all_event_types():
    """Test that FileObserver can record all event types from audit."""
    # Create a mock config
    config = Mock(spec=ObservabilityConfig)
    config.behavioral_aggregation = False
    config.correlation_tracking = False
    
    # Create temporary directory for test output
    temp_dir = tempfile.mkdtemp()
    output_path = Path(temp_dir) / "test_events.jsonl"
    
    try:
        observer = FileObserver(
            config=config,
            output_path=output_path
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
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """Run all FileObserver tests."""
    print("Running FileObserver tests...")
    print()
    
    tests = [
        ("FileObserver initialization", test_file_observer_initialization),
        ("FileObserver records events", test_file_observer_records_events),
        ("FileObserver schema compliance", test_file_observer_schema_compliance),
        ("FileObserver all event types", test_file_observer_all_event_types),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed += 1
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All FileObserver tests passed!")
        return True
    else:
        print("✗ Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
