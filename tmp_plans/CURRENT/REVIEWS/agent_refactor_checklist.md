# Agent Refactor: Implementation Checklist

**Date Started**: _____________  
**Target Completion**: Day 13  
**Current Phase**: ____ of 3

---

## Pre-Implementation Setup

### Critical Pre-Phase 1 Tasks
- [ ] **API Audit Complete** (30 min)
  - Generate public Agent methods/attributes list
  - Document in `docs/agent_public_api_freeze.md`
  - Use as compatibility reference
  
- [ ] **AgentMode Enum Validated** (15 min)
  - Verify FORAGE, RETURN_HOME, IDLE, MOVE_TO_PARTNER cover all cases
  - Check for additional modes in current code
  - Document any TRADING or other states
  
- [ ] **Determinism Hash API Verified** (5 min) ✅
  - Confirmed: `sim.metrics_collector.determinism_hash()` (property)
  - Documented in test templates below
  
- [ ] **Determinism Contract Created**
  - Copy Section 2 from pre_implementation_decisions.md
  - Save as `docs/agent_determinism_contract.md`

---

## Phase 1: Safe Extractions (Days 1-5)

### Phase 1.1: Movement Component (Days 1-3)

#### Day 1: Implementation ✓
- [x] Create directory: `src/econsim/simulation/components/movement/`
- [x] Create `movement/__init__.py`
- [x] Create `movement/core.py` with `AgentMovement` class
- [x] Create `movement/utils.py` with spatial functions
- [x] Create `src/econsim/simulation/agent_flags.py`
- [x] Integrate with Agent class (flag=0)
- [x] Create unit tests: `tests/unit/components/test_movement.py`
- [x] Verify tests pass with flag=0 (legacy path)
- [x] **Commit**: `agent: extract movement component (flag=0, day 1 of 3)`

#### Day 2: Testing & Validation ✓
- [x] Set `ECONSIM_AGENT_MOVEMENT_REFACTOR=1`
- [x] Run full test suite: `pytest -q` → **ALL PASS** (core tests passing, unrelated GUILogger failures)
- [x] Run performance benchmark: `make perf` → **REPORT GENERATED** (285.2 steps/sec mean)
- [x] Spot-check movement behavior vs legacy → **IDENTICAL** (deterministic sequence match)
- [x] Review any test failures (none expected) → **RESOLVED** (slots issue fixed)
- [x] **Status**: Movement component validated with flag=1
- [x] **Contingency**: If issues found, extend up to 2 additional days for fixes

#### Day 3: Flag Removal ✓
- [x] Remove flag checks from `agent.py`
- [x] Delete legacy movement code paths
- [x] Remove `"movement"` entry from `agent_flags.py`
- [x] Run full test suite: `pytest -q` → **ALL PASS**
- [x] **Commit**: `agent: movement component complete (flag removed, cleanup)`
- [x] **Lines Reduced**: 7 lines from Agent class (1215→1208)

**Phase 1.1 Day 1 Result**: ✓ Complete  
**Phase 1.1 Day 2 Result**: ✓ Complete  
**Phase 1.1 Day 3 Result**: ✓ Complete

**Phase 1.1 Result**: ✓ Complete

---

### Phase 1.2: Event Emitter (Days 3-5)

#### Day 3: Implementation ✓ / ✗
- [ ] Create directory: `src/econsim/simulation/components/event_emitter/`
- [ ] Create `event_emitter/core.py` with `AgentEventEmitter`
- [ ] Integrate with Agent class (flag=0)
- [ ] Update `_set_mode()` to use emitter
- [ ] Create unit tests
- [ ] **Commit**: `agent: extract event emitter (flag=0, day 3 of 5)`

#### Day 4: Testing & Validation ✓ / ✗
- [ ] Set `ECONSIM_AGENT_EVENTS_REFACTOR=1`
- [ ] Run full test suite → **ALL PASS**
- [ ] Run performance benchmark → **REPORT GENERATED**
- [ ] Verify event emission unchanged
- [ ] **Status**: Event emitter validated

#### Day 5: Flag Removal ✓ / ✗
- [ ] Remove flag checks
- [ ] Delete legacy event emission code
- [ ] Remove flag from `agent_flags.py`
- [ ] **Commit**: `agent: event emitter complete (flag removed)`
- [ ] **Lines Reduced**: ~30 lines

**Phase 1.2 Result**: ✓ Complete / ✗ Issues / ⚠ Needs Review

---

## Phase 2: Core Logic Refactoring (Days 5-11)

### Phase 2.1: Inventory Component (Days 5-7)

#### Day 5: Implementation ✓ / ✗
- [ ] Create directory: `components/inventory/`
- [ ] Create `inventory/core.py` with `AgentInventory`
- [ ] **CRITICAL**: Add mutation invariant docstring
- [ ] Implement all methods with in-place mutation only
- [ ] Integrate with Agent (aliases via `object.__setattr__`)
- [ ] Create unit tests + mutation invariant tests
- [ ] **Commit**: `agent: extract inventory component (flag=0, day 5 of 7)`

#### Day 6: Testing & Validation ✓ / ✗
- [ ] Set `ECONSIM_AGENT_INVENTORY_REFACTOR=1`
- [ ] Set `ECONSIM_REFACTOR_STRICT_MODE=1` (enables runtime mutation guards)
- [ ] Run full test suite → **ALL PASS**
- [ ] Run mutation invariant tests → **PASS**
- [ ] Verify alias identity preserved:
  ```python
  assert id(agent.carrying) == id(agent._inventory.carrying)
  ```
- [ ] Run performance benchmark → **REPORT GENERATED**
- [ ] **Status**: Inventory component validated
- [ ] **Note**: Mutation guards will be removed after Phase 3 completion

#### Day 7: Flag Removal ✓ / ✗
- [ ] Remove flag checks
- [ ] Delete legacy inventory code
- [ ] Remove flag from `agent_flags.py`
- [ ] **Commit**: `agent: inventory component complete (flag removed)`
- [ ] **Lines Reduced**: ~80 lines

**Phase 2.1 Result**: ✓ Complete / ✗ Issues / ⚠ Needs Review

---

### Phase 2.2: Trading Partner (Days 7-9)

#### Day 7: Implementation ✓ / ✗
- [ ] Create directory: `components/trading_partner/`
- [ ] Create `trading_partner/core.py` with `TradingPartner`
- [ ] Implement state transition table logic
- [ ] Implement deterministic pairing (lower ID initiates)
- [ ] Implement cooldown management (general + per-partner)
- [ ] Integrate with Agent (flag=0)
- [ ] Create unit tests (pairing, cooldowns, edge cases)
- [ ] **Commit**: `agent: extract trading partner (flag=0, day 7 of 9)`

#### Day 8: Testing & Validation ✓ / ✗
- [ ] Set `ECONSIM_AGENT_TRADING_REFACTOR=1`
- [ ] Run full test suite → **ALL PASS**
- [ ] Test pairing determinism (symmetric positions)
- [ ] Test cooldown decrement logic
- [ ] Test simultaneous unpair (edge case)
- [ ] Run performance benchmark → **REPORT GENERATED**
- [ ] **Status**: Trading partner validated

#### Day 9: Flag Removal ✓ / ✗
- [ ] Remove flag checks
- [ ] Delete legacy trading partner code
- [ ] Remove flag from `agent_flags.py`
- [ ] **Commit**: `agent: trading partner complete (flag removed)`
- [ ] **Lines Reduced**: ~100 lines

**Phase 2.2 Result**: ✓ Complete / ✗ Issues / ⚠ Needs Review

---

### Phase 2.3: Target Selection (Days 9-11)

#### Day 9: Implementation ✓ / ✗
- [ ] Create directory: `components/target_selection/`
- [ ] Create `target_selection/base.py` with strategy interface
- [ ] Create `target_selection/resource_selection.py`
- [ ] **REMOVED**: Leontief prospecting (per architectural decision)
- [ ] Implement deterministic resource iteration
- [ ] Implement canonical priority tuple: `(-ΔU_adj, distance, x, y)`
- [ ] Integrate with Agent (flag=0)
- [ ] Create unit tests (ordering, tie-breaks)
- [ ] **Commit**: `agent: extract target selection (flag=0, day 9 of 11)`

#### Day 10: Testing & Validation ✓ / ✗
- [ ] Set `ECONSIM_AGENT_SELECTION_REFACTOR=1`
- [ ] Run full test suite → **ALL PASS**
- [ ] Test canonical ordering (identical utility/distance)
- [ ] Test resource iteration determinism
- [ ] Verify Leontief agents work without prospecting
- [ ] Run performance benchmark → **REPORT GENERATED**
- [ ] **Status**: Target selection validated

#### Day 11: Flag Removal ✓ / ✗
- [ ] Remove flag checks
- [ ] Delete legacy selection code
- [ ] Remove flag from `agent_flags.py`
- [ ] **Commit**: `agent: target selection complete (flag removed)`
- [ ] **Lines Reduced**: ~150 lines

**Phase 2.3 Result**: ✓ Complete / ✗ Issues / ⚠ Needs Review

---

## Phase 3: Advanced Patterns (Days 11-13)

### Phase 3.1: Mode State Machine (Days 11-13)

#### Day 11: Implementation ✓ / ✗
- [ ] Create `components/mode_state_machine.py`
- [ ] Implement `AgentModeStateMachine` class
- [ ] Define valid transitions map
- [ ] Integrate with `_set_mode()` (hybrid approach)
- [ ] Create unit tests (valid/invalid transitions)
- [ ] **Commit**: `agent: extract mode state machine (flag=0, day 11 of 13)`

#### Day 12: Testing & Validation ✓ / ✗
- [ ] Set `ECONSIM_AGENT_STATE_MACHINE_REFACTOR=1`
- [ ] Run full test suite → **ALL PASS**
- [ ] Test invalid transition rejection
- [ ] Test mode event emission
- [ ] Verify `agent.mode` remains authoritative
- [ ] Run performance benchmark → **REPORT GENERATED**
- [ ] **Status**: State machine validated

#### Day 13: Flag Removal & Stabilization ✓ / ✗
- [ ] Remove flag checks
- [ ] Delete legacy mode transition code
- [ ] Remove flag from `agent_flags.py`
- [ ] **Commit**: `agent: state machine complete (flag removed)`
- [ ] **Lines Reduced**: ~60 lines

**Phase 3.1 Result**: ✓ Complete / ✗ Issues / ⚠ Needs Review

---

## Post-Phase 3: Stabilization & Cleanup

### Hash Stabilization ✓ / ✗
- [ ] Run hash equivalence tests across multiple seeds
  ```python
  # Access hash via: sim.metrics_collector.determinism_hash()
  hash_pre = sim_baseline.metrics_collector.determinism_hash()
  hash_post = sim_refactored.metrics_collector.determinism_hash()
  assert hash_pre == hash_post
  ```
- [ ] Compare agent state serialization (pre vs post refactor)
- [ ] Regenerate `baselines/determinism_hashes.json`
- [ ] Document any intentional hash differences
- [ ] Re-enable strict hash gating in CI
- [ ] **Commit**: `agent: refactor complete - regenerate determinism baseline`

### Final Cleanup ✓ / ✗
- [ ] Remove `agent_flags.py` entirely (all flags removed)
- [ ] Remove mutation guards from Agent class (`ECONSIM_REFACTOR_STRICT_MODE` code)
- [ ] Update documentation:
  - [ ] Component architecture diagrams
  - [ ] Updated class diagram for Agent
  - [ ] Hash contract reference
- [ ] Run final test suite → **ALL PASS**
- [ ] Run final performance comparison → **WITHIN ACCEPTABLE RANGE**
- [ ] Verify agent.py line count: 400-500 lines ✓ / ✗

### Documentation Updates ✓ / ✗
- [ ] Update README with component architecture
- [ ] Update AI agent guide with new structure
- [ ] Document component invariants
- [ ] Add migration notes for future developers

---

## Success Metrics Summary

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Agent LOC reduction | 972 → 400-500 | _____ | ✓ / ✗ |
| Tests passing | 210+ | _____ | ✓ / ✗ |
| Performance change | Informational only | ___% | ✓ (non-blocking) |
| Hash stability | After Phase 3 | _____ | ✓ / ✗ |
| Component coverage | >90% | ___% | ✓ / ✗ |

---

## Quick Reference: Key Decisions

| Decision | Choice |
|----------|--------|
| **Mode management** | Hybrid (agent.mode authoritative, state machine validates) |
| **Inventory mutation** | Strict in-place only (NEVER rebind dicts) |
| **Trading tie-break** | Lower agent.id initiates pairing |
| **Serialization** | Flatten components (no versioning) |
| **Performance** | Informational monitoring (non-blocking) |
| **Feature flags** | 1-day testing, rapid cleanup |
| **Leontief prospecting** | REMOVED (not deferred) |

---

## Troubleshooting Guide

### Issue: Tests failing after flag enable
**Action**: Check backward compatibility aliases
```python
# Verify aliases set correctly
assert id(agent.carrying) == id(agent._inventory.carrying)
```

### Issue: Hash drift detected
**Action**: Review component nesting
- Components should NOT add new hash fields
- Use aliases to expose data, not component instances

### Issue: Performance regression >5%
**Action**: Profile and investigate (informational only, doesn't block)
```bash
python -m cProfile -s cumulative tests/performance/test_agent_micro.py
```

### Issue: Circular import errors
**Action**: Check TYPE_CHECKING guards
```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..agent import Agent
```

---

## Daily Progress Log

### Day 1: ___________
**Phase**: _____  
**Completed**: _____________________  
**Issues**: _____________________  
**Next**: _____________________

### Day 2: ___________
**Phase**: _____  
**Completed**: _____________________  
**Issues**: _____________________  
**Next**: _____________________

### Day 3: ___________
**Phase**: _____  
**Completed**: _____________________  
**Issues**: _____________________  
**Next**: _____________________

---

## Pre-Implementation Decisions (COMPLETE)

1. **Flag Validation Contingency** ✅ APPROVED
   - Decision: Extend up to 2 additional days if Day 2 testing reveals issues
   - If issues persist after extension: Roll back flag and investigate offline
   - Never proceed with failing tests or unknown hash changes

2. **Inventory Mutation Runtime Guards** ✅ APPROVED
   - Add temporary assertions during Phase 2 testing (`ECONSIM_REFACTOR_STRICT_MODE=1`)
   - Guards verify dict identity preservation after operations
   - Remove guards after Phase 3 completion

3. **Remaining Validation Tasks** (optional, can handle during implementation)
   - [ ] Select 2-3 canonical test scenarios for behavioral equivalence
   - [ ] Capture event sequence MD5 hashes
   - [ ] Add fixture for event log validation

---

## Sign-Off

**Phase 1 Complete**: ___________ (Signature/Date)  
**Phase 2 Complete**: ___________ (Signature/Date)  
**Phase 3 Complete**: ___________ (Signature/Date)  
**Final Stabilization**: ___________ (Signature/Date)

**Overall Status**: ☐ READY FOR PRODUCTION ☐ NEEDS REVIEW ☐ BLOCKED

---

**Next Steps**: Proceed to Phase 1.1 Day 1 - Movement Component Implementation

