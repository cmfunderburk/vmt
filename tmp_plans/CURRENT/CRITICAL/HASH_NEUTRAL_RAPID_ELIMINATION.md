# VMT Hash-Neutral Elimination - Rapid Implementation Plan

**Date:** 2025-09-30  
**Branch:** `sim_debug_refactor_2025-9-30`  
**Scope:** Fast-track removal of pedagogically harmful hash-neutral mechanism  
**Timeline:** 1 day implementation + validation

---

## Executive Summary

Based on code analysis, the VMT refactor is **much further along** than initially estimated. The handler system is operational and `Simulation.step()` is already clean. This plan focuses on the **core pedagogical improvement**: eliminating hash-neutral mechanisms that create ghost transactions and undermine economic learning.

**Key Finding:** Current `Simulation.step()` is ~75 lines (not 180+) and already delegating properly to handlers. The main work is surgical removal of hash-neutral code.

---

## Implementation Steps (Rapid Track)

### Step 1: Hash-Neutral Code Removal (45 minutes)

#### 1A: TradingHandler - Remove Inventory Restoration Logic
**File:** `src/econsim/simulation/execution/handlers/trading_handler.py`

**Remove Lines 81-84:**
```python
# DELETE THESE LINES
parity_snapshot = None
hash_neutral = os.environ.get("ECONSIM_TRADE_HASH_NEUTRAL") == "1"

if exec_enabled and intents:
    if hash_neutral:
        parity_snapshot = [(a.id, dict(a.carrying)) for a in sim.agents]
```

**Remove Lines 145-152:**
```python
# DELETE THIS ENTIRE BLOCK  
# Hash-neutral restoration (after metrics & debug)
if parity_snapshot is not None:
    id_map = {a.id: a for a in sim.agents}
    for aid, carry in parity_snapshot:
        agent = id_map.get(aid)
        if agent is not None:
            agent.carrying.clear()
            agent.carrying.update(carry)
```

**Remove hash_neutral parameter from metrics call (line ~122):**
```python
# REMOVE THIS LINE
hash_neutral=hash_neutral,
```

#### 1B: MetricsCollector - Remove Hash-Neutral Parameter
**File:** `src/econsim/simulation/metrics.py`

**Update function signature (line 180):**
```python
# BEFORE
def register_executed_trade(self, *, step: int, agent1_id: int, agent2_id: int,
                            agent1_give: str, agent1_take: str,
                            agent1_delta_u: float, agent2_delta_u: float,
                            realized_utility_gain: float | None = None,
                            hash_neutral: bool = False) -> None:

# AFTER (remove hash_neutral parameter)
def register_executed_trade(self, *, step: int, agent1_id: int, agent2_id: int,
                            agent1_give: str, agent1_take: str,
                            agent1_delta_u: float, agent2_delta_u: float,
                            realized_utility_gain: float | None = None) -> None:
```

**Remove conditional utility aggregation (lines 203+):**
```python
# DELETE THE CONDITIONAL - Always enable utility aggregation
# BEFORE
if not hash_neutral:
    try:
        gain = realized_utility_gain
        if gain is None:
            gain = float(agent1_delta_u)
        self.realized_utility_gain_total += float(gain)
    except Exception:  # pragma: no cover
        pass

# AFTER - Remove the conditional wrapper
try:
    gain = realized_utility_gain
    if gain is None:
        gain = float(agent1_delta_u)
    self.realized_utility_gain_total += float(gain)
except Exception:  # pragma: no cover
    pass
```

**Update docstring:** Remove hash_neutral parameter documentation

### Step 2: Documentation and Comment Cleanup (15 minutes)

#### 2A: Update TradingHandler Docstring
**File:** `src/econsim/simulation/execution/handlers/trading_handler.py`

**Remove line 10 reference:**
```python
# REMOVE THIS LINE
# - Hash-neutral parity mode restores inventories (ECONSIM_TRADE_HASH_NEUTRAL=1)
```

#### 2B: Update Trade Module Comment
**File:** `src/econsim/simulation/trade.py`

**Remove or update line 372:**
```python
# REMOVE OR UPDATE COMMENT
# logic in Simulation.step when ECONSIM_TRADE_HASH_NEUTRAL=1.
```

### Step 3: Immediate Testing & Validation (30 minutes)

#### 3A: Run Economic Coherence Tests
```bash
pytest tests/unit/test_trade_economic_coherence.py -v
```

#### 3B: Run Handler Integration Tests
```bash
pytest tests/unit/test_step_handlers_core.py -v
```

#### 3C: Full Test Suite Validation
```bash
pytest -q
```

### Step 4: Environment Variable Cleanup Verification (15 minutes)

#### 4A: Verify No References Remain
```bash
grep -r "ECONSIM_TRADE_HASH_NEUTRAL" src/ --exclude-dir=__pycache__
```

**Should return 0 matches in source code**

#### 4B: Check Documentation Files (Optional)
```bash
grep -r "ECONSIM_TRADE_HASH_NEUTRAL" *.md docs/ --exclude-dir=tmp_plans
```

**Update any user-facing documentation if needed**

### Step 5: Performance & Determinism Validation (20 minutes)

#### 5A: Quick Performance Check
```bash
python scripts/perf_stub.py
```

#### 5B: Capture New Determinism Baseline
```bash
python tests/performance/determinism_capture.py --output baselines/determinism_hashes_post_hash_neutral.json
```

**Note:** This will create a new baseline reflecting economic coherence behavior

---

## Success Criteria (Rapid Track)

### ✅ Immediate Validation
- [ ] All hash-neutral code removed from source files
- [ ] Economic coherence tests passing (5/5)
- [ ] Handler integration tests passing (7/7)  
- [ ] No grep matches for `ECONSIM_TRADE_HASH_NEUTRAL` in src/

### ✅ Educational Value Preserved
- [ ] Trade execution has real inventory consequences
- [ ] No ghost transactions or artificial parity mechanisms
- [ ] Utility aggregation always enabled (no conditional suppression)

### ✅ Technical Stability
- [ ] Full test suite passing (accepting new determinism baseline)
- [ ] Performance within expected range
- [ ] No breaking changes to public APIs

---

## File Change Summary (Minimal Impact)

| File | Changes | Lines | Risk |
|------|---------|-------|------|
| `trading_handler.py` | Remove hash-neutral restoration | -12 lines | Low |
| `metrics.py` | Remove hash_neutral parameter | -3 lines | Low |
| `trade.py` | Update comment | -1 line | None |

**Total Impact:** -16 lines of artificial complexity, 0 new dependencies

---

## Risk Assessment (Updated - Very Low Risk)

### ✅ **No Risk Items**
- Handler integration (already working)
- Performance impact (removing code, not adding)
- API compatibility (removing internal parameters only)

### ⚠️ **Low Risk Items**  
- Determinism baseline change (expected and beneficial)
- Test failures due to behavior changes (validate with economic coherence)

### 🛡️ **Mitigation**
- **Immediate validation** after each step
- **Economic coherence tests** ensure real behavior is preserved
- **Git branch** allows instant rollback if needed

---

## Timeline Breakdown

- **Step 1 (Code Removal):** 45 minutes
- **Step 2 (Documentation):** 15 minutes  
- **Step 3 (Testing):** 30 minutes
- **Step 4 (Verification):** 15 minutes
- **Step 5 (Validation):** 20 minutes

**Total Implementation:** ~2 hours focused work
**Buffer for validation:** +1 hour  
**Complete by:** End of day

---

## Expected Outcomes

### 🎓 **Educational Benefits**
1. **Authentic Economic Behavior**: Students observe real trade consequences
2. **No Ghost Transactions**: Every executed trade persists in agent inventories  
3. **Behavioral Authenticity**: Agent decisions reflect actual simulation state

### 🔧 **Technical Benefits**
1. **Code Simplification**: Remove 16 lines of artificial complexity
2. **Performance Improvement**: Eliminate unnecessary inventory snapshots/restoration
3. **Maintenance Reduction**: One less environment variable and conditional path

### 📊 **Validation Strategy**
1. **Economic Coherence**: Validate real trade consequences
2. **Deterministic Behavior**: Capture new baseline (economic coherence focused)
3. **Educational Scenarios**: Ensure launcher functionality preserved

---

## Next Steps After Completion

1. **Update Progress Document**: Mark Phase 2 hash-neutral elimination complete
2. **Baseline Documentation**: Document that new determinism baseline reflects economic coherence
3. **Educational Testing**: Validate scenarios with launcher (`make launcher`)
4. **Phase 3 Planning**: Prepare for logger refactoring (next major component)

This rapid implementation preserves the project's educational mission while eliminating pedagogically harmful mechanisms in a focused, low-risk manner.