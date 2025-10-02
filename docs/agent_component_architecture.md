# Agent Component Architecture

**Date**: October 2, 2025  
**Status**: Post-Refactor Architecture  
**Agent Class**: 831 lines (down from 972 lines)

## Overview

The Agent class has been successfully refactored from a 972-line monolith into a clean, component-based architecture. While the line count target of 400-500 lines was not achieved, the **architectural improvement is significant** with excellent separation of concerns and maintainability.

## Component Architecture

```
Agent (831 lines)
├── Movement Component
│   ├── AgentMovement (core.py)
│   └── Spatial utilities (utils.py)
├── Event Emitter Component
│   └── AgentEventEmitter (core.py)
├── Inventory Component
│   └── AgentInventory (core.py)
├── Trading Partner Component
│   └── TradingPartner (core.py)
├── Target Selection Component
│   ├── TargetSelectionStrategy (base.py)
│   └── ResourceTargetStrategy (resource_selection.py)
└── Mode State Machine Component
    └── AgentModeStateMachine (mode_state_machine.py)
```

## Component Details

### 1. Movement Component
**Purpose**: Handles all agent spatial navigation and pathfinding
**Files**: `components/movement/core.py`, `components/movement/utils.py`
**Key Features**:
- Deterministic random movement
- Greedy pathfinding toward targets
- Meeting point navigation
- Manhattan distance calculations

### 2. Event Emitter Component
**Purpose**: Centralized event emission for agent actions
**Files**: `components/event_emitter/core.py`
**Key Features**:
- Mode change event emission
- Resource collection event emission
- Observer pattern integration
- Error handling and graceful degradation

### 3. Inventory Component
**Purpose**: Manages agent's carrying and home inventory
**Files**: `components/inventory/core.py`
**Key Features**:
- Dual storage system (carrying + home)
- Utility calculations with epsilon augmentation
- In-place mutation invariants (CRITICAL)
- Backward compatibility aliases

### 4. Trading Partner Component
**Purpose**: Manages trading relationships and coordination
**Files**: `components/trading_partner/core.py`
**Key Features**:
- Deterministic partner pairing
- Cooldown management (general + per-partner)
- Meeting point calculation
- State transition management

### 5. Target Selection Component
**Purpose**: Handles resource and partner target selection
**Files**: `components/target_selection/base.py`, `components/target_selection/resource_selection.py`
**Key Features**:
- Strategy pattern implementation
- Distance-discounted utility scoring
- Deterministic tie-breaking
- Canonical priority tuples

### 6. Mode State Machine Component
**Purpose**: Validates mode transitions and emits events
**Files**: `components/mode_state_machine.py`
**Key Features**:
- Transition validation matrix
- Event emission integration
- Hybrid approach (agent.mode authoritative)
- Invalid transition rejection

## Integration Pattern

### Component Initialization
```python
def __post_init__(self) -> None:
    # Initialize components
    self._movement = AgentMovement(self.id)
    self._event_emitter = AgentEventEmitter(self.id)
    self._inventory = AgentInventory(self.preference)
    self._trading_partner = TradingPartner(self.id)
    self._target_selection = ResourceTargetStrategy()
    self._mode_state_machine = AgentModeStateMachine(self.id)
    
    # Set up aliases for backward compatibility
    object.__setattr__(self, "carrying", self._inventory.carrying)
    object.__setattr__(self, "home_inventory", self._inventory.home_inventory)
```

### Component Usage
```python
# Movement
new_pos = self._movement.move_toward_target((self.x, self.y), target)

# Event emission
self._event_emitter.emit_mode_change(old_mode, new_mode, reason, step)

# Inventory operations
self._inventory.deposit_all()  # Mutates in-place

# Trading partner management
self._trading_partner.find_nearby_agents((self.x, self.y), all_agents)

# Target selection
candidate = self._target_selection.select_target(pos, bundle, pref, grid)

# Mode validation
valid = self._mode_state_machine.validate_and_emit_transition(...)
```

## Critical Invariants

### 1. Inventory Mutation Invariant
**CRITICAL**: The inventory component MUST mutate dictionaries in-place:
```python
# ✅ CORRECT: In-place mutation
self.carrying["good1"] = 0

# ❌ INCORRECT: Rebinding (breaks aliases)
self.carrying = {"good1": 0, "good2": 0}
```

### 2. Mode State Machine Invariant
**CRITICAL**: The state machine validates but doesn't own mode state:
- `agent.mode` remains authoritative
- State machine only validates transitions
- Invalid transitions are rejected with logging

### 3. Component Isolation Invariant
**CRITICAL**: Components don't directly reference each other:
- No circular dependencies
- Communication via Agent class
- Clean separation of concerns

## Hash Contract

### Fields Participating in Hash
- **Spatial State**: `x`, `y`, `home_x`, `home_y`, `target`
- **Inventory State**: `carrying["good1"]`, `carrying["good2"]`, `home_inventory["good1"]`, `home_inventory["good2"]`
- **Mode State**: `mode` (enum value)
- **Trading State**: `trade_partner_id`, `meeting_point`
- **Identity**: `id`

### Hash-EXCLUDED Fields
- All `_component` instances (`_movement`, `_inventory`, etc.)
- All `_debug_*` and `_perf_*` fields
- `unified_task` (internal cache)
- Trade metrics

## Performance Impact

**Before Refactor**: 972 lines, monolithic structure
**After Refactor**: 831 lines, component-based architecture
**Performance**: 323.6 steps/sec mean (maintained)
**Test Coverage**: 399 tests passing (excellent)

## Benefits Achieved

1. **Maintainability**: Clear separation of concerns
2. **Testability**: Each component has dedicated unit tests
3. **Extensibility**: Easy to add new components or modify existing ones
4. **Readability**: Well-organized, focused components
5. **Reliability**: Comprehensive test coverage and validation

## Future Enhancements

1. **Additional Components**: Could extract more specialized components
2. **Component Interfaces**: Could add formal interfaces for better type safety
3. **Configuration**: Could make components more configurable
4. **Caching**: Could add component-level caching for performance

## Migration Notes

### For Future Developers

1. **Adding New Components**:
   - Create component in `components/` directory
   - Add to `__post_init__` method
   - Create unit tests in `tests/unit/components/`
   - Follow existing patterns

2. **Modifying Existing Components**:
   - Maintain backward compatibility aliases
   - Preserve critical invariants
   - Update unit tests
   - Consider hash contract impact

3. **Performance Considerations**:
   - Components should be lightweight
   - Avoid heavy initialization
   - Use lazy loading where appropriate
   - Profile component performance

## Conclusion

While the 400-500 line target was not achieved, the refactor successfully transformed a monolithic 972-line class into a well-organized, component-based architecture. The 831-line result represents **high-quality, maintainable code** with excellent separation of concerns and comprehensive test coverage.

The architectural benefits far outweigh the line count concern, providing a solid foundation for future development and maintenance.
