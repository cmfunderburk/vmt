"""
Unit tests for the new extensible event schemas.

Tests the event schema definitions, validation functions, and utility functions.
"""

import pytest

from src.econsim.observability.new_architecture.event_schemas import (
    TRADE_EXECUTION_SCHEMA,
    AGENT_MODE_SCHEMA,
    RESOURCE_COLLECTION_SCHEMA,
    DEBUG_LOG_SCHEMA,
    PERFORMANCE_MONITOR_SCHEMA,
    AGENT_DECISION_SCHEMA,
    RESOURCE_EVENT_SCHEMA,
    ECONOMIC_DECISION_SCHEMA,
    GUI_DISPLAY_SCHEMA,
    SCHEMA_REGISTRY,
    validate_schema,
    get_field_code,
    get_required_fields,
    get_optional_fields,
    create_reverse_mapping,
    get_all_event_codes,
    get_schema_by_code,
    get_schemas_by_category,
    validate_all_schemas,
)


class TestEventSchemas:
    """Test suite for event schema definitions."""
    
    def test_trade_execution_schema_structure(self):
        """Test TRADE_EXECUTION_SCHEMA has correct structure."""
        schema = TRADE_EXECUTION_SCHEMA
        
        assert schema['event_code'] == 'trade'
        assert schema['version'] == '1.0'
        assert schema['category'] == 'economic_transaction'
        assert schema['description'] == 'Trade execution event between two agents'
        
        # Check required fields
        fields = schema['fields']
        assert 'seller_id' in fields
        assert 'buyer_id' in fields
        assert 'give_type' in fields
        assert 'take_type' in fields
        assert 'delta_u_seller' in fields
        assert 'delta_u_buyer' in fields
        
        # Check field codes
        assert fields['seller_id']['code'] == 'sid'
        assert fields['buyer_id']['code'] == 'bid'
        assert fields['give_type']['code'] == 'gt'
        assert fields['take_type']['code'] == 'tt'
        assert fields['delta_u_seller']['code'] == 'dus'
        assert fields['delta_u_buyer']['code'] == 'dub'
        
        # Check optional fields
        assert 'trade_location_x' in fields
        assert 'trade_location_y' in fields
        assert fields['trade_location_x']['required'] == False
        assert fields['trade_location_y']['required'] == False
    
    def test_agent_mode_schema_structure(self):
        """Test AGENT_MODE_SCHEMA has correct structure."""
        schema = AGENT_MODE_SCHEMA
        
        assert schema['event_code'] == 'mode'
        assert schema['version'] == '1.0'
        assert schema['category'] == 'agent_behavior'
        assert schema['description'] == 'Agent behavioral mode transition event'
        
        # Check required fields
        fields = schema['fields']
        assert 'agent_id' in fields
        assert 'old_mode' in fields
        assert 'new_mode' in fields
        assert 'reason' in fields
        
        # Check field codes
        assert fields['agent_id']['code'] == 'aid'
        assert fields['old_mode']['code'] == 'om'
        assert fields['new_mode']['code'] == 'nm'
        assert fields['reason']['code'] == 'r'
        
        # Check all required fields are marked as required
        for field_name in ['agent_id', 'old_mode', 'new_mode', 'reason']:
            assert fields[field_name]['required'] == True
    
    def test_resource_collection_schema_structure(self):
        """Test RESOURCE_COLLECTION_SCHEMA has correct structure."""
        schema = RESOURCE_COLLECTION_SCHEMA
        
        assert schema['event_code'] == 'collect'
        assert schema['version'] == '1.0'
        assert schema['category'] == 'resource_activity'
        assert schema['description'] == 'Resource collection event by an agent'
        
        # Check required fields
        fields = schema['fields']
        assert 'agent_id' in fields
        assert 'x' in fields
        assert 'y' in fields
        assert 'resource_type' in fields
        assert 'amount_collected' in fields
        assert 'utility_gained' in fields
        
        # Check field codes
        assert fields['agent_id']['code'] == 'aid'
        assert fields['x']['code'] == 'x'
        assert fields['y']['code'] == 'y'
        assert fields['resource_type']['code'] == 'rt'
        assert fields['amount_collected']['code'] == 'amt'
        assert fields['utility_gained']['code'] == 'ug'
    
    def test_debug_log_schema_structure(self):
        """Test DEBUG_LOG_SCHEMA has correct structure."""
        schema = DEBUG_LOG_SCHEMA
        
        assert schema['event_code'] == 'debug'
        assert schema['version'] == '1.0'
        assert schema['category'] == 'system_logging'
        assert schema['description'] == 'Debug/categorical logging message event'
        
        # Check required fields
        fields = schema['fields']
        assert 'category' in fields
        assert 'message' in fields
        
        # Check field codes
        assert fields['category']['code'] == 'cat'
        assert fields['message']['code'] == 'msg'
        
        # Check optional fields
        assert 'agent_id' in fields
        assert fields['agent_id']['required'] == False
    
    def test_performance_monitor_schema_structure(self):
        """Test PERFORMANCE_MONITOR_SCHEMA has correct structure."""
        schema = PERFORMANCE_MONITOR_SCHEMA
        
        assert schema['event_code'] == 'perf'
        assert schema['version'] == '1.0'
        assert schema['category'] == 'system_monitoring'
        assert schema['description'] == 'Performance monitoring and metrics event'
        
        # Check required fields
        fields = schema['fields']
        assert 'metric_name' in fields
        assert 'metric_value' in fields
        
        # Check field codes
        assert fields['metric_name']['code'] == 'mn'
        assert fields['metric_value']['code'] == 'mv'
        
        # Check optional fields
        assert 'threshold_exceeded' in fields
        assert 'details' in fields
        assert fields['threshold_exceeded']['required'] == False
        assert fields['details']['required'] == False
    
    def test_agent_decision_schema_structure(self):
        """Test AGENT_DECISION_SCHEMA has correct structure."""
        schema = AGENT_DECISION_SCHEMA
        
        assert schema['event_code'] == 'decision'
        assert schema['version'] == '1.0'
        assert schema['category'] == 'agent_behavior'
        assert schema['description'] == 'Agent decision-making process event'
        
        # Check required fields
        fields = schema['fields']
        assert 'agent_id' in fields
        assert 'decision_type' in fields
        assert 'decision_details' in fields
        
        # Check field codes
        assert fields['agent_id']['code'] == 'aid'
        assert fields['decision_type']['code'] == 'dt'
        assert fields['decision_details']['code'] == 'dd'
        
        # Check optional fields
        assert 'utility_delta' in fields
        assert 'position_x' in fields
        assert 'position_y' in fields
        assert fields['utility_delta']['required'] == False
        assert fields['position_x']['required'] == False
        assert fields['position_y']['required'] == False
    
    def test_resource_event_schema_structure(self):
        """Test RESOURCE_EVENT_SCHEMA has correct structure."""
        schema = RESOURCE_EVENT_SCHEMA
        
        assert schema['event_code'] == 'resource'
        assert schema['version'] == '1.0'
        assert schema['category'] == 'resource_activity'
        assert schema['description'] == 'Resource lifecycle event (spawn, despawn, move, etc.)'
        
        # Check required fields
        fields = schema['fields']
        assert 'event_type_detail' in fields
        assert 'position_x' in fields
        assert 'position_y' in fields
        assert 'resource_type' in fields
        assert 'amount' in fields
        
        # Check field codes
        assert fields['event_type_detail']['code'] == 'etd'
        assert fields['position_x']['code'] == 'px'
        assert fields['position_y']['code'] == 'py'
        assert fields['resource_type']['code'] == 'rt'
        assert fields['amount']['code'] == 'amt'
    
    def test_economic_decision_schema_structure(self):
        """Test ECONOMIC_DECISION_SCHEMA has correct structure."""
        schema = ECONOMIC_DECISION_SCHEMA
        
        assert schema['event_code'] == 'econ'
        assert schema['version'] == '1.0'
        assert schema['category'] == 'economic_analysis'
        assert schema['description'] == 'Detailed economic decision-making process event'
        
        # Check required fields
        fields = schema['fields']
        assert 'agent_id' in fields
        assert 'decision_type' in fields
        assert 'decision_context' in fields
        
        # Check field codes
        assert fields['agent_id']['code'] == 'aid'
        assert fields['decision_type']['code'] == 'dt'
        assert fields['decision_context']['code'] == 'dc'
        
        # Check optional fields
        assert 'utility_before' in fields
        assert 'utility_after' in fields
        assert 'opportunity_cost' in fields
        assert 'alternatives_considered' in fields
        assert 'decision_time_ms' in fields
        assert 'position_x' in fields
        assert 'position_y' in fields
    
    def test_gui_display_schema_structure(self):
        """Test GUI_DISPLAY_SCHEMA has correct structure."""
        schema = GUI_DISPLAY_SCHEMA
        
        assert schema['event_code'] == 'gui'
        assert schema['version'] == '1.0'
        assert schema['category'] == 'user_interface'
        assert schema['description'] == 'GUI display update and visual feedback event'
        
        # Check required fields
        fields = schema['fields']
        assert 'display_type' in fields
        assert 'element_id' in fields
        
        # Check field codes
        assert fields['display_type']['code'] == 'dt'
        assert fields['element_id']['code'] == 'eid'
        
        # Check optional fields
        assert 'data' in fields
        assert fields['data']['required'] == False
    
    def test_schema_registry_completeness(self):
        """Test that SCHEMA_REGISTRY contains all expected schemas."""
        expected_codes = {
            'trade', 'mode', 'collect', 'debug', 'perf', 
            'decision', 'resource', 'econ', 'gui'
        }
        
        actual_codes = set(SCHEMA_REGISTRY.keys())
        assert actual_codes == expected_codes
        
        # Test that all schemas are properly registered
        for code in expected_codes:
            schema = SCHEMA_REGISTRY[code]
            assert schema['event_code'] == code
            assert validate_schema(schema)
    
    def test_validate_schema_valid_schemas(self):
        """Test validate_schema with valid schemas."""
        assert validate_schema(TRADE_EXECUTION_SCHEMA) == True
        assert validate_schema(AGENT_MODE_SCHEMA) == True
        assert validate_schema(RESOURCE_COLLECTION_SCHEMA) == True
        assert validate_schema(DEBUG_LOG_SCHEMA) == True
        assert validate_schema(PERFORMANCE_MONITOR_SCHEMA) == True
        assert validate_schema(AGENT_DECISION_SCHEMA) == True
        assert validate_schema(RESOURCE_EVENT_SCHEMA) == True
        assert validate_schema(ECONOMIC_DECISION_SCHEMA) == True
        assert validate_schema(GUI_DISPLAY_SCHEMA) == True
    
    def test_validate_schema_invalid_schemas(self):
        """Test validate_schema with invalid schemas."""
        # Missing required keys
        invalid_schema1 = {'event_code': 'test'}
        assert validate_schema(invalid_schema1) == False
        
        # Invalid fields structure
        invalid_schema2 = {
            'event_code': 'test',
            'version': '1.0',
            'category': 'test',
            'description': 'test',
            'fields': 'not_a_dict'
        }
        assert validate_schema(invalid_schema2) == False
        
        # Invalid field definition
        invalid_schema3 = {
            'event_code': 'test',
            'version': '1.0',
            'category': 'test',
            'description': 'test',
            'fields': {
                'test_field': 'not_a_dict'
            }
        }
        assert validate_schema(invalid_schema3) == False
        
        # Missing code in field definition
        invalid_schema4 = {
            'event_code': 'test',
            'version': '1.0',
            'category': 'test',
            'description': 'test',
            'fields': {
                'test_field': {'type': 'str'}
            }
        }
        assert validate_schema(invalid_schema4) == False
    
    def test_get_field_code(self):
        """Test get_field_code function."""
        # Test with valid field
        code = get_field_code(TRADE_EXECUTION_SCHEMA, 'seller_id')
        assert code == 'sid'
        
        # Test with invalid field
        code = get_field_code(TRADE_EXECUTION_SCHEMA, 'nonexistent_field')
        assert code is None
        
        # Test with invalid schema
        code = get_field_code({}, 'seller_id')
        assert code is None
    
    def test_get_required_fields(self):
        """Test get_required_fields function."""
        required = get_required_fields(TRADE_EXECUTION_SCHEMA)
        expected = ['seller_id', 'buyer_id', 'give_type', 'take_type', 'delta_u_seller', 'delta_u_buyer']
        assert set(required) == set(expected)
        
        required = get_required_fields(AGENT_MODE_SCHEMA)
        expected = ['agent_id', 'old_mode', 'new_mode', 'reason']
        assert set(required) == set(expected)
        
        # Test with invalid schema
        required = get_required_fields({})
        assert required == []
    
    def test_get_optional_fields(self):
        """Test get_optional_fields function."""
        optional = get_optional_fields(TRADE_EXECUTION_SCHEMA)
        expected = ['trade_location_x', 'trade_location_y', 'trade_volume', 'market_price', 'trade_efficiency']
        assert set(optional) == set(expected)
        
        optional = get_optional_fields(AGENT_MODE_SCHEMA)
        expected = ['transition_duration', 'decision_confidence']
        assert set(optional) == set(expected)
        
        # Test with invalid schema
        optional = get_optional_fields({})
        assert optional == []
    
    def test_create_reverse_mapping(self):
        """Test create_reverse_mapping function."""
        reverse = create_reverse_mapping(TRADE_EXECUTION_SCHEMA)
        
        assert reverse['sid'] == 'seller_id'
        assert reverse['bid'] == 'buyer_id'
        assert reverse['gt'] == 'give_type'
        assert reverse['tt'] == 'take_type'
        assert reverse['dus'] == 'delta_u_seller'
        assert reverse['dub'] == 'delta_u_buyer'
        assert reverse['tx'] == 'trade_location_x'
        assert reverse['ty'] == 'trade_location_y'
        
        # Test with invalid schema
        reverse = create_reverse_mapping({})
        assert reverse == {}
    
    def test_get_all_event_codes(self):
        """Test get_all_event_codes function."""
        codes = get_all_event_codes()
        expected = ['trade', 'mode', 'collect', 'debug', 'perf', 'decision', 'resource', 'econ', 'gui']
        assert set(codes) == set(expected)
    
    def test_get_schema_by_code(self):
        """Test get_schema_by_code function."""
        schema = get_schema_by_code('trade')
        assert schema == TRADE_EXECUTION_SCHEMA
        
        schema = get_schema_by_code('mode')
        assert schema == AGENT_MODE_SCHEMA
        
        schema = get_schema_by_code('nonexistent')
        assert schema is None
    
    def test_get_schemas_by_category(self):
        """Test get_schemas_by_category function."""
        # Test agent_behavior category
        schemas = get_schemas_by_category('agent_behavior')
        assert len(schemas) == 2
        codes = [s['event_code'] for s in schemas]
        assert set(codes) == {'mode', 'decision'}
        
        # Test economic_transaction category
        schemas = get_schemas_by_category('economic_transaction')
        assert len(schemas) == 1
        assert schemas[0]['event_code'] == 'trade'
        
        # Test nonexistent category
        schemas = get_schemas_by_category('nonexistent')
        assert schemas == []
    
    def test_validate_all_schemas(self):
        """Test validate_all_schemas function."""
        results = validate_all_schemas()
        
        # All schemas should be valid
        for event_code, is_valid in results.items():
            assert is_valid == True, f"Schema {event_code} failed validation"
        
        # Should have results for all registered schemas
        expected_codes = set(SCHEMA_REGISTRY.keys())
        actual_codes = set(results.keys())
        assert actual_codes == expected_codes
    
    def test_schema_field_types(self):
        """Test that all schemas have proper field type definitions."""
        for event_code, schema in SCHEMA_REGISTRY.items():
            for field_name, field_def in schema['fields'].items():
                # Check that type is defined
                assert 'type' in field_def, f"Field {field_name} in {event_code} missing type"
                
                # Check that type is valid
                valid_types = {'int', 'float', 'str', 'bool', 'dict', 'list'}
                assert field_def['type'] in valid_types, f"Invalid type {field_def['type']} for field {field_name} in {event_code}"
                
                # Check that description is defined
                assert 'description' in field_def, f"Field {field_name} in {event_code} missing description"
    
    def test_schema_extensibility_examples(self):
        """Test that schemas include extensibility examples."""
        # Check that trade schema has future fields
        trade_fields = TRADE_EXECUTION_SCHEMA['fields']
        assert 'trade_volume' in trade_fields
        assert 'market_price' in trade_fields
        assert 'trade_efficiency' in trade_fields
        
        # Check that mode schema has future fields
        mode_fields = AGENT_MODE_SCHEMA['fields']
        assert 'transition_duration' in mode_fields
        assert 'decision_confidence' in mode_fields
        
        # Verify these are marked as optional
        assert trade_fields['trade_volume']['required'] == False
        assert trade_fields['market_price']['required'] == False
        assert trade_fields['trade_efficiency']['required'] == False
        assert mode_fields['transition_duration']['required'] == False
        assert mode_fields['decision_confidence']['required'] == False
