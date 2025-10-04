# Accelerated Phase 1 Decoupling Plan

**Date:** October 3, 2025  
**Status:** Approved by Chris  
**Duration:** 3-4 days (50% faster than original 8-day plan)  
**Strategy:** Remove deprecated components + Decouple active components

---

## Executive Summary

Based on Chris' deprecation notes and investigation, we can dramatically accelerate Phase 1 by:
1. **Removing deprecated GUI components** (safe, confirmed by Chris)
2. **Decoupling EmbeddedPygameWidget** (active usage requires decoupling, not removal)
3. **Updating test framework** to work without simulation dependency
4. **Marking unit tests as xfail** during decoupling

**Result:** Complete simulation independence in 3-4 days instead of 8 days.

---

## Chris' Answers to Key Questions

1. **Timeline:** ✅ **APPROVED** - Proceed with accelerated plan (3-4 days)
2. **Test Framework:** ✅ **UPDATE** - Make it work without simulation dependency  
3. **Unit Tests:** ✅ **MARK AS XFAIL** - Mark EmbeddedPygameWidget tests as expected failures

---

## Implementation Plan

### **Phase 1A: Remove Deprecated Components** 
**Duration:** 1-2 days  
**Risk:** LOW (confirmed safe by Chris)

#### **Step 1A.1: Create Git Checkpoint**
```bash
git tag refactor-pre-deprecated-removal -m "Before removing deprecated GUI components"
```

#### **Step 1A.2: Remove Deprecated Files**
```bash
# Remove all confirmed deprecated components
git rm src/econsim/gui/simulation_controller.py
git rm src/econsim/gui/session_factory.py  
git rm src/econsim/gui/main_window.py
git rm src/econsim/gui/panels/controls_panel.py
git rm src/econsim/gui/panels/metrics_panel.py
git rm src/econsim/gui/panels/agent_inspector_panel.py
git rm src/econsim/gui/panels/trade_inspector_panel.py
git rm src/econsim/gui/panels/event_log_panel.py
git rm src/econsim/gui/panels/status_footer_bar.py
git rm src/econsim/gui/panels/overlays_panel.py
```

#### **Step 1A.3: Clean Up Imports**
```bash
# Remove any remaining imports of deleted components
# Update __init__.py files if needed
# Remove any references in remaining files
```

#### **Step 1A.4: Validate Removal**
```bash
# Verify no broken imports
python -m py_compile src/econsim/gui/embedded_pygame.py

# Test that simulation still works
python scripts/headless_simulation_runner.py 100
```

### **Phase 1B: Decouple EmbeddedPygameWidget**
**Duration:** 1-2 days  
**Risk:** MEDIUM (active usage requires careful decoupling)

#### **Step 1B.1: Create Git Checkpoint**
```bash
git tag refactor-pre-pygame-decouple -m "Before decoupling EmbeddedPygameWidget"
```

#### **Step 1B.2: Remove Simulation Dependency from Constructor**
**Before:**
```python
def __init__(
    self,
    parent: QWidget | None = None,
    simulation: _SimulationProto | None = None,  # REMOVE THIS
    *,
    drive_simulation: bool = True,
) -> None:
```

**After:**
```python
def __init__(
    self,
    parent: QWidget | None = None,
    *,
    drive_simulation: bool = True,
) -> None:
```

#### **Step 1B.3: Remove Simulation Stepping Logic**
**Before:**
```python
def _on_tick(self) -> None:
    if self._simulation is not None:
        # ... simulation stepping logic ...
        self._simulation.step(self._sim_rng)
```

**After:**
```python
def _on_tick(self) -> None:
    # TODO: Phase 2 - will receive simulation state via observers
    # For now, just trigger repaint of static scene
    self.update()
```

#### **Step 1B.4: Remove Simulation-Related Methods**
- Remove or stub out `_update_scene()` method
- Remove simulation state access methods
- Keep rendering infrastructure for Phase 2

### **Phase 1C: Update Test Framework**
**Duration:** 0.5 days  
**Risk:** LOW (framework already supports render-only mode)

#### **Step 1C.1: Update Launcher Test Framework**
**File:** `src/econsim/tools/launcher/framework/base_test.py`

**Before:**
```python
self.pygame_widget = EmbeddedPygameWidget(
    simulation=self.simulation,
    drive_simulation=False
)
```

**After:**
```python
self.pygame_widget = EmbeddedPygameWidget(
    drive_simulation=False
)
# TODO: Phase 2 - widget will receive simulation state via observers
```

### **Phase 1D: Mark Unit Tests as Expected Failures**
**Duration:** 0.5 days  
**Risk:** LOW (expected failures, will be fixed in Phase 2)

#### **Step 1D.1: Identify Affected Tests**
```bash
# Find all tests that use EmbeddedPygameWidget
grep -r "EmbeddedPygameWidget" tests/unit/ --include="*.py"
```

**Affected Test Files:**
- `tests/unit/test_render_smoke.py`
- `tests/unit/test_shutdown.py`
- `tests/unit/test_rng_parity_widget_controller.py`
- `tests/unit/test_perf_simulation.py`
- `tests/unit/test_embedded_widget.py`
- `tests/unit/test_widget_simulation_teardown.py`
- `tests/unit/test_fps_logging_gate.py`
- `tests/unit/test_agent_inspector_highlighting.py`

#### **Step 1D.2: Add xfail Decorators**
For each affected test, add:
```python
import pytest

@pytest.mark.xfail(reason="EmbeddedPygameWidget decoupled from simulation in Phase 1")
def test_something():
    # ... existing test code ...
```

### **Phase 1E: Final Validation**
**Duration:** 0.5 days  
**Risk:** LOW (validation only)

#### **Step 1E.1: Validate Headless Simulation**
```bash
# Test headless simulation works
python scripts/headless_simulation_runner.py 1000

# Verify performance is acceptable
time python scripts/headless_simulation_runner.py 100
```

#### **Step 1E.2: Validate Zero GUI Dependencies**
```bash
# Verify no GUI imports in simulation code
grep -r "from.*gui\|import.*gui\|PyQt\|pygame" src/econsim/simulation/ --include="*.py"
grep -r "from.*gui\|import.*gui\|PyQt\|pygame" src/econsim/preferences/ --include="*.py"
grep -r "from.*gui\|import.*gui\|PyQt\|pygame" src/econsim/observability/ --include="*.py"
```

#### **Step 1E.3: Validate Test Status**
```bash
# Run simulation tests (should pass)
pytest tests/unit/test_simulation* -v

# Run EmbeddedPygameWidget tests (should xfail)
pytest tests/unit/test_embedded* -v
pytest tests/unit/test_render_smoke.py -v
```

#### **Step 1E.4: Create Final Git Checkpoint**
```bash
git tag refactor-post-phase1 -m "Phase 1 complete: Simulation fully decoupled"
```

---

## Success Criteria

### **Technical Requirements**
- [ ] All deprecated GUI components removed
- [ ] EmbeddedPygameWidget decoupled from simulation
- [ ] Simulation runs with ZERO GUI dependencies
- [ ] Headless simulation runner functional
- [ ] Test framework updated to work without simulation dependency
- [ ] Unit tests marked as xfail where appropriate

### **Performance Requirements**
- [ ] Simulation performance maintained (no regression)
- [ ] Headless runner performance acceptable
- [ ] Memory usage stable

### **Documentation Requirements**
- [ ] All changes documented
- [ ] Git checkpoints created
- [ ] REFACTOR_STATUS.md updated
- [ ] Phase 1 completion report written

---

## Risk Mitigation

### **Removal Risks**
- **Risk:** Breaking imports in remaining files
- **Mitigation:** Clean up imports systematically, test compilation

### **Decoupling Risks**
- **Risk:** Breaking test framework functionality
- **Mitigation:** Update framework to use render-only mode, test thoroughly

### **Test Risks**
- **Risk:** xfail tests masking real issues
- **Mitigation:** Document xfail reasons clearly, plan to fix in Phase 2

---

## Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| 1A | 1-2 days | Remove deprecated components |
| 1B | 1-2 days | Decouple EmbeddedPygameWidget |
| 1C | 0.5 days | Update test framework |
| 1D | 0.5 days | Mark tests as xfail |
| 1E | 0.5 days | Final validation |

**Total:** 3-4 days (vs original 8 days)

---

## Expected Outcomes

### **After Phase 1A (Deprecated Removal):**
- ✅ All HIGH and MEDIUM severity coupling points removed
- ✅ Simulation completely independent of deprecated GUI
- ✅ Clean foundation for decoupling

### **After Phase 1B (EmbeddedPygameWidget Decoupling):**
- ✅ Widget is render-only, no simulation dependency
- ✅ Simulation stepping completely removed from GUI
- ✅ Ready for Phase 2 playback system

### **After Phase 1C-D (Test Updates):**
- ✅ Test framework works without simulation dependency
- ✅ Unit tests marked as expected failures
- ✅ No test failures masking real issues

### **After Phase 1E (Final Validation):**
- ✅ Complete simulation independence verified
- ✅ Performance maintained
- ✅ Ready for Phase 2 output architecture

---

## Git Checkpoints

```bash
refactor-pre-deprecated-removal  → Before removing deprecated components
refactor-pre-pygame-decouple     → Before decoupling EmbeddedPygameWidget  
refactor-post-phase1             → Phase 1 complete: Simulation fully decoupled
```

---

## Next Phase Preparation

After Phase 1 completion:
1. **Review Phase 2 plan** for output architecture
2. **Understand GUI rebuild** as playback consumer
3. **Prepare for SimulationRecorder** development
4. **Set up Phase 2 workspace** and documentation

---

**This accelerated plan leverages Chris' deprecation insights to achieve complete simulation independence in 3-4 days instead of 8 days!** 🚀

---

**Document Status:** Ready for execution  
**Approval:** ✅ Chris approved accelerated timeline and approach  
**Next Action:** Begin Phase 1A - Remove deprecated components
