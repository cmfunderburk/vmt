# Agent Refactor: Pre-Implementation Critical Decisions

**Date**: October 2, 2025  
**Purpose**: Resolve all critical ambiguities before Phase 1 implementation  
**Status**: DRAFT - Awaiting validation

---

## Executive Summary

This document provides **concrete recommendations** for the 7 critical decisions that must be made before beginning Agent refactor Phase 1. Each recommendation includes rationale, implementation guidance, and validation criteria.

**Quick Decision Summary**:
1. Mode Management: **Hybrid approach** (external authority, internal state machine)
2. Hash Contract: **Explicit field whitelist** with component nesting rules
3. Trading Partner Cooldowns: **Deterministic state table** with tie-break rules
4. Inventory Mutation: **Strict in-place mutation contract**
5. Performance Protocol: **5-sample median with 2% threshold**
6. Serialization: **Flatten strategy** (no format versioning yet)
7. Feature Flags: **Per-component progressive flags**

---

## 1. Mode State Management Architecture ✅ CRITICAL

### Decision: **Hybrid Approach (Phased Evolution)**

**Phase 1-2 (Immediate)**:
- `agent.mode` remains the **single source of truth** (external field)
- `AgentModeStateMachine` is a **validator and event emitter** (not owner)
- State machine writes to `agent.mode` after validation
- Existing `_set_mode()` method delegates to state machine

**Phase 3 (Optional Future)**:
- Migrate to full encapsulation with property delegation
- Only if state machine proves valuable during Phases 1-2

### Rationale
- **Lower risk**: Minimizes backward compatibility surface
- **Incremental**: Can evolve to full encapsulation if needed
- **Clear authority**: No ambiguity about source of truth during refactor
- **Testable**: Easy to validate that mode changes behave identically

### Implementation Pattern

```python
# Phase 1-2: Hybrid approach
class Agent:
    def __post_init__(self):
        self.mode: AgentMode = AgentMode.FORAGE  # Still a regular field
        self._mode_machine = AgentModeStateMachine(self.id, self.mode)
    
    def _set_mode(
        self, 
        new_mode: AgentMode, 
        reason: str = "",
        observer_registry: Optional['ObserverRegistry'] = None,
        step_number: int = 0,
        event_buffer: Optional['StepEventBuffer'] = None
    ) -> None:
        """Centralized mode setter with validation and event emission."""
        if self.mode == new_mode:
            return
        
        # Validate transition
        if not self._mode_machine.is_valid_transition(self.mode, new_mode):
            # Log invalid transition attempt in debug mode
            if os.environ.get("ECONSIM_DEBUG_AGENT_MODES") == "1":
                print(f"Agent {self.id}: Invalid transition {self.mode} -> {new_mode}")
            return
        
        old_mode = self.mode
        self.mode = new_mode  # Update source of truth
        self._mode_machine.current_mode = new_mode  # Keep state machine in sync
        
        # Emit event via state machine
        self._mode_machine.emit_mode_change(
            old_mode.value, new_mode.value, reason, 
            step_number, observer_registry, event_buffer
        )
```

**State Machine Role (Phase 1-2)**:
```python
class AgentModeStateMachine:
    """Validates transitions and emits events; does NOT own mode state."""
    
    def __init__(self, agent_id: int, initial_mode: AgentMode):
        self.agent_id = agent_id
        self.current_mode = initial_mode  # Mirror of agent.mode
        self._event_emitter = AgentEventEmitter(agent_id)
    
    def is_valid_transition(self, from_mode: AgentMode, to_mode: AgentMode) -> bool:
        """Check if transition is valid (non-destructive check)."""
        if from_mode == to_mode:
            return True
        
        valid_transitions = {
            AgentMode.FORAGE: {AgentMode.RETURN_HOME, AgentMode.IDLE, AgentMode.MOVE_TO_PARTNER},
            AgentMode.RETURN_HOME: {AgentMode.FORAGE, AgentMode.IDLE},
            AgentMode.IDLE: {AgentMode.FORAGE, AgentMode.MOVE_TO_PARTNER, AgentMode.RETURN_HOME},
            AgentMode.MOVE_TO_PARTNER: {AgentMode.IDLE, AgentMode.FORAGE, AgentMode.RETURN_HOME}
        }
        return to_mode in valid_transitions.get(from_mode, set())
    
    def emit_mode_change(self, old_mode: str, new_mode: str, reason: str, 
                         step_number: int, observer_registry, event_buffer) -> None:
        """Emit mode change event."""
        self._event_emitter.emit_mode_change(
            old_mode, new_mode, reason, step_number, observer_registry, event_buffer
        )
```

### Validation Criteria
- [ ] All existing `agent.mode` accesses work unchanged
- [ ] Invalid transitions are caught in debug mode
- [ ] Event emission occurs for all valid transitions
- [ ] No performance regression (validation adds <0.1% overhead)

---

## 2. Agent Field Hash Contract ✅ CRITICAL

### Decision: **Explicit Field Whitelist with Component Exclusion Rules**

### Hash-Participating Fields (Current Baseline)

**Spatial State**:
- `x`, `y` (current position)
- `home_x`, `home_y` (home position)
- `target` (current target position, if any)

**Inventory State**:
- `carrying["good1"]`, `carrying["good2"]` (carried inventory)
- `home_inventory["good1"]`, `home_inventory["good2"]` (home storage)

**Mode State**:
- `mode` (current agent mode enum value)

**Trading State** (if trading enabled):
- `trade_partner_id` (current partner ID, if paired)
- `meeting_point` (meeting coordinates, if set)

**Identity**:
- `id` (agent unique identifier)

### Hash-EXCLUDED Fields

**Performance Instrumentation**:
- `_recent_retargets` (diagnostic counter)
- Any field prefixed with `_debug_` or `_perf_`

**Observer Infrastructure**:
- `_event_emitter` (component instance)
- `_movement` (component instance)
- `_inventory` (component instance - BUT its data fields ARE included via aliases)
- `_trading_partner` (component instance - BUT its data fields ARE included via aliases)
- `_mode_machine` (component instance)

**Temporary State** (not deterministic across steps):
- `unified_task` (internal decision cache)
- Any field marked with docstring "EXCLUDED FROM DETERMINISM HASH"

**Trade Metrics** (per existing policy):
- Trade count fields
- Debug metrics

### Component Nesting Rules

**Rule 1: Aliases Preserve Hash Surface**
```python
# Component holds the data
self._inventory = AgentInventory(...)
# Aliases expose for backward compatibility AND hash inclusion
object.__setattr__(self, "carrying", self._inventory.carrying)
object.__setattr__(self, "home_inventory", self._inventory.home_inventory)

# Hash calculation accesses agent.carrying directly (unchanged)
# Component nesting is transparent to hash calculation
```

**Rule 2: Components Don't Add Hash Fields**
```python
# BAD: Adding new fields to component that enter hash
class AgentInventory:
    def __init__(self):
        self.inventory_version = 2  # Would pollute hash if exposed

# GOOD: Keep components as pure logic wrappers
class AgentInventory:
    def __init__(self):
        self.carrying = {"good1": 0, "good2": 0}  # Exposed via alias
        self._internal_cache = {}  # Not exposed, not hashed
```

**Rule 3: New Metrics Must Be Explicitly Excluded**
```python
# When adding new diagnostic fields
class Agent:
    def __post_init__(self):
        self._movement_cache = {}  # EXCLUDED FROM DETERMINISM HASH
        # Add comment to field definition
```

### Serialization Impact

**Snapshot Format (Unchanged)**:
```python
def serialize(self) -> dict:
    """Serialize agent state for snapshots."""
    return {
        "id": self.id,
        "x": self.x,
        "y": self.y,
        "home_x": self.home_x,
        "home_y": self.home_y,
        "carrying": dict(self.carrying),  # Alias exposes component data
        "home_inventory": dict(self.home_inventory),  # Alias exposes component data
        "mode": self.mode.value,
        "target": self.target,
        "trade_partner_id": self.trade_partner_id,
        "meeting_point": self.meeting_point,
        # Components themselves are NOT serialized
        # Only their exposed data fields via aliases
    }
```

### Hash Calculation (Reference Implementation)

```python
def get_determinism_hash_fields(self) -> dict:
    """Return only fields that participate in determinism hashing."""
    fields = {
        "id": self.id,
        "position": (self.x, self.y),
        "home": (self.home_x, self.home_y),
        "carrying": dict(self.carrying),
        "home_inventory": dict(self.home_inventory),
        "mode": self.mode.value,
    }
    
    # Optional fields (only if set)
    if self.target is not None:
        fields["target"] = self.target
    if self.trade_partner_id is not None:
        fields["trade_partner_id"] = self.trade_partner_id
    if self.meeting_point is not None:
        fields["meeting_point"] = self.meeting_point
    
    return fields
```

### Validation Criteria
- [ ] Document created: `docs/agent_determinism_contract.md`
- [ ] Hash calculation function references this contract
- [ ] All new component fields documented as included/excluded
- [ ] Serialization produces identical structure pre/post refactor

---

## 3. Trading Partner Cooldown Semantics ✅ CRITICAL

### Decision: **Deterministic State Table with Tie-Break Rules**

### State Transition Table

| Event | Condition | State Changes | Cooldowns | Ordering Rule |
|-------|-----------|---------------|-----------|---------------|
| **Pairing Initiation** | Both agents have no partner, no active cooldown | `trade_partner_id` set (mutual), `meeting_point` calculated | None | Lower `agent.id` initiates (processes partner state first) |
| **Meeting Point Arrival** | Both agents at meeting point | `is_trading = True` (mutual) | None | N/A (simultaneous) |
| **Trade Execution** | At meeting point, individually rational trade exists | Execute 1 trade, update inventories | None | Existing trade priority tuple |
| **Session End (Normal)** | No individually rational trades remain | Clear `trade_partner_id`, `meeting_point`, `is_trading` | `partner_cooldowns[other_id] = 20` (mutual), `trade_cooldown = 3` (general) | N/A (mutual) |
| **Session End (Stagnation)** | `trade_stagnation_steps > threshold` | Same as normal end | Same as normal end | N/A (mutual) |
| **Pairing Rejection** | One agent has active cooldown for other | No state change | None | Skip to next candidate |

### Pairing Initiation Detailed Algorithm

**Tie-Break Rule**: When two agents could pair with each other simultaneously, **lower agent ID processes first**.

```python
def establish_pairing_deterministic(agent_a: Agent, agent_b: Agent) -> None:
    """Establish mutual pairing with deterministic ordering."""
    # Always process in ascending ID order
    initiator, responder = sorted([agent_a, agent_b], key=lambda a: a.id)
    
    # Calculate meeting point (deterministic: midpoint)
    meeting_point = calculate_meeting_point(
        (initiator.x, initiator.y), 
        (responder.x, responder.y)
    )
    
    # Set mutual state (initiator first for deterministic ordering)
    initiator._trading_partner.trade_partner_id = responder.id
    initiator._trading_partner.meeting_point = meeting_point
    
    responder._trading_partner.trade_partner_id = initiator.id
    responder._trading_partner.meeting_point = meeting_point
    
    # Update aliases for backward compatibility
    object.__setattr__(initiator, "trade_partner_id", responder.id)
    object.__setattr__(initiator, "meeting_point", meeting_point)
    object.__setattr__(responder, "trade_partner_id", initiator.id)
    object.__setattr__(responder, "meeting_point", meeting_point)
```

### Cooldown Management

**General Cooldown** (`trade_cooldown`):
- Set to **3 steps** after any pairing ends
- Prevents immediate re-pairing with ANY agent
- Decrements each step (handled by step executor)

**Per-Partner Cooldown** (`partner_cooldowns[partner_id]`):
- Set to **20 steps** after session with specific partner ends
- Prevents re-pairing with SAME agent
- Decrements each step for all tracked partners
- Removed from dict when reaches 0

**Cooldown Check Order**:
```python
def can_pair_with(self, other_agent: Agent) -> bool:
    """Check if pairing is allowed."""
    # Check general cooldown first
    if self._trading_partner.trade_cooldown > 0:
        return False
    
    # Check per-partner cooldown
    if other_agent.id in self._trading_partner.partner_cooldowns:
        return False
    
    # Check mutual availability
    if self._trading_partner.trade_partner_id is not None:
        return False  # Already paired
    if other_agent._trading_partner.trade_partner_id is not None:
        return False  # Other agent already paired
    
    return True
```

### Edge Cases

**Case 1: Simultaneous Unpair Attempt**
- **Scenario**: Handler tries to unpair both agents in same step
- **Resolution**: Use deterministic ordering (lower ID processes first)
- **Implementation**: Pairing end is always mutual and atomic

**Case 2: Unreachable Meeting Point**
- **Scenario**: Meeting point becomes blocked or agents can't reach it
- **Resolution**: Stagnation timer eventually ends session if no progress made
- **Implementation**: Stagnation detection in trading handler tracks steps without successful trade

### Validation Criteria
- [ ] All state transitions documented in table
- [ ] Tie-break ordering tests added
- [ ] Edge case tests for simultaneous operations
- [ ] Cooldown decrement logic validated

---

## 4. Inventory Mutation Invariant ✅ CRITICAL

### Decision: **Strict In-Place Mutation Contract**

### The Invariant

**RULE**: `AgentInventory` component MUST mutate dictionaries in place. It MUST NEVER rebind `self.carrying` or `self.home_inventory` references.

### Why This Matters

```python
# Agent exposes inventory via aliases
class Agent:
    def __post_init__(self):
        self._inventory = AgentInventory(...)
        object.__setattr__(self, "carrying", self._inventory.carrying)
        object.__setattr__(self, "home_inventory", self._inventory.home_inventory)

# If component rebinds (BAD):
class AgentInventory:
    def deposit_all(self):
        self.carrying = {"good1": 0, "good2": 0}  # ❌ Creates new dict
        # agent.carrying still points to old dict!

# Correct in-place mutation (GOOD):
class AgentInventory:
    def deposit_all(self):
        for key in self.carrying.keys():
            self.carrying[key] = 0  # ✅ Mutates existing dict
        # agent.carrying sees changes
```

### Enforced Pattern

**All inventory operations MUST follow this pattern**:

```python
class AgentInventory:
    def __init__(self, preference: Preference):
        # Create dicts ONCE in __init__
        self.carrying: Dict[str, int] = {"good1": 0, "good2": 0}
        self.home_inventory: Dict[str, int] = {"good1": 0, "good2": 0}
        self.preference = preference
        
        # INVARIANT: These dict objects NEVER change identity
        # Only their contents are mutated
    
    def deposit_all(self) -> bool:
        """Move all carried goods into home inventory."""
        moved = False
        # ✅ GOOD: In-place mutation via iteration
        for key in list(self.carrying.keys()):
            if self.carrying[key] > 0:
                self.home_inventory[key] += self.carrying[key]
                self.carrying[key] = 0
                moved = True
        return moved
    
    def withdraw_all(self) -> bool:
        """Move all home inventory into carrying."""
        moved = False
        # ✅ GOOD: In-place mutation via iteration
        for key in list(self.home_inventory.keys()):
            if self.home_inventory[key] > 0:
                self.carrying[key] += self.home_inventory[key]
                self.home_inventory[key] = 0
                moved = True
        return moved
    
    def collect_resource(self, resource_type: str) -> None:
        """Add resource to carrying inventory."""
        # ✅ GOOD: In-place increment
        if resource_type == "A":
            self.carrying["good1"] += 1
        elif resource_type == "B":
            self.carrying["good2"] += 1
    
    # ❌ BAD: Never do this
    def _bad_clear_carrying(self):
        self.carrying = {"good1": 0, "good2": 0}  # Breaks aliases!
```

### Testing the Invariant

```python
# Test file: tests/unit/components/test_inventory_mutation_invariant.py

def test_inventory_alias_identity_preserved():
    """Verify that inventory dict objects maintain identity through operations."""
    from src.econsim.simulation.agent import Agent
    from src.econsim.simulation.config import SimConfig
    
    # Create agent with inventory component
    agent = create_test_agent()
    
    # Capture dict identities
    carrying_id = id(agent.carrying)
    home_id = id(agent.home_inventory)
    component_carrying_id = id(agent._inventory.carrying)
    component_home_id = id(agent._inventory.home_inventory)
    
    # Verify initial alias
    assert carrying_id == component_carrying_id
    assert home_id == component_home_id
    
    # Perform operations that mutate inventory
    agent.carrying["good1"] = 5
    agent.carrying["good2"] = 3
    agent.deposit()
    agent.withdraw_all()
    agent._inventory.collect_resource("A")
    
    # Verify identity preserved throughout
    assert id(agent.carrying) == carrying_id, "carrying dict identity changed!"
    assert id(agent.home_inventory) == home_id, "home_inventory dict identity changed!"
    assert id(agent._inventory.carrying) == component_carrying_id
    assert id(agent._inventory.home_inventory) == component_home_id

def test_inventory_mutations_visible_through_aliases():
    """Verify that mutations in component are visible through agent aliases."""
    agent = create_test_agent()
    
    # Mutate via component
    agent._inventory.carrying["good1"] = 10
    
    # Verify visible via alias
    assert agent.carrying["good1"] == 10
    
    # Mutate via alias
    agent.carrying["good2"] = 5
    
    # Verify visible in component
    assert agent._inventory.carrying["good2"] == 5
```

### Code Review Checklist

For every inventory method, verify:
- [ ] No assignments to `self.carrying` or `self.home_inventory`
- [ ] Only assignments to `self.carrying[key]` or `self.home_inventory[key]`
- [ ] Iteration uses `list(dict.keys())` if modifying during iteration
- [ ] No `dict.clear()` followed by repopulation (use key iteration instead)

### Documentation Requirement

Add to every inventory component file:

```python
"""
Agent inventory management with dual storage system.

CRITICAL INVARIANT: This component MUST mutate self.carrying and 
self.home_inventory dictionaries IN PLACE. Never rebind these references.
The Agent class exposes these dicts via aliases for backward compatibility,
and rebinding would break the alias connection.

Correct:   self.carrying["good1"] = 0
Incorrect: self.carrying = {"good1": 0, "good2": 0}
"""
```

### Validation Criteria
- [ ] Inventory mutation invariant documented in component docstring
- [ ] Identity preservation tests added
- [ ] All inventory methods audited for compliance
- [ ] No dict rebinding in any inventory operation

---

## 5. Performance Measurement Protocol ✅ HIGH PRIORITY

### Decision: **5-Sample Median with 2% Threshold (Informational Only)**

### Policy: Measurement, Not Enforcement

**IMPORTANT**: During the Agent refactor, performance tests are **strictly informational** and **do not block merges**. The purpose is to:
- Monitor performance trends across refactor phases
- Provide visibility into any significant changes
- Flag potential regressions for developer awareness

**Performance tests will NOT**:
- Fail CI builds
- Block PR merges
- Require immediate optimization

**Developer triggers action**: Only if the developer explicitly identifies a performance concern after reviewing metrics should optimization be considered. Otherwise, assume performance is acceptable.

### Measurement Protocol

**Standard Benchmark Run**:
```python
# File: tests/performance/benchmark_protocol.py

def run_performance_benchmark(scenario_name: str, num_samples: int = 5) -> BenchmarkResult:
    """
    Run performance benchmark with standardized protocol.
    
    Protocol:
    1. Run 1 warmup iteration (discarded)
    2. Run num_samples measurement iterations
    3. Take median of measured samples
    4. Compare to baseline with 2% threshold
    """
    results = []
    
    # Warmup run (discard)
    _ = _run_single_benchmark(scenario_name)
    
    # Measurement runs
    for i in range(num_samples):
        result = _run_single_benchmark(scenario_name)
        results.append(result)
    
    # Statistical summary
    median = statistics.median(results)
    mean = statistics.mean(results)
    stddev = statistics.stdev(results) if len(results) > 1 else 0.0
    
    return BenchmarkResult(
        scenario=scenario_name,
        median_steps_per_sec=median,
        mean_steps_per_sec=mean,
        stddev=stddev,
        samples=results,
        warmup_discarded=True
    )

def compare_to_baseline(result: BenchmarkResult, baseline_path: str = "baselines/performance_baseline.json") -> ComparisonResult:
    """Compare benchmark result to baseline with 2% threshold."""
    with open(baseline_path) as f:
        baseline = json.load(f)
    
    baseline_value = baseline[result.scenario]["median_steps_per_sec"]
    current_value = result.median_steps_per_sec
    
    percent_change = ((current_value - baseline_value) / baseline_value) * 100
    
    # Threshold: -2% (2% slower is flag for review)
    threshold_lower = -2.0
    threshold_upper = float('inf')  # No upper limit (faster is always good)
    
    passed = percent_change >= threshold_lower
    
    return ComparisonResult(
        scenario=result.scenario,
        baseline_value=baseline_value,
        current_value=current_value,
        percent_change=percent_change,
        passed=passed,
        threshold_lower=threshold_lower,
        threshold_upper=threshold_upper
    )
```

### Baseline File Format

```json
{
    "baseline_date": "2025-10-02",
    "hardware": "baseline_hardware_id",
    "scenarios": {
        "basic_12x12_100steps": {
            "median_steps_per_sec": 999.3,
            "mean_steps_per_sec": 998.7,
            "stddev": 2.1,
            "num_samples": 5
        },
        "trading_enabled_12x12_100steps": {
            "median_steps_per_sec": 876.5,
            "mean_steps_per_sec": 875.2,
            "stddev": 3.8,
            "num_samples": 5
        }
    }
}
```

### Threshold Breach Handling

**When benchmark shows >2% change (informational report only)**:

1. **Generate informational report**:
   ```
   PERFORMANCE CHANGE DETECTED (Informational Only)
   Scenario: basic_12x12_100steps
   Baseline: 999.3 steps/sec (median)
   Current:  969.2 steps/sec (median)
   Change:   -3.01% (exceeds -2% observation threshold)
   
   Samples: [968.1, 970.5, 969.2, 967.8, 971.3]
   
   Note: This is informational only and does not block merge.
   Developer may optionally investigate if concerned.
   ```

2. **CI behavior**: Report logged, build **passes** (no blocking)
3. **Developer action**: Optional review at developer's discretion
4. **No action required**: Unless developer explicitly flags performance as a concern

### Micro-Benchmark Targets

**File**: `tests/performance/test_agent_micro.py`

**Note**: All micro-benchmark "targets" are **informational guidelines**, not hard requirements. Tests report measurements but do not fail on threshold breaches.

```python
def test_movement_performance():
    """Micro-benchmark for movement component (informational)."""
    movement = AgentMovement(agent_id=1)
    grid = create_test_grid(12, 12)
    rng = random.Random(42)
    
    # Informational target: < 0.5 microseconds per move
    num_iterations = 10000
    start = time.perf_counter()
    
    pos = (5, 5)
    for _ in range(num_iterations):
        pos = movement.move_random(pos, grid, rng)
    
    elapsed = time.perf_counter() - start
    per_move = (elapsed / num_iterations) * 1e6  # microseconds
    
    # Report only, don't assert/fail
    print(f"Movement performance: {per_move:.2f} µs/move (target: <0.5µs)")
    # assert per_move < 0.5, f"Movement too slow: {per_move:.2f} µs/move"

def test_inventory_operations_performance():
    """Micro-benchmark for inventory component (informational)."""
    inventory = AgentInventory(create_test_preference())
    
    # Informational target: < 1.0 microseconds per operation
    num_iterations = 10000
    start = time.perf_counter()
    
    for _ in range(num_iterations):
        inventory.collect_resource("A")
        inventory.current_utility()
        inventory.deposit_all()
        inventory.withdraw_all()
    
    elapsed = time.perf_counter() - start
    per_op = (elapsed / num_iterations) * 1e6
    
    # Report only, don't assert/fail
    print(f"Inventory performance: {per_op:.2f} µs/op (target: <1.0µs)")

def test_target_selection_performance():
    """Micro-benchmark for target selection (12x12 grid, informational)."""
    selector = ResourceTargetStrategy()
    grid = create_test_grid_with_resources(12, 12, num_resources=20)
    
    # Informational target: < 150 microseconds per selection
    num_iterations = 1000
    start = time.perf_counter()
    
    for _ in range(num_iterations):
        target = selector.select_target(
            agent_pos=(6, 6),
            current_bundle=(5.0, 5.0),
            preference=create_test_preference(),
            grid=grid
        )
    
    elapsed = time.perf_counter() - start
    per_selection = (elapsed / num_iterations) * 1e6
    
    # Report only, don't assert/fail
    print(f"Target selection performance: {per_selection:.2f} µs/selection (target: <150µs)")
```

### Micro-Benchmark Targets Summary (Informational)

| Component | Operation | Target Latency | Notes |
|-----------|-----------|----------------|-------|
| Movement | Single move | < 0.5 µs | Pure spatial calculation |
| Inventory | Deposit/withdraw | < 1.0 µs | Dict operations |
| Inventory | Utility calculation | < 0.5 µs | Preference function call |
| Target Selection | Resource scan (12x12) | < 150 µs | Includes distance calc |
| Pairing Evaluation | Partner scan (12x12) | < 180 µs | +25% vs resource-only |

**Note**: All targets are informational guidelines for awareness, not pass/fail criteria.

### Validation Criteria
- [ ] Protocol documented and implemented
- [ ] Baseline file format established (for trending)
- [ ] Micro-benchmarks added for all Phase 1 components (reporting only)
- [ ] CI integration logs performance reports (non-blocking)

---

## 6. Serialization/Snapshot Strategy ✅ HIGH PRIORITY

### Decision: **Flatten Strategy (No Format Versioning Yet)**

### Rationale
- **Simplicity**: Component nesting is internal implementation detail
- **Compatibility**: Existing replay/snapshot code unchanged
- **Deferred Complexity**: Version migration only if future needs demand it

### Implementation Pattern

**Agent serialization flattens component state**:

```python
class Agent:
    def serialize(self) -> Dict[str, Any]:
        """
        Serialize agent state for snapshots.
        
        Component state is flattened - internal component organization
        is not exposed in snapshot format.
        """
        return {
            # Identity
            "id": self.id,
            
            # Spatial state (direct fields)
            "x": self.x,
            "y": self.y,
            "home_x": self.home_x,
            "home_y": self.home_y,
            "target": self.target,
            
            # Inventory state (flattened from component via aliases)
            "carrying": dict(self.carrying),
            "home_inventory": dict(self.home_inventory),
            
            # Mode state
            "mode": self.mode.value,
            
            # Trading state (flattened from component via aliases)
            "trade_partner_id": self.trade_partner_id,
            "meeting_point": self.meeting_point,
            "is_trading": self.is_trading,
            "trade_cooldown": self.trade_cooldown,
            "partner_cooldowns": dict(self.partner_cooldowns),
            
            # Preference (serialized)
            "preference": self.preference.serialize(),
            
            # NOTE: Component instances (_inventory, _movement, etc.) 
            # are NOT serialized - only their data via exposed aliases
        }
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'Agent':
        """
        Deserialize agent from snapshot.
        
        Reconstructs components internally from flattened data.
        """
        from ...preferences.factory import create_preference
        
        preference = create_preference(data["preference"])
        
        # Create agent (components initialized in __post_init__)
        agent = cls(
            id=data["id"],
            x=data["x"],
            y=data["y"],
            home_x=data["home_x"],
            home_y=data["home_y"],
            preference=preference
        )
        
        # Restore state via public interface (which updates components)
        agent.carrying.update(data["carrying"])
        agent.home_inventory.update(data["home_inventory"])
        agent.mode = AgentMode(data["mode"])
        agent.target = data.get("target")
        
        # Restore trading state
        if data.get("trade_partner_id") is not None:
            agent._trading_partner.trade_partner_id = data["trade_partner_id"]
            agent._trading_partner.meeting_point = data.get("meeting_point")
            agent._trading_partner.is_trading = data.get("is_trading", False)
            agent._trading_partner.trade_cooldown = data.get("trade_cooldown", 0)
            agent._trading_partner.partner_cooldowns = dict(data.get("partner_cooldowns", {}))
            
            # Update aliases
            object.__setattr__(agent, "trade_partner_id", agent._trading_partner.trade_partner_id)
            object.__setattr__(agent, "meeting_point", agent._trading_partner.meeting_point)
            object.__setattr__(agent, "is_trading", agent._trading_partner.is_trading)
        
        return agent
```

### Compatibility Test

```python
# File: tests/integration/test_snapshot_compatibility.py

def test_pre_refactor_snapshot_loads_post_refactor():
    """Verify that snapshots from pre-refactor code load correctly."""
    # Load a snapshot saved before refactor
    with open("tests/fixtures/pre_refactor_snapshot.json") as f:
        snapshot_data = json.load(f)
    
    # Deserialize with refactored Agent class
    agent = Agent.deserialize(snapshot_data["agents"][0])
    
    # Verify state correctly restored
    assert agent.x == snapshot_data["agents"][0]["x"]
    assert agent.carrying == snapshot_data["agents"][0]["carrying"]
    # ... etc
    
    # Run simulation forward
    sim = Simulation.from_snapshot(snapshot_data)
    for _ in range(10):
        sim.step()
    
    # Verify deterministic behavior continues
    # (hash comparison after N steps)
```

### Future Migration Path (If Needed)

**If format versioning becomes necessary**:

```python
# Future versioned format (Phase 4+)
{
    "snapshot_version": 2,
    "agents": [
        {
            "id": 1,
            "spatial": {"x": 5, "y": 3, ...},
            "inventory": {"carrying": {...}, "home": {...}},
            "trading": {"partner_id": null, ...},
            "components_metadata": {"version": "refactor_v2"}
        }
    ]
}

# With migration support
def deserialize(cls, data: Dict[str, Any]) -> 'Agent':
    version = data.get("snapshot_version", 1)
    if version == 1:
        return cls._deserialize_v1(data)  # Flatten strategy
    elif version == 2:
        return cls._deserialize_v2(data)  # Structured format
```

**But defer this until there's a concrete need.**

### Validation Criteria
- [ ] Serialization produces identical structure pre/post refactor
- [ ] Deserialization reconstructs components correctly
- [ ] Pre-refactor snapshots load successfully
- [ ] Round-trip test: serialize → deserialize → verify state

---

## 7. Feature Flag Naming Convention ✅ HIGH PRIORITY

### Decision: **Per-Component Progressive Flags with Rapid Cleanup**

### Core Principle: Minimize Flag Lifespan

**Critical Policy**: Feature flags are **temporary scaffolding** only. Each flag exists for:
- **Day 1**: Implementation with flag=0 (disabled by default)
- **Day 2**: Enable with flag=1, run full test suite + production-like validation
- **Day 3**: Remove flag entirely, delete legacy code path

**Rationale**: Avoid flag proliferation and technical debt. Flags are rollback safety nets, not long-term configuration. After 1 day of validation, commit to the refactored path.

### Flag Naming Scheme

**Pattern**: `ECONSIM_AGENT_<COMPONENT>_REFACTOR=<0|1>`

**Defined Flags**:

```bash
# Phase 1 flags
ECONSIM_AGENT_MOVEMENT_REFACTOR=1      # Movement component extraction
ECONSIM_AGENT_EVENTS_REFACTOR=1        # Event emitter consolidation

# Phase 2 flags
ECONSIM_AGENT_INVENTORY_REFACTOR=1     # Inventory component extraction
ECONSIM_AGENT_TRADING_REFACTOR=1       # Trading partner component extraction
ECONSIM_AGENT_SELECTION_REFACTOR=1     # Target selection strategies

# Phase 3 flags
ECONSIM_AGENT_STATE_MACHINE_REFACTOR=1 # Mode state machine
ECONSIM_AGENT_COMMANDS_REFACTOR=1      # Command pattern (optional)
```

### Flag Behavior

**Default Values** (progressive rollout):
```python
# File: src/econsim/simulation/agent_flags.py

import os
from typing import Dict

def get_refactor_flags() -> Dict[str, bool]:
    """Get current refactor feature flag values."""
    return {
        # Phase 1 (deployed after validation)
        "movement": os.environ.get("ECONSIM_AGENT_MOVEMENT_REFACTOR", "1") == "1",
        "events": os.environ.get("ECONSIM_AGENT_EVENTS_REFACTOR", "1") == "1",
        
        # Phase 2 (deployed after validation)
        "inventory": os.environ.get("ECONSIM_AGENT_INVENTORY_REFACTOR", "1") == "1",
        "trading": os.environ.get("ECONSIM_AGENT_TRADING_REFACTOR", "1") == "1",
        "selection": os.environ.get("ECONSIM_AGENT_SELECTION_REFACTOR", "1") == "1",
        
        # Phase 3 (deployed after validation)
        "state_machine": os.environ.get("ECONSIM_AGENT_STATE_MACHINE_REFACTOR", "1") == "1",
        "commands": os.environ.get("ECONSIM_AGENT_COMMANDS_REFACTOR", "0") == "1",  # Optional
    }

def is_refactor_enabled(component: str) -> bool:
    """Check if specific refactor component is enabled."""
    flags = get_refactor_flags()
    return flags.get(component, False)
```

### Usage Pattern

**In agent code**:
```python
from .agent_flags import is_refactor_enabled

class Agent:
    def __post_init__(self):
        # Initialize components based on flags
        if is_refactor_enabled("movement"):
            self._movement = AgentMovement(self.id)
        
        if is_refactor_enabled("inventory"):
            self._inventory = AgentInventory(self.preference)
            # Set up aliases...
        
        # etc.
    
    def move_random(self, grid: Grid, rng: random.Random) -> None:
        """Move one step randomly."""
        if is_refactor_enabled("movement"):
            # Use refactored movement component
            new_pos = self._movement.move_random((self.x, self.y), grid, rng)
            self.x, self.y = new_pos
        else:
            # Legacy inline implementation
            x, y = self.x, self.y
            moves = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]
            dx, dy = rng.choice(moves)
            # ... legacy code ...
```

### Rollout Timeline (Accelerated)

**Policy**: Feature flags exist for **1 day of testing** before removal to minimize technical debt.

| Phase | Implementation | Flag Default | Testing Period | Flag Removal |
|-------|----------------|--------------|----------------|--------------|
| 1.1 | Day 1 | `MOVEMENT_REFACTOR=0` | Day 2 (=1) | Day 3 |
| 1.2 | Day 3 | `EVENTS_REFACTOR=0` | Day 4 (=1) | Day 5 |
| 2.1 | Day 5 | `INVENTORY_REFACTOR=0` | Day 6 (=1) | Day 7 |
| 2.2 | Day 7 | `TRADING_REFACTOR=0` | Day 8 (=1) | Day 9 |
| 2.3 | Day 9 | `SELECTION_REFACTOR=0` | Day 10 (=1) | Day 11 |
| 3.1 | Day 11 | `STATE_MACHINE_REFACTOR=0` | Day 12 (=1) | Day 13 |
| 3.2 | Day 13+ | `COMMANDS_REFACTOR=0` | Opt-in only | TBD (optional feature) |

### Flag Removal Process (Accelerated)

**After 1 day of testing with default=1 and no critical issues**:

1. Remove flag check from code
2. Delete legacy code path
3. Remove flag from `agent_flags.py`
4. Update documentation
5. Commit message: `agent: remove <COMPONENT>_REFACTOR flag (cleanup after 1-day validation)`

**Rationale**: Minimize technical debt from flag proliferation. Each component gets 1 day of production-like testing before permanent integration.

### Testing with Flags

```python
# File: tests/conftest.py

import pytest
import os

@pytest.fixture
def refactor_flags_all_enabled():
    """Fixture to enable all refactor flags."""
    original = {}
    flags = [
        "ECONSIM_AGENT_MOVEMENT_REFACTOR",
        "ECONSIM_AGENT_EVENTS_REFACTOR",
        "ECONSIM_AGENT_INVENTORY_REFACTOR",
        "ECONSIM_AGENT_TRADING_REFACTOR",
        "ECONSIM_AGENT_SELECTION_REFACTOR",
        "ECONSIM_AGENT_STATE_MACHINE_REFACTOR",
    ]
    
    for flag in flags:
        original[flag] = os.environ.get(flag)
        os.environ[flag] = "1"
    
    yield
    
    # Restore
    for flag, value in original.items():
        if value is None:
            os.environ.pop(flag, None)
        else:
            os.environ[flag] = value

@pytest.fixture
def refactor_flags_all_disabled():
    """Fixture to disable all refactor flags (test legacy path)."""
    # Similar pattern, set all to "0"
    pass
```

### Validation Criteria
- [ ] All flags documented in `agent_flags.py`
- [ ] Default values align with accelerated rollout timeline
- [ ] Test fixtures support flag combinations
- [ ] Removal timeline established (1 day testing per flag)
- [ ] Legacy code paths removed promptly after flag removal

---

## 8. Additional Clarifications

### Error Handling Philosophy

**Principle**: Components raise exceptions; only outer step loop swallows.

**Exception**: Event emission failures are swallowed with single warning (non-critical).

```python
# Components raise
class AgentMovement:
    def move_toward_target(self, current_pos, target):
        if target is None:
            raise ValueError("Target cannot be None")
        # ...

# Agent methods propagate
class Agent:
    def move_toward_target_wrapper(self):
        try:
            new_pos = self._movement.move_toward_target((self.x, self.y), self.target)
            self.x, self.y = new_pos
        except ValueError as e:
            # Only if this is non-critical and recoverable
            pass

# Step executor catches
class StepExecutor:
    def execute_step(self):
        try:
            for agent in agents:
                agent.step_decision()
        except Exception as e:
            # Log and continue or fail depending on severity
            pass
```

### Package Layout

**Adopt consistent subpackage structure**:

```
src/econsim/simulation/components/
├── __init__.py
├── movement/
│   ├── __init__.py          # exports AgentMovement, utils
│   ├── core.py              # AgentMovement class
│   └── utils.py             # manhattan_distance, etc.
├── inventory/
│   ├── __init__.py
│   └── core.py              # AgentInventory class
├── trading_partner/
│   ├── __init__.py
│   └── core.py              # TradingPartner class
├── event_emitter/
│   ├── __init__.py
│   └── core.py              # AgentEventEmitter class
└── target_selection/
    ├── __init__.py
    ├── base.py              # Strategy interfaces
    ├── resource_selection.py
    ├── unified_selection.py
    └── leontief_prospecting.py (REMOVED per finalreview.md Section 5.6)
```

### Import Rules

**Codified dependency rules**:

```python
# Rule 1: TYPE_CHECKING for Agent references in components
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..agent import Agent

# Rule 2: No circular instantiation
# Components instantiated BY agent, never instantiate agent themselves

# Rule 3: Late local imports for optional dependencies
def optional_feature(self):
    if feature_enabled:
        from ..optional_module import OptionalClass
        # Use OptionalClass
```

### Utility Centralization

**Single canonical location**: `src/econsim/simulation/utils/spatial.py`

```python
# File: src/econsim/simulation/utils/spatial.py

def manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """Calculate Manhattan distance between two points."""
    return abs(x1 - x2) + abs(y1 - y2)

def calculate_meeting_point(pos1: tuple[int, int], pos2: tuple[int, int]) -> tuple[int, int]:
    """Calculate midpoint between two positions for meeting."""
    x1, y1 = pos1
    x2, y2 = pos2
    return (x1 + x2) // 2, (y1 + y2) // 2
```

**Migration**: Remove duplicates from `grid.py`, `agent.py` after refactor.

---

## 9. Summary Decision Matrix

| Decision Point | Choice | Phase | Rationale |
|----------------|--------|-------|-----------|
| **Mode Management** | Hybrid (external authority, internal validator) | 1-2 | Lower risk, incremental migration path |
| **Hash Contract** | Explicit field whitelist, component exclusion | 1 | Prevents drift, clear determinism boundary |
| **Trading Cooldowns** | Deterministic state table, lower ID tie-break | 2 | Eliminates edge case ambiguity |
| **Inventory Mutation** | Strict in-place mutation only | 2 | Preserves alias integrity |
| **Performance Protocol** | 5-sample median, informational reporting only | 1+ | Monitoring without blocking; developer-triggered action |
| **Serialization** | Flatten components (no versioning) | 1-2 | Simplicity, defer complexity |
| **Feature Flags** | Per-component progressive flags (1-day testing) | 1-3 | Granular rollout, rapid cleanup, minimal debt |
| **Error Handling** | Components raise, step loop catches | 1+ | Clear responsibility, debuggability |
| **Package Layout** | Consistent subpackages | 1+ | Maintainability, scalability |

---

## 10. Next Steps

**Immediate Artifacts to Create**:

1. **`docs/agent_determinism_contract.md`**
   - Copy hash contract section from this document
   - Reference in all component implementations

2. **`docs/agent_public_api_freeze.md`**
   - Generate current public API list
   - Freeze as compatibility requirement

3. **`src/econsim/simulation/agent_flags.py`**
   - Implement flag management module
   - Document accelerated rollout timeline (1-day testing per component)

4. **`tests/unit/components/test_mutation_invariants.py`**
   - Implement identity preservation tests
   - Run as part of component test suite

5. **`tests/performance/benchmark_protocol.py`**
   - Implement standardized measurement
   - Add micro-benchmarks for Phase 1 components

**Validation Before Phase 1 Start**:

- [ ] All 7 critical decisions documented and approved
- [ ] Determinism contract created
- [ ] API freeze list generated
- [ ] Feature flags module implemented
- [ ] Performance protocol in place
- [ ] Mutation invariant tests written
- [ ] Team review completed

---

## 11. Open Questions for Final Validation

1. **Mode Management**: Approve hybrid approach or prefer full property delegation from start?

2. **Leontief Prospecting**: Confirm removal per finalreview.md Section 5.6, or keep with refactor?

3. **Command Pattern**: Defer to Phase 4+ or implement in Phase 3?

4. **Snapshot Format**: Any existing snapshots that need compatibility testing?

5. **Feature Flag Defaults**: All flags start at 0 on implementation day, flip to 1 for testing day, removed on day 3 (per accelerated timeline)

6. **Hash Enforcement Timeline**: When to re-enable strict hash checking after deferred period?

---

**Status**: Ready for final validation and approval to proceed to Phase 1 implementation.

