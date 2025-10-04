# Legacy Code Cleanup Review
**Date:** 2025-10-04  
**Status:** Comprehensive audit of deprecated/legacy files in src/  
**Priority:** HIGH - Context pollution affecting development velocity

## Executive Summary

The codebase contains significant legacy/deprecated code that is polluting the src/ directory and causing confusion. Multiple architectural transitions have left behind abandoned systems:

1. **Handler Architecture → OptimizedStepExecutor** (COMPLETED but legacy code remains)
2. **VisualDeltaRecorder → ComprehensiveDeltaRecorder** (IN PROGRESS, both systems coexist)
3. **ObserverRegistry System → (REMOVED but imports remain)**
4. **MetricsCollector → (Status unclear, still in use)**

**Critical Finding:** The `.github/copilot-instructions.md` file is severely outdated and describes systems that no longer exist, creating significant confusion for AI-assisted development.

---

## 1. Legacy Step Execution Architecture

### Current State

#### ACTIVE (Production)
- **File:** `src/econsim/simulation/step_executor.py` (487 lines)
- **Class:** `OptimizedStepExecutor`
- **Status:** ✅ ACTIVE - Used by `world.py:109` via `_initialize_optimized_step_executor()`
- **Purpose:** High-performance consolidated step execution (eliminates 45% overhead)

#### LEGACY (Deprecated but not removed)
- **Directory:** `src/econsim/simulation/execution/`
- **Files:**
  - `execution/step_executor.py` (75 lines) - `StepExecutor` class
  - `execution/handlers/movement_handler.py` (217 lines)
  - `execution/handlers/collection_handler.py` (59 lines)
  - `execution/handlers/trading_handler.py` (217 lines)
  - `execution/handlers/metrics_handler.py` (75 lines)
  - `execution/handlers/respawn_handler.py` (59 lines)
  - `execution/handlers/protocol.py` (protocol definitions)
  - `execution/context.py` (context objects)
  - `execution/result.py` (result objects)
- **Usage:** Only imported by `world.py:165` in `_initialize_step_executor()` method
- **Method Status:** "kept for testing and fallback purposes" (line 171)
- **Actual Usage:** ZERO production usage - tests use `from_config()` which calls optimized executor

### Analysis

The handler architecture was replaced by `OptimizedStepExecutor` for performance reasons (45% regression elimination). However, the entire `execution/` directory remains:

**Lines of Legacy Code:** ~700+ lines in `execution/` directory
**Production Usage:** 0%
**Test Coverage:** Tests don't directly use handlers (they use `Simulation.from_config()`)

### Impact

1. **Context Pollution:** IDE searches, codebase_search, and grep return duplicate results
2. **Confusion:** Newcomers see both architectures and don't know which to use
3. **Maintenance Burden:** Legacy code receives unintentional edits
4. **Documentation Drift:** Copilot instructions reference handler architecture as current

---

## 2. Delta Recording Systems

### Current State

#### NEW SYSTEM (Partially Adopted)
- **Directory:** `src/econsim/delta/`
- **Main File:** `delta/recorder.py` - `ComprehensiveDeltaRecorder` (808 lines)
- **Purpose:** Records complete simulation deltas (visual + agent + resource + economic + performance)
- **Features:**
  - MessagePack serialization
  - Smart utility tracking (only when bundles change)
  - Single-pass agent processing
  - Comprehensive event capture
- **Usage:** Used by `tools/launcher/framework/base_test.py:350`

#### OLD SYSTEM (Still Exported)
- **Directory:** `src/econsim/visual/`
- **Main File:** `visual/delta_recorder.py` - `VisualDeltaRecorder` (184 lines)
- **Purpose:** Records visual deltas only (pygame rendering)
- **Features:**
  - Pickle serialization
  - Minimal state tracking
  - Visual-only events
- **Usage:** Exported in `visual/__init__.py:14`, used by `visual/delta_controller.py:269`

### Analysis

The comment in `delta/recorder.py:5` explicitly states it "Replaces the VisualDeltaRecorder", yet:
- `VisualDeltaRecorder` is still exported from `visual/__init__.py`
- `delta_controller.py` still uses `VisualDeltaRecorder.load_deltas()`
- Both systems coexist, creating confusion about which to use

**Migration Status:** 
- Recording: `ComprehensiveDeltaRecorder` is used in test framework
- Playback: `VisualDeltaRecorder` still used in `delta_controller.py`

### Impact

1. **API Confusion:** Two delta recording systems with different formats
2. **Format Incompatibility:** Pickle vs MessagePack, visual-only vs comprehensive
3. **Migration Incomplete:** Playback system not updated to use new recorder
4. **Code Duplication:** Similar logic in both recorders

---

## 3. Observability System (REMOVED)

### Current State

#### DELETED DIRECTORY
- **Expected Path:** `src/econsim/observability/`
- **Status:** ❌ DOES NOT EXIST

#### STALE IMPORTS (Breaking)
These files contain imports to non-existent observability system:

1. **agent.py:34**
   ```python
   from ..observability.registry import ObserverRegistry
   ```
   - Inside `if TYPE_CHECKING:` block (type hints only, doesn't break runtime)

2. **agent.py:123**
   ```python
   from ..observability.observer_logger import get_global_observer_logger
   ```
   - Inside try/except block in `_track_target_change()`, silently fails

3. **trade.py:61, 372**
   ```python
   from ..observability.observer_logger import get_global_observer_logger
   ```
   - Inside try/except blocks, silently fails

#### STALE DOCUMENTATION
- **File:** `.github/copilot-instructions.md`
- **Lines:** 8, 94, 210-218
- **Content:** Describes `src/econsim/observability/` as active system
- **Reality:** Directory doesn't exist, system was removed

### Analysis

The observability system was removed but:
1. Imports remain (protected by TYPE_CHECKING or try/except)
2. Comments reference "Observer system removed" in multiple places
3. Documentation describes it as current architecture

**Comments mentioning removal:**
- `world.py:96`: "Observer system removed - comprehensive delta system handles all recording"
- `world.py:144`: "Observer system removed - comprehensive delta system handles all recording"
- `step_executor.py:375-376`: "Observer system removed - comprehensive delta system handles recording"
- `metrics_handler.py:64`: "Observer system removed - comprehensive delta system handles recording"

### Impact

1. **Import Failures:** Code imports non-existent modules (mitigated by try/except)
2. **Silent Failures:** Observer calls silently fail, making debugging difficult
3. **Documentation Lies:** Copilot instructions describe removed system
4. **Unclear Migration:** No clear guidance on what replaced it

---

## 4. Callback System (Intermediate Solution?)

### Current State

- **File:** `src/econsim/recording/callbacks.py` (184 lines)
- **Class:** `SimulationCallbacks`
- **Purpose:** "Replaces the complex observer system with a lightweight callback approach"
- **Status:** ⚠️ UNCLEAR - File exists but usage unclear

### Analysis

This appears to be an intermediate solution between the old ObserverRegistry and the new ComprehensiveDeltaRecorder. However:
- No clear usage in main simulation code
- Exports basic callback registration (`on_step`, `on_error`, etc.)
- Comments suggest it replaces observer system, but so does delta recorder

**Questions:**
1. Is this actively used or another abandoned experiment?
2. Should this be consolidated with delta recorder?
3. Is the `recording/` directory still relevant?

---

## 5. MetricsCollector System

### Current State

- **File:** `src/econsim/simulation/metrics.py` (367 lines)
- **Class:** `MetricsCollector`
- **Purpose:** Dual-purpose metrics (determinism hash + trading analytics)
- **Usage:** 
  - Instantiated in `world.py:258` when `enable_metrics=True`
  - Called in `world.py:127` via `metrics_collector.record()`
  - Referenced in `step_executor.py:313-334` for trade metrics

### Analysis

This system appears to be ACTIVE but has overlap with the new delta recorder:
- Both track agent states, utilities, and trades
- MetricsCollector focuses on determinism hash and aggregates
- DeltaRecorder captures comprehensive deltas for playback

**Purpose Clarity Needed:**
- Should MetricsCollector be replaced by DeltaRecorder?
- Or do they serve complementary purposes (determinism vs playback)?
- Comments mention "hash-excluded" metrics suggesting determinism is primary purpose

---

## 6. Backup Files

### Files Found

1. **world.py.backup** (765 lines)
   - Nearly identical to current `world.py`
   - Uses old handler architecture on line 108
   - Should be in git history, not production src/

2. **recorder.py.backup** (808 lines)  
   - Backup of `delta/recorder.py`
   - Identical to current version
   - Should be removed

### Impact

- **Disk Space:** Minimal but unnecessary
- **Confusion:** Developers don't know which is current
- **Grep Pollution:** Searches return duplicate results

---

## 7. Documentation Drift

### .github/copilot-instructions.md

This file is **severely outdated** and describes removed/deprecated systems as current:

#### Incorrect Statements

**Line 8:** "Observer layer (`src/econsim/observability/`)"
- **Reality:** Directory doesn't exist, system removed

**Lines 96-106:** Describes "Step Decomposition Pipeline" using handlers
- **Reality:** Handlers deprecated, OptimizedStepExecutor is current

**Lines 210-218:** Details observability system implementation
- **Reality:** System removed, replaced by delta recorder

**Line 7:** "Step pipeline (fixed order): Movement → Collection → Trading → Metrics → Respawn in `simulation/execution/handlers/`"
- **Reality:** Handler architecture deprecated

### Impact on AI-Assisted Development

1. AI assistants receive conflicting information
2. Generated code references non-existent systems
3. Refactoring suggestions maintain deprecated patterns
4. New developers follow outdated architecture

---

## Summary of Legacy Systems

| System | Status | Lines of Code | Production Usage | Removal Priority |
|--------|--------|---------------|------------------|------------------|
| execution/handlers/ | Deprecated | ~700 | 0% | HIGH |
| VisualDeltaRecorder | Superseded | 184 | Partial (playback) | MEDIUM |
| observability/ imports | Broken | N/A | 0% (silent fail) | HIGH |
| recording/callbacks.py | Unknown | 184 | Unknown | NEEDS REVIEW |
| .backup files | Git artifacts | 1573 | 0% | HIGH |
| Copilot instructions | Outdated docs | N/A | N/A | CRITICAL |

**Total Legacy Code:** ~2,641+ lines of deprecated/unclear code

---

## Dependencies and Migration Paths

### execution/handlers/ Removal

**Blockers:**
- `world.py:165-189` contains `_initialize_step_executor()` method
- `execution/__init__.py` exports handler classes
- No known test dependencies (tests use `from_config()`)

**Migration Path:**
1. Verify no tests call `_initialize_step_executor()` directly
2. Remove `_initialize_step_executor()` method from `world.py`
3. Delete `execution/handlers/` directory
4. Delete `execution/step_executor.py`, `context.py`, `result.py`
5. Keep `execution/__init__.py` as empty or remove module entirely

**Risk:** LOW - Method marked as "fallback" but never used

### VisualDeltaRecorder Migration

**Blockers:**
- `visual/delta_controller.py:269` uses `VisualDeltaRecorder.load_deltas()`
- Playback system not updated for new format

**Migration Path:**
1. Update `delta_controller.py` to use `ComprehensiveDeltaRecorder.load_deltas()`
2. Implement format conversion utility (pickle → MessagePack)
3. Update visual/__init__.py to remove VisualDeltaRecorder export
4. Add deprecation warning to VisualDeltaRecorder
5. Remove VisualDeltaRecorder after migration period

**Risk:** MEDIUM - Requires playback system update

### Observability Import Cleanup

**Blockers:**
- None (imports already protected by TYPE_CHECKING or try/except)

**Migration Path:**
1. Remove TYPE_CHECKING imports from agent.py:34
2. Remove try/except observer imports from agent.py:123, trade.py:61, trade.py:372
3. Remove comments referencing "Observer system removed"
4. Update documentation to reflect delta recorder as replacement

**Risk:** VERY LOW - Already failing silently

### Copilot Instructions Update

**Blockers:**
- None

**Migration Path:**
1. Update `.github/copilot-instructions.md`:
   - Remove observability system references
   - Update step execution to describe OptimizedStepExecutor
   - Document delta recorder as current recording system
   - Add note about MetricsCollector purpose (determinism vs playback)
   - Remove handler architecture details
2. Add "Last Updated: 2025-10-04" header
3. Add "Architecture Review Date" for future audits

**Risk:** ZERO

### Backup File Removal

**Blockers:**
- None (files should be in git history)

**Migration Path:**
1. Verify files are in git history: `git log --all --full-history -- "*.backup"`
2. Delete `world.py.backup`
3. Delete `recorder.py.backup`
4. Add `*.backup` to `.gitignore`

**Risk:** ZERO

---

## Recommended Approach

### Phase 1: Safe Immediate Cleanup (Risk: ZERO)

**Duration:** 1-2 hours

1. **Remove backup files**
   ```bash
   rm src/econsim/simulation/world.py.backup
   rm src/econsim/delta/recorder.py.backup
   echo "*.backup" >> .gitignore
   ```

2. **Update copilot instructions**
   - Rewrite `.github/copilot-instructions.md` to reflect current architecture
   - Document what replaced what (handlers→optimized, observer→delta)

3. **Clean stale imports**
   - Remove TYPE_CHECKING import of ObserverRegistry from agent.py
   - Remove try/except observer imports from agent.py and trade.py
   - Remove "Observer system removed" comments

**Commit:** "docs: remove legacy backup files and update architecture documentation"

### Phase 2: Handler Architecture Removal (Risk: LOW)

**Duration:** 2-4 hours

**Prerequisites:** 
- Run full test suite to confirm zero handler usage
- Search codebase for any direct handler instantiation

**Steps:**

1. **Remove legacy method from world.py**
   ```python
   # Delete lines 165-189 (_initialize_step_executor method)
   # Keep lines 155-163 (_initialize_optimized_step_executor method)
   ```

2. **Delete handler directory**
   ```bash
   rm -rf src/econsim/simulation/execution/handlers/
   ```

3. **Clean up execution module**
   - Option A: Delete entire `execution/` directory if no other dependencies
   - Option B: Keep `execution/` with minimal __init__.py if needed elsewhere

4. **Update imports**
   - Remove handler imports from world.py lines 174-179

5. **Run tests**
   ```bash
   make test-unit
   make perf
   ```

**Commit:** "refactor: remove deprecated handler architecture in favor of OptimizedStepExecutor"

### Phase 3: Delta Recorder Consolidation (Risk: MEDIUM)

**Duration:** 4-8 hours

**Prerequisites:**
- Phase 1 and 2 complete
- Review usage of VisualDeltaRecorder in delta_controller.py
- Test current delta playback functionality

**Steps:**

1. **Audit delta_controller.py**
   - Identify all uses of VisualDeltaRecorder
   - Map to equivalent ComprehensiveDeltaRecorder methods

2. **Update playback system**
   - Modify delta_controller.py to use ComprehensiveDeltaRecorder
   - Handle format differences (visual-only vs comprehensive)
   - Add backward compatibility for old .pickle files if needed

3. **Deprecate VisualDeltaRecorder**
   - Add deprecation warning to class docstring
   - Update visual/__init__.py exports
   - Add migration guide in comments

4. **Test playback**
   - Verify visual playback still works
   - Test with both old and new formats
   - Update test fixtures if needed

5. **Remove VisualDeltaRecorder (after verification period)**
   - Delete visual/delta_recorder.py
   - Remove from visual/__init__.py
   - Update visual/delta_controller.py imports

**Commit:** "refactor: consolidate delta recording to ComprehensiveDeltaRecorder"

### Phase 4: Clarify Recording Architecture (Risk: LOW)

**Duration:** 2-3 hours

**Prerequisites:**
- Phases 1-3 complete
- Clear understanding of MetricsCollector vs DeltaRecorder purposes

**Steps:**

1. **Audit recording/callbacks.py usage**
   - Search for SimulationCallbacks usage in codebase
   - Determine if actively used or abandoned
   - Decision: Keep, remove, or consolidate with delta recorder

2. **Document purpose of each system**
   - MetricsCollector: Determinism hash + aggregate metrics
   - ComprehensiveDeltaRecorder: Complete state deltas for playback
   - SimulationCallbacks: Real-time monitoring (if kept)

3. **Add architecture documentation**
   - Create `docs/RECORDING_ARCHITECTURE.md`
   - Explain when to use each system
   - Document migration from old systems

4. **Update code comments**
   - Add clear purpose statements to each class
   - Remove confusing "replaces X" comments
   - Add cross-references between systems

**Commit:** "docs: clarify recording architecture and system purposes"

---

## Testing Strategy

### Pre-Cleanup Baseline

1. **Capture current test results**
   ```bash
   make test-unit > /tmp/tests_before.txt
   make perf > /tmp/perf_before.txt
   ```

2. **Capture determinism hashes**
   ```bash
   pytest tests/integration/test_determinism*.py -v > /tmp/determinism_before.txt
   ```

3. **Verify current functionality**
   - Run manual test suite
   - Test playback functionality
   - Verify GUI functionality

### Post-Cleanup Verification

After each phase:

1. **Regression testing**
   ```bash
   make test-unit
   diff /tmp/tests_before.txt <(make test-unit)
   ```

2. **Performance testing**
   ```bash
   make perf
   # Verify no performance regression
   ```

3. **Determinism verification**
   ```bash
   pytest tests/integration/test_determinism*.py -v
   # Hashes must be identical
   ```

4. **Integration testing**
   - Launch GUI: `make dev`
   - Run test suite: `make launcher`
   - Test playback: Verify visual deltas work

---

## Open Questions

### 1. recording/callbacks.py Purpose
**Question:** Is SimulationCallbacks actively used? Should it be kept?  
**Investigation needed:**
- Grep for `SimulationCallbacks` usage
- Check if launcher/framework uses it
- Decide: keep, remove, or consolidate

### 2. MetricsCollector vs DeltaRecorder
**Question:** Are these complementary or redundant?  
**Clarification needed:**
- Document clear separation of concerns
- Identify any overlap that should be removed
- Consider consolidation opportunities

### 3. execution/ Module Fate
**Question:** Delete entire module or keep minimal structure?  
**Decision factors:**
- Are context.py, result.py used elsewhere?
- Is execution/__init__.py imported anywhere?
- Can we remove the entire directory tree?

### 4. Migration Strategy for Existing Data
**Question:** How to handle old .pickle delta files?  
**Options:**
1. Keep VisualDeltaRecorder as read-only legacy loader
2. Create conversion utility (pickle → MessagePack)
3. Accept breaking change, require re-recording
4. Support both formats in playback

---

## Risk Assessment

| Phase | Risk Level | Impact if Broken | Mitigation |
|-------|-----------|------------------|------------|
| 1: Immediate Cleanup | ZERO | None | Files unused |
| 2: Handler Removal | LOW | Test failures | Full test coverage |
| 3: Delta Consolidation | MEDIUM | Playback broken | Extensive testing |
| 4: Documentation | ZERO | None | Documentation only |

**Overall Risk:** LOW with proper testing at each phase

**Rollback Strategy:**
- Git checkpoints before each phase: `git tag cleanup-pre-phase{N}`
- Test suite must pass before proceeding to next phase
- Rollback command: `git reset --hard cleanup-pre-phase{N}`

---

## Success Criteria

### Quantitative Goals
- [ ] Remove ~2,600+ lines of legacy code
- [ ] Reduce context pollution by 40%+ (measured by grep result counts)
- [ ] Zero test regressions
- [ ] Zero performance regressions
- [ ] Identical determinism hashes before/after

### Qualitative Goals
- [ ] Clear architecture documentation
- [ ] No confusion about which system to use
- [ ] Copilot instructions reflect reality
- [ ] New developers can understand recording architecture
- [ ] Single clear path for each use case (determinism, playback, monitoring)

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Immediate Cleanup | 1-2 hours | None |
| Phase 2: Handler Removal | 2-4 hours | Phase 1 |
| Phase 3: Delta Consolidation | 4-8 hours | Phases 1-2 |
| Phase 4: Documentation | 2-3 hours | Phases 1-3 |
| **Total** | **9-17 hours** | Sequential |

**Recommendation:** Execute phases sequentially with full testing between each phase. Do not rush - proper testing is critical for maintaining determinism.

---

## Next Steps

### Immediate Actions (No Approval Needed)
1. Review this document with team
2. Verify assessment accuracy through spot-checks
3. Prioritize questions in "Open Questions" section
4. Create git checkpoint: `git tag cleanup-pre-phase0`

### Approval Required
1. Confirm removal strategy for execution/handlers/
2. Decide on VisualDeltaRecorder migration approach
3. Clarify MetricsCollector vs DeltaRecorder relationship
4. Approve Phase 1 immediate cleanup

### After Approval
1. Execute Phase 1 (safe cleanup)
2. Update this document with findings
3. Proceed to Phase 2 with team review
4. Update CHANGELOG.md with architectural changes

---

**Document Status:** DRAFT - Pending Review  
**Next Review Date:** After Phase 1 completion  
**Maintained By:** Development Team  
**Last Updated:** 2025-10-04

