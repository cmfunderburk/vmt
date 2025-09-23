# GATE_GUI_FIX_CHECKLIST
Date: 2025-09-23
Gate: GUI Fix (Determinism & UX Remediation)

## Acceptance Criteria (Binary)
- [x] 1. Hash parity: manual(3)+auto(7) == auto(10) (see `tests/unit/test_manual_auto_hash_parity.py`)
- [x] 2. Legacy mode manual steps follow random walk path (see `test_legacy_mode_manual_randomness.py`)
- [x] 3a. Turn mode defaults to 1.0 tps (pacing label '(pacing)'; `test_pacing_defaults.py::test_turn_mode_defaults_to_1_tps_with_label`)
- [x] 3b. Continuous / legacy modes default to Unlimited (`test_pacing_defaults.py`)
- [x] 3c. Switching from 1.0 tps to Unlimited increases observed step rate (`test_pacing_unlimited_speedup.py`)
- [x] 4. Invalid start menu input triggers QMessageBox (`test_start_menu_invalid_input_dialog.py`)
- [x] 5. No `[FPS]` output under default env (`test_fps_logging_gate.py::test_fps_logging_suppressed_without_flag`)
- [x] 6. Initial pause button label matches paused state (`test_pause_button_initial_label.py`)
- [x] 7. New GUI tests run unflagged (`test_new_gui_unflagged_smoke.py`)

## Implementation Steps
- [x] RNG unified for manual & auto steps (single persistent RNG)
- [x] Manual stepping respects active mode flag (legacy vs decision)
- [x] Added test: `test_manual_auto_hash_parity` (hash parity)
- [x] Added test: `test_legacy_mode_manual_randomness`
- [x] Unlimited option added to speed dropdown
- [x] Mode-aware default selection implemented (turn=1.0 tps, others=Unlimited)
- [x] Pacing label appears only when throttled at 1.0 tps
- [x] Added test: `test_pacing_defaults`
- [x] Start menu validation wrapped with QMessageBox fallback
- [x] Added test: `test_start_menu_invalid_input_dialog`
- [x] FPS logging gated behind `ECONSIM_DEBUG_FPS` env var
- [x] Added test: `test_fps_logging_gate`
- [x] Pause button label sync implemented
- [x] Added test: `test_pause_button_initial_label`
- [x] Always-on GUI smoke test added (unflagged)
- [ ] Documentation updated (`.github/copilot-instructions.md`) if RNG accessor added (PENDING doc sync)

## Evidence Collection
- [x] Captured determinism hashes (auto vs hybrid) — enforced by `test_manual_plus_auto_matches_pure_auto` (91 tests passed including new parity test)
- [x] Captured stdout sample (no FPS spam) via `test_fps_logging_gate` assertion
- [x] Screenshot / text dump of initial button label (proxy: `test_pause_button_initial_label` assertion)
- [ ] CI run log showing GUI tests executed (Pending CI run)

## Retrospective Preparation
- [ ] Draft `GATE_GUI_FIX_EVAL.md` with criteria → evidence mapping
- [ ] Note any residual risks / deferred items
- [ ] Confirm no unintended hash drift in pure auto path

## Ready to Commit / Push
- [ ] All acceptance criteria checked
- [ ] Retrospective completed & stored
- [ ] Stakeholder sign-off recorded
