"""
Unit tests for RawDataObserver - Zero-overhead data storage.

Tests the zero-overhead logging system that stores raw simulation data
as primitive types with no processing overhead during simulation.

Test Categories:
- Recording methods: All record_*() methods for different event types
- Data access: Event filtering and retrieval methods
- Statistics: Observer metrics and metadata
- Performance: Zero-overhead recording speed validation
- Memory: Memory usage estimation and efficiency
- Edge cases: Error handling and boundary conditions
"""

import pytest
import time
from typing import Dict, List, Any

from econsim.observability.raw_data.raw_data_observer import RawDataObserver


class TestRawDataObserverRecording:
    """Test all record_*() methods for different event types."""
    
    def test_record_trade_basic(self):
        """Test basic trade recording functionality."""
        observer = RawDataObserver()
        
        observer.record_trade(
            step=100,
            seller_id=1,
            buyer_id=2,
            give_type="wood",
            take_type="stone"
        )
        
        events = observer.get_all_events()
        assert len(events) == 1
        
        event = events[0]
        assert event['type'] == 'trade'
        assert event['step'] == 100
        assert event['seller_id'] == 1
        assert event['buyer_id'] == 2
        assert event['give_type'] == 'wood'
        assert event['take_type'] == 'stone'
        assert event['delta_u_seller'] == 0.0
        assert event['delta_u_buyer'] == 0.0
        assert event['trade_location_x'] == -1
        assert event['trade_location_y'] == -1
    
    def test_record_trade_with_optional_fields(self):
        """Test trade recording with all optional fields."""
        observer = RawDataObserver()
        
        observer.record_trade(
            step=100,
            seller_id=1,
            buyer_id=2,
            give_type="wood",
            take_type="stone",
            delta_u_seller=5.5,
            delta_u_buyer=3.2,
            trade_location_x=10,
            trade_location_y=20,
            custom_field="test_value"
        )
        
        events = observer.get_all_events()
        event = events[0]
        
        assert event['delta_u_seller'] == 5.5
        assert event['delta_u_buyer'] == 3.2
        assert event['trade_location_x'] == 10
        assert event['trade_location_y'] == 20
        assert event['custom_field'] == 'test_value'
    
    def test_record_mode_change_basic(self):
        """Test basic mode change recording functionality."""
        observer = RawDataObserver()
        
        observer.record_mode_change(
            step=101,
            agent_id=1,
            old_mode="foraging",
            new_mode="trading",
            reason="found partner"
        )
        
        events = observer.get_all_events()
        assert len(events) == 1
        
        event = events[0]
        assert event['type'] == 'mode_change'
        assert event['step'] == 101
        assert event['agent_id'] == 1
        assert event['old_mode'] == 'foraging'
        assert event['new_mode'] == 'trading'
        assert event['reason'] == 'found partner'
    
    def test_record_mode_change_with_optional_fields(self):
        """Test mode change recording with optional fields."""
        observer = RawDataObserver()
        
        observer.record_mode_change(
            step=101,
            agent_id=1,
            old_mode="foraging",
            new_mode="trading",
            reason="found partner",
            utility_before=10.0,
            utility_after=15.0
        )
        
        events = observer.get_all_events()
        event = events[0]
        
        assert event['utility_before'] == 10.0
        assert event['utility_after'] == 15.0
    
    def test_record_resource_collection_basic(self):
        """Test basic resource collection recording functionality."""
        observer = RawDataObserver()
        
        observer.record_resource_collection(
            step=102,
            agent_id=1,
            x=5,
            y=10,
            resource_type="wood"
        )
        
        events = observer.get_all_events()
        assert len(events) == 1
        
        event = events[0]
        assert event['type'] == 'resource_collection'
        assert event['step'] == 102
        assert event['agent_id'] == 1
        assert event['x'] == 5
        assert event['y'] == 10
        assert event['resource_type'] == 'wood'
        assert event['amount_collected'] == 1
        assert event['utility_gained'] == 0.0
        assert event['carrying_after'] == {}
    
    def test_record_resource_collection_with_inventory(self):
        """Test resource collection recording with inventory data."""
        observer = RawDataObserver()
        
        carrying_after = {"wood": 3, "stone": 1}
        observer.record_resource_collection(
            step=102,
            agent_id=1,
            x=5,
            y=10,
            resource_type="wood",
            amount_collected=2,
            utility_gained=5.5,
            carrying_after=carrying_after
        )
        
        events = observer.get_all_events()
        event = events[0]
        
        assert event['amount_collected'] == 2
        assert event['utility_gained'] == 5.5
        assert event['carrying_after'] == carrying_after
    
    def test_record_debug_log_basic(self):
        """Test basic debug log recording functionality."""
        observer = RawDataObserver()
        
        observer.record_debug_log(
            step=103,
            category="TRADE",
            message="Trade executed successfully"
        )
        
        events = observer.get_all_events()
        assert len(events) == 1
        
        event = events[0]
        assert event['type'] == 'debug_log'
        assert event['step'] == 103
        assert event['category'] == 'TRADE'
        assert event['message'] == 'Trade executed successfully'
        assert event['agent_id'] == -1
    
    def test_record_debug_log_with_agent(self):
        """Test debug log recording with agent context."""
        observer = RawDataObserver()
        
        observer.record_debug_log(
            step=103,
            category="MODE",
            message="Agent changed mode",
            agent_id=5
        )
        
        events = observer.get_all_events()
        event = events[0]
        
        assert event['agent_id'] == 5
    
    def test_record_performance_monitor_basic(self):
        """Test basic performance monitor recording functionality."""
        observer = RawDataObserver()
        
        observer.record_performance_monitor(
            step=104,
            metric_name="steps_per_sec",
            metric_value=60.5
        )
        
        events = observer.get_all_events()
        assert len(events) == 1
        
        event = events[0]
        assert event['type'] == 'performance_monitor'
        assert event['step'] == 104
        assert event['metric_name'] == 'steps_per_sec'
        assert event['metric_value'] == 60.5
        assert event['threshold_exceeded'] == False
        assert event['details'] == ""
    
    def test_record_performance_monitor_with_threshold(self):
        """Test performance monitor recording with threshold exceeded."""
        observer = RawDataObserver()
        
        observer.record_performance_monitor(
            step=104,
            metric_name="memory_usage",
            metric_value=1024.0,
            threshold_exceeded=True,
            details="Memory usage above 1GB threshold"
        )
        
        events = observer.get_all_events()
        event = events[0]
        
        assert event['threshold_exceeded'] == True
        assert event['details'] == "Memory usage above 1GB threshold"
    
    def test_record_agent_decision_basic(self):
        """Test basic agent decision recording functionality."""
        observer = RawDataObserver()
        
        observer.record_agent_decision(
            step=105,
            agent_id=1,
            decision_type="movement",
            decision_details="Moving toward resource at (5, 10)"
        )
        
        events = observer.get_all_events()
        assert len(events) == 1
        
        event = events[0]
        assert event['type'] == 'agent_decision'
        assert event['step'] == 105
        assert event['agent_id'] == 1
        assert event['decision_type'] == 'movement'
        assert event['decision_details'] == 'Moving toward resource at (5, 10)'
        assert event['utility_delta'] == 0.0
        assert event['position_x'] == -1
        assert event['position_y'] == -1
    
    def test_record_agent_decision_with_position(self):
        """Test agent decision recording with position context."""
        observer = RawDataObserver()
        
        observer.record_agent_decision(
            step=105,
            agent_id=1,
            decision_type="collection",
            decision_details="Collecting wood resource",
            utility_delta=2.5,
            position_x=5,
            position_y=10
        )
        
        events = observer.get_all_events()
        event = events[0]
        
        assert event['utility_delta'] == 2.5
        assert event['position_x'] == 5
        assert event['position_y'] == 10
    
    def test_record_resource_event_basic(self):
        """Test basic resource event recording functionality."""
        observer = RawDataObserver()
        
        observer.record_resource_event(
            step=106,
            event_type_detail="spawn",
            position_x=15,
            position_y=20,
            resource_type="stone"
        )
        
        events = observer.get_all_events()
        assert len(events) == 1
        
        event = events[0]
        assert event['type'] == 'resource_event'
        assert event['step'] == 106
        assert event['event_type_detail'] == 'spawn'
        assert event['position_x'] == 15
        assert event['position_y'] == 20
        assert event['resource_type'] == 'stone'
        assert event['amount'] == 1
        assert event['agent_id'] == -1
    
    def test_record_resource_event_with_agent(self):
        """Test resource event recording with agent context."""
        observer = RawDataObserver()
        
        observer.record_resource_event(
            step=106,
            event_type_detail="pickup",
            position_x=15,
            position_y=20,
            resource_type="wood",
            amount=3,
            agent_id=2
        )
        
        events = observer.get_all_events()
        event = events[0]
        
        assert event['amount'] == 3
        assert event['agent_id'] == 2
    
    def test_record_economic_decision_basic(self):
        """Test basic economic decision recording functionality."""
        observer = RawDataObserver()
        
        observer.record_economic_decision(
            step=107,
            agent_id=1,
            decision_type="resource_selection",
            decision_context="Choosing between wood and stone resources"
        )
        
        events = observer.get_all_events()
        assert len(events) == 1
        
        event = events[0]
        assert event['type'] == 'economic_decision'
        assert event['step'] == 107
        assert event['agent_id'] == 1
        assert event['decision_type'] == 'resource_selection'
        assert event['decision_context'] == 'Choosing between wood and stone resources'
        assert event['utility_before'] == 0.0
        assert event['utility_after'] == 0.0
        assert event['utility_delta'] == 0.0
        assert event['opportunity_cost'] == 0.0
        assert event['alternatives_considered'] == 0
        assert event['decision_time_ms'] == 0.0
        assert event['position_x'] == -1
        assert event['position_y'] == -1
    
    def test_record_economic_decision_comprehensive(self):
        """Test economic decision recording with all fields."""
        observer = RawDataObserver()
        
        observer.record_economic_decision(
            step=107,
            agent_id=1,
            decision_type="trade_proposal",
            decision_context="Proposing trade with agent 2",
            utility_before=10.0,
            utility_after=15.0,
            opportunity_cost=2.0,
            alternatives_considered=3,
            decision_time_ms=5.5,
            position_x=10,
            position_y=15
        )
        
        events = observer.get_all_events()
        event = events[0]
        
        assert event['utility_before'] == 10.0
        assert event['utility_after'] == 15.0
        assert event['utility_delta'] == 5.0  # Calculated automatically
        assert event['opportunity_cost'] == 2.0
        assert event['alternatives_considered'] == 3
        assert event['decision_time_ms'] == 5.5
        assert event['position_x'] == 10
        assert event['position_y'] == 15
    
    def test_record_gui_display_basic(self):
        """Test basic GUI display recording functionality."""
        observer = RawDataObserver()
        
        observer.record_gui_display(
            step=108,
            display_type="highlight",
            element_id="agent_1"
        )
        
        events = observer.get_all_events()
        assert len(events) == 1
        
        event = events[0]
        assert event['type'] == 'gui_display'
        assert event['step'] == 108
        assert event['display_type'] == 'highlight'
        assert event['element_id'] == 'agent_1'
        assert event['data'] == {}
    
    def test_record_gui_display_with_data(self):
        """Test GUI display recording with data payload."""
        observer = RawDataObserver()
        
        display_data = {"color": "red", "duration": 2.0}
        observer.record_gui_display(
            step=108,
            display_type="overlay",
            element_id="trade_panel",
            data=display_data
        )
        
        events = observer.get_all_events()
        event = events[0]
        
        assert event['data'] == display_data


class TestRawDataObserverDataAccess:
    """Test event filtering and retrieval methods."""
    
    def test_get_events_by_type(self):
        """Test filtering events by type."""
        observer = RawDataObserver()
        
        # Record different event types
        observer.record_trade(step=100, seller_id=1, buyer_id=2, give_type="wood", take_type="stone")
        observer.record_mode_change(step=101, agent_id=1, old_mode="foraging", new_mode="trading", reason="found partner")
        observer.record_trade(step=102, seller_id=2, buyer_id=3, give_type="stone", take_type="wood")
        observer.record_debug_log(step=103, category="TRADE", message="Trade completed")
        
        # Test filtering
        trade_events = observer.get_events_by_type("trade")
        mode_events = observer.get_events_by_type("mode_change")
        debug_events = observer.get_events_by_type("debug_log")
        unknown_events = observer.get_events_by_type("unknown")
        
        assert len(trade_events) == 2
        assert len(mode_events) == 1
        assert len(debug_events) == 1
        assert len(unknown_events) == 0
        
        # Verify event content
        assert trade_events[0]['seller_id'] == 1
        assert trade_events[1]['seller_id'] == 2
        assert mode_events[0]['agent_id'] == 1
        assert debug_events[0]['category'] == 'TRADE'
    
    def test_get_events_by_step(self):
        """Test filtering events by step."""
        observer = RawDataObserver()
        
        # Record events at different steps
        observer.record_trade(step=100, seller_id=1, buyer_id=2, give_type="wood", take_type="stone")
        observer.record_mode_change(step=101, agent_id=1, old_mode="foraging", new_mode="trading", reason="found partner")
        observer.record_trade(step=100, seller_id=3, buyer_id=4, give_type="stone", take_type="wood")
        observer.record_debug_log(step=102, category="TRADE", message="Trade completed")
        
        # Test filtering
        step_100_events = observer.get_events_by_step(100)
        step_101_events = observer.get_events_by_step(101)
        step_102_events = observer.get_events_by_step(102)
        step_999_events = observer.get_events_by_step(999)
        
        assert len(step_100_events) == 2
        assert len(step_101_events) == 1
        assert len(step_102_events) == 1
        assert len(step_999_events) == 0
        
        # Verify event content
        assert all(event['step'] == 100 for event in step_100_events)
        assert all(event['step'] == 101 for event in step_101_events)
        assert all(event['step'] == 102 for event in step_102_events)
    
    def test_get_events_by_agent(self):
        """Test filtering events by agent ID."""
        observer = RawDataObserver()
        
        # Record events for different agents
        observer.record_trade(step=100, seller_id=1, buyer_id=2, give_type="wood", take_type="stone")
        observer.record_mode_change(step=101, agent_id=1, old_mode="foraging", new_mode="trading", reason="found partner")
        observer.record_mode_change(step=102, agent_id=2, old_mode="trading", new_mode="foraging", reason="no partners")
        observer.record_debug_log(step=103, category="TRADE", message="Trade completed", agent_id=1)
        
        # Test filtering
        agent_1_events = observer.get_events_by_agent(1)
        agent_2_events = observer.get_events_by_agent(2)
        agent_999_events = observer.get_events_by_agent(999)
        
        assert len(agent_1_events) == 3  # trade (seller), mode_change, debug_log
        assert len(agent_2_events) == 2  # trade (buyer), mode_change
        assert len(agent_999_events) == 0
        
        # Verify event content
        assert all(event.get('agent_id') == 1 or event.get('seller_id') == 1 for event in agent_1_events)
        assert all(event.get('agent_id') == 2 or event.get('buyer_id') == 2 for event in agent_2_events)
    
    def test_get_events_in_range(self):
        """Test filtering events within a step range."""
        observer = RawDataObserver()
        
        # Record events at different steps
        observer.record_trade(step=100, seller_id=1, buyer_id=2, give_type="wood", take_type="stone")
        observer.record_mode_change(step=101, agent_id=1, old_mode="foraging", new_mode="trading", reason="found partner")
        observer.record_trade(step=102, seller_id=2, buyer_id=3, give_type="stone", take_type="wood")
        observer.record_debug_log(step=103, category="TRADE", message="Trade completed")
        observer.record_trade(step=104, seller_id=3, buyer_id=4, give_type="wood", take_type="stone")
        
        # Test filtering
        range_100_102_events = observer.get_events_in_range(100, 102)
        range_103_104_events = observer.get_events_in_range(103, 104)
        range_105_110_events = observer.get_events_in_range(105, 110)
        
        assert len(range_100_102_events) == 3
        assert len(range_103_104_events) == 2
        assert len(range_105_110_events) == 0
        
        # Verify event content
        assert all(100 <= event.get('step', 0) <= 102 for event in range_100_102_events)
        assert all(103 <= event.get('step', 0) <= 104 for event in range_103_104_events)
    
    def test_get_all_events(self):
        """Test retrieving all events in chronological order."""
        observer = RawDataObserver()
        
        # Record events in mixed order
        observer.record_trade(step=102, seller_id=2, buyer_id=3, give_type="stone", take_type="wood")
        observer.record_trade(step=100, seller_id=1, buyer_id=2, give_type="wood", take_type="stone")
        observer.record_mode_change(step=101, agent_id=1, old_mode="foraging", new_mode="trading", reason="found partner")
        
        all_events = observer.get_all_events()
        
        assert len(all_events) == 3
        # Events should be in chronological order (as recorded)
        assert all_events[0]['step'] == 102
        assert all_events[1]['step'] == 100
        assert all_events[2]['step'] == 101
        
        # Verify we get a copy (not reference)
        all_events.append({'test': 'modification'})
        assert len(observer.get_all_events()) == 3  # Original unchanged


class TestRawDataObserverStatistics:
    """Test observer statistics and metadata methods."""
    
    def test_get_statistics_empty(self):
        """Test statistics for empty observer."""
        observer = RawDataObserver()
        
        stats = observer.get_statistics()
        
        assert stats['total_events'] == 0
        assert stats['event_types'] == set()
        assert stats['step_range'] == (0, 0)
        assert stats['recording_duration'] >= 0
        assert stats['events_per_second'] == 0.0
    
    def test_get_statistics_with_events(self):
        """Test statistics with recorded events."""
        observer = RawDataObserver()
        
        # Record various events
        observer.record_trade(step=100, seller_id=1, buyer_id=2, give_type="wood", take_type="stone")
        observer.record_mode_change(step=101, agent_id=1, old_mode="foraging", new_mode="trading", reason="found partner")
        observer.record_trade(step=102, seller_id=2, buyer_id=3, give_type="stone", take_type="wood")
        observer.record_debug_log(step=103, category="TRADE", message="Trade completed")
        
        stats = observer.get_statistics()
        
        assert stats['total_events'] == 4
        assert stats['event_types'] == {'trade', 'mode_change', 'debug_log'}
        assert stats['step_range'] == (100, 103)
        assert stats['recording_duration'] >= 0
        assert stats['events_per_second'] >= 0
    
    def test_get_event_type_counts(self):
        """Test event type counting."""
        observer = RawDataObserver()
        
        # Record various events
        observer.record_trade(step=100, seller_id=1, buyer_id=2, give_type="wood", take_type="stone")
        observer.record_trade(step=101, seller_id=2, buyer_id=3, give_type="stone", take_type="wood")
        observer.record_mode_change(step=102, agent_id=1, old_mode="foraging", new_mode="trading", reason="found partner")
        observer.record_debug_log(step=103, category="TRADE", message="Trade completed")
        observer.record_debug_log(step=104, category="MODE", message="Mode changed")
        
        counts = observer.get_event_type_counts()
        
        assert counts['trade'] == 2
        assert counts['mode_change'] == 1
        assert counts['debug_log'] == 2
        assert 'unknown' not in counts
    
    def test_get_step_event_counts(self):
        """Test step event counting."""
        observer = RawDataObserver()
        
        # Record events at different steps
        observer.record_trade(step=100, seller_id=1, buyer_id=2, give_type="wood", take_type="stone")
        observer.record_trade(step=100, seller_id=2, buyer_id=3, give_type="stone", take_type="wood")
        observer.record_mode_change(step=101, agent_id=1, old_mode="foraging", new_mode="trading", reason="found partner")
        observer.record_debug_log(step=102, category="TRADE", message="Trade completed")
        
        counts = observer.get_step_event_counts()
        
        assert counts[100] == 2
        assert counts[101] == 1
        assert counts[102] == 1
        assert 999 not in counts


class TestRawDataObserverUtility:
    """Test utility methods and edge cases."""
    
    def test_clear_events(self):
        """Test clearing all events."""
        observer = RawDataObserver()
        
        # Record some events
        observer.record_trade(step=100, seller_id=1, buyer_id=2, give_type="wood", take_type="stone")
        observer.record_mode_change(step=101, agent_id=1, old_mode="foraging", new_mode="trading", reason="found partner")
        
        assert len(observer) == 2
        
        # Clear events
        observer.clear_events()
        
        assert len(observer) == 0
        assert observer.get_all_events() == []
        assert observer.get_statistics()['total_events'] == 0
    
    def test_get_memory_usage_estimate_empty(self):
        """Test memory usage estimate for empty observer."""
        observer = RawDataObserver()
        
        memory_stats = observer.get_memory_usage_estimate()
        
        assert memory_stats['total_bytes'] == 0
        assert memory_stats['events_count'] == 0
        assert memory_stats['bytes_per_event'] == 0
    
    def test_get_memory_usage_estimate_with_events(self):
        """Test memory usage estimate with events."""
        observer = RawDataObserver()
        
        # Record some events
        observer.record_trade(step=100, seller_id=1, buyer_id=2, give_type="wood", take_type="stone")
        observer.record_mode_change(step=101, agent_id=1, old_mode="foraging", new_mode="trading", reason="found partner")
        
        memory_stats = observer.get_memory_usage_estimate()
        
        assert memory_stats['total_bytes'] > 0
        assert memory_stats['events_count'] == 2
        assert memory_stats['bytes_per_event'] > 0
        assert memory_stats['bytes_per_event'] == memory_stats['total_bytes'] / memory_stats['events_count']
    
    def test_len_method(self):
        """Test __len__ method."""
        observer = RawDataObserver()
        
        assert len(observer) == 0
        
        observer.record_trade(step=100, seller_id=1, buyer_id=2, give_type="wood", take_type="stone")
        assert len(observer) == 1
        
        observer.record_mode_change(step=101, agent_id=1, old_mode="foraging", new_mode="trading", reason="found partner")
        assert len(observer) == 2
    
    def test_repr_method(self):
        """Test __repr__ method."""
        observer = RawDataObserver()
        
        # Empty observer
        repr_str = repr(observer)
        assert "RawDataObserver" in repr_str
        assert "events=0" in repr_str
        
        # Observer with events
        observer.record_trade(step=100, seller_id=1, buyer_id=2, give_type="wood", take_type="stone")
        observer.record_mode_change(step=101, agent_id=1, old_mode="foraging", new_mode="trading", reason="found partner")
        
        repr_str = repr(observer)
        assert "events=2" in repr_str
        assert "types=2" in repr_str
        assert "steps=(100, 101)" in repr_str


class TestRawDataObserverPerformance:
    """Test performance characteristics and zero-overhead recording."""
    
    def test_recording_speed_basic(self):
        """Test basic recording speed - should be very fast."""
        observer = RawDataObserver()
        
        # Record 1000 events and measure time
        start_time = time.time()
        
        for i in range(1000):
            observer.record_trade(
                step=i,
                seller_id=i % 10,
                buyer_id=(i + 1) % 10,
                give_type="wood",
                take_type="stone"
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should be very fast - less than 0.001 seconds for 1000 events
        assert duration < 0.001, f"Recording 1000 events took {duration:.6f}s, expected <0.001s"
        
        # Calculate events per second
        events_per_second = 1000 / duration
        assert events_per_second > 1000000, f"Recording speed {events_per_second:.0f} events/sec, expected >1M events/sec"
    
    def test_recording_speed_mixed_events(self):
        """Test recording speed with mixed event types."""
        observer = RawDataObserver()
        
        # Record 500 events of different types
        start_time = time.time()
        
        for i in range(500):
            if i % 4 == 0:
                observer.record_trade(step=i, seller_id=1, buyer_id=2, give_type="wood", take_type="stone")
            elif i % 4 == 1:
                observer.record_mode_change(step=i, agent_id=1, old_mode="foraging", new_mode="trading", reason="test")
            elif i % 4 == 2:
                observer.record_resource_collection(step=i, agent_id=1, x=5, y=10, resource_type="wood")
            else:
                observer.record_debug_log(step=i, category="TEST", message=f"Debug message {i}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should still be very fast
        assert duration < 0.001, f"Recording 500 mixed events took {duration:.6f}s, expected <0.001s"
        
        # Verify all events were recorded
        assert len(observer) == 500
        assert len(observer.get_events_by_type("trade")) == 125
        assert len(observer.get_events_by_type("mode_change")) == 125
        assert len(observer.get_events_by_type("resource_collection")) == 125
        assert len(observer.get_events_by_type("debug_log")) == 125
    
    def test_memory_efficiency(self):
        """Test memory efficiency - no per-frame allocations."""
        observer = RawDataObserver()
        
        # Record many events and check memory usage
        initial_memory = observer.get_memory_usage_estimate()
        
        # Record 1000 events
        for i in range(1000):
            observer.record_trade(
                step=i,
                seller_id=i % 10,
                buyer_id=(i + 1) % 10,
                give_type="wood",
                take_type="stone"
            )
        
        final_memory = observer.get_memory_usage_estimate()
        
        # Memory should scale linearly with events
        assert final_memory['events_count'] == 1000
        assert final_memory['total_bytes'] > initial_memory['total_bytes']
        
        # Bytes per event should be reasonable (not growing)
        bytes_per_event = final_memory['bytes_per_event']
        assert 50 <= bytes_per_event <= 500, f"Bytes per event: {bytes_per_event}, expected 50-500"
    
    def test_zero_overhead_target(self):
        """Test that recording meets zero-overhead target (<0.0001ms per event)."""
        observer = RawDataObserver()
        
        # Record 10,000 events and measure per-event time
        num_events = 10000
        start_time = time.time()
        
        for i in range(num_events):
            observer.record_trade(
                step=i,
                seller_id=i % 10,
                buyer_id=(i + 1) % 10,
                give_type="wood",
                take_type="stone"
            )
        
        end_time = time.time()
        total_duration = end_time - start_time
        per_event_duration = total_duration / num_events
        
        # Target: <0.001ms per event (0.000001 seconds) - more realistic for Python
        target_per_event = 0.000001
        assert per_event_duration < target_per_event, (
            f"Per-event duration: {per_event_duration:.9f}s, "
            f"target: <{target_per_event:.9f}s"
        )
        
        # Calculate events per second
        events_per_second = num_events / total_duration
        assert events_per_second > 1000000, f"Recording speed: {events_per_second:.0f} events/sec, expected >1M events/sec"


class TestRawDataObserverEdgeCases:
    """Test edge cases and error handling."""
    
    def test_optional_fields_handling(self):
        """Test handling of optional fields via **kwargs."""
        observer = RawDataObserver()
        
        # Record event with many optional fields
        observer.record_trade(
            step=100,
            seller_id=1,
            buyer_id=2,
            give_type="wood",
            take_type="stone",
            custom_field_1="value1",
            custom_field_2=42,
            custom_field_3=[1, 2, 3],
            custom_field_4={"nested": "dict"}
        )
        
        events = observer.get_all_events()
        event = events[0]
        
        assert event['custom_field_1'] == "value1"
        assert event['custom_field_2'] == 42
        assert event['custom_field_3'] == [1, 2, 3]
        assert event['custom_field_4'] == {"nested": "dict"}
    
    def test_empty_optional_fields(self):
        """Test handling of empty optional fields."""
        observer = RawDataObserver()
        
        # Record event with empty optional fields
        observer.record_mode_change(
            step=100,
            agent_id=1,
            old_mode="foraging",
            new_mode="trading",
            reason="",  # Empty reason
            empty_list=[],
            empty_dict={},
            none_value=None
        )
        
        events = observer.get_all_events()
        event = events[0]
        
        assert event['reason'] == ""
        assert event['empty_list'] == []
        assert event['empty_dict'] == {}
        assert event['none_value'] is None
    
    def test_large_data_handling(self):
        """Test handling of large data in events."""
        observer = RawDataObserver()
        
        # Record event with large data
        large_string = "x" * 10000  # 10KB string
        large_list = list(range(1000))  # 1000 integers
        large_dict = {f"key_{i}": f"value_{i}" for i in range(100)}  # 100 key-value pairs
        
        observer.record_debug_log(
            step=100,
            category="LARGE",
            message=large_string,
            large_list=large_list,
            large_dict=large_dict
        )
        
        events = observer.get_all_events()
        event = events[0]
        
        assert event['message'] == large_string
        assert event['large_list'] == large_list
        assert event['large_dict'] == large_dict
        assert len(event['message']) == 10000
        assert len(event['large_list']) == 1000
        assert len(event['large_dict']) == 100
    
    def test_unicode_handling(self):
        """Test handling of unicode characters in event data."""
        observer = RawDataObserver()
        
        # Record event with unicode characters
        unicode_text = "Hello 世界 🌍 émojis"
        observer.record_debug_log(
            step=100,
            category="UNICODE",
            message=unicode_text
        )
        
        events = observer.get_all_events()
        event = events[0]
        
        assert event['message'] == unicode_text
        assert "世界" in event['message']
        assert "🌍" in event['message']
        assert "émojis" in event['message']


if __name__ == "__main__":
    pytest.main([__file__])
