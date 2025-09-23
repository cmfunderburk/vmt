# GUI Critique (Post Gate 6 Review)

Date: 2025-09-23
Scope: Critical assessment of new GUI control + playback + determinism integration vs core simulation invariants.

## 1. Summary of Issues (Ranked)
| Severity | Issue | Location | Core Risk |
|----------|-------|----------|-----------|
| HIGH | Manual step creates fresh `random.Random(999)` each invocation and always uses `use_decision=True` | `src/econsim/gui/simulation_controller.py` (`manual_step`) | Breaks determinism & legacy/decision parity when mixed with auto playback RNG + mode; hash divergence & confusing behavior |
| HIGH | Default playback throttle at 1 turn/sec | `src/econsim/gui/panels/controls_panel.py` | Perceived freeze; invalid performance signal; undermines real-time feedback |
| MEDIUM | Validation raises `ValueError` directly inside Qt slot | `src/econsim/gui/start_menu.py` | User-level mis-entry produces traceback instead of user-facing message; UX + stability hit |
| MEDIUM | Continuous FPS log spam (`[Gate1] Frames=...`) every second | `src/econsim/gui/embedded_pygame.py` | Log noise in long sessions / CI; obscures real warnings |
| LOW | Pause button initial label mismatches actual paused state in turn-mode | `src/econsim/gui/panels/controls_panel.py` + `main_window.py` | Initial interaction confusing; minor polish + cognitive load |
| CROSS-CUT | GUI tests skipped unless `ECONSIM_NEW_GUI=1` | `tests/unit/test_gui_*_new_gui.py` | Issues above can bypass standard CI; reduced safety net |

## 2. Root Cause Analysis
- RNG Split: Controller did not reuse simulation-owned or widget RNG; created ad-hoc deterministic seed each manual step, effectively forking timeline segments and forcing decision path.
- Mode Drift: Manual path hardcodes `use_decision=True`, ignoring legacy mode toggles / env semantics.
- Throttle Default: UI component prioritizes turn-based pedagogy but overrides baseline expectation of continuous simulation without providing explicit affordance to disable.
- Exception Surfacing: Direct raising leverages Python error flow instead of Qt-friendly validation channel (no localized message handling layer).
- Logging Residue: Early Gate 1 diagnostic FPS print left un-gated through later gates.
- Label Mismatch: Pause state established externally (turn-mode start paused) but control text not synchronized post-construction.
- Skipped Tests: Feature flag gating new GUI prevented baseline determinism / interaction regressions from failing CI by default.

## 3. Impact Assessment
- Determinism: Mixed manual + auto sessions produce divergent metrics hash sequences; snapshot/replay validity perception compromised.
- User Trust: Inconsistent behavior (legacy mode claims) vs observed decisions erodes interpretability for educational goals.
- Performance Perception: Artificial 1 Hz throttle can be misinterpreted as performance regression.
- UX/Adoption: Validation crash & mislabeled pause degrade first-run experience.
- Observability: FPS spam hides meaningful warnings; log-based performance diagnostics become noisy.
- QA Coverage: Reduced probability of early detection for GUI control regressions.

## 4. Remediation Plan (Minimal, Ordered)
1. RNG & Mode Unification (HIGH):
   - Add a persistent `self._manual_rng` (initialized once to same seed as widget RNG or derive from simulation.config.seed) OR reuse widget's `_sim_rng` via accessor.
   - Use currently active mode flag when invoking `simulation.step` (respect legacy override).
   - Add unit test: manual then auto stepping yields identical hash vs pure auto for N steps.
2. Throttle Default (HIGH):
   - Change default dropdown value to "Unlimited" (no enforced delay) while retaining turn-mode explicit throttle when that mode is selected.
   - Provide an internal constant for pedagogical presets; document in code.
3. Validation Handling (MEDIUM):
   - Wrap validation call in try/except; show `QMessageBox.warning` with sanitized message; keep stack out of user view.
   - Test: simulate invalid input -> no exception raised; dialog invocation mocked.
4. FPS Logging Gate (MEDIUM):
   - Guard with env flag `ECONSIM_DEBUG_FPS=1` or remove; silence by default.
   - Test: ensure no stdout lines matching pattern under default.
5. Pause Label Sync (LOW):
   - Initialize label text based on controller.is_paused() after controller injection.
   - Test: start paused -> button shows "Resume".
6. CI Coverage (CROSS-CUT):
   - Enable a minimal smoke GUI test path unconditionally (surface creation + one manual & one auto step).
   - Add explicit RNG consistency test (see step 1).

## 5. Test Additions (Draft Matrix)
| Test Name | Purpose | Scenario |
|-----------|---------|----------|
| `test_manual_vs_auto_hash_consistency` | Ensure manual + auto hybrid equals pure auto | Step sequence: manual(3) + auto(7) vs auto(10) |
| `test_manual_respects_legacy_mode` | Legacy mode manual steps use random walk path | Set env legacy + manual steps |
| `test_controls_default_unthrottled` | Verify default throttle implies no enforced delay | Inspect controller interval |
| `test_start_menu_invalid_input_dialog` | Prevent uncaught exception | Feed invalid grid size |
| `test_fps_logging_suppressed_by_default` | Ensure no spam | Capture stdout 1.2s |
| `test_pause_button_initial_label` | Label matches state | Start paused; inspect text |

## 6. Determinism Safeguards During Fixes
- Re-run determinism hash suite after RNG unification; update only if expected (should remain unchanged in pure auto scenario).
- Snapshot replay test must pass unchanged; if hash shifts due to RNG seed alignment, document explicitly in commit message.

## 7. Risk Mitigation Notes
- RNG change could expose latent reliance on previous manual-step randomness; isolate by feature flag if unexpected drift appears.
- Validation UI changes must avoid blocking (modal deadlock) in headless CI; use conditional skip or patch QMessageBox for tests.
- Removing FPS print reduces observability; provide optional debug flag to restore.

## 8. Effort & Sequencing Estimate
| Step | Effort (dev hours) | Risk | Parallelizable |
|------|--------------------|------|----------------|
| RNG & mode unification + tests | 1.0 | Medium (hash drift) | No |
| Throttle default change + test | 0.3 | Low | Yes (after RNG) |
| Validation handling + test | 0.5 | Low | Yes |
| FPS logging gate + test | 0.2 | Very Low | Yes |
| Pause label sync + test | 0.2 | Very Low | Yes |
| Smoke test enablement | 0.4 | Low | Yes |
| Total | ~2.6 | — | — |

## 9. Acceptance Criteria
- Manual + auto mixed run deterministically matches pure auto sequence (hash equality)
- Legacy mode honored for manual stepping (no decision path forced)
- Default playback not artificially throttled
- Invalid start menu input yields non-crashing user-visible message
- No FPS spam in logs under default env
- Initial pause button label correct
- Added tests pass under default CI without needing `ECONSIM_NEW_GUI=1`

## 10. Follow-Up (Optional Enhancements)
- Centralize RNG ownership in SimulationController to reduce cross-component leakage.
- Add a lightweight performance overlay toggle that piggybacks metrics collector (with overhead measurement).
- Provide a deterministic seed display in HUD for reproducibility transparency.

---
Prepared for planning discussion; ready to convert to Gate 7 preparatory tasks if approved.
