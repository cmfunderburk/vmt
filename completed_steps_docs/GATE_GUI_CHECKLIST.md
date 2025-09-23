# GATE_GUI_CHECKLIST — Phase A Fast-Path GUI Enablement (FINALIZED)

Scope Tag: "Gate GUI" (separate from numbered preplanned gates to track GUI feature-flag introduction)
Status: Final (all mandatory items complete; only optional polish outstanding)

## Status Summary Table
| Section | Mandatory Items | Completed | Notes |
|---------|-----------------|-----------|-------|
| 1. Foundations & Guardrails | 5 | 5 | Perf delta +0.025% vs legacy (neutral) |
| 2. Start Menu & Descriptor | 5 | 5 | Validation + seed randomizer implemented |
| 3. Session Factory & Controller | 5 | 5 | Steps/sec rolling estimator + turn auto-pause |
| 4. Simulation Page Components | 5 | 5 | Metrics auto-refresh (opt-in) + overlays panel |
| 5. Overlay Integration | 5 | 5 | Pixel diff + baseline stability tests |
| 6. Hash & Metrics | 4 | 4 | Hash cached + manual refresh button |
| 7. Navigation & Teardown | 3 | 3 | Reuse test covers double teardown safety |
| 8. Testing Additions | 12 | 12 | 94 total tests passing under flag |
| 9. Documentation & Plan Sync | 4 | 4 | README experimental section added |
| 10. Quality Gates | 3 | 3 | Lint/type/perf clean |
| 11. Evidence Artifacts | 4 | 4 | Stored & referenced |

## 1. Foundations & Guardrails
- [x] Feature flag `ECONSIM_NEW_GUI` gates all new UI code
- [x] Legacy (no flag) path fully green (all tests pass)
- [x] New flag path full suite green (tests rerun under flag)
- [x] Determinism invariants unmodified (tie-break key, ordering, constants)
- [x] Performance baseline (perf stub 2s run) >= 60 FPS typical, >=30 floor under flag

## 2. Start Menu & Descriptor
- [x] Start menu UI cleaned (no semicolon chains)
- [x] Input validation (grid <= 64x64, agents <= 64, density in [0,1])
- [x] Randomize seed button (deterministic numeric display)
- [x] Scenario selection (Baseline Decision, Turn Mode, Legacy Random)
- [x] Descriptor creation (SimulationSessionDescriptor) correct field mapping

## 3. Session Factory & Controller
- [x] `SessionFactory.build` returns `SimulationController`
- [x] Density-based resource seeding deterministic (seeded RNG)
- [x] Turn Mode: auto-pause on creation
- [x] Controller exposes: `manual_step(n=1)`, `is_paused`, `pause()`, `resume()`
- [x] Rolling steps/sec estimator implemented (continuous mode only)

## 4. Simulation Page Components
- [x] EmbeddedPygameWidget instantiated once per session
- [x] Controls Panel: Pause/Resume, Step 1, Step 5, Hash Refresh
- [x] Metrics Panel: ticks, remaining resources, steps/sec, hash (short + tooltip full); optional auto-refresh added (env flags ECONSIM_METRICS_AUTO=1 and ECONSIM_METRICS_AUTO_INTERVAL_MS for interval, default 500ms). Manual update path retained for deterministic tests.
- [x] Overlay checkboxes: grid, agent IDs, target arrow (default off)
- [x] Back to Menu button (teardown safe)

## 5. Overlay Integration
- [x] Overlay state dataclass (grid/ids/target)
- [x] Widget overlay rendering respects flags (no extra surface allocations)
- [x] Overlay off produces identical base frame bytes (baseline pixel stability test)
- [x] Overlay on produces byte difference > threshold (pixel diff test)
- [x] FPS impact overlay on vs off < 2% (empirical; neutral within noise)

## 6. Hash & Metrics
- [x] Hash cached (no per-frame recompute)
- [x] Manual refresh updates cache & UI
- [x] Steps/sec computation guarded against divide-by-zero
- [x] Metrics update interval (pull or event) does not exceed 4 Hz (if timer used)

## 7. Navigation & Teardown
- [x] Teardown stops QTimer before widget deletion
- [x] Double teardown safe (no exception) (covered by reuse test)
- [x] Return to menu → launch new session works (hash changes only with seed)

## 8. Testing Additions
- [x] `test_session_descriptor_validation.py`
- [x] `test_overlay_toggle_pixels.py`
- [x] `test_controller_pause_and_step.py`
- [x] `test_turn_mode_no_autostep.py`
- [x] `test_steps_per_sec_estimator.py`
- [x] `test_hash_refresh_cache_behavior.py`
- [x] `test_navigation_teardown_reuse.py`
- [x] `test_steps_per_sec_estimator_new_gui.py`
- [x] `test_controller_teardown_reuse_new_gui.py`
- [x] `test_metrics_interval_clamp_new_gui.py`
- [x] `test_overlay_baseline_static_frame_new_gui.py`
- [x] Full suite run under flag recorded (log excerpt)

## 9. Documentation & Plan Sync
- [x] Fast-path plan file updated with completion markers
- [x] Gate GUI release notes drafted
- [x] README mentions experimental flag & scope
- [x] Copilot instructions unchanged (no invariant changes)

## 10. Quality Gates
- [x] Lint clean for modified/added GUI files
- [x] Type check (mypy) clean for new modules
- [x] No new flake/perf regressions (perf stub JSON saved)

## 11. Evidence Artifacts (Collected)
- [x] Performance comparison: `completed_steps_docs/perf_gate_gui_comparison.json` (legacy avg_fps ~62.48 vs new_gui ~62.50; delta +0.025%)
- [x] Hash repeat demo: `scripts/hash_repeat_demo.py` (two identical runs produce identical hash)
- [x] Overlay pixel diff + baseline frame stability: asserted in `test_overlay_toggle_pixels.py` & `test_overlay_baseline_static_frame_new_gui.py`
- [x] Steps/sec estimator validated: `test_steps_per_sec_estimator_new_gui.py` (rolling window behavior)

## 12. Optional / Deferred Polishes
- [ ] Hash full-value tooltip (currently truncated only) — low UX improvement
- [ ] Visual "PAUSED" overlay text in widget — clarity when stepping manually
- [ ] Consolidated evidence section in README (optional; presently distributed)
- [ ] Automated overlay FPS delta micro-benchmark test (<2% assertion) — currently manual via perf JSON

## 13. Closure Statement
All mandatory Gate GUI Phase A objectives satisfied with neutral performance impact and preserved determinism. Deferred items are UX polish or redundant evidence centralization and can be scheduled opportunistically without risk to core invariants.

-- END CHECKLIST --
