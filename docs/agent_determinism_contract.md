# Agent Determinism Contract

**Date**: October 2, 2025  
**Status**: Pre-Refactor Baseline  
**Purpose**: Define hash stability requirements for agent refactor

---

## Overview

This document establishes the determinism contract that MUST be maintained during the agent refactor. The contract defines which agent fields participate in the determinism hash and which are excluded, ensuring behavioral equivalence before and after refactoring.

**Critical Requirement**: The determinism hash MUST remain stable across the refactor. Any changes to hash-participating fields require explicit justification and baseline regeneration.

---

## Hash-Participating Fields

These fields are included in the determinism hash and MUST maintain identical values and behavior after refactoring:

### Spatial State
- `x: int` - Current X coordinate
- `y: int` - Current Y coordinate  
- `home_x: int` - Home position X coordinate
- `home_y: int` - Home position Y coordinate
- `target: Position | None` - Current movement target `(x, y)` or `None`

### Inventory State
- `carrying["good1"]: int` - Good1 units being carried
- `carrying["good2"]: int` - Good2 units being carried
- `home_inventory["good1"]: int` - Good1 units stored at home
- `home_inventory["good2"]: int` - Good2 units stored at home

### Mode State
- `mode: AgentMode` - Current behavioral mode (enum value)

### Trading State (if trading enabled)
- `trade_partner_id: int | None` - ID of current trade partner
- `meeting_point: Position | None` - Established meeting coordinates

### Identity
- `id: int` - Unique agent identifier

---

## Hash-EXCLUDED Fields

These fields are explicitly excluded from the determinism hash and may be modified during refactoring without affecting hash stability:

### Component Instances
- All `_component` instances (`_movement`, `_inventory`, `_trading_partner`, etc.)
- Component instances are implementation details and should not affect behavioral hash

### Debug & Performance Fields
- All `_debug_*` fields
- All `_perf_*` fields
- Performance monitoring data
- Debug logging state

### Internal Caches
- `unified_task` - Internal cache for unified target selection
- `current_unified_task` - GUI/testing metadata
- `unified_commitment` - Selection commitment tracking
- `_recent_retargets` - Target change history for instrumentation

### Trade Metrics
- Trade execution statistics
- Trade performance counters
- Trade debugging information

### Stagnation Tracking (Informational Only)
- `last_trade_mode_utility: float` - Utility tracking for stagnation detection
- `trade_stagnation_steps: int` - Steps in trade mode without improvement
- `force_deposit_once: bool` - Stagnation recovery flag

**Note**: Stagnation fields affect behavior but are considered informational for hash purposes since they represent adaptive recovery mechanisms rather than core economic state.

---

## Serialization Contract

Components must be flattened during serialization - component instances are NOT serialized directly:

```python
def serialize(self) -> dict:
    """Serialize agent state - components are flattened."""
    return {
        # Hash-participating fields
        "id": self.id,
        "x": self.x, "y": self.y,
        "home_x": self.home_x, "home_y": self.home_y,
        "carrying": dict(self.carrying),  # Alias exposes component data
        "home_inventory": dict(self.home_inventory),
        "mode": self.mode.value,
        "target": self.target,
        "trade_partner_id": self.trade_partner_id,
        "meeting_point": self.meeting_point,
        
        # Components NOT serialized - data exposed via aliases
        # "_movement": NOT INCLUDED
        # "_inventory": NOT INCLUDED  
        # "_trading_partner": NOT INCLUDED
    }
```

**Critical Invariant**: Component data is exposed through agent attribute aliases (e.g., `agent.carrying` → `agent._inventory.carrying`), ensuring serialization captures the same data before and after refactoring.

---

## Mutation Invariants

### Dictionary Identity Preservation

The inventory dictionaries MUST maintain object identity throughout the refactor:

```python
# Before refactor
carrying_id = id(agent.carrying)
home_id = id(agent.home_inventory)

# After operations
agent.carrying["good1"] = 5
agent.deposit()
agent.withdraw_all()

# Identity MUST be preserved
assert id(agent.carrying) == carrying_id
assert id(agent.home_inventory) == home_id
```

**Rationale**: External code may hold references to these dictionaries. Rebinding would break those references and violate backward compatibility.

### In-Place Mutation Only

All inventory operations MUST mutate dictionaries in place:

```python
# ✅ CORRECT:
agent.carrying["good1"] = 5
agent.carrying["good2"] += 1

# ❌ WRONG (breaks identity):
agent.carrying = {"good1": 5, "good2": 0}
```

---

## Hash Validation Protocol

### Test Implementation

```python
def test_hash_equivalence_pre_post_refactor():
    """Verify determinism hash unchanged after refactor."""
    # Create identical simulations
    config = SimConfig(seed=12345, grid_size=(10, 10))
    sim_baseline = Simulation.from_config(config)
    sim_refactored = Simulation.from_config(config)
    
    # Run identical steps
    for _ in range(100):
        sim_baseline.step()
        sim_refactored.step()
    
    # Compare hashes
    hash_baseline = sim_baseline.metrics_collector.determinism_hash()
    hash_refactored = sim_refactored.metrics_collector.determinism_hash()
    
    assert hash_baseline == hash_refactored, "Hash drift detected after refactor"
```

### Hash Access API

**Correct API**: `simulation.metrics_collector.determinism_hash()` (property)

**Note**: This is the authoritative hash calculation method. Do not implement separate hash functions.

---

## Component Design Requirements

### No Hash Field Addition

Components MUST NOT introduce new fields that participate in the determinism hash:

```python
# ❌ WRONG - adds new hash field
class AgentMovement:
    def __init__(self):
        self.movement_history = []  # Would affect hash if exposed

# ✅ CORRECT - internal state only
class AgentMovement:
    def __init__(self):
        self._movement_cache = []  # Internal, not exposed via agent
```

### Alias-Based Data Exposure

Components expose data through agent aliases, not direct access:

```python
# Component implementation
class AgentInventory:
    def __init__(self):
        self.carrying = {"good1": 0, "good2": 0}
        self.home_inventory = {"good1": 0, "good2": 0}

# Agent integration
class Agent:
    def __post_init__(self):
        self._inventory = AgentInventory()
        # Set up aliases (not copies!)
        object.__setattr__(self, "carrying", self._inventory.carrying)
        object.__setattr__(self, "home_inventory", self._inventory.home_inventory)
```

---

## Baseline Management

### Current Baseline

**File**: `baselines/determinism_hashes.json`

**Status**: Valid for pre-refactor codebase

### Regeneration Protocol

Hash baselines may only be regenerated when:

1. **Behavioral Changes**: Intentional changes to agent decision logic
2. **Bug Fixes**: Corrections to deterministic behavior
3. **Feature Additions**: New hash-participating features (rare)

**Required Documentation**: Each baseline regeneration MUST include:
- Commit message explaining WHAT changed
- Justification for WHY the change was necessary
- Verification that change is intentional, not accidental drift

### Regeneration Command

```bash
# After completing refactor and validating behavior
make test-determinism-update-baseline
git add baselines/determinism_hashes.json
git commit -m "agent: refactor complete - regenerate determinism baseline

- Agent class reduced from 972 to ~450 lines via component extraction
- All behavioral logic preserved, hash drift expected due to serialization changes
- Components: movement, inventory, trading_partner, target_selection, mode_state_machine
- Validation: 210+ tests pass, performance within acceptable range"
```

---

## Risk Mitigation

### Hash Drift Prevention

| Risk | Mitigation |
|------|-----------|
| Component state leakage | Flatten serialization; components don't add hash fields |
| Dictionary rebinding | Strict in-place mutation contract; identity tests |
| Accidental field addition | Component design review; hash field audit |
| Serialization changes | Alias-based data exposure; round-trip tests |

### Validation Strategy

1. **Per-Phase Testing**: Hash validation after each component extraction
2. **Identity Preservation**: Dictionary identity tests with mutation guards
3. **Serialization Round-Trip**: Verify `Agent(**agent.serialize())` equivalence
4. **Multi-Seed Testing**: Validate hash stability across different random seeds

---

## Enforcement During Refactor

### Phase-by-Phase Approach

**Phase 1-2**: Hash enforcement **DEFERRED** (informational monitoring only)
- Components may cause temporary hash drift during extraction
- Focus on functional correctness and test passage
- Performance monitoring continues (non-blocking)

**Phase 3**: Hash stabilization and enforcement **ENABLED**
- All components extracted and integrated
- Hash equivalence tests mandatory
- Baseline regeneration if needed

### Temporary Hash Drift Acceptance

During active refactoring, temporary hash drift is acceptable if:
1. All 210+ tests continue to pass
2. Behavioral equivalence is maintained (spot checks)
3. Performance remains within acceptable range
4. Drift is due to serialization/component changes, not logic changes

---

## Success Criteria

### Hash Stability Validation

- [ ] Hash equivalence across multiple seeds (12345, 67890, 11111)
- [ ] Serialization round-trip produces identical agents
- [ ] Dictionary identity preserved through all operations
- [ ] Component data accessible via original agent attributes
- [ ] No new hash-participating fields introduced

### Behavioral Equivalence

- [ ] All 210+ tests pass with refactored components
- [ ] Agent decision sequences identical (spot check validation)
- [ ] Mode transitions follow same patterns
- [ ] Resource collection behavior unchanged
- [ ] Trading partner selection deterministic

---

**Contract Date**: October 2, 2025  
**Review Status**: ✅ Ready for Implementation  
**Next Review**: After Phase 3 completion (hash stabilization)

