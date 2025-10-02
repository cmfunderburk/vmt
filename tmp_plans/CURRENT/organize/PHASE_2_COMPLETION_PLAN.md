# VMT Phase 2 Completion Implementation Plan

**Date:** 2025-09-30  
**Branch:** `sim_debug_refactor_2025-9-30`  
**Scope:** Complete Phase 2 - Step Decomposition with Hash-Neutral Elimination

---

## Executive Summary

This plan implements the remaining Phase 2 tasks to complete the handler decomposition of `Simulation.step()` while eliminating the pedagogically harmful hash-neutral mechanism. The goal is to reduce `Simulation.step()` from 402 lines to <100 lines of orchestration while preserving economic coherence and deterministic behavior.

## Current State Analysis (Updated Post Hash-Neutral Removal)

### ✅ Completed (~70%)
- **Hash-Neutral Elimination COMPLETE**: TradingHandler snapshot/restore removed; MetricsCollector always aggregates utility.
- **StepExecutor Framework**: Stable; `Simulation.step()` already slim (<100 lines, orchestration only).
- **MovementHandler**: Complete (legacy + decision hooks scaffold present).
- **CollectionHandler**: Complete (diff metrics + resource collection logic).
- **TradingHandler (Core Execution)**: Single-intent deterministic execution, economic coherence preserved.

### ⚠️ Discovered Gaps / Regressions (from full test suite)
1. Decision mode flag not propagating → unified selection path inactive (no targets / no resource pickup).
2. Legacy vs decision divergence missing → random walk & decision produce identical paths.
3. Runtime trading toggle yields zero intents after enabling (draft gating logic).
4. FPS debug output removed prematurely (expected `[FPS]` token absent).
5. Micro-delta threshold event emitted twice (one-shot guard ineffective).
6. Overlay / rendering tests fail (no frame variance / overlay bytes delta = 0%).
7. Respawn density underfills target (interval or target arithmetic off-by-one).
8. Pair convergence & partner pairing not activating (unified pairing path gated off).
9. Tiebreak / selection ordering tests fail (agent.target remains None).
10. Widget constructor `decision_mode=True` override ignored (UI flag not plumbed through step context).

### 🎯 Stabilization Focus (Remaining Phase 2 Work)
- Restore decision/unified selection pipeline & target assignment.
- Reinstate FPS & spike logging via MetricsHandler (throttled, feature-flagged).
- Fix trading draft runtime toggle & ensure intent enumeration independent of execution flag.
- Tighten micro-delta single-emission guard.
- Re-align respawn interval & density math to previous semantics.
- Re-enable pairing search & meeting point logic under unified selection.
- Ensure widget-level decision override influences step context every tick.
- Restore minimal overlay dynamism (frame counter / metrics hook) to satisfy rendering variance tests.

---

## Implementation Steps

### Phase 2A: Hash-Neutral Elimination (COMPLETE)

#### Step 1: Remove Hash-Neutral from TradingHandler
**File:** `src/econsim/simulation/execution/handlers/trading_handler.py`

**Remove Lines 81-84:**
```python
# DELETE THIS BLOCK
hash_neutral = os.environ.get("ECONSIM_TRADE_HASH_NEUTRAL") == "1"

if exec_enabled and intents:
    if hash_neutral:
        parity_snapshot = [(a.id, dict(a.carrying)) for a in sim.agents]
```

**Remove Lines 145-152:**
```python
# DELETE THIS BLOCK  
# Hash-neutral restoration (after metrics & debug)
if parity_snapshot is not None:
    id_map = {a.id: a for a in sim.agents}
    for aid, carry in parity_snapshot:
        agent = id_map.get(aid)
        if agent is not None:
            agent.carrying.clear()
            agent.carrying.update(carry)
```

**Update docstring:** Remove hash-neutral references

#### Step 2: Remove Hash-Neutral from MetricsCollector  
**File:** `src/econsim/simulation/metrics.py`

**Modify Line 180 function signature:**
```python
# BEFORE
def record_trade(self, step: int, executed_trade: dict[str, object] | None = None, hash_neutral: bool = False) -> None:

# AFTER  
def record_trade(self, step: int, executed_trade: dict[str, object] | None = None) -> None:
```

**Remove Lines 203 conditional:**
```python
# DELETE THIS BLOCK
if not hash_neutral:
    # ... utility aggregation logic
```

**Keep utility aggregation always enabled** - remove the conditional wrapper

#### Step 3: Update TradingHandler Metrics Call
**File:** `src/econsim/simulation/execution/handlers/trading_handler.py`

**Remove hash_neutral parameter from metrics call (line 122):**
```python
# BEFORE
hash_neutral=hash_neutral,

# AFTER
# (remove this line entirely)
```

### Phase 2B (Revised): Stabilization & Feature Parity Restoration

#### Step 4 (Revised): Decision / Unified Selection Reintegration
Add `decision_enabled` (and/or `unified_enabled`) to `StepContext`; have Movement/Selection logic set `agent.target` & drive resource approach/collection; re-enable tiebreak ordering.

#### Step 5 (Revised): Legacy vs Decision Divergence
Ensure legacy path uses only legacy random walk; decision path invokes selection; verify divergence test.

#### Step 6: Trading Runtime Toggle Resilience
Recompute feature flags each step; enumerate intents when draft enabled even if execution off.

#### Step 7: MetricsHandler FPS & Spike Output
Emit `[FPS]` line when `ECONSIM_DEBUG_FPS=1` (match legacy token) + optional spike tagging.

#### Step 8: Micro-Delta One-Shot Guard
Single guarded emission in enumeration path only.

#### Step 9: Overlay / Frame Variance
Reintroduce frame counter & overlay refresh ensuring byte delta > 2% when enabled.

#### Step 10: Respawn Density Parity
Align interval step check (pre-increment) & target fill logic to restore ≥95% tolerance.

#### Step 11: Pairing & Convergence
Activate pairing search under unified/trading draft; ensure meeting point logic reachable.

#### Step 12: Widget Decision Override
Propagate widget constructor flag to step context each tick (override env / legacy flag).

#### Optional Step 13: Post-Stabilization Determinism / Perf Snapshot
Capture new baseline once all above green.

#### Step 4: Complete MetricsHandler Migration
**File:** `src/econsim/simulation/execution/handlers/metrics_handler.py`

**Extract from Simulation.step():**
- FPS timing logic (lines ~165-175 in world.py)
- Debug output for performance spikes  
- Steps/second calculation refinement
- Any remaining metrics coordination

**Current handler is ~74 lines, target ~120 lines**

#### Step 5: Complete RespawnHandler Migration  
**File:** `src/econsim/simulation/execution/handlers/respawn_handler.py`

**Current handler is ~59 lines, needs:**
- Validation of interval arithmetic logic
- Error handling for respawn failures
- Density calculation metrics
- Integration with existing respawn scheduler

**Target ~80-100 lines**

#### Step 6: Final TradingHandler Cleanup
**File:** `src/econsim/simulation/execution/handlers/trading_handler.py`

**Post hash-neutral removal:**
- Clean up variable declarations (`parity_snapshot = None`)
- Remove unused imports if any
- Simplify conditional logic flows
- Update comments and docstrings

### Phase 2C: Final Orchestration Verification (Simulation.step())
Already within target size; confirm no reintroduced logic creeps back in; keep only orchestration + determinism hash update.

#### Step 7: Move Remaining Logic to Handlers
**File:** `src/econsim/simulation/world.py`

**Current `step()` method ~180 lines, target <100 lines**

**Move to appropriate handlers:**
- Any remaining performance timing → MetricsHandler
- Resource counting → CollectionHandler or MetricsHandler  
- Trade highlight expiration → TradingHandler
- Debug output coordination → MetricsHandler

**Keep in Simulation.step():**
- Handler orchestration (already implemented)
- Observer registry flushing  
- Determinism hash recording
- Step counter increment
- Transient data cleanup

### Phase 2D: Rolling Testing & Validation
Run failing test subsets after each fix (fast loop) before full suite.

#### Step 8: Add Handler Tests
**New Files:**
- `tests/unit/test_trading_handler.py` (economic coherence focused)
- `tests/unit/test_metrics_handler.py` (performance timing)  
- `tests/unit/test_respawn_handler.py` (interval logic)

#### Step 9: Integration Validation
**Existing Test Files:**
- Update `test_trade_economic_coherence.py` - ensure hash-neutral removal doesn't break
- Run full test suite (`pytest -q`) 
- Performance baseline validation (`make perf`)

#### Step 10: Determinism Baseline Update
**Required:** Hash-neutral removal will change determinism baselines
- Capture new baseline with economic coherence behavior
- Update `baselines/determinism_hashes.json`
- Document that this is intentional pedagogical improvement

---

## Success Criteria Checklist

### Code Quality
- [x] Hash-neutral code removed (0 functional references)
- [ ] Decision/unified selection path restored (targets populated)
- [ ] All 5 handlers feature-complete & tested (Trading stabilization + Metrics FPS + Respawn parity pending)
- [x] `Simulation.step()` <100 lines (orchestration only)
- [ ] No new public API regressions (to be confirmed post-fixes)

### Educational Value  
- [x] Trade execution has real inventory consequences (economic coherence preserved)
- [ ] Agent decision behavior (selection, pairing) restored (currently degraded)
- [ ] Launcher scenarios operate with unified selection & pairing (post-fix verification)

### Technical Quality
- [ ] All tests passing (12 failing groups outstanding)
- [ ] Performance within 2% baseline (re-benchmark after stabilization)
- [ ] Deterministic behavior preserved (capture new baseline post-fix)
- [ ] Handler timing budgets met (movement ≤3ms after reintroducing selection path)

---

## Risk Mitigation

### Low Risk Items ✅
- Hash-neutral elimination (pedagogically beneficial)
- Handler completion (established patterns)
- Test suite updates (economic coherence focused)

### Medium Risk Items ⚠️
- Determinism baseline changes (acceptable for educational improvement)  
- Performance impact from handler overhead (monitor closely)
- Integration edge cases (incremental testing)

### Mitigation Strategies
1. **Incremental Validation**: Test after each major step
2. **Economic Testing**: Validate real trade consequences at each stage
3. **Performance Monitoring**: Benchmark after handler completions
4. **Rollback Plan**: Git branch allows easy revert if issues arise

---

## File Modification Summary

| File | Changes | Lines Impact | Risk |
|------|---------|--------------|------|
| `trading_handler.py` | Hash-neutral removed (DONE); add runtime toggle robustness | small delta | Low |
| `movement_handler.py` | Reinstate decision/unified target selection & pairing hooks | +40 lines | Medium |
| `metrics_handler.py` | Add FPS & spike output | +20 lines | Low |
| `respawn_handler.py` | Density/interval parity fix | ±10 lines | Low |
| `trade.py` | Micro-delta guard tightening | +5 lines | Low |
| GUI widget / world | Decision override propagation | +10 lines | Low |
| Tests (adjust/add) | Stabilization verification | +120 lines | Low |

**Revised Net Impact (Estimate):** +185–220 lines (tests + restored selection); runtime core delta modest (<+75 lines total).

---

## Timeline Estimate

- **Day 1 Morning:** Steps 1-3 (Hash-neutral elimination) 
- **Day 1 Afternoon:** Steps 4-6 (Handler completion)
- **Day 2 Morning:** Step 7 (Final step() reduction)
- **Day 2 Afternoon:** Steps 8-9 (Testing & validation)
- **Day 3:** Step 10 (Baseline updates) + final validation

**Total:** 2.5 days for complete Phase 2 implementation

---

## Next Steps

1. **User Review:** Discuss this plan and any modifications needed
2. **Environment Setup:** Ensure `vmt-dev` venv is active and tests baseline
3. **Implementation:** Execute steps in order with validation at each stage
4. **Documentation:** Update progress tracking and prepare for Phase 3

This plan preserves the project's educational mission while completing the architectural refactor for better maintainability and pedagogical clarity.