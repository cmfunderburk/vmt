"""
Unit tests for the new extensible translation layer.

Tests the translator module including event decompression, schema lookup,
and batch translation functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.econsim.observability.new_architecture.translator import (
    translate_event,
    _parse_compressed_data,
    _parse_field_value,
    decompress_trade_event,
    decompress_agent_mode_event,
    decompress_resource_collection_event,
    decompress_debug_log_event,
    decompress_performance_monitor_event,
    decompress_agent_decision_event,
    decompress_resource_event,
    decompress_economic_decision_event,
    decompress_gui_display_event,
    translate_log_file,
    translate_events_by_type,
    get_translation_statistics,
    validate_compressed_event,
    get_supported_event_types,
    is_event_type_supported,
)


class TestTranslatorCore:
    """Test suite for core translation functionality."""
    
    def test_translate_event_trade_execution(self):
        """Test translating trade execution event."""
        compressed_event = {
            "s": 42,
            "dt": 0.1,
            "e": "trade",
            "d": "sid:1,bid:2,gt:good1,tt:good2,dus:0.5,dub:0.3,tx:5,ty:7"
        }
        
        result = translate_event(compressed_event)
        
        assert result['event_type'] == 'trade'
        assert result['step'] == 42
        assert result['timestamp'] == 0.1
        assert result['schema_category'] == 'economic_transaction'
        assert result['seller_id'] == 1
        assert result['buyer_id'] == 2
        assert result['give_type'] == 'good1'
        assert result['take_type'] == 'good2'
        assert result['delta_u_seller'] == 0.5
        assert result['delta_u_buyer'] == 0.3
        assert result['trade_location_x'] == 5
        assert result['trade_location_y'] == 7
    
    def test_translate_event_agent_mode_change(self):
        """Test translating agent mode change event."""
        compressed_event = {
            "s": 42,
            "dt": 0.1,
            "e": "mode",
            "d": "aid:1,om:forage,nm:trade,r:found_partner,dur:0.1,conf:0.8"
        }
        
        result = translate_event(compressed_event)
        
        assert result['event_type'] == 'mode'
        assert result['step'] == 42
        assert result['timestamp'] == 0.1
        assert result['schema_category'] == 'agent_behavior'
        assert result['agent_id'] == 1
        assert result['old_mode'] == 'forage'
        assert result['new_mode'] == 'trade'
        assert result['reason'] == 'found_partner'
        assert result['transition_duration'] == 0.1
        assert result['decision_confidence'] == 0.8
    
    def test_translate_event_resource_collection(self):
        """Test translating resource collection event."""
        compressed_event = {
            "s": 42,
            "dt": 0.1,
            "e": "collect",
            "d": "aid:1,x:5,y:7,rt:good1,amt:2,ug:1.5,ca:good1:3,good2:1"
        }
        
        result = translate_event(compressed_event)
        
        assert result['event_type'] == 'collect'
        assert result['step'] == 42
        assert result['timestamp'] == 0.1
        assert result['schema_category'] == 'resource_activity'
        assert result['agent_id'] == 1
        assert result['x'] == 5
        assert result['y'] == 7
        assert result['resource_type'] == 'good1'
        assert result['amount_collected'] == 2
        assert result['utility_gained'] == 1.5
        assert result['carrying_after'] == {'good1': 3, 'good2': 1}
    
    def test_translate_event_debug_log(self):
        """Test translating debug log event."""
        compressed_event = {
            "s": 42,
            "dt": 0.1,
            "e": "debug",
            "d": "cat:TRADE,msg:Trade executed successfully,aid:1"
        }
        
        result = translate_event(compressed_event)
        
        assert result['event_type'] == 'debug'
        assert result['step'] == 42
        assert result['timestamp'] == 0.1
        assert result['schema_category'] == 'system_logging'
        assert result['category'] == 'TRADE'
        assert result['message'] == 'Trade executed successfully'
        assert result['agent_id'] == 1
    
    def test_translate_event_performance_monitor(self):
        """Test translating performance monitor event."""
        compressed_event = {
            "s": 42,
            "dt": 0.1,
            "e": "perf",
            "d": "mn:steps_per_sec,mv:60.0,te:True,det:Performance target met"
        }
        
        result = translate_event(compressed_event)
        
        assert result['event_type'] == 'perf'
        assert result['step'] == 42
        assert result['timestamp'] == 0.1
        assert result['schema_category'] == 'system_monitoring'
        assert result['metric_name'] == 'steps_per_sec'
        assert result['metric_value'] == 60.0
        assert result['threshold_exceeded'] == True
        assert result['details'] == 'Performance target met'
    
    def test_translate_event_agent_decision(self):
        """Test translating agent decision event."""
        compressed_event = {
            "s": 42,
            "dt": 0.1,
            "e": "decision",
            "d": "aid:1,dt:movement,dd:Moved to resource location,ud:1.5,px:5,py:7"
        }
        
        result = translate_event(compressed_event)
        
        assert result['event_type'] == 'decision'
        assert result['step'] == 42
        assert result['timestamp'] == 0.1
        assert result['schema_category'] == 'agent_behavior'
        assert result['agent_id'] == 1
        assert result['decision_type'] == 'movement'
        assert result['decision_details'] == 'Moved to resource location'
        assert result['utility_delta'] == 1.5
        assert result['position_x'] == 5
        assert result['position_y'] == 7
    
    def test_translate_event_resource_event(self):
        """Test translating resource event."""
        compressed_event = {
            "s": 42,
            "dt": 0.1,
            "e": "resource",
            "d": "etd:spawn,px:5,py:7,rt:good1,amt:3,aid:2"
        }
        
        result = translate_event(compressed_event)
        
        assert result['event_type'] == 'resource'
        assert result['step'] == 42
        assert result['timestamp'] == 0.1
        assert result['schema_category'] == 'resource_activity'
        assert result['event_type_detail'] == 'spawn'
        assert result['position_x'] == 5
        assert result['position_y'] == 7
        assert result['resource_type'] == 'good1'
        assert result['amount'] == 3
        assert result['agent_id'] == 2
    
    def test_translate_event_economic_decision(self):
        """Test translating economic decision event."""
        compressed_event = {
            "s": 42,
            "dt": 0.1,
            "e": "econ",
            "d": "aid:1,dt:trade_proposal,dc:Proposed trade with agent 2,ub:5.0,ua:6.5,oc:0.5,ac:3,dtm:15.2,px:5,py:7"
        }
        
        result = translate_event(compressed_event)
        
        assert result['event_type'] == 'econ'
        assert result['step'] == 42
        assert result['timestamp'] == 0.1
        assert result['schema_category'] == 'economic_analysis'
        assert result['agent_id'] == 1
        assert result['decision_type'] == 'trade_proposal'
        assert result['decision_context'] == 'Proposed trade with agent 2'
        assert result['utility_before'] == 5.0
        assert result['utility_after'] == 6.5
        assert result['opportunity_cost'] == 0.5
        assert result['alternatives_considered'] == 3
        assert result['decision_time_ms'] == 15.2
        assert result['position_x'] == 5
        assert result['position_y'] == 7
    
    def test_translate_event_gui_display(self):
        """Test translating GUI display event."""
        compressed_event = {
            "s": 42,
            "dt": 0.1,
            "e": "gui",
            "d": "dt:highlight,eid:agent_1,data:color:red,duration:2.0"
        }
        
        result = translate_event(compressed_event)
        
        assert result['event_type'] == 'gui'
        assert result['step'] == 42
        assert result['timestamp'] == 0.1
        assert result['schema_category'] == 'user_interface'
        assert result['display_type'] == 'highlight'
        assert result['element_id'] == 'agent_1'
        assert result['data'] == {'color': 'red', 'duration': 2.0}
    
    def test_translate_event_unknown_type(self):
        """Test translating unknown event type."""
        compressed_event = {
            "s": 42,
            "dt": 0.1,
            "e": "unknown_type",
            "d": "field1:value1,field2:value2"
        }
        
        result = translate_event(compressed_event)
        
        assert result['event_type'] == 'unknown_type'
        assert result['step'] == 42
        assert result['timestamp'] == 0.1
        assert result['compressed_data'] == 'field1:value1,field2:value2'
        assert result['translation_status'] == 'unknown_event_type'
    
    def test_translate_event_malformed(self):
        """Test translating malformed event."""
        # Test with non-dict input
        result = translate_event("not a dict")
        assert result == "not a dict"
        
        # Test with missing fields
        compressed_event = {"s": 42}  # Missing required fields
        result = translate_event(compressed_event)
        assert result['event_type'] == 'unknown'
        assert result['step'] == 42
    
    def test_parse_compressed_data(self):
        """Test parsing compressed data string."""
        from src.econsim.observability.new_architecture.translator import _parse_compressed_data
        
        reverse_mapping = {
            'sid': 'seller_id',
            'bid': 'buyer_id',
            'gt': 'give_type',
            'tt': 'take_type'
        }
        
        compressed_data = "sid:1,bid:2,gt:good1,tt:good2"
        result = _parse_compressed_data(compressed_data, reverse_mapping)
        
        assert result['seller_id'] == 1
        assert result['buyer_id'] == 2
        assert result['give_type'] == 'good1'
        assert result['take_type'] == 'good2'
    
    def test_parse_compressed_data_empty(self):
        """Test parsing empty compressed data."""
        from src.econsim.observability.new_architecture.translator import _parse_compressed_data
        
        result = _parse_compressed_data("", {})
        assert result == {}
        
        result = _parse_compressed_data(None, {})
        assert result == {}
    
    def test_parse_compressed_data_malformed(self):
        """Test parsing malformed compressed data."""
        from src.econsim.observability.new_architecture.translator import _parse_compressed_data
        
        reverse_mapping = {'sid': 'seller_id'}
        
        # Test with malformed parts
        compressed_data = "sid:1,malformed,gt:good1"
        result = _parse_compressed_data(compressed_data, reverse_mapping)
        
        assert result['seller_id'] == 1
        assert 'gt' in result  # Unknown code should be preserved
    
    def test_parse_field_value(self):
        """Test parsing field values into appropriate types."""
        from src.econsim.observability.new_architecture.translator import _parse_field_value
        
        # Test string values
        assert _parse_field_value("hello") == "hello"
        assert _parse_field_value("") == ""
        
        # Test integer values
        assert _parse_field_value("42") == 42
        assert _parse_field_value("-10") == -10
        
        # Test float values
        assert _parse_field_value("3.14") == 3.14
        assert _parse_field_value("-2.5") == -2.5
        assert _parse_field_value("1e-5") == 1e-5
        
        # Test boolean values
        assert _parse_field_value("true") == True
        assert _parse_field_value("false") == False
        assert _parse_field_value("True") == True
        assert _parse_field_value("False") == False
        
        # Test dict values
        assert _parse_field_value("key1:value1,key2:value2") == {'key1': 'value1', 'key2': 'value2'}
        assert _parse_field_value("good1:3,good2:1") == {'good1': 3, 'good2': 1}


class TestSpecificDecompressionFunctions:
    """Test suite for specific decompression functions."""
    
    def test_decompress_trade_event(self):
        """Test trade event decompression function."""
        compressed_data = "sid:1,bid:2,gt:good1,tt:good2,dus:0.5,dub:0.3"
        result = decompress_trade_event(compressed_data)
        
        assert result['seller_id'] == 1
        assert result['buyer_id'] == 2
        assert result['give_type'] == 'good1'
        assert result['take_type'] == 'good2'
        assert result['delta_u_seller'] == 0.5
        assert result['delta_u_buyer'] == 0.3
    
    def test_decompress_agent_mode_event(self):
        """Test agent mode event decompression function."""
        compressed_data = "aid:1,om:forage,nm:trade,r:found_partner"
        result = decompress_agent_mode_event(compressed_data)
        
        assert result['agent_id'] == 1
        assert result['old_mode'] == 'forage'
        assert result['new_mode'] == 'trade'
        assert result['reason'] == 'found_partner'
    
    def test_decompress_resource_collection_event(self):
        """Test resource collection event decompression function."""
        compressed_data = "aid:1,x:5,y:7,rt:good1,amt:2,ug:1.5"
        result = decompress_resource_collection_event(compressed_data)
        
        assert result['agent_id'] == 1
        assert result['x'] == 5
        assert result['y'] == 7
        assert result['resource_type'] == 'good1'
        assert result['amount_collected'] == 2
        assert result['utility_gained'] == 1.5
    
    def test_decompress_debug_log_event(self):
        """Test debug log event decompression function."""
        compressed_data = "cat:TRADE,msg:Trade executed successfully"
        result = decompress_debug_log_event(compressed_data)
        
        assert result['category'] == 'TRADE'
        assert result['message'] == 'Trade executed successfully'
    
    def test_decompress_performance_monitor_event(self):
        """Test performance monitor event decompression function."""
        compressed_data = "mn:steps_per_sec,mv:60.0,te:True"
        result = decompress_performance_monitor_event(compressed_data)
        
        assert result['metric_name'] == 'steps_per_sec'
        assert result['metric_value'] == 60.0
        assert result['threshold_exceeded'] == True
    
    def test_decompress_agent_decision_event(self):
        """Test agent decision event decompression function."""
        compressed_data = "aid:1,dt:movement,dd:Moved to resource location"
        result = decompress_agent_decision_event(compressed_data)
        
        assert result['agent_id'] == 1
        assert result['decision_type'] == 'movement'
        assert result['decision_details'] == 'Moved to resource location'
    
    def test_decompress_resource_event(self):
        """Test resource event decompression function."""
        compressed_data = "etd:spawn,px:5,py:7,rt:good1,amt:3"
        result = decompress_resource_event(compressed_data)
        
        assert result['event_type_detail'] == 'spawn'
        assert result['position_x'] == 5
        assert result['position_y'] == 7
        assert result['resource_type'] == 'good1'
        assert result['amount'] == 3
    
    def test_decompress_economic_decision_event(self):
        """Test economic decision event decompression function."""
        compressed_data = "aid:1,dt:trade_proposal,dc:Proposed trade with agent 2"
        result = decompress_economic_decision_event(compressed_data)
        
        assert result['agent_id'] == 1
        assert result['decision_type'] == 'trade_proposal'
        assert result['decision_context'] == 'Proposed trade with agent 2'
    
    def test_decompress_gui_display_event(self):
        """Test GUI display event decompression function."""
        compressed_data = "dt:highlight,eid:agent_1"
        result = decompress_gui_display_event(compressed_data)
        
        assert result['display_type'] == 'highlight'
        assert result['element_id'] == 'agent_1'


class TestBatchTranslation:
    """Test suite for batch translation functionality."""
    
    def test_translate_log_file(self):
        """Test translating an entire log file."""
        # Create a temporary log file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            log_file_path = f.name
            
            # Write some compressed log entries
            entries = [
                {"s": 42, "dt": 0.1, "e": "trade", "d": "sid:1,bid:2,gt:good1,tt:good2"},
                {"s": 43, "dt": 0.2, "e": "mode", "d": "aid:1,om:forage,nm:trade,r:found_partner"},
                {"s": 44, "dt": 0.3, "e": "collect", "d": "aid:1,x:5,y:7,rt:good1,amt:2"}
            ]
            
            for entry in entries:
                f.write(json.dumps(entry) + '\n')
        
        try:
            # Translate the log file
            translated_entries = translate_log_file(log_file_path)
            
            assert len(translated_entries) == 3
            
            # Check first entry (trade)
            assert translated_entries[0]['event_type'] == 'trade'
            assert translated_entries[0]['step'] == 42
            assert translated_entries[0]['seller_id'] == 1
            assert translated_entries[0]['buyer_id'] == 2
            
            # Check second entry (mode)
            assert translated_entries[1]['event_type'] == 'mode'
            assert translated_entries[1]['step'] == 43
            assert translated_entries[1]['agent_id'] == 1
            assert translated_entries[1]['old_mode'] == 'forage'
            
            # Check third entry (collect)
            assert translated_entries[2]['event_type'] == 'collect'
            assert translated_entries[2]['step'] == 44
            assert translated_entries[2]['agent_id'] == 1
            assert translated_entries[2]['x'] == 5
            
        finally:
            # Clean up
            Path(log_file_path).unlink()
    
    def test_translate_log_file_malformed(self):
        """Test translating log file with malformed entries."""
        # Create a temporary log file with malformed entries
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            log_file_path = f.name
            
            # Write mix of valid and malformed entries
            f.write('{"s": 42, "dt": 0.1, "e": "trade", "d": "sid:1,bid:2"}\n')
            f.write('malformed json line\n')
            f.write('{"s": 43, "dt": 0.2, "e": "mode", "d": "aid:1,om:forage,nm:trade"}\n')
            f.write('\n')  # Empty line
            f.write('{"s": 44, "dt": 0.3, "e": "unknown", "d": "field:value"}\n')
        
        try:
            # Translate the log file
            translated_entries = translate_log_file(log_file_path)
            
            assert len(translated_entries) == 4
            
            # Check valid entries
            assert translated_entries[0]['event_type'] == 'trade'
            assert translated_entries[2]['event_type'] == 'mode'
            
            # Check malformed entry
            assert 'error' in translated_entries[1]
            assert 'JSON decode error' in translated_entries[1]['error']
            
            # Check unknown event type
            assert translated_entries[3]['event_type'] == 'unknown'
            assert translated_entries[3]['translation_status'] == 'unknown_event_type'
            
        finally:
            # Clean up
            Path(log_file_path).unlink()
    
    def test_translate_log_file_not_found(self):
        """Test translating non-existent log file."""
        result = translate_log_file("/nonexistent/file.log")
        
        assert len(result) == 1
        assert 'error' in result[0]
        assert 'Log file not found' in result[0]['error']
    
    def test_translate_events_by_type(self):
        """Test filtering translated entries by event type."""
        translated_entries = [
            {'event_type': 'trade', 'step': 42, 'seller_id': 1},
            {'event_type': 'mode', 'step': 43, 'agent_id': 1},
            {'event_type': 'trade', 'step': 44, 'seller_id': 2},
            {'event_type': 'collect', 'step': 45, 'agent_id': 1}
        ]
        
        # Filter by trade events
        trade_events = translate_events_by_type(translated_entries, 'trade')
        assert len(trade_events) == 2
        assert all(event['event_type'] == 'trade' for event in trade_events)
        
        # Filter by mode events
        mode_events = translate_events_by_type(translated_entries, 'mode')
        assert len(mode_events) == 1
        assert mode_events[0]['event_type'] == 'mode'
        
        # Filter by non-existent event type
        unknown_events = translate_events_by_type(translated_entries, 'unknown')
        assert len(unknown_events) == 0
    
    def test_get_translation_statistics(self):
        """Test getting translation statistics."""
        translated_entries = [
            {'event_type': 'trade', 'step': 42},
            {'event_type': 'mode', 'step': 43},
            {'event_type': 'trade', 'step': 44},
            {'error': 'JSON decode error', 'line_number': 5},
            {'event_type': 'unknown', 'translation_status': 'unknown_event_type', 'step': 45}
        ]
        
        stats = get_translation_statistics(translated_entries)
        
        assert stats['total_entries'] == 5
        assert stats['event_type_counts']['trade'] == 2
        assert stats['event_type_counts']['mode'] == 1
        assert stats['error_count'] == 1
        assert stats['unknown_event_count'] == 1


class TestUtilityFunctions:
    """Test suite for utility functions."""
    
    def test_validate_compressed_event_valid(self):
        """Test validating a valid compressed event."""
        compressed_event = {
            "s": 42,
            "dt": 0.1,
            "e": "trade",
            "d": "sid:1,bid:2,gt:good1,tt:good2"
        }
        
        result = validate_compressed_event(compressed_event)
        
        assert result['is_valid'] == True
        assert len(result['errors']) == 0
        assert len(result['warnings']) == 0
    
    def test_validate_compressed_event_missing_fields(self):
        """Test validating compressed event with missing fields."""
        compressed_event = {
            "s": 42,
            "e": "trade"
            # Missing 'dt' and 'd' fields
        }
        
        result = validate_compressed_event(compressed_event)
        
        assert result['is_valid'] == False
        assert len(result['errors']) == 2
        assert 'Missing required field: dt' in result['errors']
        assert 'Missing required field: d' in result['errors']
    
    def test_validate_compressed_event_unknown_type(self):
        """Test validating compressed event with unknown event type."""
        compressed_event = {
            "s": 42,
            "dt": 0.1,
            "e": "unknown_type",
            "d": "field:value"
        }
        
        result = validate_compressed_event(compressed_event)
        
        assert result['is_valid'] == True  # Structure is valid
        assert len(result['warnings']) == 1
        assert 'Unknown event type: unknown_type' in result['warnings'][0]
    
    def test_validate_compressed_event_not_dict(self):
        """Test validating non-dictionary input."""
        result = validate_compressed_event("not a dict")
        
        assert result['is_valid'] == False
        assert len(result['errors']) == 1
        assert 'Event must be a dictionary' in result['errors']
    
    def test_get_supported_event_types(self):
        """Test getting supported event types."""
        supported_types = get_supported_event_types()
        
        expected_types = ['trade', 'mode', 'collect', 'debug', 'perf', 'decision', 'resource', 'econ', 'gui']
        assert set(supported_types) == set(expected_types)
    
    def test_is_event_type_supported(self):
        """Test checking if event type is supported."""
        assert is_event_type_supported('trade') == True
        assert is_event_type_supported('mode') == True
        assert is_event_type_supported('collect') == True
        assert is_event_type_supported('unknown') == False
        assert is_event_type_supported('') == False


class TestRoundTripCompression:
    """Test suite for round-trip compression/decompression."""
    
    def test_round_trip_trade_event(self):
        """Test round-trip compression/decompression for trade events."""
        # This test simulates the round-trip process
        # In practice, compression happens in ExtensibleObserver, decompression in translator
        
        # Simulate compressed data that would be generated by ExtensibleObserver
        compressed_data = "sid:1,bid:2,gt:good1,tt:good2,dus:0.5,dub:0.3,tx:5,ty:7"
        
        # Decompress using translator
        result = decompress_trade_event(compressed_data)
        
        # Verify all fields are correctly decompressed
        assert result['seller_id'] == 1
        assert result['buyer_id'] == 2
        assert result['give_type'] == 'good1'
        assert result['take_type'] == 'good2'
        assert result['delta_u_seller'] == 0.5
        assert result['delta_u_buyer'] == 0.3
        assert result['trade_location_x'] == 5
        assert result['trade_location_y'] == 7
    
    def test_round_trip_agent_mode_event(self):
        """Test round-trip compression/decompression for agent mode events."""
        compressed_data = "aid:1,om:forage,nm:trade,r:found_partner,dur:0.1,conf:0.8"
        
        result = decompress_agent_mode_event(compressed_data)
        
        assert result['agent_id'] == 1
        assert result['old_mode'] == 'forage'
        assert result['new_mode'] == 'trade'
        assert result['reason'] == 'found_partner'
        assert result['transition_duration'] == 0.1
        assert result['decision_confidence'] == 0.8
    
    def test_round_trip_resource_collection_event(self):
        """Test round-trip compression/decompression for resource collection events."""
        compressed_data = "aid:1,x:5,y:7,rt:good1,amt:2,ug:1.5,ca:good1:3,good2:1"
        
        result = decompress_resource_collection_event(compressed_data)
        
        assert result['agent_id'] == 1
        assert result['x'] == 5
        assert result['y'] == 7
        assert result['resource_type'] == 'good1'
        assert result['amount_collected'] == 2
        assert result['utility_gained'] == 1.5
        assert result['carrying_after'] == {'good1': 3, 'good2': 1}
    
    def test_round_trip_complex_data_types(self):
        """Test round-trip with complex data types."""
        # Test with dict values (this is how carrying_after would be formatted)
        compressed_data = "good1:3,good2:1"
        result = _parse_field_value(compressed_data)
        
        assert result == {'good1': 3, 'good2': 1}
        
        # Test with mixed types in a single field value
        compressed_data = "str_field:hello,int_field:42,float_field:3.14,bool_field:true"
        parts = compressed_data.split(',')
        parsed = {}
        for part in parts:
            key, value = part.split(':', 1)
            parsed[key] = _parse_field_value(value)
        
        assert parsed['str_field'] == 'hello'
        assert parsed['int_field'] == 42
        assert parsed['float_field'] == 3.14
        assert parsed['bool_field'] == True
