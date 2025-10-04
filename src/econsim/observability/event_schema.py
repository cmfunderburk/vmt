"""Official event schema for VMT EconSim observability.

Schema Version: 1.0.0-dev
Note: Schema unstable during refactor. Versioning comes post-refactor.

This schema defines all event types recorded by the RawDataObserver system,
providing type definitions, field requirements, and examples for each event.
"""

SCHEMA_VERSION = "1.0.0-dev"

# Document all event types based on RawDataObserver record_ methods
EVENT_TYPES = {
    "trade": {
        "description": "Records trade execution events between agents",
        "emitted_by": "Observer implementations when processing 'trade_execution' events",
        "emission_conditions": "When trade_execution events are processed through observer registry",
        "fields": {
            "step": {"type": int, "required": True, "description": "Simulation step number"},
            "seller_id": {"type": int, "required": True, "description": "ID of agent giving resource"},
            "buyer_id": {"type": int, "required": True, "description": "ID of agent receiving resource"},
            "give_type": {"type": str, "required": True, "description": "Resource type being given"},
            "take_type": {"type": str, "required": True, "description": "Resource type being received"},
            "delta_u_seller": {"type": float, "required": False, "default": 0.0, "description": "Utility change for seller"},
            "delta_u_buyer": {"type": float, "required": False, "default": 0.0, "description": "Utility change for buyer"},
            "trade_location_x": {"type": int, "required": False, "default": -1, "description": "X coordinate of trade location"},
            "trade_location_y": {"type": int, "required": False, "default": -1, "description": "Y coordinate of trade location"}
        },
        "example": {
            "step": 100,
            "seller_id": 1,
            "buyer_id": 2,
            "give_type": "wood",
            "take_type": "stone",
            "delta_u_seller": 5.0,
            "delta_u_buyer": 3.0,
            "trade_location_x": 15,
            "trade_location_y": 20
        }
    },
    
    "mode_change": {
        "description": "Records agent behavioral mode changes",
        "emitted_by": "Simulation world, movement handlers, event emitters, and observer implementations",
        "emission_conditions": "When agents change behavioral modes or when processing 'agent_mode_change' events",
        "fields": {
            "step": {"type": int, "required": True, "description": "Simulation step number"},
            "agent_id": {"type": int, "required": True, "description": "ID of agent changing mode"},
            "old_mode": {"type": str, "required": True, "description": "Previous behavioral mode"},
            "new_mode": {"type": str, "required": True, "description": "New behavioral mode"},
            "reason": {"type": str, "required": False, "default": "", "description": "Explanation for mode change"}
        },
        "example": {
            "step": 101,
            "agent_id": 1,
            "old_mode": "foraging",
            "new_mode": "trading",
            "reason": "found partner"
        }
    },
    
    "resource_collection": {
        "description": "Records resource collection events by agents",
        "emitted_by": "Simulation agents during resource collection and observer implementations",
        "emission_conditions": "When agents collect resources or when processing 'resource_collection' events",
        "fields": {
            "step": {"type": int, "required": True, "description": "Simulation step number"},
            "agent_id": {"type": int, "required": True, "description": "ID of agent collecting resource"},
            "x": {"type": int, "required": True, "description": "X coordinate of resource"},
            "y": {"type": int, "required": True, "description": "Y coordinate of resource"},
            "resource_type": {"type": str, "required": True, "description": "Type of resource collected"},
            "amount_collected": {"type": int, "required": False, "default": 1, "description": "Amount collected"},
            "utility_gained": {"type": float, "required": False, "default": 0.0, "description": "Utility gained from collection"},
            "carrying_after": {"type": dict, "required": False, "default": {}, "description": "Agent's inventory after collection"}
        },
        "example": {
            "step": 102,
            "agent_id": 1,
            "x": 15,
            "y": 20,
            "resource_type": "wood",
            "amount_collected": 2,
            "utility_gained": 4.0,
            "carrying_after": {"wood": 3, "stone": 1}
        }
    },
    
    "debug_log": {
        "description": "Records debug and logging information",
        "emitted_by": "Simulation agents, world, and observer implementations",
        "emission_conditions": "For debug information, agent mode changes, movement decisions, partner search, and as fallback for unknown event types",
        "fields": {
            "step": {"type": int, "required": True, "description": "Simulation step number"},
            "category": {"type": str, "required": True, "description": "Log category (TRADE, MODE, ECON, etc.)"},
            "message": {"type": str, "required": True, "description": "Debug message text"},
            "agent_id": {"type": int, "required": False, "default": -1, "description": "Optional agent context"}
        },
        "example": {
            "step": 103,
            "category": "MOVEMENT",
            "message": "Agent 1 moved from (10,10) to (11,10)",
            "agent_id": 1
        }
    },
    
    "performance_monitor": {
        "description": "Records performance monitoring metrics",
        "emitted_by": "Observer implementations when processing 'performance_monitor' events",
        "emission_conditions": "When performance monitoring events are processed through observer registry",
        "fields": {
            "step": {"type": int, "required": True, "description": "Simulation step number"},
            "metric_name": {"type": str, "required": True, "description": "Name of performance metric"},
            "metric_value": {"type": float, "required": True, "description": "Numeric value of metric"},
            "threshold_exceeded": {"type": bool, "required": False, "default": False, "description": "Whether metric exceeded threshold"},
            "details": {"type": str, "required": False, "default": "", "description": "Additional context or details"}
        },
        "example": {
            "step": 104,
            "metric_name": "avg_step_time_ms",
            "metric_value": 15.5,
            "threshold_exceeded": False,
            "details": "Performance within normal range"
        }
    },
    
    "agent_decision": {
        "description": "Records agent decision-making events",
        "emitted_by": "Simulation world during agent decision recording and observer implementations",
        "emission_conditions": "When agents make decisions or when processing 'agent_decision' events",
        "fields": {
            "step": {"type": int, "required": True, "description": "Simulation step number"},
            "agent_id": {"type": int, "required": True, "description": "ID of agent making decision"},
            "decision_type": {"type": str, "required": True, "description": "Type of decision (movement, collection, trade_intent, etc.)"},
            "decision_details": {"type": str, "required": True, "description": "Detailed description of decision"},
            "utility_delta": {"type": float, "required": False, "default": 0.0, "description": "Utility change associated with decision"},
            "position_x": {"type": int, "required": False, "default": -1, "description": "Optional X coordinate context"},
            "position_y": {"type": int, "required": False, "default": -1, "description": "Optional Y coordinate context"}
        },
        "example": {
            "step": 105,
            "agent_id": 1,
            "decision_type": "movement",
            "decision_details": "Moving to nearest wood resource",
            "utility_delta": 2.0,
            "position_x": 15,
            "position_y": 20
        }
    },
    
    "resource_event": {
        "description": "Records resource-related events (spawn, despawn, move, etc.)",
        "emitted_by": "Observer implementations when processing 'resource_event' events",
        "emission_conditions": "When resource-related events are processed through observer registry",
        "fields": {
            "step": {"type": int, "required": True, "description": "Simulation step number"},
            "event_type_detail": {"type": str, "required": True, "description": "Specific type of resource event (spawn, despawn, move, etc.)"},
            "position_x": {"type": int, "required": True, "description": "X coordinate of resource"},
            "position_y": {"type": int, "required": True, "description": "Y coordinate of resource"},
            "resource_type": {"type": str, "required": True, "description": "Type of resource"},
            "amount": {"type": int, "required": False, "default": 1, "description": "Amount of resource"},
            "agent_id": {"type": int, "required": False, "default": -1, "description": "Optional agent context"}
        },
        "example": {
            "step": 106,
            "event_type_detail": "spawn",
            "position_x": 25,
            "position_y": 30,
            "resource_type": "stone",
            "amount": 3,
            "agent_id": -1
        }
    },
    
    "economic_decision": {
        "description": "Records detailed economic decision-making events",
        "emitted_by": "Observer implementations when processing 'economic_decision' events",
        "emission_conditions": "When economic decision events are processed through observer registry",
        "fields": {
            "step": {"type": int, "required": True, "description": "Simulation step number"},
            "agent_id": {"type": int, "required": True, "description": "ID of agent making economic decision"},
            "decision_type": {"type": str, "required": True, "description": "Type of economic decision (resource_selection, trade_proposal, etc.)"},
            "decision_context": {"type": str, "required": True, "description": "Detailed context of decision"},
            "utility_before": {"type": float, "required": False, "default": 0.0, "description": "Agent's utility before decision"},
            "utility_after": {"type": float, "required": False, "default": 0.0, "description": "Agent's utility after decision"},
            "utility_delta": {"type": float, "required": False, "description": "Calculated as utility_after - utility_before"},
            "opportunity_cost": {"type": float, "required": False, "default": 0.0, "description": "Cost of not choosing alternatives"},
            "alternatives_considered": {"type": int, "required": False, "default": 0, "description": "Number of alternatives evaluated"},
            "decision_time_ms": {"type": float, "required": False, "default": 0.0, "description": "Time taken to make decision"},
            "position_x": {"type": int, "required": False, "default": -1, "description": "Optional X coordinate context"},
            "position_y": {"type": int, "required": False, "default": -1, "description": "Optional Y coordinate context"}
        },
        "example": {
            "step": 107,
            "agent_id": 1,
            "decision_type": "resource_selection",
            "decision_context": "Choosing between wood and stone for next collection",
            "utility_before": 10.0,
            "utility_after": 15.0,
            "utility_delta": 5.0,
            "opportunity_cost": 2.0,
            "alternatives_considered": 2,
            "decision_time_ms": 1.5,
            "position_x": 15,
            "position_y": 20
        }
    }
}

# Event categories for organization
EVENT_CATEGORIES = {
    "agent_events": ["mode_change", "agent_decision"],
    "resource_events": ["resource_collection", "resource_event"],
    "trade_events": ["trade"],
    "economic_events": ["economic_decision"],
    "system_events": ["debug_log", "performance_monitor"]
}

def validate_event(event_data: dict) -> bool:
    """Validate event data against schema.
    
    Args:
        event_data: Dictionary containing event data to validate
        
    Returns:
        True if event is valid, False otherwise
    """
    if not isinstance(event_data, dict):
        return False
        
    event_type = event_data.get('type')
    if not event_type or event_type not in EVENT_TYPES:
        return False
        
    schema = EVENT_TYPES[event_type]
    fields = schema.get('fields', {})
    
    # Check required fields
    for field_name, field_info in fields.items():
        if field_info.get('required', False):
            if field_name not in event_data:
                return False
                
            # Type validation
            expected_type = field_info.get('type')
            if expected_type and not isinstance(event_data[field_name], expected_type):
                return False
    
    return True

def get_event_schema(event_type: str) -> dict:
    """Get schema for specific event type.
    
    Args:
        event_type: Name of the event type
        
    Returns:
        Dictionary containing schema information for the event type
    """
    return EVENT_TYPES.get(event_type, {})

def get_all_event_types() -> list:
    """Get list of all supported event types.
    
    Returns:
        List of event type names
    """
    return list(EVENT_TYPES.keys())

def get_events_by_category(category: str) -> list:
    """Get event types in a specific category.
    
    Args:
        category: Category name
        
    Returns:
        List of event type names in the category
    """
    return EVENT_CATEGORIES.get(category, [])

def get_required_fields(event_type: str) -> list:
    """Get list of required fields for an event type.
    
    Args:
        event_type: Name of the event type
        
    Returns:
        List of required field names
    """
    schema = get_event_schema(event_type)
    fields = schema.get('fields', {})
    return [field_name for field_name, field_info in fields.items() 
            if field_info.get('required', False)]

def get_optional_fields(event_type: str) -> list:
    """Get list of optional fields for an event type.
    
    Args:
        event_type: Name of the event type
        
    Returns:
        List of optional field names with their default values
    """
    schema = get_event_schema(event_type)
    fields = schema.get('fields', {})
    optional_fields = {}
    for field_name, field_info in fields.items():
        if not field_info.get('required', False):
            optional_fields[field_name] = field_info.get('default')
    return optional_fields
