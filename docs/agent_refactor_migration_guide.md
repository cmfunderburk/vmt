# Agent Refactor Migration Guide

**Date**: October 2, 2025  
**Status**: Post-Refactor Documentation  
**Purpose**: Guide for future developers working with the agent component architecture

---

## Overview

This guide provides migration information for developers working with the agent system after the October 2025 refactor. The Agent class has been modularized into 6 specialized components while maintaining backward compatibility.

---

## What Changed

### Before Refactor (Legacy)
```python
# Monolithic Agent class (972 lines)
class Agent:
    def __init__(self, ...):
        # All logic in single class
        self.mode = AgentMode.FORAGE
        self.carrying = {"good1": 0, "good2": 0}
        self.home_inventory = {"good1": 0, "good2": 0}
        # ... 900+ more lines of mixed responsibilities
    
    def move_toward_target(self, ...):
        # Movement logic mixed with other concerns
        pass
    
    def collect_resource(self, ...):
        # Collection logic mixed with other concerns
        pass
```

### After Refactor (Component Architecture)
```python
# Modular Agent class (831 lines) with 6 components
class Agent:
    def __init__(self, ...):
        # Core agent properties
        self.mode = AgentMode.FORAGE
        # ... core properties only
    
    def __post_init__(self):
        # Initialize specialized components
        self._movement = AgentMovement(self.id)
        self._event_emitter = AgentEventEmitter(self.id)
        self._inventory = AgentInventory(self.preference)
        self._trading_partner = TradingPartner(self.id)
        self._target_selection = ResourceTargetStrategy()
        self._mode_state_machine = AgentModeStateMachine(self.id)
```

---

## Migration Patterns

### 1. Agent Creation (No Changes)
```python
# ✅ Works exactly the same
agent = Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
```

### 2. Accessing Agent Properties (No Changes)
```python
# ✅ All existing properties work the same
print(agent.mode)           # AgentMode.FORAGE
print(agent.carrying)       # {"good1": 0, "good2": 0}
print(agent.home_inventory) # {"good1": 0, "good2": 0}
print(agent.x, agent.y)     # (0, 0)
```

### 3. Mode Changes (Use Centralized Method)
```python
# ✅ CORRECT - Use centralized method
agent._set_mode(AgentMode.RETURN_HOME, "resource_found", registry, step)

# ❌ AVOID - Direct assignment bypasses events
agent.mode = AgentMode.RETURN_HOME  # No events emitted!
```

### 4. Inventory Operations (No Changes)
```python
# ✅ All existing inventory operations work
agent.carrying["good1"] += 1
agent.home_inventory["good2"] += 2
```

### 5. Trading Partner Access (No Changes)
```python
# ✅ All existing trading properties work
print(agent.trade_partner_id)  # None or partner ID
print(agent.meeting_point)     # None or (x, y)
print(agent.is_trading)        # True/False
```

---

## Component Access Patterns

### Direct Component Access (Advanced)
```python
# ✅ Access components directly for advanced operations
agent._movement.move_toward_target(target_pos)
agent._event_emitter.emit_mode_change(old_mode, new_mode, reason, step)
agent._inventory.add_resource("good1", 1)
agent._trading_partner.pair_with(other_agent)
agent._target_selection.select_best_resource(grid, agent)
agent._mode_state_machine.validate_transition(from_mode, to_mode)
```

### Component Integration (Internal)
```python
# ✅ Components work together automatically
# Movement component calls target selection
# Target selection calls inventory
# Inventory calls event emitter
# Mode changes go through state machine
```

---

## Common Migration Scenarios

### Scenario 1: Adding New Agent Behavior
**Before**: Add method to Agent class
```python
class Agent:
    def new_behavior(self):
        # Mixed with other concerns
        pass
```

**After**: Create new component or extend existing
```python
# Option 1: Extend existing component
class AgentMovement:
    def new_movement_behavior(self):
        # Focused on movement concerns
        pass

# Option 2: Create new component
class AgentNewComponent:
    def __init__(self, agent_id: int):
        self.agent_id = agent_id
    
    def new_behavior(self):
        # Focused on specific concern
        pass
```

### Scenario 2: Modifying Agent State
**Before**: Direct state modification
```python
def modify_agent_state(agent):
    agent.mode = AgentMode.IDLE  # Direct assignment
    agent.carrying = {"good1": 5}  # Dict rebinding
```

**After**: Use proper methods and preserve invariants
```python
def modify_agent_state(agent):
    agent._set_mode(AgentMode.IDLE, "manual_change", registry, step)
    agent.carrying["good1"] = 5  # In-place mutation
```

### Scenario 3: Testing Agent Components
**Before**: Test entire Agent class
```python
def test_agent_behavior():
    agent = Agent(...)
    # Test mixed concerns together
    assert agent.mode == AgentMode.FORAGE
```

**After**: Test components in isolation
```python
def test_movement_component():
    movement = AgentMovement(agent_id=1)
    # Test movement concerns only
    assert movement.can_move_to((1, 1))

def test_inventory_component():
    inventory = AgentInventory(preference)
    # Test inventory concerns only
    assert inventory.carrying == {"good1": 0, "good2": 0}
```

---

## Debugging Guide

### Issue: Mode Changes Not Working
**Symptoms**: Agents stuck in same mode, no events in logs
**Likely Cause**: AgentMode enum mismatch
**Solution**:
```python
# Check enum consistency
from econsim.simulation.agent import AgentMode
print(AgentMode.FORAGE.value)  # Should be "forage" (lowercase)

# Verify state machine integration
assert agent._mode_state_machine._event_emitter is not None
```

### Issue: Inventory Operations Failing
**Symptoms**: Runtime errors accessing agent.carrying
**Likely Cause**: Dict identity broken
**Solution**:
```python
# Check alias identity
assert id(agent.carrying) == id(agent._inventory.carrying)

# Use in-place mutations only
agent.carrying["good1"] += 1  # ✅ Correct
# agent.carrying = {...}      # ❌ Wrong - breaks aliases
```

### Issue: No Events in Logs
**Symptoms**: Observer events not appearing
**Likely Cause**: Event emitter not connected
**Solution**:
```python
# Check event emitter integration
assert agent._event_emitter is not None
assert agent._mode_state_machine._event_emitter is not None

# Use centralized mode changes
agent._set_mode(AgentMode.RETURN_HOME, "test", registry, step)
```

### Issue: Non-Deterministic Behavior
**Symptoms**: Hash mismatches, inconsistent results
**Likely Cause**: Non-deterministic component behavior
**Solution**:
```python
# Check target selection ordering
assert agent._target_selection.priority_order == (-delta_utility, distance, x, y)

# Check trading partner determinism
assert agent._trading_partner.pairing_rule == "lower_id_initiates"
```

---

## Performance Considerations

### Component Overhead
- **Per Agent**: ~0.01ms per step per component
- **Total Overhead**: ~0.06ms per agent per step
- **Memory**: ~1KB per agent for all components

### Optimization Guidelines
```python
# ✅ Efficient component usage
agent._movement.move_toward_target(target)  # Direct call
agent._inventory.add_resource("good1", 1)   # In-place mutation

# ❌ Inefficient patterns
for component in [agent._movement, agent._inventory, ...]:  # Unnecessary iteration
    component.do_something()
```

---

## Testing Patterns

### Unit Testing Components
```python
def test_movement_component():
    movement = AgentMovement(agent_id=1)
    assert movement.can_move_to((1, 1))
    assert not movement.can_move_to((-1, -1))

def test_inventory_component():
    inventory = AgentInventory(preference)
    inventory.add_resource("good1", 1)
    assert inventory.carrying["good1"] == 1
```

### Integration Testing
```python
def test_agent_component_integration():
    agent = Agent(id=1, x=0, y=0, preference=pref)
    
    # Test component initialization
    assert agent._movement is not None
    assert agent._event_emitter is not None
    assert agent._inventory is not None
    
    # Test alias preservation
    assert id(agent.carrying) == id(agent._inventory.carrying)
    
    # Test mode change integration
    events = []
    registry.register(TestObserver(events))
    agent._set_mode(AgentMode.RETURN_HOME, "test", registry, 1)
    assert len(events) == 1
```

---

## Future Development Guidelines

### Adding New Components
1. **Single Responsibility**: Each component has one clear purpose
2. **Interface Consistency**: Follow established patterns
3. **Error Isolation**: Failures must not break simulation
4. **Performance Awareness**: Minimal overhead per step
5. **Test Coverage**: Comprehensive testing

### Modifying Existing Components
1. **Backward Compatibility**: Preserve existing APIs
2. **Invariant Preservation**: Maintain critical invariants
3. **Test Updates**: Update tests for new behavior
4. **Documentation**: Update migration guide

### Best Practices
- **Use Components**: Prefer component methods over direct state manipulation
- **Preserve Invariants**: Follow component invariants document
- **Test Thoroughly**: Test both unit and integration scenarios
- **Document Changes**: Update documentation for new patterns

---

## Resources

### Documentation
- `docs/agent_component_invariants.md` - Critical invariants and constraints
- `src/econsim/simulation/components/` - Component implementations
- `tests/unit/components/` - Component unit tests

### Key Files
- `src/econsim/simulation/agent.py` - Main Agent class
- `src/econsim/simulation/components/` - Component implementations
- `src/econsim/simulation/agent_mode_utils.py` - Mode change utilities

### Testing
- `pytest tests/unit/components/` - Run component tests
- `pytest tests/unit/test_mode_change_events.py` - Test mode change integration
- `pytest tests/unit/test_priority2_integration.py` - Test system integration

---

## Conclusion

The agent refactor provides significant benefits in modularity, testability, and maintainability. The migration is designed to be backward-compatible, so existing code should continue to work with minimal changes.

**Key Success Factors**:
1. **Use Centralized Methods**: Prefer `_set_mode()` over direct assignment
2. **Preserve Invariants**: Follow component invariants document
3. **Test Components**: Test both unit and integration scenarios
4. **Document Changes**: Update documentation for new patterns

**Getting Help**:
- Check component invariants document for critical constraints
- Run component tests to verify behavior
- Use debugging guide for common issues
- Review existing component implementations for patterns

---

**Document Version**: 1.0  
**Last Updated**: October 2, 2025  
**Next Review**: After any component architecture changes
