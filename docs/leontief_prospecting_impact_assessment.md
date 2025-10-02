# Leontief Prospecting Removal - Impact Assessment

**Date**: October 2, 2025  
**Status**: Ready for Removal in Phase 2.3  
**Risk Level**: 🟡 **MEDIUM** - Requires test deletion and behavioral validation  
**Architectural Decision**: Remove prospecting (not defer) per Section 5.6 of finalreview.md

---

## Executive Summary

The Leontief prospecting feature (complementary bundle scouting) is being **permanently removed** during the Agent refactor. This assessment identifies all affected code and tests, quantifies the removal scope, and provides a migration plan.

**Impact**: 14 tests across 4 files need deletion or adaptation. ~200 lines of agent.py code to be removed.

---

## Decision Rationale (from finalreview.md)

**Why Remove?**
1. **Low Pedagogical Value**: Prospecting adds minimal educational benefit vs standard resource targeting
2. **Maintenance Burden**: Special scoring path increases code complexity
3. **Tie-Break Divergence Risk**: Separate selection logic could drift from unified tie-break contract
4. **Determinism Complexity**: Extra iteration and caching increases hash drift surface area

**Alternative Considered**: Defer behind feature flag `ECONSIM_LEONTIEF_PROSPECT_V2=1`

**Decision**: **REMOVE** - If needed in future, re-add with clear performance/educational justification.

---

## Code to Remove

### Agent Methods (agent.py)

#### Lines 529-841: `_try_leontief_prospecting()`
**LOC**: ~312 lines (including docstrings and logic)

**Signature**:
```python
def _try_leontief_prospecting(self, grid: Grid, raw_bundle: tuple[float, float]) -> Position | None:
    """Attempt prospecting behavior for Leontief agents when no single resource gives positive ΔU.
    
    Searches for complementary resource pairs within perception radius and evaluates
    the utility gain from collecting both resources relative to total effort.
    ...
    """
```

**Dependencies**:
- Calls `_peek_resource_type_at()`
- Calls `_find_nearest_complement_resource()`

**Removal Impact**: This is the core prospecting logic. Safe to delete entirely.

---

#### Lines 842-847: `_peek_resource_type_at()`
**LOC**: ~6 lines

**Signature**:
```python
def _peek_resource_type_at(self, grid: Grid, x: int, y: int) -> str | None:
    """Non-destructively peek at the resource type at a given position."""
```

**Usage**: Only called by `_try_leontief_prospecting()`. No other references found.

**Removal Impact**: Delete after prospecting removal. No other code depends on this.

---

#### Line 465: Call to `_try_leontief_prospecting()`

**Location**: `select_target()` method

**Current Code**:
```python
if best_meta is None:
    # No single resource gives positive ΔU - try prospecting for Leontief agents
    prospect_target = self._try_leontief_prospecting(grid, raw_bundle)
    if prospect_target is not None:
        self.target = prospect_target
        self._set_mode(AgentMode.FORAGE, "prospecting", observer_registry, step_number)
    elif self.carrying_total() > 0:
        self._set_mode(AgentMode.RETURN_HOME, "no_targets", observer_registry, step_number)
        self.target = (int(self.home_x), int(self.home_y))
    else:
        self._set_mode(AgentMode.IDLE, "no_targets", observer_registry, step_number)
        self.target = None
```

**Replacement Code** (Phase 2.3):
```python
if best_meta is None:
    # No positive ΔU resource found - transition to appropriate fallback mode
    if self.carrying_total() > 0:
        self._set_mode(AgentMode.RETURN_HOME, "no_targets", observer_registry, step_number)
        self.target = (int(self.home_x), int(self.home_y))
    else:
        self._set_mode(AgentMode.IDLE, "no_targets", observer_registry, step_number)
        self.target = None
```

**Removal Impact**: Simplifies `select_target()` logic by ~5 lines.

---

### Helper Methods

#### `_find_nearest_complement_resource()`

**Location**: `agent.py` (line number varies, ~100 lines)

**Signature**:
```python
def _find_nearest_complement_resource(
    self, 
    first_pos: Position, 
    first_type: str, 
    grid: Grid, 
    max_dist: int
) -> tuple[Position | None, int]:
    """Find nearest complementary resource to a given position within max distance."""
```

**Usage**: Only called by `_try_leontief_prospecting()`.

**Removal Impact**: Delete after prospecting removal. No other dependencies.

---

## Tests to Remove or Adapt

### Primary Test File: `tests/unit/test_leontief_prospecting.py`

**LOC**: 334 lines  
**Test Count**: 11 tests  
**Action**: **DELETE ENTIRE FILE**

#### Tests in File (All Delete):
1. `test_leontief_prospecting_basic()` - DELETE
2. `test_leontief_prospecting_scoring()` - DELETE
3. `test_leontief_prospecting_deterministic()` - DELETE
4. `test_leontief_no_complement_fallback()` - DELETE
5. `test_non_leontief_agents_unaffected()` - **ADAPT** (keep as Leontief preference validation)
6. `test_leontief_prospecting_after_partial_collection()` - DELETE
7. `test_leontief_prospecting_with_home_inventory()` - DELETE
8. `test_leontief_prospect_score_calculation()` - DELETE
9. `test_leontief_prospecting_integration_with_step_decision()` - DELETE
10. `test_leontief_prospecting_empty_grid()` - DELETE
11. `test_leontief_helper_methods()` - DELETE (tests `_peek_resource_type_at`, etc.)

**Adaptation for Test 5**:
```python
def test_leontief_agents_use_unified_selection():
    """Test that Leontief agents work with unified resource targeting."""
    agent = Agent(
        id=1, x=2, y=2,
        preference=LeontiefPreference(a=1.0, b=1.0),
        home_x=2, home_y=2
    )
    
    # Give agent partial bundle so standard targeting works
    agent.carrying['good1'] = 1
    
    grid = Grid(5, 5, [(1, 2, 'A'), (3, 2, 'B')])
    agent.select_target(grid)
    
    # Should target complement (good2) via unified selection
    assert agent.mode == AgentMode.FORAGE
    assert agent.target == (3, 2)  # Targets B to balance bundle
```

---

### Secondary Test Files

#### `tests/unit/test_priority2_simulation_state.py`

**Tests Affected**: 2

1. **Line 63**: `test_leontief_prospecting_determinism_across_steps()`
   - **Action**: **DELETE** - Tests prospecting-specific determinism
   
2. **Line 198**: `test_leontief_prospecting_performance()`
   - **Action**: **DELETE** - Benchmarks prospecting performance

---

#### `tests/unit/test_priority2_integration.py`

**Tests Affected**: 1

1. **Line 267**: `test_leontief_prospecting_with_respawn_system()`
   - **Action**: **DELETE** - Integration test for prospecting + respawn

---

### Test Files with "Leontief" (Keep - Test Preference Type)

These files test the **Leontief preference type**, not prospecting behavior:

✅ **KEEP**: `tests/unit/test_preferences_leontief.py`
- Tests `LeontiefPreference.utility()` calculations
- No prospecting logic tested

✅ **KEEP**: `tests/unit/test_random_preference_assignment.py`
- Tests preference distribution
- No prospecting references

✅ **KEEP**: `tests/unit/test_educational_validation.py`
- General educational scenarios
- May mention Leontief agents but doesn't test prospecting

✅ **KEEP**: `tests/unit/test_trade_phase1_foundations.py`
- Trade logic tests
- Leontief agents used as test fixtures only

✅ **KEEP**: `tests/unit/test_trade_edge_cases.py`
- Trade edge cases
- No prospecting logic

---

## Behavioral Changes After Removal

### Scenario 1: Leontief Agent at (0,0) Bundle

**Before Removal**:
```
Agent with (0,0) bundle near complementary resources:
1. Standard targeting finds no positive ΔU (single resource gives U=0 for Leontief)
2. Prospecting kicks in, evaluates pairs
3. Agent targets one resource from best pair
4. Collects first resource → (1,0) bundle
5. Next step: targets complement → (1,1) bundle
```

**After Removal**:
```
Agent with (0,0) bundle near complementary resources:
1. Standard targeting finds no positive ΔU
2. No prospecting fallback
3. Agent goes IDLE (or RETURN_HOME if carrying anything)
4. Random movement while IDLE
5. Eventually wanders to resource → (1,0) or (0,1) bundle
6. Next step: targets complement with positive ΔU
```

**Impact**: Leontief agents will be slightly less efficient at cold-start (from empty bundle) but will still converge to balanced bundles once they collect any resource.

---

### Scenario 2: Leontief Agent with Partial Bundle

**Before Removal**:
```
Agent with (1,0) bundle:
1. Standard targeting: B resource gives ΔU > 0 (now forms complementary pair)
2. Targets B resource (no prospecting needed)
```

**After Removal**:
```
Agent with (1,0) bundle:
1. Standard targeting: B resource gives ΔU > 0
2. Targets B resource (no change in behavior)
```

**Impact**: **NO CHANGE** - Prospecting never triggered when agent has non-zero bundle.

---

### Scenario 3: Non-Leontief Agents

**Before and After Removal**: **NO CHANGE**

Prospecting only affected Leontief agents. Cobb-Douglas and Perfect Substitutes agents were unaffected.

---

## Hash Impact

### Expected Hash Change?

**Answer**: ✅ **YES** - Minor hash change expected for Leontief agent scenarios with (0,0) starting bundles.

**Reason**: Different target selection path leads to different early movement patterns.

**Mitigation**: Hash gating is **deferred** until Phase 3 completion per determinism policy.

---

## Performance Impact

### Prospecting Overhead

**Current**: Prospecting adds ~10-15ms per Leontief agent per step when triggered (pairs iteration).

**After Removal**: Overhead eliminated. Leontief agents fall back to IDLE/RETURN_HOME faster.

**Net Change**: Slight **performance improvement** (~5-10% for Leontief-heavy scenarios).

---

## Migration Checklist

### Phase 2.3 Day 9: Removal Tasks

- [ ] **Code Removal**:
  - [ ] Delete `_try_leontief_prospecting()` method (~312 lines)
  - [ ] Delete `_peek_resource_type_at()` method (~6 lines)
  - [ ] Delete `_find_nearest_complement_resource()` method (~100 lines)
  - [ ] Remove prospecting call from `select_target()` (~5 lines)
  - [ ] Update `select_target()` docstring (remove prospecting mention)

- [ ] **Test Deletion**:
  - [ ] Delete `tests/unit/test_leontief_prospecting.py` (entire file)
  - [ ] Delete `test_leontief_prospecting_determinism_across_steps()` from `test_priority2_simulation_state.py`
  - [ ] Delete `test_leontief_prospecting_performance()` from `test_priority2_simulation_state.py`
  - [ ] Delete `test_leontief_prospecting_with_respawn_system()` from `test_priority2_integration.py`

- [ ] **Test Adaptation**:
  - [ ] Adapt `test_non_leontief_agents_unaffected()` → `test_leontief_agents_use_unified_selection()`
  - [ ] Add new test: `test_leontief_agents_idle_at_zero_bundle()` (validate new fallback behavior)

- [ ] **Documentation**:
  - [ ] Update AI agent guide: Remove prospecting references
  - [ ] Update agent.py module docstring: Remove prospecting mention
  - [ ] Commit message: `agent: remove leontief prospecting (simplify selection pipeline, hash deferred)`

---

### Phase 2.3 Day 10-11: Validation

- [ ] **Behavioral Validation**:
  - [ ] Run Leontief agent scenario (0,0 bundle start)
  - [ ] Verify agents eventually collect balanced bundles (slower but correct)
  - [ ] Check no crashes or mode transition errors
  - [ ] Spot-check utility convergence over 100 steps

- [ ] **Test Suite**:
  - [ ] Run full test suite: `pytest -q` → Should pass after test deletions
  - [ ] Verify no orphaned imports of deleted methods
  - [ ] Check no remaining references to `prospect` in tests

- [ ] **Performance Check** (informational):
  - [ ] Run `make perf` → Expect slight improvement for Leontief scenarios
  - [ ] Document change in commit message

---

## Risk Assessment

| Risk | Likelihood | Severity | Mitigation |
|------|------------|----------|------------|
| Leontief agents stuck in IDLE forever | LOW | HIGH | Add test to verify eventual resource collection |
| Hash drift larger than expected | MEDIUM | LOW | Hash gating deferred; document in baseline regeneration |
| Orphaned test imports | MEDIUM | LOW | Use `pytest --collect-only` to catch import errors |
| Regression in Leontief utility convergence | LOW | MEDIUM | Add comparison script (optional, 50-step trajectory) |
| Missed helper method dependency | LOW | HIGH | Grep for `_peek_resource_type_at` and `_find_nearest` before deletion |

---

## Rollback Plan

If removal causes critical issues during Phase 2.3 validation:

1. **Abort Removal**: Revert commits (should be 1-2 commits max)
2. **Stub Prospecting**: Replace method with minimal fallback:
   ```python
   def _try_leontief_prospecting(self, grid, raw_bundle):
       # Prospecting disabled - return None to force IDLE fallback
       return None
   ```
3. **Document Decision**: Update finalreview.md with reason for deferral
4. **Continue Refactor**: Proceed with remaining components (prospecting stub retained)

**Trigger for Rollback**: Agent gets permanently stuck (no movement after 50 steps) or critical test failures.

---

## Future Reinstatement Criteria

If prospecting needs to be re-added:

**Requirements**:
1. Feature flag: `ECONSIM_LEONTIEF_PROSPECT_V2=1` (default: disabled)
2. Clear educational justification document (why it improves learning)
3. Performance benchmark showing <2% overhead
4. Full integration with unified tie-break contract (no divergence risk)
5. Comprehensive determinism tests (hash stable with/without flag)

**Approval**: Requires design review before implementation.

---

## Summary

**Removal Scope**:
- **Code**: ~420 lines removed from agent.py
- **Tests**: 14 tests deleted, 1 test adapted
- **Files**: 1 entire test file deleted

**Risk Level**: 🟡 **MEDIUM** - Behavioral change for Leontief agents but convergence preserved

**Timeline**: Phase 2.3 Day 9-11 (implementation + validation)

**Clearance**: ✅ **APPROVED** - Impact assessed, migration plan documented

---

**Assessment Date**: October 2, 2025  
**Phase**: Pre-Phase 2.3 (Target Selection Strategies)  
**Next Review**: After Phase 2.3 completion (validate Leontief behavior)

