# Gate 6 Todos – Integration & Minimal Overlay Toggle (Revised 2025-09-23)

Objective: Integrate existing Gate 5 components (decision mode, respawn, metrics, SimConfig) into a cohesive default runtime, add a minimal overlay toggle, and eliminate ad-hoc wiring patterns—without introducing new economics (trading deferred to Gate 7).

## Deliverables
1. `Simulation.from_config(SimConfig)` factory applying seed + optional respawn/metrics.
2. GUI defaults to decision mode (legacy path behind env `ECONSIM_LEGACY_RANDOM=1`).
3. Minimal overlay toggle (HUD/resources text) via key `O` (off by default).
4. Public wiring helpers; tests no longer mutate internal hooks directly.
5. Updated docs: README, API_GUIDE (factory usage), ROADMAP_REVISED.
6. Performance parity (≥60 FPS typical; ≥30 FPS floor) overlay on/off.
7. Determinism unchanged (trajectory & hash tests pass as-is).

## Out of Scope / Deferred
* Trading / agent interaction logic (Gate 7)
* Control panels / parameter sliders (Gate 8)
* Utility contour visualization, tails, heatmaps (future visualization gate)
* Economic indicators beyond current metrics

## Acceptance Criteria
| # | Criterion | Validation |
|---|-----------|------------|
| 1 | Factory constructs sim with active hooks | New test `test_factory_integration.py` (respawn + metrics auto active) |
| 2 | Decision mode default in GUI | Env var toggles legacy; smoke test verifies movement pattern difference |
| 3 | Overlay toggle functional & cheap | GUI test toggles flag; perf delta <5% over 2s run |
| 4 | No private wiring in tests | Grep for `sim._rng` & direct hook assignment returns none |
| 5 | Determinism preserved | Existing determinism & hash tests unchanged and green |
| 6 | Docs updated | README & API_GUIDE contain factory usage; roadmap added |
| 7 | Performance maintained | perf stub extended or separate test captures FPS ≥ baseline floor |

## Task List
- [ ] Extend `SimConfig` with `enable_respawn`, `enable_metrics`, respawn params.
- [ ] Implement `Simulation.from_config` (creates internal RNG, attaches hooks conditionally).
- [ ] Refactor `world.py` construction in tests to use factory where appropriate.
- [ ] Modify `EmbeddedPygameWidget` to call decision path by default (env guard).
- [ ] Implement overlay toggle key handler (`keyPressEvent`).
- [ ] Add new test: overlay toggle does not crash & flips state.
- [ ] Add factory integration test (auto respawn + metrics operative without manual assignment).
- [ ] Update existing tests to drop direct hook assignment (except specialized edge tests if any).
- [ ] Add or update perf test to run factory-created sim.
- [ ] Update README & API_GUIDE with factory examples; link to roadmap.
- [ ] Add `ROADMAP_REVISED.md` (Gates 6–9 realistic sequencing).
- [ ] Write `GATE6_CHECKLIST.md` from acceptance criteria.

## Risk Mitigation
| Risk | Mitigation |
|------|------------|
| Factory changes ordering causing hash drift | Keep agent list & step loop identical; attach hooks pre-first step |
| Overlay reduces FPS | Minimal text only; reuse font; measure before/after |
| Tests still need internal access | Provide helper or fixture using factory instead of private members |
| Env flag confusion | Single documented variable `ECONSIM_LEGACY_RANDOM=1` |

## Metrics to Capture
* FPS (widget) overlay off vs on (2s sample)
* Determinism hash for canonical scenario (unchanged)
* Respawn density convergence unchanged under factory path

## Exit Summary Template (for Evaluation)
Provide: diff summary, perf table (before/after), determinism hash sample, grep evidence of removed private wiring.

-- END --
