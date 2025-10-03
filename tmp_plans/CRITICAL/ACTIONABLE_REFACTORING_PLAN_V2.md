# VMT EconSim: Actionable Refactoring Implementation Plan

**Date:** October 3, 2025  
**Status:** Execution Blueprint - Final Decisions Made  
**Version:** 2.0 (Clean Architecture Edition)  
**Parent Document:** REFACTORING_TECHNICAL_DEBT_REPORT.md  
**Decisions Summary:** REFACTORING_DECISIONS_SUMMARY.md

---

## Executive Summary

This document transforms the high-level refactoring plan into concrete, actionable tasks with explicit dependencies, success criteria, and risk mitigation strategies. Each phase is broken down into granular steps that can be executed, tested, and validated independently.

**Architecture-First Approach:** All critical gaps have been addressed with final decisions prioritizing clean architecture over backward compatibility. The refactor will:
- **Clean observer system FIRST** (Phase 0) before building output architecture on top
- **Aggressively decouple GUI/simulation** with no backward compatibility shims (Phase 1)
- **Accept temporary breakage** during refactor with git checkpoints for rollback
- **Invalidate all existing saved outputs** to enable rapid iteration

**Key Insight:** Building the output system on a clean observer foundation and decoupled simulation core is worth short-term disruption for long-term maintainability.

**Critical Decision:** No backward compatibility, no feature flags, no parallel systems. Clean implementation with git checkpoints for safety.

---

## Table of Contents

1. [Critical Gaps - Final Decisions](#critical-gaps-in-original-plan)
2. [Phase 0: Observer System Cleanup](#phase-0-observer-system-cleanup)
3. [Phase 1: Coupling Analysis & Clean Decoupling](#phase-1-coupling-analysis--clean-decoupling)
4. [Phase 2: Simulation Output Architecture](#phase-2-simulation-output-architecture)
5. [Phase 3: Test Suite Cleanup](#phase-3-test-suite-cleanup)
6. [Phase 4: MANUAL_TESTS Consolidation](#phase-4-manual_tests-consolidation)
7. [Phase 5: Preference Type Extension Improvements](#phase-5-preference-type-extension-improvements)
8. [Phase 6: Extension Point Documentation](#phase-6-extension-point-documentation)
9. [Execution Strategy](#execution-strategy)
10. [Risk Register](#risk-register)
11. [Success Criteria](#success-criteria)

---

## Critical Gaps in Original Plan

> **All Outstanding Gaps: Final Decisions and Resolutions**  
> All previously open architectural and process gaps have been reviewed and explicit, final decisions have been made. See REFACTORING_DECISIONS_SUMMARY.md for complete rationale.

---

### Gap 1: Underestimated GUI/Simulation Coupling Depth ⚠️  
**[FINAL DECISION: Full Coupling Audit, Then Clean Decoupling—No Adapters, No Backward Compatibility]**

**Summary of Issue:**  
The original plan underestimated the depth of coupling between the simulation core and the GUI (e.g., event loop, state, observer lifecycle, rendering logic).

**Final Resolution:**  
- **Step 1:** Conduct comprehensive audit of all simulation/GUI coupling points
- **Step 2:** Refactor simulation core to remove ALL GUI dependencies
- **No intermediate adapter layers or backward compatibility**
- **GUI breakage is acceptable and expected during refactor**
- **All changes managed via git checkpoints**

**Rationale:**  
Clean, maintainable architecture is the top priority, even at the cost of breaking existing integrations during the refactor.

---

### Gap 2: No Migration Strategy for Existing Saved Outputs ⚠️  
**[FINAL DECISION: No Backward Compatibility for Saved Outputs—All Old Runs Invalidated]**

**Summary of Issue:**  
The plan did not address migration or compatibility for existing simulation output files.

**Final Resolution:**  
- **All output schema changes made without regard for backward compatibility**
- **No migration or loading of old output files**
- **All saved runs from previous versions will be invalidated**

**Rationale:**  
Enables rapid iteration and keeps codebase simple. Loss of historical data is acceptable at this stage.

---

### Gap 3: PlaybackEngine Performance Unvalidated ⚠️  
**[FINAL DECISION: Prototype and Benchmark Playback Before Full Implementation]**

**Summary of Issue:**  
Playback performance (load times, memory, seek responsiveness) for large simulations is unproven.

**Final Resolution:**  
- **Step 2.1 is now mandatory gate:** Create prototype and benchmark before proceeding
- **If benchmarks fail:** Adjust architecture before full implementation
- **Performance requirements documented in Phase 2**

**Rationale:**  
Performance must be validated early to avoid wasted effort.

---

### Gap 4: Test Suite Cleanup Scope Unclear ⚠️  
**[FINAL DECISION: Single Steward Review with Quarantine Workflow]**

**Summary of Issue:**  
The scope and process for test suite cleanup was ambiguous.

**Final Resolution:**  
- **Single steward (Chris) personally reviews all tests**
- **Uncertain tests moved to `tests/QUARANTINE/` for async decision**
- **Weekly quarantine review, 2-week max quarantine period**
- **Default: KEEP if still uncertain after quarantine**
- **All decisions documented in `QUARANTINE_NOTES.md`**

**Rationale:**  
Ensures consistency while providing workflow for uncertain decisions.

---

### Gap 5: No Rollback Strategy 🚨  
**[FINAL DECISION: Git Checkpoint Strategy]**

**Summary of Issue:**  
The original plan lacked rollback mechanism.

**Final Resolution:**  
- **Before each phase:** Create tag `refactor-pre-phase{N}`
- **After each phase:** Create tag `refactor-post-phase{N}` when stable
- **Rollback procedure:** `git checkout refactor-post-phase{N-1}`
- **All checkpoints documented in CHANGELOG.md**

**Rationale:**  
Simple, reliable safety net during major changes.

---

### Gap 6: Observer System Cleanup Timing 🧹  
**[FINAL DECISION: Observer Cleanup Moved to Phase 0—Before Everything Else]**

**Summary of Issue:**  
Observer cleanup was scheduled late, risking rework if output architecture built on "dirty" foundation.

**Final Resolution:**  
- **Observer cleanup is now Phase 0** (first thing to do)
- **Phase 2 (Output Architecture) depends on clean observer system**
- **FileObserver must be production-ready before Phase 2 begins**

**Rationale:**  
Building output system on clean foundation prevents rework and technical debt.

---

## Phase 0: Observer System Cleanup

**Goal:** Clean and formalize observer system BEFORE building output architecture on top of it.

**Duration:** 1-2 weeks  
**Priority:** P0 (must complete before Phase 2)  
**Prerequisites:** None (this is the first phase)

**Rationale:** Per Gap 6 decision, observer cleanup must happen first to avoid rework.

**Git Checkpoints:**
- Tag `refactor-pre-phase0` before starting
- Tag `refactor-post-phase0` when complete and stable

**Breaking Changes:**
- None expected (cleanup only, no API changes)

**Rollback:**
If critical issues: `git checkout main` (no prior phase to revert to)

---

### Step 0.1: Observer System Audit

**Task:** Systematically review all observer-related code.

**Actionable Steps:**

1. **List all observer files:**
   ```bash
   find src/econsim/observability/ -name "*.py"
   ```

2. **For each file, document:**
   - Purpose and responsibility
   - Current status (active, deprecated, legacy)
   - Dependencies (what uses it?)
   - Issues (TODOs, FIXMEs, "deprecated" comments)

3. **Create observer map in:**
   `tmp_plans/CURRENT/CRITICAL/OBSERVER_SYSTEM_AUDIT.md`

**Success Criteria:**
- [ ] All observer files documented
- [ ] Status clarity for each component
- [ ] Issues identified
- [ ] Removal candidates flagged

**Duration:** 1-2 days

---

### Step 0.2: Remove Deprecated Components

**Task:** Clean up observer system of dead code.

**Actionable Steps:**

1. **Confirm GUILogger removal:**
   ```bash
   grep -r "GUILogger" src/
   grep -r "gui_logger" src/
   ```
   If found, remove all references

2. **Resolve GUIObserver status:**
   - If truly deprecated → remove it
   - If still needed → remove "deprecated" comments, document why
   - If partially needed → extract useful parts, remove rest

3. **Clean up legacy event classes:**
   - Remove unused event definitions
   - Document what remains and why

4. **Remove obsolete observer types:**
   - Consolidate duplicate functionality if found

**Success Criteria:**
- [ ] No "deprecated" comments in observer code
- [ ] All imports updated
- [ ] Tests still pass
- [ ] No dead code

**Duration:** 2-3 days

---

### Step 0.3: Formalize Event Schema

**Task:** Create official event schema documentation.

**Actionable Steps:**

1. **Audit FileObserver events:**
   ```bash
   grep -r "record_" src/econsim/observability/
   ```

2. **Document complete schema:**
   - All event types and their fields
   - Required vs optional fields
   - Data types for each field
   - When each event is emitted

3. **Create schema file:**
   `src/econsim/observability/event_schema.py`
   
   ```python
   """Official event schema for VMT EconSim observability.
   
   Schema Version: 1.0.0
   """
   
   SCHEMA_VERSION = "1.0.0"
   
   # Document all event types
   EVENT_TYPES = {
       "agent_move": {
           "step": int,
           "agent_id": int,
           "from_pos": tuple[int, int],
           "to_pos": tuple[int, int],
           "mode": str
       },
       # ... etc
   }
   ```

4. **Note on versioning:**
   - Schema versioning will be added post-refactor
   - During refactor, schema can change freely
   - Focus: Get schema right, document clearly

**Success Criteria:**
- [ ] All event types documented
- [ ] Schema file created
- [ ] Examples provided
- [ ] Ready for use in Phase 2

**Duration:** 2-3 days

---

### Step 0.4: Consolidate Observer Responsibilities

**Task:** Ensure FileObserver is production-ready.

**Actionable Steps:**

1. **Create test suite:**
   ```python
   # tests/observability/test_file_observer.py
   
   def test_file_observer_records_events():
       """Test that FileObserver captures all events."""
       pass
   
   def test_file_observer_output_format():
       """Test output format matches schema."""
       pass
   
   def test_file_observer_handles_errors():
       """Test graceful error handling."""
       pass
   ```

2. **Run FileObserver in real simulation:**
   - Capture 1000 steps of simulation
   - Verify all events captured
   - Check file format validity

3. **Document any issues:**
   - File format problems
   - Missing events
   - Performance concerns

**Success Criteria:**
- [ ] FileObserver test suite passes
- [ ] Real simulation test successful
- [ ] Output format validated
- [ ] Performance acceptable (<0.01ms/event)

**Duration:** 2 days

---

### Step 0.5: Observer Documentation

**Task:** Document observer system for Phase 2 developers.

**Actionable Steps:**

1. **Create observer guide:**
   `docs/OBSERVABILITY_GUIDE.md`
   - How observer system works
   - When to use each observer
   - How to attach observers
   - Event schema reference

2. **Update code comments:**
   - Remove confusing legacy comments
   - Add clear docstrings
   - Document observer lifecycle

**Success Criteria:**
- [ ] Observer guide complete
- [ ] Code comments clear
- [ ] Examples provided
- [ ] Ready for Phase 2 use

**Duration:** 1-2 days

---

### Phase 0 Exit Criteria

Before proceeding to Phase 1:
- [ ] All deprecated components removed or documented
- [ ] Event schema formalized and documented
- [ ] FileObserver tested and production-ready
- [ ] No confusing "deprecated" comments remain
- [ ] All observer tests pass
- [ ] Documentation complete
- [ ] Git checkpoint `refactor-post-phase0` created

**Estimated Duration:** 1-2 weeks  
**Risk Level:** Low (cleanup only, no breaking changes)

---

## Phase 1: Coupling Analysis & Clean Decoupling

**Goal:** Systematically identify and eliminate ALL GUI/Simulation coupling, producing a pure headless simulation core.

**Duration:** 1 week  
**Priority:** P0 (must complete before Phase 2)  
**Prerequisites:** Phase 0 complete

**Approach:** Aggressive decoupling with NO backward compatibility. GUI WILL break temporarily—this is acceptable and expected.

**Git Checkpoints:**
- Tag `refactor-pre-phase1` before starting (MANDATORY)
- Tag `refactor-post-phase1` when complete

**Breaking Changes:**
- **GUI will be non-functional after this phase**
- **All GUI-specific code removed from simulation/**
- **Phase 2 will rebuild GUI integration cleanly**

**Rollback:**
If critical issues: `git checkout refactor-post-phase0`

---

### Step 1.1: GUI → Simulation Dependency Mapping

**Task:** Identify every place GUI code calls simulation code.

**Actionable Steps:**

1. **Grep for imports:**
   ```bash
   cd src/econsim
   grep -r "from.*simulation" gui/
   grep -r "import.*simulation" gui/
   ```

2. **Create dependency graph:**
   - `gui/main_gui.py` → which simulation modules?
   - `gui/embedded_pygame_widget.py` → which simulation modules?
   - `gui/simulation_controller.py` → which simulation modules?

3. **Categorize dependencies:**
   - **Control flow** (GUI drives simulation stepping)
   - **State queries** (GUI reads simulation state for rendering)
   - **Configuration** (GUI constructs simulation objects)
   - **Callbacks** (GUI registers callbacks with simulation)

4. **Document in:**
   `tmp_plans/CURRENT/CRITICAL/GUI_SIMULATION_COUPLING_MAP.md`

**Success Criteria:**
- [ ] All imports documented
- [ ] Each import categorized by type
- [ ] Call graph created
- [ ] Dependency map complete

**Duration:** 1 day

---

### Step 1.2: Simulation → GUI Dependency Audit

**Task:** Identify reverse dependencies (simulation importing or depending on GUI).

**Actionable Steps:**

1. **Grep for GUI imports in simulation code:**
   ```bash
   cd src/econsim/simulation
   grep -r "from.*gui" .
   grep -r "import.*gui" .
   grep -r "PyQt" .
   grep -r "pygame" .
   ```

2. **Search for GUI-specific state:**
   - Search for `_last_trade_highlight` and similar
   - Look for comments mentioning "GUI", "display", "visualization"
   - Check for GUI-specific methods in simulation classes

3. **Categorize reverse dependencies:**
   - **Hard dependencies** (simulation imports GUI)
   - **Soft dependencies** (simulation has GUI-specific state)
   - **Implicit dependencies** (simulation assumes GUI will call methods)

4. **For each dependency:**
   - Design removal strategy
   - **No shims, no adapters, no compatibility layers**
   - Document expected impact

**Success Criteria:**
- [ ] All reverse dependencies documented
- [ ] Severity assessed (hard/soft/implicit)
- [ ] Removal strategy outlined for each
- [ ] Expected breakage documented

**Duration:** 1 day

---

### Step 1.3: Observer System as Acceptable Coupling

**Task:** Confirm observer system is the ONLY acceptable coupling.

**Actionable Steps:**

1. **Document observer initialization flow:**
   - Where are observers created?
   - Who registers observers with simulation?
   - Can simulation run with zero observers?

2. **Test headless simulation feasibility:**
   ```python
   # scripts/test_headless_basic.py
   from econsim.simulation import Simulation
   
   # Try running without ANY GUI imports
   sim = Simulation(...)
   for step in range(100):
       sim.step()
   print("Success: Headless simulation works")
   ```

3. **Decision:**
   - Observer registry is acceptable coupling
   - Simulation emits events, consumers attach observers
   - **All other coupling must be eliminated**

**Success Criteria:**
- [ ] Observer coupling policy documented
- [ ] Headless simulation test runs (or failure points identified)
- [ ] Decision recorded: observers = only acceptable coupling

**Duration:** 1 day

---

### Step 1.4: Aggressive Decoupling Execution

**Task:** Execute removal of ALL GUI dependencies from simulation.

**Git Checkpoint:** Create `refactor-pre-decouple` tag BEFORE this step

**Actionable Steps:**

1. **Remove all GUI imports from simulation/:**
   ```bash
   # Remove every PyQt, pygame, gui import found in Step 1.2
   ```

2. **Remove GUI-specific state variables:**
   - Delete `_last_trade_highlight`
   - Delete any display-related state
   - Delete GUI callback storage

3. **Remove GUI-specific methods:**
   - Remove rendering helpers
   - Remove GUI event handlers
   - Keep only core simulation logic

4. **QTimer replacement:**
   - Simulation has internal step loop OR
   - External runner calls `simulation.step()` repeatedly
   - No GUI event loop dependencies

5. **Rendering logic:**
   - Move ALL rendering to GUI layer
   - Simulation knows nothing about display
   - State queries via observer events only

6. **Configuration:**
   - GUI creates config objects
   - Simulation receives config, no GUI awareness
   - No GUI-specific config handling in simulation

**Expected Outcome:**
- **GUI WILL BREAK** - this is OK
- Simulation is pure, headless
- Will be fixed in Phase 2

**Success Criteria:**
- [ ] All GUI imports removed from simulation/
- [ ] All GUI-specific state removed
- [ ] All GUI-specific methods removed
- [ ] Simulation tests still pass (non-GUI tests)

**Duration:** 2-3 days

---

### Step 1.5: Headless Simulation Runner

**Task:** Build runner that proves simulation is truly headless.

**Actionable Steps:**

1. **Create runner:**
   ```python
   # src/econsim/simulation/runner.py
   """Headless simulation runner with zero GUI dependencies."""
   
   class SimulationRunner:
       def __init__(self, config):
           self.simulation = Simulation.from_config(config)
       
       def run(self, max_steps):
           """Run simulation to completion."""
           for step in range(max_steps):
               self.simulation.step()
           return self.simulation.get_final_state()
   ```

2. **Create test script:**
   ```python
   # scripts/test_headless_runner.py
   from econsim.simulation.runner import SimulationRunner
   from econsim.tools.launcher.framework.test_configuration import get_test_by_name
   
   config = get_test_by_name("basic_foraging")
   runner = SimulationRunner(config)
   result = runner.run(max_steps=100)
   print(f"✓ Completed {result.final_step} steps headless")
   ```

3. **Run and validate:**
   ```bash
   python scripts/test_headless_runner.py
   ```

4. **Verify zero GUI dependencies:**
   ```bash
   grep -r "PyQt\|pygame\|gui" src/econsim/simulation/runner.py
   # Should return NOTHING
   ```

**Success Criteria:**
- [ ] Headless runner executes basic simulation
- [ ] No GUI imports in runner or simulation code
- [ ] Test script completes successfully
- [ ] Performance comparable to previous execution

**Duration:** 1-2 days

---

### Step 1.6: Validation

**Task:** Prove decoupling is complete.

**Actionable Steps:**

1. **Comprehensive grep check:**
   ```bash
   # This MUST return NOTHING:
   grep -r "PyQt\|pygame\|gui" src/econsim/simulation/
   ```

2. **Test headless runner with all configurations:**
   - basic_foraging
   - basic_trading
   - multiple_agents
   - etc.

3. **Verify simulation tests pass:**
   ```bash
   pytest tests/simulation/
   ```

4. **Verify observer system still works:**
   - Attach FileObserver to headless simulation
   - Verify events captured correctly

5. **Document remaining GUI breakage:**
   - List what doesn't work
   - Confirm it's all in gui/ directory
   - Confirm simulation/ is clean

**Success Criteria:**
- [ ] `grep -r "PyQt\|pygame\|gui" src/econsim/simulation/` returns NOTHING
- [ ] Headless runner works for all test configurations
- [ ] Simulation tests pass without GUI
- [ ] Observer system still functional
- [ ] No GUI-specific logic in simulation
- [ ] Breakage documented and contained to gui/

**Duration:** 1 day

**Git Checkpoint:** Create `refactor-post-phase1` tag when complete

---

### Phase 1 Exit Criteria

Before proceeding to Phase 2:
- [ ] Headless simulation runs successfully
- [ ] Zero GUI dependencies in simulation/
- [ ] All simulation tests pass (non-GUI)
- [ ] Observer system functional
- [ ] Coupling map document complete
- [ ] GUI breakage documented (expected)
- [ ] Git checkpoint `refactor-post-phase1` created

**Estimated Duration:** 1 week  
**Risk Level:** High (intentional breaking changes)  
**Rollback:** `git checkout refactor-post-phase0` if needed

---

## Phase 2: Simulation Output Architecture

**Goal:** Build complete output recording and playback system on clean simulation core.

**Duration:** 3-4 weeks  
**Priority:** P0  
**Prerequisites:** Phase 0 AND Phase 1 complete

**Approach:** Clean implementation, single code path. No backward compatibility, no feature flags. Schema can change freely during development.

**Git Checkpoints:**
- Tag `refactor-pre-phase2` before starting
- Tag `refactor-post-phase2` when complete

**Breaking Changes:**
- All existing saved outputs will be invalidated
- Output schema will change during development
- GUI will be rebuilt to use playback system

**Rollback:**
If critical issues: `git checkout refactor-post-phase1`

---

### Step 2.1: Performance Prototype (MANDATORY GATE)

**Task:** Validate playback performance BEFORE building full system.

**This step is a MANDATORY GATE. If benchmarks fail, STOP and adjust architecture.**

**Actionable Steps:**

1. **Create test simulation output:**
   ```python
   # scripts/generate_test_output.py
   # Run 1000-step simulation with 20 agents
   # Save events to JSONL using FileObserver
   # Measure file size and write time
   ```

2. **Build minimal playback loader:**
   ```python
   # scripts/test_playback_loader.py
   class SimplePlaybackEngine:
       def load_output(self, filepath):
           # Load JSONL, build state snapshots
           pass
       
       def seek_to_step(self, step_number):
           # Reconstruct state at step N
           pass
   ```

3. **Benchmark key metrics:**
   - File size for 1000-step simulation with 20 agents
   - Load time from disk
   - Memory footprint of loaded data
   - Time to seek to arbitrary step (worst case: step 999)
   - Time to reconstruct full state from events

4. **Acceptance criteria:**
   - File size: <10MB per 1000 steps (JSONL) or <5MB (MessagePack)
   - Load time: <2 seconds for typical simulation
   - Seek time: <200ms for worst-case step
   - Memory usage: <500MB for typical simulation

5. **If benchmarks FAIL:**
   - Consider more frequent snapshots
   - Consider compression (MessagePack, gzip)
   - Consider alternative storage format
   - **DO NOT proceed to Step 2.2 until performance acceptable**

**Deliverable:** `tmp_plans/CURRENT/CRITICAL/PLAYBACK_PERFORMANCE_BENCHMARK.md`

**Success Criteria:**
- [ ] All benchmarks meet acceptance criteria
- [ ] Performance model validated
- [ ] Any adjustments documented
- [ ] Green light to proceed

**Duration:** 2-3 days  
**Risk:** Medium (might need approach changes)

---

### Step 2.2: Output Schema Design

**Task:** Define complete event schema for recording.

**Note:** No versioning or migration during refactor. Schema can change freely. Versioning comes post-refactor.

**Actionable Steps:**

1. **Audit existing FileObserver events:**
   ```bash
   grep -r "record_" src/econsim/observability/
   ```
   Use schema from Phase 0 as starting point.

2. **Design complete schema:**
   ```json
   {
     "schema_version": "1.0.0-dev",
     "metadata": {
       "config": {...},
       "seed": 42,
       "timestamp": "2025-10-03T12:00:00Z"
     },
     "events": [
       {
         "event_type": "agent_move",
         "step": 42,
         "agent_id": 0,
         "from_pos": [10, 10],
         "to_pos": [11, 10],
         "mode": "foraging"
       }
     ]
   }
   ```

3. **Add missing event types:**
   - Initial state (full snapshot at step 0)
   - Periodic snapshots (every N steps for fast seeking)
   - Simulation metadata

4. **Schema evolution during refactor:**
   - Schema version: "1.0.0-dev" during development
   - Can change freely, no migration needed
   - All old outputs invalidated by changes (acceptable)
   - Lock schema only at release candidate

5. **Write schema documentation:**
   - Update `docs/SIMULATION_OUTPUT_SCHEMA.md`
   - Example events for each type
   - Note: "Schema unstable during refactor"

**Deliverable:**
- `docs/SIMULATION_OUTPUT_SCHEMA.md`
- `src/econsim/observability/output_schema.py`

**Success Criteria:**
- [ ] All event types documented
- [ ] Schema file created
- [ ] Example output file generated
- [ ] Clear note: schema unstable during refactor

**Duration:** 2-3 days

---

### Step 2.3: SimulationRecorder Implementation

**Task:** Create class to orchestrate output recording.

**Actionable Steps:**

1. **Design SimulationRecorder interface:**
   ```python
   # src/econsim/simulation/recorder.py
   class SimulationRecorder:
       """Coordinates recording of simulation output to disk."""
       
       def __init__(self, output_dir: Path, config: SimulationConfig):
           self.output_dir = output_dir
           self.config = config
       
       def start_recording(self, simulation: Simulation):
           """Initialize recording for a simulation run."""
           # Create output directory with timestamp
           # Write metadata (config, seed, git hash)
           # Attach FileObserver
           # Record initial state snapshot
       
       def finalize_recording(self):
           """Clean up and close output files."""
   ```

2. **Implement output directory structure:**
   ```
   sim_runs/
   └── 20251003_120530_basic_foraging/
       ├── metadata.json
       ├── events.jsonl
       └── manifest.json
   ```

3. **Integrate with SimulationRunner:**
   ```python
   # In runner.py
   recorder = SimulationRecorder(output_dir="sim_runs", config=self.config)
   recorder.start_recording(self.simulation)
   
   for step in range(max_steps):
       self.simulation.step()
   
   recorder.finalize_recording()
   ```

4. **Add periodic snapshots:**
   - Every 100 steps, write full state snapshot
   - Enables fast seeking without replaying all events

**Deliverable:** `src/econsim/simulation/recorder.py`

**Success Criteria:**
- [ ] Recorder creates proper directory structure
- [ ] Metadata file written correctly
- [ ] Events captured via FileObserver
- [ ] Periodic snapshots written
- [ ] Unit tests pass

**Duration:** 3-4 days

---

### Step 2.4: PlaybackEngine Implementation

**Task:** Create engine to load and reconstruct simulation state from saved output.

**Actionable Steps:**

1. **Design PlaybackEngine interface:**
   ```python
   # src/econsim/simulation/playback_engine.py
   class PlaybackEngine:
       """Loads and reconstructs simulation state from saved output."""
       
       def __init__(self, run_directory: Path):
           self.run_dir = run_directory
       
       def load(self):
           """Load output files into memory."""
       
       def get_state_at_step(self, step: int) -> SimulationState:
           """Reconstruct state at given step."""
       
       def get_step_range(self) -> Tuple[int, int]:
           """Return (min_step, max_step) in recording."""
   ```

2. **Implement state reconstruction:**
   ```python
   class SimulationState:
       """Immutable snapshot of simulation state at a step."""
       agents: List[AgentState]
       resources: List[ResourceState]
       trades: List[TradeEvent]
       step: int
       
       @classmethod
       def from_snapshot(cls, snapshot_data: dict):
           """Build state from snapshot event."""
       
       def apply_event(self, event: dict) -> 'SimulationState':
           """Apply single event, return new state."""
   ```

3. **Implement efficient seeking:**
   - Use snapshots to avoid replaying from step 0
   - Cache reconstructed states for recent seeks
   - Lazy load events

4. **Add validation:**
   - Verify schema version compatibility
   - Validate event order (steps monotonic)
   - Check for corrupted data

**Deliverable:** `src/econsim/simulation/playback_engine.py`

**Success Criteria:**
- [ ] Engine loads recorded output
- [ ] State reconstruction correct
- [ ] Seeking fast (<200ms per seek)
- [ ] Validation catches corrupted data
- [ ] Unit tests pass
- [ ] Integration test: record → load → verify states match

**Duration:** 4-5 days

---

### Step 2.5: GUI Playback Mode Implementation

**Task:** Rebuild GUI to use playback mode (no more live mode).

**Actionable Steps:**

1. **Create PlaybackController:**
   ```python
   # src/econsim/gui/playback_controller.py
   class PlaybackController:
       """Controls playback of recorded simulation."""
       
       def __init__(self, playback_engine: PlaybackEngine):
           self.engine = playback_engine
           self.current_step = 0
           self.playing = False
           self.speed = 1.0
       
       def play(self): pass
       def pause(self): pass
       def step_forward(self): pass
       def step_backward(self): pass
       def seek(self, step: int): pass
       def set_speed(self, speed: float): pass
   ```

2. **Refactor EmbeddedPygameWidget:**
   ```python
   def render_from_state(self, state: SimulationState):
       """Render simulation state (playback mode)."""
       # Draw agents, resources, etc. from state object
   ```

3. **Update main GUI window:**
   - Step 1: Run simulation headless with SimulationRunner
   - Step 2: Show progress bar during run
   - Step 3: Load output with PlaybackEngine
   - Step 4: Switch to playback controls

4. **Add VCR controls:**
   - Play/Pause button
   - Step forward/backward buttons
   - Seek slider
   - Speed control (0.5x, 1x, 2x, 5x)
   - Step counter display

**Deliverable:** Updated GUI files

**Success Criteria:**
- [ ] GUI runs simulation headless first
- [ ] VCR controls work correctly
- [ ] Rendering matches expected visuals
- [ ] Speed control works
- [ ] Seeking responsive
- [ ] Manual testing checklist complete

**Duration:** 5-6 days

---

### Step 2.6: Integration Testing & Validation

**Task:** Comprehensive testing of output/playback pipeline.

**Actionable Steps:**

1. **Create integration test suite:**
   ```python
   # tests/integration/test_output_playback.py
   
   def test_record_and_playback():
       """Run simulation, save, load, verify states match."""
   
   def test_playback_determinism():
       """Multiple loads produce identical results."""
   
   def test_seeking_accuracy():
       """Seeking produces correct state."""
   
   def test_corrupted_output_handling():
       """Graceful handling of corrupted files."""
   ```

2. **Manual testing checklist:**
   - [ ] Run basic_foraging in playback mode
   - [ ] Test all VCR controls
   - [ ] Test seeking to start/middle/end
   - [ ] Test speed control
   - [ ] Close and reopen saved run
   - [ ] Test with large simulation (1000+ steps)

3. **Performance validation:**
   - Verify benchmarks from Step 2.1 still met
   - Profile any slow paths

4. **Documentation:**
   - Update user documentation
   - Add troubleshooting guide

**Success Criteria:**
- [ ] All integration tests pass
- [ ] Manual testing 100% complete
- [ ] Performance meets benchmarks
- [ ] Documentation updated

**Duration:** 3-4 days

**Git Checkpoint:** Create `refactor-post-phase2` tag when complete

---

### Phase 2 Exit Criteria

Before proceeding to Phase 3:
- [ ] Performance benchmarks met
- [ ] SimulationRecorder working
- [ ] PlaybackEngine accurate
- [ ] GUI playback mode functional
- [ ] All integration tests pass
- [ ] Documentation updated
- [ ] Git checkpoint `refactor-post-phase2` created

**Estimated Duration:** 3-4 weeks  
**Risk Level:** High (major new system)

---

## Phase 3: Test Suite Cleanup

**Goal:** Reduce test suite to <100 files, all relevant and maintainable.

**Duration:** 2-3 weeks  
**Priority:** P1  
**Prerequisites:** None (can run parallel to Phase 2)

**Approach:** Single steward (Chris) reviews all tests using clear criteria. Uncertain tests quarantined for async decision.

**Git Checkpoints:**
- Tag `refactor-pre-phase3` before starting
- Tag `refactor-post-phase3` when complete

**Breaking Changes:**
- Test files will be deleted
- Git history preserves deleted tests for recovery

**Rollback:**
If critical issues: `git checkout refactor-post-phase2` and restore tests from git history

---

### Step 3.1: Test Retention Criteria Definition

**Task:** Define explicit rules for keeping vs removing tests.

**Actionable Steps:**

1. **Define retention criteria:**

   **KEEP if test meets ANY of:**
   - Tests current production code behavior
   - Tests a known bug that was fixed (regression test)
   - Tests critical path (agent movement, trading, metrics)
   - Tests determinism or performance guarantees
   - Tests public API of a module
   
   **REMOVE if test meets ANY of:**
   - Tests removed code or feature
   - Tests intermediate refactoring state (e.g., "new_gui" flag)
   - Tests internal implementation detail (not behavior)
   - Duplicates another test's coverage
   - Has misleading name or unclear purpose
   
   **QUARANTINE if:**
   - Uncertain which of the above applies
   - Need time to investigate
   - Need second opinion

2. **Create quarantine workflow:**
   ```
   tests/
   └── QUARANTINE/
       ├── README.md            # Quarantine workflow documentation
       ├── QUARANTINE_NOTES.md  # Decision log for quarantined tests
       └── [quarantined tests]
   ```

3. **Quarantine rules:**
   - Move uncertain tests to `tests/QUARANTINE/`
   - Document reason for quarantine in `QUARANTINE_NOTES.md`
   - Weekly review of quarantined tests
   - 2-week max quarantine period
   - **Default after 2 weeks: KEEP (safe choice if still uncertain)**

**Deliverable:** `tmp_plans/CURRENT/CRITICAL/TEST_RETENTION_CRITERIA.md`

**Success Criteria:**
- [ ] KEEP/REMOVE/QUARANTINE criteria documented
- [ ] Quarantine workflow established
- [ ] Examples provided
- [ ] Criteria reviewed

**Duration:** 1 day

---

### Step 3.2: Automated Test Analysis

**Task:** Use tools to identify test candidates.

**Actionable Steps:**

1. **Analyze test names:**
   ```bash
   find tests/ -name "*.py" | xargs grep -l "legacy\|old\|new_gui\|deprecated"
   ```

2. **Check import usage:**
   ```python
   # Script: scripts/analyze_test_imports.py
   # For each test file:
   # - Parse imports
   # - Check if imported module still exists
   # - Flag for review if imports missing
   ```

3. **Measure test age:**
   ```bash
   # For each test file, get last modified date
   # Flag tests not modified in >6 months
   ```

4. **Generate initial spreadsheet:**
   `tmp_plans/CURRENT/CRITICAL/TEST_AUDIT_INITIAL.csv`

**Success Criteria:**
- [ ] All test files listed
- [ ] Automated flags populated
- [ ] High-confidence removal candidates identified

**Duration:** 2 days

---

### Step 3.3: Manual Test Audit (Single Steward)

**Task:** Chris personally reviews each test file.

**Actionable Steps:**

1. **For each test file, document:**
   - Purpose (what does it test?)
   - Current relevance (does code still exist?)
   - Coverage value (unique or duplicate?)
   - Verdict (KEEP/REMOVE/QUARANTINE)
   - Notes (rationale for verdict)

2. **Pay special attention to:**
   - Tests with "legacy", "old", "new" in names
   - Tests flagged by automated analysis
   - Tests of removed features (GUILogger, random walk)
   - Tests with no assertions

3. **If uncertain:**
   - Mark as QUARANTINE
   - Move to `tests/QUARANTINE/`
   - Document specific questions in `QUARANTINE_NOTES.md`
   - Preserve test until uncertainty resolved

4. **Weekly quarantine review:**
   - Review quarantined tests each week
   - Make decision or extend quarantine
   - Max 2 weeks in quarantine
   - **After 2 weeks: Default to KEEP**

**Deliverable:** `tmp_plans/CURRENT/CRITICAL/TEST_AUDIT_FINAL.csv`

**Success Criteria:**
- [ ] Every test file has verdict
- [ ] All uncertain tests quarantined
- [ ] Quarantine workflow active
- [ ] Rationale documented

**Duration:** 4-5 days

---

### Step 3.4: Test Removal Execution

**Task:** Remove tests marked for deletion.

**Actionable Steps:**

1. **Create removal branch:**
   ```bash
   git checkout -b refactor/test-suite-cleanup
   ```

2. **Remove tests in batches:**
   ```bash
   # Batch 1: Tests of removed code
   git rm tests/unit/test_legacy_feature.py
   make test-unit  # Verify no failures
   git commit -m "Remove tests of removed features (Batch 1)"
   
   # Batch 2: Duplicate tests
   # ... etc
   ```

3. **Document removed tests:**
   Create `tests/REMOVED_TESTS.md` with:
   - List of removed tests
   - Removal rationale
   - Git commit hash for recovery

**Success Criteria:**
- [ ] All REMOVE-verdict tests deleted
- [ ] Remaining tests pass
- [ ] Test count <100 files
- [ ] Documentation updated

**Duration:** 2-3 days

---

### Step 3.5: Test Reorganization

**Task:** Reorganize remaining tests into logical structure.

**Actionable Steps:**

1. **Create new structure:**
   ```bash
   mkdir -p tests/simulation
   mkdir -p tests/preferences
   mkdir -p tests/gui
   mkdir -p tests/observability
   mkdir -p tests/integration
   ```

2. **Move tests:**
   ```bash
   git mv tests/unit/test_agent.py tests/simulation/
   git mv tests/unit/test_preferences_*.py tests/preferences/
   # ... etc
   ```

3. **Update imports and verify:**
   ```bash
   pytest tests/
   ```

**Success Criteria:**
- [ ] All tests moved to new structure
- [ ] All imports updated
- [ ] pytest finds all tests
- [ ] No failures from reorganization

**Duration:** 2-3 days

**Git Checkpoint:** Create `refactor-post-phase3` tag when complete

---

### Phase 3 Exit Criteria

Before proceeding to Phase 4:
- [ ] Test suite <100 files
- [ ] All removed tests documented
- [ ] Tests reorganized
- [ ] All remaining tests pass
- [ ] Quarantine empty (all decisions made)
- [ ] Git checkpoint created

**Estimated Duration:** 2-3 weeks (can overlap Phase 2)  
**Risk Level:** Medium (might break tests accidentally)

---

## Phase 4: MANUAL_TESTS Consolidation

**Goal:** Single source of truth for test configurations via launcher registry.

**Duration:** 1 week  
**Priority:** P1  
**Prerequisites:** None

**Git Checkpoints:**
- Tag `refactor-pre-phase4` before starting
- Tag `refactor-post-phase4` when complete

**Breaking Changes:**
- Original `test_1.py` through `test_7.py` will be removed
- All migrated to launcher registry

**Rollback:**
If needed: `git checkout refactor-post-phase3`

---

### Step 4.1: Audit MANUAL_TESTS Directory

**Task:** Catalog all manual tests.

**Actionable Steps:**

1. **List all files:**
   ```bash
   find MANUAL_TESTS/ -name "*.py"
   ```

2. **For each, document:**
   - Purpose
   - Equivalent in launcher? (yes/no)
   - Still relevant?
   - Verdict (MIGRATE/KEEP/REMOVE)

**Deliverable:** `tmp_plans/CURRENT/CRITICAL/MANUAL_TESTS_INVENTORY.md`

**Success Criteria:**
- [ ] All files cataloged
- [ ] Verdicts assigned
- [ ] Migration targets identified

**Duration:** 1 day

---

### Step 4.2: Migrate Tests to Launcher

**Task:** Convert scripts to TestConfiguration objects.

**Actionable Steps:**

1. **For each test:**
   - Extract configuration
   - Create TestConfiguration in launcher
   - Test in launcher GUI
   - Document in migration log

2. **Handle special cases:**
   - Custom logic → keep in MANUAL_TESTS/examples/
   - Outdated tests → document but don't migrate

**Success Criteria:**
- [ ] All tests migrated
- [ ] Behavior verified equivalent
- [ ] Migration log complete

**Duration:** 2-3 days

---

### Step 4.3-4.5: [Condensed from original plan]

**Remaining steps:**
- Custom test JSON schema
- Config editor updates
- MANUAL_TESTS cleanup

**Success Criteria:**
- [ ] JSON schema for custom tests
- [ ] Config editor saves JSON
- [ ] MANUAL_TESTS directory cleaned

**Duration:** 2-3 days

**Git Checkpoint:** Create `refactor-post-phase4` tag when complete

---

### Phase 4 Exit Criteria

- [ ] Manual tests migrated
- [ ] JSON schema implemented
- [ ] MANUAL_TESTS directory cleaned
- [ ] Git checkpoint created

**Estimated Duration:** 1 week

---

## Phase 5: Preference Type Extension Improvements

**Goal:** Make adding preference types trivial with automatic registration.

**Duration:** 1 week  
**Priority:** P2  
**Prerequisites:** None

**Git Checkpoints:**
- Tag `refactor-pre-phase5` before starting
- Tag `refactor-post-phase5` when complete

**Breaking Changes:**
- None (backward compatible addition)

---

### Steps 5.1-5.4: [Condensed from original plan]

**Key deliverables:**
- Decorator-based registration
- Template generator
- Launcher auto-discovery
- Documentation

**Success Criteria:**
- [ ] @register_preference decorator working
- [ ] Template generator creates boilerplate
- [ ] Launcher discovers preferences automatically
- [ ] Documentation complete

**Duration:** 1 week

**Git Checkpoint:** Create `refactor-post-phase5` tag when complete

---

### Phase 5 Exit Criteria

- [ ] Registration system working
- [ ] Template generator working
- [ ] Auto-discovery functional
- [ ] Documentation complete
- [ ] Git checkpoint created

**Estimated Duration:** 1 week

---

## Phase 6: Extension Point Documentation

**Goal:** Document how to extend architecture for future features.

**Duration:** 1 week  
**Priority:** P3  
**Prerequisites:** Phases 0-5 complete

**Git Checkpoints:**
- Tag `refactor-pre-phase6` before starting
- Tag `refactor-post-phase6` when complete

**Breaking Changes:**
- None (documentation only)

---

### Steps 6.1-6.5: [Condensed from original plan]

**Key deliverables:**
- Handler extension documentation
- Observer extension documentation
- Preference extension documentation
- Architecture diagrams
- Extension checklists

**Success Criteria:**
- [ ] EXTENDING.md complete
- [ ] All patterns documented
- [ ] Diagrams updated
- [ ] Checklists created

**Duration:** 1 week

**Git Checkpoint:** Create `refactor-post-phase6` tag when complete

---

### Phase 6 Exit Criteria

- [ ] Complete extension documentation
- [ ] Architecture diagrams updated
- [ ] Checklists for common tasks
- [ ] Git checkpoint created

**Estimated Duration:** 1 week

---

## Execution Strategy

### Git Checkpoint Strategy

**Before Each Phase:**
Create tag: `refactor-pre-phase{N}` (e.g., `refactor-pre-phase0`)

**After Each Phase:**
Create tag: `refactor-post-phase{N}` when all success criteria met

**Rollback Procedure:**
If critical issues discovered:
```bash
git checkout refactor-post-phase{N-1}
# Fix issues
# Resume from stable checkpoint
```

**Checkpoint Discipline:**
- Tag before any major breaking change
- Document in CHANGELOG.md
- Test thoroughly before creating "post" tag
- Never create "post" tag if tests failing

---

### Testing Strategy

**For each phase:**
1. Unit tests for new components
2. Integration tests for new workflows
3. Regression tests (must still pass)
4. Manual testing checklist
5. Performance validation
6. Create git checkpoint when stable

---

### Branch Strategy

```
main
  └─ refactor/phase-0-observers
  └─ refactor/phase-1-decoupling
  └─ refactor/phase-2-output
  └─ refactor/phase-3-tests
  └─ refactor/phase-4-manual
  └─ refactor/phase-5-preferences
  └─ refactor/phase-6-docs
```

Each branch:
- Merges to main when complete
- Must pass all tests
- Requires review
- Includes documentation

---

### Time Allocation

```
Phase 0: Observer Cleanup           1-2 weeks
Phase 1: Coupling & Decoupling      1 week
Phase 2: Output Architecture        3-4 weeks
Phase 3: Test Suite Cleanup         2-3 weeks  (parallel with Phase 2)
Phase 4: MANUAL_TESTS               1 week
Phase 5: Preference Extensions      1 week
Phase 6: Documentation              1 week
Buffer & Integration                1-2 weeks
─────────────────────────────────────────────
Total:                              11-16 weeks (~3 months)
```

---

## Risk Register

### New/Increased Risks

#### R9: Temporary GUI Breakage Blocks Work
**Probability:** HIGH  
**Impact:** MEDIUM  
**Description:** GUI non-functional during/after Phase 1  
**Mitigation:** Work in branch, use git checkpoints  
**Contingency:** Revert to `refactor-post-phase0` for demos

#### R10: Schema Changes Break Active Work
**Probability:** MEDIUM  
**Impact:** LOW  
**Description:** Output schema unstable during refactor  
**Mitigation:** Clear communication, schema marked "dev"  
**Contingency:** Git checkpoints for rollback

#### R11: Single Reviewer Bottleneck
**Probability:** HIGH  
**Impact:** MEDIUM  
**Description:** Test cleanup depends on Chris's availability  
**Mitigation:** Quarantine for async decisions  
**Contingency:** Extend Phase 3 timeline

---

### Maintained Risks

#### R1: Phase 1 Coupling Deeper Than Expected
**Probability:** HIGH (increased from medium)  
**Impact:** High  
**Mitigation:** Comprehensive audit, accept breakage  
**Contingency:** Git rollback, simplify scope

#### R3: Accidentally Delete Important Tests
**Probability:** MEDIUM (increased from low)  
**Impact:** High  
**Mitigation:** Quarantine workflow, git history  
**Contingency:** Restore from git

---

### Eliminated Risks

#### R4: Observer Cleanup Breaks Output Architecture
**Status:** ELIMINATED  
**Reason:** Observer cleanup now Phase 0 (before output work)

---

## Success Criteria

The refactor is successful when:

### Technical Quality
- [ ] Simulation core has zero GUI dependencies
- [ ] `grep -r "PyQt\|pygame\|gui" src/econsim/simulation/` returns NOTHING
- [ ] All git checkpoints documented and tested
- [ ] Observer system clean with formalized schema
- [ ] Can replay any saved simulation (created after refactor)

### User Experience
- [ ] Simulations run headless and save to `sim_runs/`
- [ ] GUI loads and replays saved simulations
- [ ] VCR controls work smoothly
- [ ] Playback responsive (<200ms seeks)

### Developer Experience
- [ ] Test suite <100 files, all relevant
- [ ] Adding preferences trivial (decorator + template)
- [ ] Extension patterns documented
- [ ] Architecture ready for new features

### Process
- [ ] All phases completed with git checkpoints
- [ ] No temporary infrastructure remaining (quarantine empty)
- [ ] REFACTOR_STATUS.md shows all components working
- [ ] Documentation complete and accurate

---

## Out of Scope

**The following are explicitly NOT part of this refactor:**

- ❌ Market-price implementation
- ❌ N-good generalization
- ❌ New economic mechanisms
- ❌ Performance optimization (unless regression)
- ❌ New features of any kind

**Focus:** Clean existing implementation to standards.

---

## Conclusion

This plan represents a **clean architecture approach** with:
- No backward compatibility during refactor
- No feature flags or parallel systems
- Git checkpoints for safety
- Aggressive decoupling with expected breakage
- Single steward for test decisions
- Quarantine workflow for uncertainty

**Key Decision:** Accept temporary disruption for long-term maintainability.

**Recommended Start:** Phase 0 (Observer Cleanup) immediately. Low risk, high value.

---

**Document Version:** 2.0  
**Created:** October 3, 2025  
**Status:** Ready for Execution  
**Previous Version:** ACTIONABLE_REFACTORING_PLAN.md v1.0  
**Changes:** Complete rewrite incorporating all Gap decisions and Phase Updates Guide


