# Gate GUI Fix (Determinism & UX Remediation)

Date: 2025-09-23
Gate Identifier: GUI_FIX (pre–Gate 7 hygiene)
Scope Statement: Eliminate GUI-induced determinism drift, remove misleading throttles/log noise, and align user controls with actual simulation state while adding minimal CI coverage.

## 1. Objectives
- Preserve core simulation determinism across manual + auto step combinations.
- Provide accurate real-time playback by default (no artificial 1 Hz throttle).
- Replace crashy validation path with user-facing messaging.
- Suppress non-essential frame logging unless explicitly enabled.
- Align initial control labels with actual paused state.
- Add minimal always-on GUI smoke & determinism tests (no env flag required).

## 2. Success / Acceptance Criteria
1. Hash parity: manual(3)+auto(7) == auto(10).
2. Legacy mode respected: manual steps do NOT force decision path (observed movement pattern matches random walk path for same seed).
3. Default control throttle = unthrottled (continuous) unless user selects a turn rate.
4. Invalid start menu inputs produce QMessageBox (no uncaught ValueError in stderr).
5. No `[Gate1] Frames=` spam under default env.
6. Pause button initial label reflects `controller.is_paused()` state (e.g., shows `Resume` if paused at start).
7. New tests run in standard CI (no ECONSIM_NEW_GUI flag) and pass.

## 3. Non-Goals / Out of Scope
- Adding new overlays or HUD metrics.
- Refactoring broader controller architecture beyond RNG unification.
- Performance micro-optimizations outside removing throttle/log noise.

## 4. Constraints
- Must not alter existing determinism hash in pure auto decision mode scenarios.
- Maintain O(agents+resources) per frame.
- No new threads or event loops.

## 5. Ordered Implementation Steps
1. RNG Unification – COMPLETED (see controller diff & checklist)
2. Manual vs Auto Hash Test – COMPLETED (`test_manual_auto_hash_parity.py`)
3. Legacy Mode Manual Test – COMPLETED (`test_legacy_mode_manual_randomness.py`)
4. Throttle / Pacing Defaults – COMPLETED (`test_pacing_defaults.py`, `test_pacing_unlimited_speedup.py`)
5. Validation Handling – COMPLETED (`test_start_menu_invalid_input_dialog.py`)
6. FPS Logging Gate – COMPLETED (`test_fps_logging_gate.py`)
7. Pause Label Sync – COMPLETED (`test_pause_button_initial_label.py`)
8. Always-On GUI Smoke – COMPLETED (`test_new_gui_unflagged_smoke.py`)
9. Documentation Update – COMPLETED (instructions addendum) *(RNG accessor doc sync not required beyond pacing/FPS section)*
10. Checklist Review & Adjustments – COMPLETED (`GATE_GUI_FIX_CHECKLIST.md` updated)
11. Retrospective – COMPLETED (`GATE_GUI_FIX_EVAL.md`)
12. Commit & Push – PENDING stakeholder sign-off

## 6. Risk & Mitigation Summary
| Risk | Mitigation |
|------|------------|
| Hash drift from RNG change | Run determinism suite before/after; if drift only in hybrid path, document rationale. |
| GUI tests flaky headless | Use offscreen platform flags already present; keep tests minimal in duration. |
| QMessageBox blocks CI | Patch/monkeypatch in tests to avoid actual dialog. |

## 7. Metrics / Evidence to Capture
- Determinism hash values for: auto(10) run vs manual(3)+auto(7).
- Stdout log snippet (absence of FPS line) for 1.2s run.
- Screenshot or textual dump of initial pause button label state.

## 8. Exit Criteria Checklist Pointer
See `GATE_GUI_FIX_CHECKLIST.md` (to be created) for binary validation items.

---
Prepared for stakeholder review. After approval -> execute steps in order.
