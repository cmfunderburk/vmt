"""
Event schema definitions for the new extensible log architecture.

This module provides declarative schema definitions for all event types used in the
VMT simulation system. Schemas serve two purposes:
1. Documentation - Single source of truth for field codes and compression format
2. Translation - Used by translator.py to decompress logs for GUI/analysis tools

Schemas are NOT used during emission - Direct methods have hardcoded compression for performance.

Schema Format:
- event_code: Short code used in compressed logs (e.g., 'trade', 'mode')
- version: Schema version for format evolution
- category: Event category for GUI grouping and filtering
- description: Human-readable description of the event type
- fields: Dictionary mapping field names to compression codes and metadata
"""

from typing import Dict, Any, Optional, Union


# ============================================================================
# TRADE EXECUTION SCHEMA
# ============================================================================

TRADE_EXECUTION_SCHEMA = {
    'event_code': 'trade',
    'version': '1.0',
    'category': 'economic_transaction',
    'description': 'Trade execution event between two agents',
    'fields': {
        'seller_id': {'code': 'sid', 'type': 'int', 'required': True, 'description': 'Agent giving the resource'},
        'buyer_id': {'code': 'bid', 'type': 'int', 'required': True, 'description': 'Agent receiving the resource'},
        'give_type': {'code': 'gt', 'type': 'str', 'required': True, 'description': 'Resource type being given'},
        'take_type': {'code': 'tt', 'type': 'str', 'required': True, 'description': 'Resource type being received'},
        'delta_u_seller': {'code': 'dus', 'type': 'float', 'required': True, 'description': 'Utility change for seller'},
        'delta_u_buyer': {'code': 'dub', 'type': 'float', 'required': True, 'description': 'Utility change for buyer'},
        'trade_location_x': {'code': 'tx', 'type': 'int', 'required': False, 'description': 'X coordinate of trade location'},
        'trade_location_y': {'code': 'ty', 'type': 'int', 'required': False, 'description': 'Y coordinate of trade location'},
        # FUTURE: Easy to add new fields
        'trade_volume': {'code': 'vol', 'type': 'float', 'required': False, 'description': 'Volume of trade'},
        'market_price': {'code': 'price', 'type': 'float', 'required': False, 'description': 'Market price at time of trade'},
        'trade_efficiency': {'code': 'eff', 'type': 'float', 'required': False, 'description': 'Trade efficiency score'},
    }
}


# ============================================================================
# AGENT MODE CHANGE SCHEMA
# ============================================================================

AGENT_MODE_SCHEMA = {
    'event_code': 'mode',
    'version': '1.0',
    'category': 'agent_behavior',
    'description': 'Agent behavioral mode transition event',
    'fields': {
        'agent_id': {'code': 'aid', 'type': 'int', 'required': True, 'description': 'Unique agent identifier'},
        'old_mode': {'code': 'om', 'type': 'str', 'required': True, 'description': 'Previous behavioral mode'},
        'new_mode': {'code': 'nm', 'type': 'str', 'required': True, 'description': 'New behavioral mode'},
        'reason': {'code': 'r', 'type': 'str', 'required': True, 'description': 'Reason for mode change'},
        # FUTURE: Easy to add new mode transition data
        'transition_duration': {'code': 'dur', 'type': 'float', 'required': False, 'description': 'Duration of transition'},
        'decision_confidence': {'code': 'conf', 'type': 'float', 'required': False, 'description': 'Confidence in decision'},
    }
}


# ============================================================================
# RESOURCE COLLECTION SCHEMA
# ============================================================================

RESOURCE_COLLECTION_SCHEMA = {
    'event_code': 'collect',
    'version': '1.0',
    'category': 'resource_activity',
    'description': 'Resource collection event by an agent',
    'fields': {
        'agent_id': {'code': 'aid', 'type': 'int', 'required': True, 'description': 'Agent collecting the resource'},
        'x': {'code': 'x', 'type': 'int', 'required': True, 'description': 'X coordinate of resource'},
        'y': {'code': 'y', 'type': 'int', 'required': True, 'description': 'Y coordinate of resource'},
        'resource_type': {'code': 'rt', 'type': 'str', 'required': True, 'description': 'Type of resource collected'},
        'amount_collected': {'code': 'amt', 'type': 'int', 'required': True, 'description': 'Amount of resource collected'},
        'utility_gained': {'code': 'ug', 'type': 'float', 'required': True, 'description': 'Utility gained from collection'},
        'carrying_after': {'code': 'ca', 'type': 'dict', 'required': False, 'description': 'Agent inventory after collection'},
    }
}


# ============================================================================
# DEBUG LOG SCHEMA
# ============================================================================

DEBUG_LOG_SCHEMA = {
    'event_code': 'debug',
    'version': '1.0',
    'category': 'system_logging',
    'description': 'Debug/categorical logging message event',
    'fields': {
        'category': {'code': 'cat', 'type': 'str', 'required': True, 'description': 'Log category (TRADE, MODE, ECON, etc.)'},
        'message': {'code': 'msg', 'type': 'str', 'required': True, 'description': 'Debug message text'},
        'agent_id': {'code': 'aid', 'type': 'int', 'required': False, 'description': 'Optional agent context'},
    }
}


# ============================================================================
# PERFORMANCE MONITOR SCHEMA
# ============================================================================

PERFORMANCE_MONITOR_SCHEMA = {
    'event_code': 'perf',
    'version': '1.0',
    'category': 'system_monitoring',
    'description': 'Performance monitoring and metrics event',
    'fields': {
        'metric_name': {'code': 'mn', 'type': 'str', 'required': True, 'description': 'Name of performance metric'},
        'metric_value': {'code': 'mv', 'type': 'float', 'required': True, 'description': 'Numeric value of metric'},
        'threshold_exceeded': {'code': 'te', 'type': 'bool', 'required': False, 'description': 'Whether threshold was exceeded'},
        'details': {'code': 'det', 'type': 'str', 'required': False, 'description': 'Additional context or details'},
    }
}


# ============================================================================
# AGENT DECISION SCHEMA
# ============================================================================

AGENT_DECISION_SCHEMA = {
    'event_code': 'decision',
    'version': '1.0',
    'category': 'agent_behavior',
    'description': 'Agent decision-making process event',
    'fields': {
        'agent_id': {'code': 'aid', 'type': 'int', 'required': True, 'description': 'ID of agent making decision'},
        'decision_type': {'code': 'dt', 'type': 'str', 'required': True, 'description': 'Type of decision (movement, collection, etc.)'},
        'decision_details': {'code': 'dd', 'type': 'str', 'required': True, 'description': 'Detailed description of decision'},
        'utility_delta': {'code': 'ud', 'type': 'float', 'required': False, 'description': 'Utility change from decision'},
        'position_x': {'code': 'px', 'type': 'int', 'required': False, 'description': 'X coordinate context'},
        'position_y': {'code': 'py', 'type': 'int', 'required': False, 'description': 'Y coordinate context'},
    }
}


# ============================================================================
# RESOURCE EVENT SCHEMA
# ============================================================================

RESOURCE_EVENT_SCHEMA = {
    'event_code': 'resource',
    'version': '1.0',
    'category': 'resource_activity',
    'description': 'Resource lifecycle event (spawn, despawn, move, etc.)',
    'fields': {
        'event_type_detail': {'code': 'etd', 'type': 'str', 'required': True, 'description': 'Specific type of resource event'},
        'position_x': {'code': 'px', 'type': 'int', 'required': True, 'description': 'X coordinate of resource'},
        'position_y': {'code': 'py', 'type': 'int', 'required': True, 'description': 'Y coordinate of resource'},
        'resource_type': {'code': 'rt', 'type': 'str', 'required': True, 'description': 'Type of resource'},
        'amount': {'code': 'amt', 'type': 'int', 'required': True, 'description': 'Amount of resource'},
        'agent_id': {'code': 'aid', 'type': 'int', 'required': False, 'description': 'Optional agent context'},
    }
}


# ============================================================================
# ECONOMIC DECISION SCHEMA
# ============================================================================

ECONOMIC_DECISION_SCHEMA = {
    'event_code': 'econ',
    'version': '1.0',
    'category': 'economic_analysis',
    'description': 'Detailed economic decision-making process event',
    'fields': {
        'agent_id': {'code': 'aid', 'type': 'int', 'required': True, 'description': 'ID of agent making economic decision'},
        'decision_type': {'code': 'dt', 'type': 'str', 'required': True, 'description': 'Type of economic decision'},
        'decision_context': {'code': 'dc', 'type': 'str', 'required': True, 'description': 'Detailed context of decision'},
        'utility_before': {'code': 'ub', 'type': 'float', 'required': False, 'description': 'Agent utility before decision'},
        'utility_after': {'code': 'ua', 'type': 'float', 'required': False, 'description': 'Agent utility after decision'},
        'opportunity_cost': {'code': 'oc', 'type': 'float', 'required': False, 'description': 'Cost of not choosing alternatives'},
        'alternatives_considered': {'code': 'ac', 'type': 'int', 'required': False, 'description': 'Number of alternatives evaluated'},
        'decision_time_ms': {'code': 'dtm', 'type': 'float', 'required': False, 'description': 'Time taken to make decision'},
        'position_x': {'code': 'px', 'type': 'int', 'required': False, 'description': 'X coordinate context'},
        'position_y': {'code': 'py', 'type': 'int', 'required': False, 'description': 'Y coordinate context'},
    }
}


# ============================================================================
# GUI DISPLAY SCHEMA (Optional)
# ============================================================================

GUI_DISPLAY_SCHEMA = {
    'event_code': 'gui',
    'version': '1.0',
    'category': 'user_interface',
    'description': 'GUI display update and visual feedback event',
    'fields': {
        'display_type': {'code': 'dt', 'type': 'str', 'required': True, 'description': 'Type of display update'},
        'element_id': {'code': 'eid', 'type': 'str', 'required': True, 'description': 'GUI element identifier'},
        'data': {'code': 'data', 'type': 'dict', 'required': False, 'description': 'Flexible data payload for display info'},
    }
}


# ============================================================================
# SCHEMA REGISTRY
# ============================================================================

SCHEMA_REGISTRY: Dict[str, Dict[str, Any]] = {
    'trade': TRADE_EXECUTION_SCHEMA,
    'mode': AGENT_MODE_SCHEMA,
    'collect': RESOURCE_COLLECTION_SCHEMA,
    'debug': DEBUG_LOG_SCHEMA,
    'perf': PERFORMANCE_MONITOR_SCHEMA,
    'decision': AGENT_DECISION_SCHEMA,
    'resource': RESOURCE_EVENT_SCHEMA,
    'econ': ECONOMIC_DECISION_SCHEMA,
    'gui': GUI_DISPLAY_SCHEMA,
}


# ============================================================================
# SCHEMA VALIDATION HELPERS
# ============================================================================

def validate_schema(schema: Dict[str, Any]) -> bool:
    """Validate that a schema has the required structure.
    
    Args:
        schema: Schema dictionary to validate
        
    Returns:
        True if schema is valid, False otherwise
    """
    required_keys = {'event_code', 'version', 'category', 'description', 'fields'}
    if not all(key in schema for key in required_keys):
        return False
    
    if not isinstance(schema['fields'], dict):
        return False
    
    # Validate field definitions
    for field_name, field_def in schema['fields'].items():
        if not isinstance(field_def, dict):
            return False
        if 'code' not in field_def or 'type' not in field_def:
            return False
    
    return True


def get_field_code(schema: Dict[str, Any], field_name: str) -> Optional[str]:
    """Get the compression code for a field in a schema.
    
    Args:
        schema: Schema dictionary
        field_name: Name of the field
        
    Returns:
        Compression code for the field, or None if not found
    """
    if 'fields' not in schema:
        return None
    return schema['fields'].get(field_name, {}).get('code')


def get_required_fields(schema: Dict[str, Any]) -> list[str]:
    """Get list of required field names from a schema.
    
    Args:
        schema: Schema dictionary
        
    Returns:
        List of required field names
    """
    if 'fields' not in schema:
        return []
    
    required = []
    for field_name, field_def in schema['fields'].items():
        if field_def.get('required', False):
            required.append(field_name)
    
    return required


def get_optional_fields(schema: Dict[str, Any]) -> list[str]:
    """Get list of optional field names from a schema.
    
    Args:
        schema: Schema dictionary
        
    Returns:
        List of optional field names
    """
    if 'fields' not in schema:
        return []
    
    optional = []
    for field_name, field_def in schema['fields'].items():
        if not field_def.get('required', False):
            optional.append(field_name)
    
    return optional


def create_reverse_mapping(schema: Dict[str, Any]) -> Dict[str, str]:
    """Create reverse mapping from field codes to field names.
    
    Args:
        schema: Schema dictionary
        
    Returns:
        Dictionary mapping field codes to field names
    """
    if 'fields' not in schema:
        return {}
    
    reverse = {}
    for field_name, field_def in schema['fields'].items():
        code = field_def.get('code')
        if code:
            reverse[code] = field_name
    
    return reverse


# ============================================================================
# SCHEMA UTILITIES
# ============================================================================

def get_all_event_codes() -> list[str]:
    """Get all registered event codes.
    
    Returns:
        List of all event codes in the registry
    """
    return list(SCHEMA_REGISTRY.keys())


def get_schema_by_code(event_code: str) -> Optional[Dict[str, Any]]:
    """Get schema by event code.
    
    Args:
        event_code: Event code to lookup
        
    Returns:
        Schema dictionary or None if not found
    """
    return SCHEMA_REGISTRY.get(event_code)


def get_schemas_by_category(category: str) -> list[Dict[str, Any]]:
    """Get all schemas in a specific category.
    
    Args:
        category: Category to filter by
        
    Returns:
        List of schema dictionaries in the category
    """
    schemas = []
    for schema in SCHEMA_REGISTRY.values():
        if schema.get('category') == category:
            schemas.append(schema)
    return schemas


def validate_all_schemas() -> Dict[str, bool]:
    """Validate all schemas in the registry.
    
    Returns:
        Dictionary mapping event codes to validation results
    """
    results = {}
    for event_code, schema in SCHEMA_REGISTRY.items():
        results[event_code] = validate_schema(schema)
    return results
