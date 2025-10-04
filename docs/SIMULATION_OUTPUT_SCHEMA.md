# Simulation Output Schema

**Version:** 1.0.0-dev  
**Status:** Unstable during refactor  
**Last Updated:** 2025-01-03

## Overview

This document describes the event schema used by the observer system to record simulation state changes. The schema defines all event types that can be recorded during VMT EconSim execution, providing type definitions, field requirements, and usage examples.

**Important:** Schema is unstable during refactor. All saved outputs will be invalidated by changes.

## Architecture

The observer system uses a zero-overhead recording architecture where events are stored as raw dictionaries during simulation, with analysis and formatting deferred until needed. All concrete observers (`FileObserver`, `EducationalObserver`, `PerformanceObserver`, `MemoryObserver`, `EconomicObserver`) inherit from `RawDataObserver` and use the same event recording interface.

## Event Types

### Agent Events

#### mode_change
Records agent behavioral mode changes.

**Emitted By:** Simulation world, movement handlers, event emitters, and observer implementations  
**Conditions:** When agents change behavioral modes or when processing 'agent_mode_change' events

**Fields:**
- `step` (int, required): Simulation step number
- `agent_id` (int, required): ID of agent changing mode
- `old_mode` (str, required): Previous behavioral mode
- `new_mode` (str, required): New behavioral mode
- `reason` (str, optional): Explanation for mode change (default: "")

**Example:**
```json
{
  "step": 101,
  "agent_id": 1,
  "old_mode": "foraging",
  "new_mode": "trading",
  "reason": "found partner"
}
```

#### agent_decision
Records agent decision-making events.

**Emitted By:** Simulation world during agent decision recording and observer implementations  
**Conditions:** When agents make decisions or when processing 'agent_decision' events

**Fields:**
- `step` (int, required): Simulation step number
- `agent_id` (int, required): ID of agent making decision
- `decision_type` (str, required): Type of decision (movement, collection, trade_intent, etc.)
- `decision_details` (str, required): Detailed description of decision
- `utility_delta` (float, optional): Utility change associated with decision (default: 0.0)
- `position_x` (int, optional): Optional X coordinate context (default: -1)
- `position_y` (int, optional): Optional Y coordinate context (default: -1)

**Example:**
```json
{
  "step": 105,
  "agent_id": 1,
  "decision_type": "movement",
  "decision_details": "Moving to nearest wood resource",
  "utility_delta": 2.0,
  "position_x": 15,
  "position_y": 20
}
```

### Resource Events

#### resource_collection
Records resource collection events by agents.

**Emitted By:** Simulation agents during resource collection and observer implementations  
**Conditions:** When agents collect resources or when processing 'resource_collection' events

**Fields:**
- `step` (int, required): Simulation step number
- `agent_id` (int, required): ID of agent collecting resource
- `x` (int, required): X coordinate of resource
- `y` (int, required): Y coordinate of resource
- `resource_type` (str, required): Type of resource collected
- `amount_collected` (int, optional): Amount collected (default: 1)
- `utility_gained` (float, optional): Utility gained from collection (default: 0.0)
- `carrying_after` (dict, optional): Agent's inventory after collection (default: {})

**Example:**
```json
{
  "step": 102,
  "agent_id": 1,
  "x": 15,
  "y": 20,
  "resource_type": "wood",
  "amount_collected": 2,
  "utility_gained": 4.0,
  "carrying_after": {"wood": 3, "stone": 1}
}
```

#### resource_event
Records resource-related events (spawn, despawn, move, etc.).

**Emitted By:** Observer implementations when processing 'resource_event' events  
**Conditions:** When resource-related events are processed through observer registry

**Fields:**
- `step` (int, required): Simulation step number
- `event_type_detail` (str, required): Specific type of resource event (spawn, despawn, move, etc.)
- `position_x` (int, required): X coordinate of resource
- `position_y` (int, required): Y coordinate of resource
- `resource_type` (str, required): Type of resource
- `amount` (int, optional): Amount of resource (default: 1)
- `agent_id` (int, optional): Optional agent context (default: -1)

**Example:**
```json
{
  "step": 106,
  "event_type_detail": "spawn",
  "position_x": 25,
  "position_y": 30,
  "resource_type": "stone",
  "amount": 3,
  "agent_id": -1
}
```

### Trade Events

#### trade
Records trade execution events between agents.

**Emitted By:** Observer implementations when processing 'trade_execution' events  
**Conditions:** When trade_execution events are processed through observer registry

**Fields:**
- `step` (int, required): Simulation step number
- `seller_id` (int, required): ID of agent giving resource
- `buyer_id` (int, required): ID of agent receiving resource
- `give_type` (str, required): Resource type being given
- `take_type` (str, required): Resource type being received
- `delta_u_seller` (float, optional): Utility change for seller (default: 0.0)
- `delta_u_buyer` (float, optional): Utility change for buyer (default: 0.0)
- `trade_location_x` (int, optional): X coordinate of trade location (default: -1)
- `trade_location_y` (int, optional): Y coordinate of trade location (default: -1)

**Example:**
```json
{
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
```

### Economic Events

#### economic_decision
Records detailed economic decision-making events.

**Emitted By:** Observer implementations when processing 'economic_decision' events  
**Conditions:** When economic decision events are processed through observer registry

**Fields:**
- `step` (int, required): Simulation step number
- `agent_id` (int, required): ID of agent making economic decision
- `decision_type` (str, required): Type of economic decision (resource_selection, trade_proposal, etc.)
- `decision_context` (str, required): Detailed context of decision
- `utility_before` (float, optional): Agent's utility before decision (default: 0.0)
- `utility_after` (float, optional): Agent's utility after decision (default: 0.0)
- `utility_delta` (float, optional): Calculated as utility_after - utility_before
- `opportunity_cost` (float, optional): Cost of not choosing alternatives (default: 0.0)
- `alternatives_considered` (int, optional): Number of alternatives evaluated (default: 0)
- `decision_time_ms` (float, optional): Time taken to make decision (default: 0.0)
- `position_x` (int, optional): Optional X coordinate context (default: -1)
- `position_y` (int, optional): Optional Y coordinate context (default: -1)

**Example:**
```json
{
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
```

### System Events

#### debug_log
Records debug and logging information.

**Emitted By:** Simulation agents, world, and observer implementations  
**Conditions:** For debug information, agent mode changes, movement decisions, partner search, and as fallback for unknown event types

**Fields:**
- `step` (int, required): Simulation step number
- `category` (str, required): Log category (TRADE, MODE, ECON, etc.)
- `message` (str, required): Debug message text
- `agent_id` (int, optional): Optional agent context (default: -1)

**Example:**
```json
{
  "step": 103,
  "category": "MOVEMENT",
  "message": "Agent 1 moved from (10,10) to (11,10)",
  "agent_id": 1
}
```

#### performance_monitor
Records performance monitoring metrics.

**Emitted By:** Observer implementations when processing 'performance_monitor' events  
**Conditions:** When performance monitoring events are processed through observer registry

**Fields:**
- `step` (int, required): Simulation step number
- `metric_name` (str, required): Name of performance metric
- `metric_value` (float, required): Numeric value of metric
- `threshold_exceeded` (bool, optional): Whether metric exceeded threshold (default: false)
- `details` (str, optional): Additional context or details (default: "")

**Example:**
```json
{
  "step": 104,
  "metric_name": "avg_step_time_ms",
  "metric_value": 15.5,
  "threshold_exceeded": false,
  "details": "Performance within normal range"
}
```

## Event Categories

Events are organized into logical categories for easier management and filtering:

- **Agent Events**: `mode_change`, `agent_decision`
- **Resource Events**: `resource_collection`, `resource_event`
- **Trade Events**: `trade`
- **Economic Events**: `economic_decision`
- **System Events**: `debug_log`, `performance_monitor`

## Usage Patterns

### High Usage Events
These events are actively used throughout the simulation:
- `debug_log`: Used extensively for logging and debugging
- `mode_change`: Used in world, movement handlers, and event emitters
- `resource_collection`: Used in agents during resource collection

### Medium Usage Events
These events are used in specific simulation components:
- `agent_decision`: Used in simulation world for decision tracking
- `trade`: Used in observer implementations

### Low Usage Events
These events are defined but have limited current usage:
- `performance_monitor`: Used only in observer implementations
- `resource_event`: Used only in observer implementations
- `economic_decision`: Used only in observer implementations

## Data Flow

1. **Event Generation**: Events are generated by simulation components (agents, world, handlers)
2. **Observer Registry**: Events are distributed through the observer registry
3. **Observer Processing**: Each observer's `notify()` method processes events
4. **Raw Recording**: `record_` methods are called to store raw event data
5. **Analysis**: Raw data is later processed for analysis, formatting, or output

## Schema Evolution

During refactor:
- Schema can change freely
- No migration needed
- All old outputs invalidated
- Version locked at release candidate

## Validation

The schema includes validation functions in `src/econsim/observability/event_schema.py`:

- `validate_event()`: Validates event data against schema
- `get_event_schema()`: Retrieves schema for specific event type
- `get_all_event_types()`: Lists all supported event types
- `get_events_by_category()`: Gets events by category
- `get_required_fields()`: Lists required fields for an event type
- `get_optional_fields()`: Lists optional fields with defaults

## Implementation Notes

- All events are stored as dictionaries in chronological order
- Optional fields use sensible defaults to minimize storage overhead
- The `**kwargs` pattern allows for extensibility without schema changes
- Zero-overhead recording achieves <0.0001ms per event target
- Events accumulate in memory with no automatic cleanup during simulation
