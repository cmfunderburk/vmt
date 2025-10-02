# VMT Tier 1 Implementation Plan
**Behavior & Events Phase**

**Date:** 2025-09-30  
**Branch:** `sim_debug_refactor_2025-9-30`  
**Prerequisites:** Phase 2 structural refactor complete (handler pipeline active)  
**Target:** Complete mode event coverage, add ResourceCollectionEvent, surface decision override

---

## Task 1: Mode Helper Implementation

### Objective
Centralize all `agent.mode = ...` assignments behind an event-emitting helper to achieve 100% mode change event coverage.

### Implementation Steps

#### Step 1.1: Create Mode Helper Function
**File:** `src/econsim/simulation/agent.py`

Add helper method to `Agent` class:
```python
def _set_mode(self, new_mode: AgentMode, reason: str, observer_registry=None, step_number: int = 0):
    """
    Centralized mode setter that emits AgentModeChangeEvent.
    
    Args:
        new_mode: Target AgentMode
        reason: Brief description for analytics (e.g., "resource_found", "returned_home")
        observer_registry: Event registry (optional, for testing)
        step_number: Current step for event context
    """
    if self.mode == new_mode:
        return  # No-op if mode unchanged
        
    old_mode = self.mode
    self.mode = new_mode
    
    if observer_registry:
        from econsim.observability.events import AgentModeChangeEvent
        event = AgentModeChangeEvent(
            step=step_number,
            agent_id=self.id,
            old_mode=old_mode,
            new_mode=new_mode,
            reason=reason
        )
        observer_registry.notify(event)
```

#### Step 1.2: Find Direct Mode Assignments
**Command to locate targets:**
```bash
cd /home/chris/PROJECTS/vmt
grep -r "\.mode\s*=" src/econsim/simulation/ --include="*.py" -n
```

Expected locations (from Phase 1 analysis):
- `agent.py`: `step_decision()` method
- `world.py`: Possible initialization or reset paths
- Handler files: Movement, trading logic

#### Step 1.3: Migrate First Batch (Agent.step_decision)
**File:** `src/econsim/simulation/agent.py`

**Before:**
```python
def step_decision(self, grid, observer_registry=None, step_number: int = 0):
    # ... existing logic ...
    if some_condition:
        self.mode = AgentMode.RETURN_HOME
    # ... more assignments ...
```

**After:**
```python
def step_decision(self, grid, observer_registry=None, step_number: int = 0):
    # ... existing logic ...
    if some_condition:
        self._set_mode(AgentMode.RETURN_HOME, "carrying_capacity_full", observer_registry, step_number)
    # ... migrate other assignments ...
```

**Testing:**
- Run determinism tests: `pytest tests/unit/test_determinism.py -v`
- Verify event count matches expected mode transitions
- Ensure no hash change (mode events excluded from hash)

#### Step 1.4: Migrate Handler Mode Changes
**Files to check:**
- `src/econsim/simulation/execution/handlers/movement_handler.py`
- `src/econsim/simulation/execution/handlers/trading_handler.py`

Pass `observer_registry` and `step_number` from handler context to agent methods.

---

## Task 2: ResourceCollectionEvent Implementation

### Objective
Add pedagogical visibility into resource collection actions with new event type.

### Implementation Steps

#### Step 2.1: Define Event Class
**File:** `src/econsim/observability/events.py`

Add to existing events:
```python
@dataclass
class ResourceCollectionEvent:
    """Emitted when an agent collects a resource."""
    step: int
    agent_id: int
    x: int  # Collection location
    y: int
    resource_type: str  # 'A' or 'B'
    
    def to_dict(self) -> dict:
        return {
            'type': 'resource_collection',
            'step': self.step,
            'agent_id': self.agent_id,
            'x': self.x,
            'y': self.y,
            'resource_type': self.resource_type
        }
```

#### Step 2.2: Emit Event in CollectionHandler
**File:** `src/econsim/simulation/execution/handlers/collection_handler.py`

Locate the resource collection logic and add event emission:

**Before:**
```python
# Find the existing collection code (likely in run() method)
if agent.at_position(resource_x, resource_y):
    grid.consume(resource_x, resource_y)
    agent.carrying[resource_type] += 1
```

**After:**
```python
if agent.at_position(resource_x, resource_y):
    grid.consume(resource_x, resource_y)
    agent.carrying[resource_type] += 1
    
    # Emit collection event
    from econsim.observability.events import ResourceCollectionEvent
    event = ResourceCollectionEvent(
        step=ctx.step_number,
        agent_id=agent.id,
        x=resource_x,
        y=resource_y,
        resource_type=resource_type
    )
    ctx.observer_registry.notify(event)
```

#### Step 2.3: Update Event Registry
**File:** `src/econsim/observability/registry.py`

Ensure `ResourceCollectionEvent` is registered if needed (check existing pattern).

#### Step 2.4: Add Collection Event Test
**File:** `tests/unit/handlers/test_collection_handler.py` (create if not exists)

```python
def test_collection_event_emission():
    """Verify ResourceCollectionEvent is emitted when agent collects resource."""
    # Setup: agent at resource location
    # Execute: run CollectionHandler
    # Assert: event emitted with correct fields
    pass  # Implement based on existing handler test patterns
```

---

## Task 3: Decision Override in StepContext

### Objective
Surface the `use_decision` parameter through `StepContext` to give handlers access to external decision control.

### Implementation Steps

#### Step 3.1: Extend StepContext
**File:** `src/econsim/simulation/execution/context.py`

Add field to `StepContext` dataclass:
```python
@dataclass(frozen=True)
class StepContext:
    simulation: 'Simulation'
    step_number: int
    external_rng: random.Random
    observer_registry: Any
    # ... existing fields ...
    decision_enabled: bool = True  # New field with default
```

#### Step 3.2: Pass Through from Simulation.step()
**File:** `src/econsim/simulation/world.py`

Update `Simulation.step()` method:

**Before:**
```python
def step(self, external_rng: random.Random, use_decision: bool = True):
    # ... existing code ...
    ctx = StepContext(
        simulation=self,
        step_number=self.current_step,
        external_rng=external_rng,
        observer_registry=self.observer_registry
    )
```

**After:**
```python
def step(self, external_rng: random.Random, use_decision: bool = True):
    # ... existing code ...
    ctx = StepContext(
        simulation=self,
        step_number=self.current_step,
        external_rng=external_rng,
        observer_registry=self.observer_registry,
        decision_enabled=use_decision  # Surface the parameter
    )
```

#### Step 3.3: Adapt MovementHandler Logic
**File:** `src/econsim/simulation/execution/handlers/movement_handler.py`

Use `ctx.decision_enabled` instead of hardcoded decision behavior:

**Before:**
```python
def run(self, ctx: StepContext) -> dict:
    # ... existing logic ...
    if some_condition:
        # Always use decision mode
        agent.step_decision(grid, ctx.observer_registry, ctx.step_number)
```

**After:**
```python
def run(self, ctx: StepContext) -> dict:
    # ... existing logic ...
    if some_condition:
        if ctx.decision_enabled:
            agent.step_decision(grid, ctx.observer_registry, ctx.step_number)
        else:
            agent.move_random(grid, ctx.external_rng)  # Fallback to legacy
```

#### Step 3.4: Update Handler Tests
Add test cases verifying handlers respect `decision_enabled` flag:

```python
def test_movement_handler_respects_decision_flag():
    """Verify MovementHandler uses decision vs random based on context flag."""
    # Test with decision_enabled=True -> calls step_decision
    # Test with decision_enabled=False -> calls move_random
    pass
```

---

## Validation & Testing Protocol

### After Each Task
1. **Run Determinism Tests:**
   ```bash
   pytest tests/unit/test_determinism.py::test_hash_determinism -v
   ```

2. **Check Performance Impact:**
   ```bash
   python scripts/perf_baseline_scenario.py
   # Verify <2% overhead vs baseline
   ```

3. **Run Handler-Specific Tests:**
   ```bash
   pytest tests/unit/handlers/ -v
   ```

### Full Integration Test
After completing all 3 tasks:

```bash
# Complete test suite
pytest -q

# Launcher functionality
make launcher
# -> Verify scenarios still work with new events

# Event coverage verification
grep -r "AgentModeChangeEvent\|ResourceCollectionEvent" tests/ --include="*.py"
# -> Should show comprehensive event testing
```

---

## Success Criteria

### Task 1 - Mode Helper
- [ ] All direct `agent.mode = ...` assignments replaced with `_set_mode()` calls
- [ ] `AgentModeChangeEvent` emitted for every mode transition
- [ ] Determinism hash unchanged (events excluded from hash)
- [ ] Performance impact <1% overhead

### Task 2 - ResourceCollectionEvent
- [ ] Event defined in `observability/events.py`
- [ ] Emitted in CollectionHandler for every resource collection
- [ ] Event fields match specification: `step, agent_id, x, y, resource_type`
- [ ] Unit test validates event emission

### Task 3 - Decision Override
- [ ] `decision_enabled` field added to `StepContext`
- [ ] MovementHandler respects flag (decision vs random movement)
- [ ] External `use_decision` parameter flows through to handlers
- [ ] Backward compatibility maintained (default `True`)

### Overall Integration
- [ ] All tests pass (`pytest -q`)
- [ ] Launcher scenarios functional
- [ ] Performance within 2% of baseline
- [ ] No determinism hash changes
- [ ] Events ready for Phase 3 observer consumption

---

## Risk Mitigation

### Event Migration Ordering Risk
**Mitigation:** Migrate mode assignments in small batches (5-10 sites at a time), run hash test after each batch.

### Performance Risk
**Monitor:** Event emission overhead should be <0.1ms per event. If higher, consider batched emission.

### Testing Coverage Risk
**Ensure:** Each new event type has dedicated unit test verifying correct emission and field population.

---

## Next Steps (Post-Tier 1)

After completing Tier 1, the codebase will be ready for:
- **Tier 2:** FPS centralization, trade utility metrics refinement
- **Tier 3:** Performance scaling tests, determinism baseline refresh
- **Phase 3:** Modular observer decomposition with rich event stream

This foundation ensures comprehensive observability for educational analytics and debugging.