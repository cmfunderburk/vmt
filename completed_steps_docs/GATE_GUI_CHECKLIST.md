# GATE_GUI_CHECKLIST — Phase A Fast-Path GUI Enablement

Scope Tag: "Gate GUI" (separate from numbered preplanned gates to track GUI feature-flag introduction)
Status: Draft (pending execution of Step 1 in fast-path plan)

## 1. Foundations & Guardrails
- [ ] Feature flag `ECONSIM_NEW_GUI` gates all new UI code
- [ ] Legacy (no flag) path fully green (all tests pass)
- [ ] New flag path full suite green (tests rerun under flag)
- [ ] Determinism invariants unmodified (tie-break key, ordering, constants)
- [ ] Performance baseline (perf stub 2s run) >= 60 FPS typical, >=30 floor under flag

## 2. Start Menu & Descriptor
- [ ] Start menu UI cleaned (no semicolon chains)
- [ ] Input validation (grid <= 64x64, agents <= 64, density in [0,1])
- [ ] Randomize seed button (deterministic numeric display)
- [ ] Scenario selection (Baseline Decision, Turn Mode, Legacy Random)
- [ ] Descriptor creation (SimulationSessionDescriptor) correct field mapping

## 3. Session Factory & Controller
- [ ] `SessionFactory.build` returns `SimulationController`
- [ ] Density-based resource seeding deterministic (seeded RNG)
- [ ] Turn Mode: auto-pause on creation
- [ ] Controller exposes: `manual_step(n=1)`, `is_paused`, `pause()`, `resume()`
- [ ] Rolling steps/sec estimator implemented (continuous mode only)

## 4. Simulation Page Components
- [ ] EmbeddedPygameWidget instantiated once per session
- [ ] Controls Panel: Pause/Resume, Step 1, Step 5, Hash Refresh
- [ ] Metrics Panel: ticks, remaining resources, steps/sec, hash (short + tooltip full)
- [ ] Overlay checkboxes: grid, agent IDs, target arrow (default off)
- [ ] Back to Menu button (teardown safe)

## 5. Overlay Integration
- [ ] Overlay state dataclass (grid/ids/target)
- [ ] Widget overlay rendering respects flags (no extra surface allocations)
- [ ] Overlay off produces identical base frame bytes (within existing test tolerance)
- [ ] Overlay on produces byte difference > threshold (test assertion)
- [ ] FPS impact overlay on vs off < 2% (sampled, documented)

## 6. Hash & Metrics
- [ ] Hash cached (no per-frame recompute)
- [ ] Manual refresh updates cache & UI
- [ ] Steps/sec computation guarded against divide-by-zero
- [ ] Metrics update interval (pull or event) does not exceed 4 Hz (if timer used)

## 7. Navigation & Teardown
- [ ] Teardown stops QTimer before widget deletion
- [ ] Double teardown safe (no exception)
- [ ] Return to menu → launch new session works (hash changes only with seed)

## 8. Testing Additions
- [ ] `test_session_descriptor_validation.py`
- [ ] `test_overlay_toggle_pixels.py`
- [ ] `test_controller_pause_and_step.py`
- [ ] `test_turn_mode_no_autostep.py`
- [ ] `test_steps_per_sec_estimator.py`
- [ ] `test_hash_refresh_cache_behavior.py`
- [ ] `test_navigation_teardown_reuse.py`
- [ ] Full suite run under flag recorded (log excerpt)

## 9. Documentation & Plan Sync
- [ ] Fast-path plan file updated with completion markers
- [ ] Gate GUI release notes drafted
- [ ] README mentions experimental flag & scope
- [ ] Copilot instructions unchanged (no invariant changes)

## 10. Quality Gates
- [ ] Lint clean for modified/added GUI files
- [ ] Type check (mypy) clean for new modules
- [ ] No new flake/perf regressions (perf stub JSON saved)

## 11. Evidence Artifacts (to collect during execution)
- Perf JSON sample (flag on) stored (e.g., `tmp_perf_gate_gui.json`)
- Hash comparison log (two identical descriptor runs)
- Overlay pixel diff metrics (counts, ratio)
- Steps/sec sample value after warmup (~1s)

-- END CHECKLIST --
