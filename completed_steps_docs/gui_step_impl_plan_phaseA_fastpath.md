# GUI Phase A Fast-Path Implementation Plan (Draft v0.1)

Purpose: Narrow, high-certainty sequence to reach a FUNCTIONAL & TESTED Phase A GUI (feature-flagged) with minimal moving parts while preserving determinism & performance invariants.

Status: Draft v0.1 (derived from `gui_comprehensive_plan.md` v0.2)
Scope Goal: Achieve interactive launch → start menu → simulation page with overlays & basic controls + automated tests validating hash stability & overlay toggles.

---
## 0. Guiding Constraints (Do Not Alter)
- Single Qt event loop; existing 16ms `QTimer` inside `EmbeddedPygameWidget` only frame driver.
- Fixed 320x240 RGBA surface (no per-frame reallocation).
- Determinism invariants (tie-break key, ordering, epsilon constants) untouched.
- Per-frame cost target: keep added GUI logic < ~2ms.
- Optional hooks (metrics, respawn) remain O(n) and skipped if disabled.
- All new code permanently behind `ECONSIM_NEW_GUI=1` until Phase A completion tests green.

## 1. Minimal Feature Set (Fast Path)
INCLUDED:
1. Start Menu with seed, grid size, agents, density, scenario select (Baseline Decision / Legacy Random / Turn Mode placeholder).
2. Launch → builds `SimulationSessionDescriptor` → `SessionFactory` → `SimulationController` → Simulation Page.
3. Simulation Page panels:
   - Viewport (existing embedded widget from `Simulation` instance)
   - Controls: Step 1, Step 5, Pause/Resume (toggle), Hash Refresh
   - Overlays: Grid, Agent IDs, Target Arrow (checkboxes; default off)
   - Back to Menu button (teardown safe)
4. Metrics mini panel: tick count, remaining resources, cached hash (8-char + full via tooltip) + steps/sec estimate (simple rolling window of last 32 steps).
5. Manual turn mode: if mode == 'turn', disable auto stepping (timer paused) and enable only manual step buttons.
6. Smoke + determinism tests:
   - Headless build & step test (already present -> extend)
   - Overlay toggle renders different pixel byte signature (rehook existing overlay regression logic under flag)
   - Determinism hash identical for same descriptor across two runs.

EXCLUDED (defer): Snapshot export, speed selector, agent inspector, preference comparison, extended metrics, auto hash refresh toggle.

## 2. Step-by-Step Task Sequence
(Each step includes exit criteria & test hooks) 

### Step 1: Normalize Existing Scaffold
- Clean `start_menu.py` semicolon style; ensure deterministic default values.
- Add explicit descriptor validation (bounds: grid <= 64x64, agents <= 64, density in [0,1]).
Exit Criteria: Lint clean for file section; invalid values raise ValueError (covered in unit test).

### Step 2: Overlay State Wiring
- Introduce lightweight `OverlayState` dataclass (grid: bool, ids: bool, target: bool).
- Inject into `EmbeddedPygameWidget` via attribute (no constructor signature change; set after creation).
- Add draw branches (cheap) respecting existing render flow (no new surfaces). Use existing font surface if available.
Exit Criteria: With all overlays False, frame bytes identical to legacy (within existing variance limits). New test passes toggling flags.

### Step 3: ControlsPanel Expansion
- Add Pause/Resume toggle (stores boolean on controller; if paused, widget skips calling `simulation.step`).
- Add Step 5 invoking 5 sequential steps when paused (ensures deterministic sequential stepping).
Exit Criteria: Unit test verifies paused state prevents step increment; step 5 increments exactly +5.

### Step 4: Turn Mode Handling
- On descriptor.mode == 'turn': auto-pause on entry; hide Pause/Resume toggle (or repurpose label 'Turn Mode').
- Ensure manual stepping reuses same path as paused continuous mode.
Exit Criteria: Test constructing turn mode session reports no auto progression over N timer ticks.

### Step 5: Steps/sec Estimation
- Maintain deque of timestamps when steps occur (only when auto stepping active).
- Expose computed rolling average to metrics panel (len(deque)/time span).
Exit Criteria: Test simulating synthetic timestamp injections yields expected numeric formatting (stubbed controller method unit test).

### Step 6: Hash Caching & Refresh
- Controller stores last hash; refresh button triggers recompute; metrics panel updates label & tooltip.
- Ensure no hash recompute occurs per frame.
Exit Criteria: Test ensures successive accesses without refresh keep object identity (same string) until refresh invoked.

### Step 7: Back Navigation & Teardown
- Implement safe teardown: stop widget timer → delete widget → return to menu page; controller dropped.
- Guard double teardown (idempotent).
Exit Criteria: Test: create session, navigate back, create second session; ensure second hash differs only by seed, no crash.

### Step 8: Determinism & Overlay Tests Finalization
- Augment existing determinism test to run under new GUI path (flag) with overlays off.
- Add overlay pixel diff test (skip if PyQt offscreen not available).
Exit Criteria: All new tests pass locally with flag; legacy tests unaffected.

### Step 9: Lint & Style Targeted Cleanup
- Apply fixes only to new/changed GUI files to reduce noise.
Exit Criteria: `make lint` shows no new errors in modified files (global backlog acknowledged separately).

### Step 10: Documentation Delta
- Add `PHASE_A_FASTPATH.md` snippet in docs or append section to existing plan referencing this execution track.
Exit Criteria: Doc lists implemented subset + deferred items for transparency.

## 3. Risk Matrix (Focused)
| Task | Risk | Mitigation |
|------|------|------------|
| Overlay drawing | Performance dip | Branch early; measure perf stub with overlays off/on (<2% diff). |
| Pause logic | Stepping drift | Centralize step invocation in single method gating paused flag. |
| Turn mode | Hidden auto steps | Explicit timer skip path w/ assert in test. |
| Steps/sec calc | Division by zero | Guard with min time span; fallback '—'. |
| Teardown | Timer leak | Ensure timer stopped before widget deletion; test leak via second instantiation. |

## 4. Test Additions Summary
- `test_session_descriptor_validation.py`
- `test_overlay_toggle_pixels.py` (flagged, may reuse existing overlay regression harness)
- `test_controller_pause_and_step.py`
- `test_turn_mode_no_autostep.py`
- `test_steps_per_sec_estimator.py`
- `test_hash_refresh_cache_behavior.py`
- `test_navigation_teardown_reuse.py`

## 5. Acceptance Criteria (Phase A Fast Path)
- Launch flow functional under flag; legacy path unchanged.
- All new tests pass; existing suite still green.
- Overlays toggle visually (pixel diff) and default off.
- No auto steps in turn mode; manual stepping works.
- Steps/sec displays a plausible value (>0 in continuous baseline after warmup).
- Lint clean for modified GUI files.

## 6. Out-of-Scope (Explicit Deferral)
- Inspector panel, snapshot export, preference comparison scenarios, speed multiplier, agent utility text overlay, extended metrics history, event log, dynamic scenario presets UI.

## 7. Execution Ordering Justification
Ordering minimizes rework: stabilize style + descriptor early → overlay state (needed by panels) → control mechanics → mode specialization → performance-neutral metrics → teardown & tests → final polish.

## 8. Next Immediate Action
Proceed with Step 1 (normalize `start_menu.py` + validation + unit test scaffold) under feature flag branchless (behind env). After Step 1 merges cleanly, continue sequentially.

---
Feedback welcome. Mark changes or approve to begin Step 1 implementation.
