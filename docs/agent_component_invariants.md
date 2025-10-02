# Agent Component Architecture Invariants

**Date**: October 2, 2025  
**Status**: Post-Refactor Documentation  
**Purpose**: Document critical invariants and constraints for the agent component architecture

---

## Overview

The Agent class has been refactored into a modular component architecture with 6 specialized components. This document outlines the critical invariants that must be maintained to ensure system stability, determinism, and performance.

---

## Component Architecture

### Component List
1. **Movement** (`AgentMovement`) - Spatial navigation & pathfinding
2. **Event Emitter** (`AgentEventEmitter`) - Observer pattern integration
3. **Inventory** (`AgentInventory`) - Dual inventory management
4. **Trading Partner** (`TradingPartner`) - Bilateral exchange coordination
5. **Target Selection** (`ResourceTargetStrategy`) - Resource & partner targeting
6. **Mode State Machine** (`AgentModeStateMachine`) - Behavioral mode transitions

### Component Integration Pattern
```python
# Components initialized in Agent.__post_init__()
self._movement = AgentMovement(self.id)
self._event_emitter = AgentEventEmitter(self.id)
self._inventory = AgentInventory(self.preference)
self._trading_partner = TradingPartner(self.id)
self._target_selection = ResourceTargetStrategy()
self._mode_state_machine = AgentModeStateMachine(self.id)
```

---

## Critical Invariants

### 1. AgentMode Enum Consistency
**CRITICAL**: All components must use the same `AgentMode` enum from `agent.py`

```python
# ✅ CORRECT - Import from agent module
from ..agent import AgentMode

# ❌ WRONG - Never define duplicate enums
class AgentMode(Enum):  # This breaks mode transitions!
    FORAGE = "FORAGE"  # Uppercase vs lowercase mismatch
```

**Impact**: Enum mismatch causes all mode transitions to fail validation, breaking agent behavior.

### 2. Inventory Mutation Safety
**CRITICAL**: Inventory components must preserve dict identity for backward compatibility

```python
# ✅ CORRECT - In-place mutation only
def add_resource(self, resource_type: str, amount: int) -> None:
    self.carrying[resource_type] += amount  # Mutates existing dict

# ❌ WRONG - Never rebind dict references
def add_resource(self, resource_type: str, amount: int) -> None:
    self.carrying = {**self.carrying, resource_type: amount}  # Breaks aliases!
```

**Impact**: Dict rebinding breaks `agent.carrying` aliases, causing runtime errors.

### 3. Event Emitter Integration
**CRITICAL**: All mode changes must go through the event emitter

```python
# ✅ CORRECT - Use centralized _set_mode()
agent._set_mode(AgentMode.RETURN_HOME, "resource_found", registry, step)

# ❌ WRONG - Direct mode assignment bypasses events
agent.mode = AgentMode.RETURN_HOME  # No events emitted!
```

**Impact**: Direct mode assignment breaks observer pattern, causing event system failures.

### 4. Component Initialization Order
**CRITICAL**: Event emitter must be initialized before state machine

```python
# ✅ CORRECT - Event emitter first, then state machine
self._event_emitter = AgentEventEmitter(self.id)
self._mode_state_machine = AgentModeStateMachine(self.id)
self._mode_state_machine.set_event_emitter(self._event_emitter)

# ❌ WRONG - State machine without event emitter
self._mode_state_machine = AgentModeStateMachine(self.id)  # No events!
```

**Impact**: State machine without event emitter cannot emit mode change events.

### 5. Deterministic Target Selection
**CRITICAL**: Target selection must use canonical priority ordering

```python
# ✅ CORRECT - Canonical priority tuple
priority = (-delta_utility, distance, x, y)

# ❌ WRONG - Inconsistent ordering breaks determinism
priority = (distance, -delta_utility, y, x)  # Different order!
```

**Impact**: Inconsistent ordering breaks determinism, causing hash mismatches.

### 6. Trading Partner Determinism
**CRITICAL**: Trading partner selection must be deterministic

```python
# ✅ CORRECT - Lower ID initiates pairing
if agent1.id < agent2.id:
    agent1._trading_partner.pair_with(agent2)

# ❌ WRONG - Non-deterministic pairing
if random.random() > 0.5:  # Breaks determinism!
    agent1._trading_partner.pair_with(agent2)
```

**Impact**: Non-deterministic pairing breaks simulation determinism.

---

## Component-Specific Invariants

### Movement Component
- **Manhattan Distance Only**: No diagonal movement or pathfinding
- **Collision Avoidance**: Agents cannot occupy same position
- **Target Persistence**: Target cleared only on arrival or mode change

### Event Emitter Component
- **Observer Registry Integration**: Must support both immediate and buffered events
- **Error Isolation**: Event emission failures must not break simulation
- **Performance Target**: <2% logging overhead per step

### Inventory Component
- **Dict Identity Preservation**: `agent.carrying` must alias `_inventory.carrying`
- **Mutation Safety**: All operations must be in-place only
- **Type Consistency**: All inventories use `dict[str, int]` format

### Trading Partner Component
- **Deterministic Pairing**: Lower agent ID always initiates
- **Cooldown Management**: Both general and per-partner cooldowns
- **State Consistency**: Partner state must match between paired agents

### Target Selection Component
- **Sorted Resource Iteration**: Must use `Grid.iter_resources_sorted()`
- **Priority Consistency**: Always use `(-ΔU, distance, x, y)` ordering
- **Tie-Breaking**: Deterministic tie-breaking for identical priorities

### Mode State Machine Component
- **Transition Validation**: All mode changes must be validated
- **Event Emission**: Valid transitions must emit events
- **State Authority**: Agent.mode remains authoritative, state machine validates only

---

## Testing Invariants

### Required Test Coverage
Each component must have tests for:
1. **Initialization**: Component creates correctly
2. **Integration**: Component works with Agent class
3. **Invariant Preservation**: Critical invariants maintained
4. **Error Handling**: Graceful degradation on failures
5. **Performance**: No significant overhead

### Test Patterns
```python
# Test inventory identity preservation
def test_inventory_alias_identity():
    agent = Agent(id=1, x=0, y=0, preference=pref)
    assert id(agent.carrying) == id(agent._inventory.carrying)

# Test mode transition validation
def test_mode_transition_validation():
    agent = Agent(id=1, x=0, y=0, preference=pref)
    assert agent._mode_state_machine.is_valid_transition(
        AgentMode.FORAGE, AgentMode.RETURN_HOME
    )

# Test event emission
def test_mode_change_event_emission():
    events = []
    registry.register(TestObserver(events))
    agent._set_mode(AgentMode.RETURN_HOME, "test", registry, 1)
    assert len(events) == 1
```

---

## Common Pitfalls

### 1. Enum Mismatch
**Symptom**: Mode transitions fail, no events emitted
**Cause**: Duplicate AgentMode enum definitions
**Fix**: Import AgentMode from agent module only

### 2. Dict Rebinding
**Symptom**: Runtime errors accessing agent.carrying
**Cause**: Inventory component rebinds dict references
**Fix**: Use in-place mutation only

### 3. Missing Event Emitter
**Symptom**: No mode change events in logs
**Cause**: State machine not connected to event emitter
**Fix**: Call `set_event_emitter()` after initialization

### 4. Non-Deterministic Selection
**Symptom**: Hash mismatches in tests
**Cause**: Inconsistent priority ordering or random selection
**Fix**: Use canonical ordering, deterministic tie-breaking

### 5. Direct Mode Assignment
**Symptom**: Observer events not triggered
**Cause**: Bypassing `_set_mode()` method
**Fix**: Always use `agent._set_mode()` for mode changes

---

## Maintenance Guidelines

### Adding New Components
1. **Single Responsibility**: Each component has one clear purpose
2. **Interface Consistency**: Follow established patterns
3. **Error Isolation**: Failures must not break simulation
4. **Performance Awareness**: Minimal overhead per step
5. **Test Coverage**: Comprehensive invariant testing

### Modifying Existing Components
1. **Backward Compatibility**: Preserve existing APIs
2. **Invariant Preservation**: Maintain all critical invariants
3. **Test Updates**: Update tests for new behavior
4. **Documentation**: Update this document for changes

### Performance Considerations
- **Component Overhead**: Each component adds ~0.01ms per agent per step
- **Event Emission**: Observer events should be <2% of step time
- **Memory Usage**: Components should not significantly increase memory footprint
- **Initialization**: Component creation should be <1ms per agent

---

## Conclusion

The agent component architecture provides significant benefits in modularity, testability, and maintainability. However, these benefits depend on maintaining the critical invariants outlined in this document.

**Key Success Factors**:
1. **Consistent Enum Usage**: Single source of truth for AgentMode
2. **Safe Mutations**: Preserve dict identity in inventory operations
3. **Event Integration**: All state changes go through observer system
4. **Deterministic Behavior**: Consistent ordering and tie-breaking
5. **Error Isolation**: Component failures don't break simulation

**Regular Validation**: Run component tests regularly to ensure invariants are maintained.

---

**Document Version**: 1.0  
**Last Updated**: October 2, 2025  
**Next Review**: After any component architecture changes
