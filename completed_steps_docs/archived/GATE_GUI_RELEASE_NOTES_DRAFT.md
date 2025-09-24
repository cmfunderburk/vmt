# Gate GUI Release Notes (Draft)

Date: 2025-09-23 (initial draft prior to implementation)
Scope: Feature-flagged Phase A fast-path GUI enabling structured session launch, overlays, and basic control loop without altering simulation determinism or performance guarantees.

## Planned Highlights
- New Start Menu (flagged) for constructing `SimulationSessionDescriptor`
- Session Factory returns `SimulationController` maintaining pause/step semantics
- Overlays (grid, agent IDs, target arrow) default off, toggle via checkboxes (no keybinding reliance)
- Controls: Pause/Resume, Step 1, Step 5, hash refresh
- Metrics mini panel: ticks, remaining resources, steps/sec, deterministic hash (short + full tooltip)
- Turn Mode (manual stepping) vs Continuous vs Legacy Random scenario options
- Safe teardown / return-to-menu (timer stop discipline preserved)

## Invariants Preserved
- Single Qt event loop & 16ms frame timer
- 320x240 fixed surface; no new surfaces per frame
- Tie-break ordering & epsilon constants untouched
- O(agents + resources) per-step complexity unchanged

## Performance Expectations
- Overlays off: parity with existing baseline (~60+ FPS)
- Overlays on: <2% FPS deviation target
- No per-frame hash recomputation (manual refresh only)

## Determinism Guarantees
- Identical descriptor (same seed/params) yields identical determinism hash irrespective of overlay state or GUI controls usage (except number of steps taken)
- Turn Mode ensures no steps unless explicitly triggered

## Test Additions (Planned)
- Descriptor validation
- Overlay pixel diff
- Pause & multi-step execution
- Turn mode no-autostep
- Steps/sec estimator correctness
- Hash cache vs refresh
- Navigation teardown reuse

## User Workflow (Flag Enabled)
1. Export environment variable: `ECONSIM_NEW_GUI=1`
2. Launch app (`make dev` or equivalent)
3. Configure scenario in Start Menu → Launch
4. Toggle overlays / pause / step; observe metrics
5. Back to Menu to start a new session

## Deferred Items (Future Iterations)
- Inspector panel
- Snapshot/export
- Preference comparison scenario
- Speed selector
- Utility text overlay & advanced metrics history
- Event log & scenario preset matrix

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Overlay rendering cost creep | Keep draw operations minimal; measure with perf stub |
| Pause logic drift | Centralize step gating in controller; tests assert paused invariants |
| Hash misuse (per-frame) | Cache strategy + explicit refresh UI control |
| Turn Mode confusion | Distinct labeling & hidden pause button in turn mode |

## Upgrade / Adoption Notes
- Legacy path unaffected unless flag set
- Existing determinism & competition tests continue unmodified
- No API change to `Simulation` core; addition is orchestration layer only

-- Draft; will update upon task completion with empirical FPS, test counts, and sample hashes. --
