# Gate 6 Implementation Plan – Integration & Minimal Overlay Toggle
Date: 2025-09-23
Status: Planning (Pre-Coding)

## 1. Objectives (Restated Precisely)
Integrate existing Gate 5 components behind a clean public construction path while preserving determinism and current performance:
1. Public factory: `Simulation.from_config(SimConfig)` applies seed + optional respawn & metrics.
2. GUI default path = decision mode (legacy random available via env flag).
3. Minimal overlay toggle (HUD on/off) bound to key `O` (off by default) with <5% FPS impact.
4. Tests shifted to public API (no private hook / RNG access).
5. Documentation updated to reflect new integration path; manual wiring demoted.
6. Determinism & performance baselines unchanged.

## 2. Acceptance Criteria Mapping
| Checklist Item | Plan Section | Evidence Artifact |
|----------------|--------------|-------------------|
| SimConfig extended | Phase A Step 1 | Diff + validation test |
| Factory implemented | Phase A Step 2 | `test_factory_integration.py` |
| Respawn attached when enabled | Phase A Step 2 | Factory test asserts scheduler active |
| Metrics attached when enabled | Phase A Step 2 | Factory test asserts collector active |
| Internal RNG seeded | Phase A Step 2 | Determinism hash parity across runs |
| Decision mode default GUI | Phase B Step 1 | GUI smoke test comparing movement vs env override |
| Env flag fallback works | Phase B Step 1 | Test launching with env var set |
| Legacy path still functional | Phase B Step 1 | Existing widget tests still green |
| Overlay toggle key works | Phase B Step 2 | New overlay toggle test |
| Overlay off by default | Phase B Step 2 | Test initial state assert |
| No hash change from toggle | Phase B Step 2 | Hash sample before/after toggle |
| FPS delta <5% | Phase B Step 2 | Perf stub measurement table |
| No test references `sim._rng` | Phase C Step 2 | Grep evidence in evaluation |
| No direct hook assignments | Phase C Step 2 | Grep evidence in evaluation |
| Determinism tests unchanged | Phase C Step 1 | Test suite pass log |
| Perf thresholds met | Phase C Step 3 | Perf JSON snippet |
| Docs updated (README/API_GUIDE) | Phase D Step 1 | Diff excerpts |
| Copilot instructions still valid | Phase D Step 2 | Note unchanged or minor tweak |
| Gate_6_todos scope closure | Phase D Step 3 | Updated checklist + eval doc |
| Evidence bundle ready | Phase E | `GATE6_EVAL.md` with tables |

## 3. Phase Breakdown & Detailed Steps

### Phase A – Core Construction Path (Factory)
1. Extend `SimConfig`:
   - Add fields: `enable_respawn: bool = True`, `enable_metrics: bool = True`, `respawn_rate: float = 0.1`, `respawn_target_density: float = 0.25`, `max_spawn_per_tick: int = 3`, `seed: int = 0`.
   - Lightweight validation (value ranges) in `__post_init__` or helper.
2. Implement `Simulation.from_config(cls, config: SimConfig) -> Simulation`:
   - Instantiate grid & agents (initial method: adapt existing manual wiring fixture or minimal internal helper—keep simple).
   - Create internal RNG seeded from `config.seed` (store as `_rng`).
   - Conditionally attach `RespawnScheduler` & `MetricsCollector` instances using config fields.
   - Return fully initialized instance.
3. Add factory integration test:
   - Construct config; call factory; run N steps (decision mode on) and assert: respawn active (resource count increases toward target), metrics hash produced, no exceptions.
4. Backward compatibility decision: retain direct `Simulation(...)` usage in existing tests until refactor phase.
5. (Optional) Provide small helper `build_basic_config()` in tests to reduce duplication.

### Phase B – GUI Default & Overlay Toggle
1. Flip GUI to decision mode default:
   - In widget or main bootstrap, branch: if `os.getenv('ECONSIM_LEGACY_RANDOM') == '1'` use legacy path else decision.
   - Add smoke test verifying different first 10 positions under each mode.
2. Implement overlay toggle:
   - Add `self.show_overlay: bool = False` to widget.
   - Handle `keyPressEvent`: if key == `Key_O`: flip flag.
   - In paint path, if `show_overlay`: draw minimal HUD (FPS, step count, agent count).
   - Ensure drawing uses already-allocated font / avoids per-frame allocations.
3. Overlay tests:
   - Test initial state off.
   - Toggle on; ensure no crash; optionally snapshot small pixel checksum difference.
   - Hash determinism test: run steps with overlay off vs on (overlay should not influence simulation state or hash).
4. Perf measurement: run perf stub overlay off/on 2s each; record FPS delta (<5%).

### Phase C – Test & Surface Migration
1. Update tests referencing manual hook assignment:
   - Replace manual `sim.respawn_scheduler = ...` + `sim.metrics_collector = ...` with factory usage.
   - Keep one explicit test for manual override (optional) if still desirable.
2. Remove private internal references:
   - Grep for `sim._rng`, `respawn_scheduler =`, `metrics_collector =` after migration.
   - Add assertion in integration test that `_rng` exists but not accessed externally.
3. Add / adjust perf tests to use factory path so performance reflects integrated runtime.

### Phase D – Documentation & Instructions
1. Update `README.md` and `API_GUIDE.md`:
   - Add factory example at top of usage section.
   - Demote manual wiring to “Legacy / Advanced Overrides”.
2. Review `.github/copilot-instructions.md`:
   - If no invariant changed, add single line: “Factory path (`Simulation.from_config`) now preferred.”
3. Update Gate docs:
   - Mark tasks complete in `GATE6_CHECKLIST.md`.
   - Prepare `GATE6_EVAL.md` skeleton with evidence placeholders early to avoid scramble.

### Phase E – Evidence & Evaluation
1. Capture determinism evidence:
   - Record hash sequence prefix (e.g., first 5 hashes) pre- and post-integration (should match).
2. Capture performance evidence:
   - JSON output from perf stub (overlay off/on).
3. Grep output:
   - Show zero hits for forbidden private wiring patterns.
4. Finalize `GATE6_EVAL.md` with: diff summary, metrics table, risk review closure.

## 4. Risk Matrix (Execution Focus)
| Risk | Phase | Trigger | Mitigation | Abort Criteria |
|------|-------|---------|------------|----------------|
| Factory changes ordering | A | Hook attach order affects agent step | Attach before any steps; run determinism tests immediately | Revert / isolate hook assignment |
| Overlay FPS regression | B | Draw loop adds >5% cost | Cache font, minimal text; measure early | Simplify overlay (single line) |
| Test migration churn | C | Many failing tests simultaneously | Migrate in small PRs (factory first, then overlay) | Pause & isolate failing subset |
| Doc drift | D | README updated late | Stage doc edits in parallel with Phase C | Block merge until diff reviewed |
| Hidden private usage | C/E | Residual direct assignments | Automated grep in eval script | Add failing test to guard |

## 5. Proposed PR Sequencing
1. PR #1: SimConfig extension + factory + integration test (no other changes).
2. PR #2: GUI default decision mode + env flag smoke test.
3. PR #3: Overlay toggle + overlay tests + perf measurement script adjustment.
4. PR #4: Test migration (convert remaining tests to factory path).
5. PR #5: Documentation updates + minor copilot addendum.
6. PR #6: Evaluation artifacts (`GATE6_EVAL.md`), checklist closure.

(Smaller PRs reduce review surface and isolate regressions.)

## 6. Evidence Capture Checklist (Inline During Work)
- After PR #1 merge: Store determinism hash sample to reuse later.
- After PR #3: Capture overlay on/off FPS JSON.
- After PR #4: Run grep & paste zero-results output into eval draft.
- Before PR #6: Assemble table (hash unchanged, FPS delta, resource density convergence).

## 7. Non-Goals Clarification
- No change to tie-break logic, preference APIs, or grid storage.
- No introduction of trading placeholders or proto APIs.
- No expansion of metrics beyond existing hash & aggregates.
- No config persistence (serialization optional future gate).

## 8. Open Questions (Finalize Before Coding)
| Topic | Proposed | Rationale | Decision |
|-------|----------|-----------|----------|
| Config field naming | `enable_respawn`, `enable_metrics` | Consistent boolean prefix | TBD |
| Include perception radius in config | Defer | Avoid unfreezing constant prematurely | TBD |
| Overlay content | FPS + steps + agent count | Value vs complexity balance | TBD |
| RNG exposure | Keep private (`_rng`) | Prevent misuse; determinism sealed | TBD |
| Logging on factory build | Quiet default; optional flag later | Keep noise low | TBD |

## 9. Ready-to-Implement Summary
All prerequisites satisfied: docs reconciled, risks enumerated, checklist explicit. Next concrete action: decide open questions, then execute PR #1 (SimConfig + factory) immediately.

-- END --
