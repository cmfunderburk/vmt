# Raw Data Observer API Documentation

**Date**: October 3, 2025  
**Status**: ✅ Current API - Pure Raw Data Architecture  
**Version**: Phase 4 Complete  

## Overview

The Raw Data Observer API provides zero-overhead event recording for the simulation system. All events are stored as raw dictionaries with no transformation layers, achieving excellent performance (0.319% frame budget overhead).

## Core Interface

### RawDataObserver

**Location**: `src/econsim/observability/raw_data/raw_data_observer.py`

The primary interface for recording simulation events as raw dictionaries.

#### Initialization

```python
from econsim.observability.raw_data import RawDataObserver, RawDataWriter

# Create observer with file output
writer = RawDataWriter(output_dir="logs", compress=True)
observer = RawDataObserver(writer=writer)

# Create observer for in-memory testing
observer = RawDataObserver()  # No writer = in-memory only
```

#### Core Recording Methods

##### record_trade(data: Dict[str, Any]) -> None

Records trade execution events.

**Required Fields**:
```python
{
    'type': 'trade',                    # Event type identifier
    'step': int,                        # Simulation step number
    'seller_id': int,                   # Selling agent ID
    'buyer_id': int,                    # Buying agent ID
    'give_type': str,                   # Resource type given
    'take_type': str,                   # Resource type received
    'delta_u_seller': float,            # Utility change for seller
    'delta_u_buyer': float,             # Utility change for buyer
    'location_x': int,                  # Trade location X coordinate
    'location_y': int                   # Trade location Y coordinate
}
```

**Example Usage**:
```python
observer.record_trade({
    'type': 'trade',
    'step': 42,
    'seller_id': 1,
    'buyer_id': 2,
    'give_type': 'wood',
    'take_type': 'stone',
    'delta_u_seller': 0.15,
    'delta_u_buyer': 0.23,
    'location_x': 5,
    'location_y': 3
})
```

##### record_mode_change(data: Dict[str, Any]) -> None

Records agent mode transition events.

**Required Fields**:
```python
{
    'type': 'mode_change',              # Event type identifier
    'step': int,                        # Simulation step number
    'agent_id': int,                    # Agent ID
    'old_mode': str,                    # Previous mode (FORAGING, TRADING, etc.)
    'new_mode': str,                    # New mode
    'reason': str                       # Business logic reason for change
}
```

**Example Usage**:
```python
observer.record_mode_change({
    'type': 'mode_change',
    'step': 42,
    'agent_id': 1,
    'old_mode': 'FORAGING',
    'new_mode': 'TRADING',
    'reason': 'found_trading_partner'
})
```

##### record_resource_collection(data: Dict[str, Any]) -> None

Records resource collection events.

**Required Fields**:
```python
{
    'type': 'resource_collection',      # Event type identifier
    'step': int,                        # Simulation step number
    'agent_id': int,                    # Collecting agent ID
    'resource_type': str,               # Type of resource collected
    'amount_collected': int,            # Amount collected
    'location_x': int,                  # Collection location X coordinate
    'location_y': int,                  # Collection location Y coordinate
    'utility_gained': float,            # Utility gained from collection
    'inventory_after': dict             # Agent inventory after collection
}
```

**Example Usage**:
```python
observer.record_resource_collection({
    'type': 'resource_collection',
    'step': 43,
    'agent_id': 2,
    'resource_type': 'stone',
    'amount_collected': 1,
    'location_x': 7,
    'location_y': 4,
    'utility_gained': 0.08,
    'inventory_after': {'wood': 0, 'stone': 3}
})
```

##### record_debug_log(data: Dict[str, Any]) -> None

Records debug and diagnostic messages.

**Required Fields**:
```python
{
    'type': 'debug_log',                # Event type identifier
    'step': int,                        # Simulation step number
    'category': str,                    # Log category (TRADE, MODE, ECON, etc.)
    'message': str,                     # Technical message
    'agent_id': int                     # Agent ID (-1 if not agent-specific)
}
```

**Example Usage**:
```python
observer.record_debug_log({
    'type': 'debug_log',
    'step': 44,
    'category': 'TRADE',
    'message': 'trade_execution_skipped_no_benefit',
    'agent_id': 1
})
```

##### record_performance_monitor(data: Dict[str, Any]) -> None

Records performance monitoring metrics.

**Required Fields**:
```python
{
    'type': 'performance_monitor',      # Event type identifier
    'step': int,                        # Simulation step number
    'metric_name': str,                 # Performance metric name
    'metric_value': float,              # Measured value
    'threshold_exceeded': bool,         # Whether threshold was exceeded
    'measurement_details': dict         # Additional measurement data
}
```

**Example Usage**:
```python
observer.record_performance_monitor({
    'type': 'performance_monitor',
    'step': 45,
    'metric_name': 'step_execution_time',
    'metric_value': 0.0023,
    'threshold_exceeded': False,
    'measurement_details': {
        'target_threshold': 0.016,
        'measurement_unit': 'seconds'
    }
})
```

#### Data Access Methods

##### get_events() -> List[Dict[str, Any]]

Returns all recorded events as raw dictionaries.

```python
events = observer.get_events()
print(f"Recorded {len(events)} events")

# Filter events by type
trade_events = [e for e in events if e.get('type') == 'trade']
```

##### clear()

Clears all recorded events (useful for testing).

```python
observer.clear()
assert len(observer.get_events()) == 0
```

## Integration with ObserverRegistry

### Automatic Registration

The `ObserverRegistry` provides automatic distribution to all registered observers:

```python
from econsim.observability import ObserverRegistry

registry = ObserverRegistry()
registry.add_observer(observer)

# Calls observer.record_trade() automatically
registry.record_trade({
    'type': 'trade',
    'step': 1,
    # ... trade data ...
})
```

### Handler Integration

Simulation handlers use the observer registry:

```python
# In simulation handler
def execute(self, context: StepContext) -> StepResult:
    # ... simulation logic ...
    
    # Record events via registry
    context.observer_registry.record_trade({
        'type': 'trade',
        'step': context.step_number,
        'seller_id': seller.agent_id,
        'buyer_id': buyer.agent_id,
        'give_type': give_type,
        'take_type': take_type,
        'delta_u_seller': delta_u_seller,
        'delta_u_buyer': delta_u_buyer,
        'location_x': seller.position[0],
        'location_y': seller.position[1]
    })
    
    return StepResult(metrics={'trades_recorded': 1})
```

## File Output

### RawDataWriter Configuration

```python
from econsim.observability.raw_data import RawDataWriter

# Basic configuration
writer = RawDataWriter(
    output_dir="simulation_logs",      # Output directory
    compress=True,                     # Enable gzip compression
    filename_prefix="events"           # File prefix
)

# Creates files like: simulation_logs/events_20251003_143022.jsonl.gz
```

### Output Format

Events are written as JSON Lines format:

```jsonl
{"type": "trade", "step": 42, "seller_id": 1, "buyer_id": 2, "give_type": "wood", "take_type": "stone", "delta_u_seller": 0.15, "delta_u_buyer": 0.23, "location_x": 5, "location_y": 3}
{"type": "mode_change", "step": 42, "agent_id": 1, "old_mode": "FORAGING", "new_mode": "TRADING", "reason": "found_trading_partner"}
{"type": "resource_collection", "step": 43, "agent_id": 2, "resource_type": "stone", "amount_collected": 1, "location_x": 7, "location_y": 4, "utility_gained": 0.08, "inventory_after": {"wood": 0, "stone": 3}}
```

## Performance Characteristics

### Overhead Metrics

- **Recording Overhead**: 0.051ms per step
- **Frame Budget Usage**: 0.319% (of 16ms frame)
- **Memory Usage**: 1.74KB per step
- **Throughput Impact**: Negligible (<1% performance impact)

### Best Practices

1. **Raw Dictionaries Only**: Never transform data before recording
2. **Business Logic Fields**: Include only simulation-relevant data
3. **Consistent Schema**: Use consistent field names across event types
4. **Minimal Processing**: Defer any analysis to post-simulation processing

## Testing Support

### In-Memory Testing

```python
# Create observer without writer for testing
observer = RawDataObserver()

# Record test events
observer.record_trade(test_trade_data)

# Verify events
events = observer.get_events()
assert len(events) == 1
assert events[0]['type'] == 'trade'

# Clear for next test
observer.clear()
```

### Performance Testing

```python
# Test recording overhead
import time

observer = RawDataObserver()
start_time = time.perf_counter()

# Record 1000 events
for i in range(1000):
    observer.record_trade({
        'type': 'trade',
        'step': i,
        # ... minimal test data ...
    })

end_time = time.perf_counter()
overhead_per_event = (end_time - start_time) / 1000

# Should be < 0.000051 seconds (0.051ms)
assert overhead_per_event < 0.000051
```

## Migration from Legacy Systems

### Replacing Event Objects

**Before (Event Objects)**:
```python
# Legacy approach
event = TradeExecutionEvent.create(
    step=step,
    seller=seller,
    buyer=buyer,
    # ... many parameters ...
)
logger.log_event(event)
```

**After (Raw Dictionary)**:
```python
# Pure raw data approach
observer.record_trade({
    'type': 'trade',
    'step': step,
    'seller_id': seller.agent_id,
    'buyer_id': buyer.agent_id,
    # ... only business logic fields ...
})
```

### Benefits of Migration

1. **Performance**: 100x+ improvement in recording overhead
2. **Simplicity**: No complex event class hierarchy
3. **Flexibility**: Easy to add new fields or event types
4. **Maintainability**: Clear data contracts with raw dictionaries
5. **Tool Compatibility**: Standard JSON format works with any tool

## Error Handling

The raw data observer uses minimal error handling to maintain performance:

```python
# Observer will not raise exceptions during recording
# Invalid data will be stored as-provided
observer.record_trade({"invalid": "data"})  # Still recorded

# File writing errors are logged but don't stop recording
# Check logs for I/O issues if needed
```

## Advanced Usage

### Custom Event Types

Add new event types by extending the observer:

```python
# Add new recording method
def record_inventory_update(self, data: Dict[str, Any]) -> None:
    """Record inventory change events"""
    self._events.append(data)

# Use with consistent schema
observer.record_inventory_update({
    'type': 'inventory_update',
    'step': 50,
    'agent_id': 1,
    'old_inventory': {'wood': 2, 'stone': 1},
    'new_inventory': {'wood': 3, 'stone': 1},
    'change_reason': 'resource_collection'
})
```

### Filtering and Analysis

```python
# Filter events by type and step range
events = observer.get_events()

trade_events = [
    e for e in events 
    if e.get('type') == 'trade' and 40 <= e.get('step', 0) <= 50
]

# Calculate aggregate metrics
total_trades = len(trade_events)
avg_seller_utility = sum(e.get('delta_u_seller', 0) for e in trade_events) / len(trade_events)
```

---

**Summary**: The Raw Data Observer API provides a simple, high-performance interface for recording simulation events as raw dictionaries. With 0.319% overhead and zero transformation layers, it delivers excellent performance while maintaining complete flexibility for analysis and tool integration.