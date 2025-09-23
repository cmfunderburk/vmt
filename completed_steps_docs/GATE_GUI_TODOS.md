# GATE_GUI_TODOS — Execution Tasks (Phase A Fast Path)

Source Plan: `tmp_plans/gui_step_impl_plan_phaseA_fastpath.md`
Status Legend: ☐ pending · ⧖ in-progress · ✔ done · ⚑ blocked

## Batch 1 — Foundations & Validation
1. ☐ Refactor `start_menu.py` formatting (remove semicolons) & add validation helpers
2. ☐ Add `test_session_descriptor_validation.py`
3. ☐ Gate all new imports behind `should_use_new_gui()` checks (defensive)

## Batch 2 — Overlay State & Rendering
4. ☐ Add `OverlayState` dataclass & integration into widget (post-instantiation assignment)
5. ☐ Implement grid lines render (lightweight line draw)
6. ☐ Implement agent IDs (small font) & target arrow (triangle or line)
7. ☐ Add `test_overlay_toggle_pixels.py` (skip if headless unsupported)

## Batch 3 — Controls & Turn Mode
8. ☐ Expand ControlsPanel: Pause/Resume, Step 1, Step 5, Hash Refresh buttons
9. ☐ Controller pause/resume logic centralizing step gating
10. ☐ Implement turn mode (auto-pause + hidden pause button)
11. ☐ `test_controller_pause_and_step.py`
12. ☐ `test_turn_mode_no_autostep.py`

## Batch 4 — Metrics & Hash
13. ☐ Rolling steps/sec estimator (deque timestamps)
14. ☐ Hash caching + refresh method
15. ☐ Metrics panel wiring to steps/sec + truncated hash + tooltip
16. ☐ `test_steps_per_sec_estimator.py`
17. ☐ `test_hash_refresh_cache_behavior.py`

## Batch 5 — Navigation & Teardown
18. ☐ Back to menu action stops timer, deletes widget, clears controller
19. ☐ Idempotent teardown guard
20. ☐ `test_navigation_teardown_reuse.py`

## Batch 6 — Perf & Evidence
21. ☐ Run perf stub baseline (flag off) store JSON
22. ☐ Run perf stub with overlays off (flag on) store JSON
23. ☐ Run perf stub with overlays on (all toggled) store JSON
24. ☐ Compare FPS deltas (<2% overlay cost); embed summary in release notes

## Batch 7 — Lint & Type Hygiene
25. ☐ Apply targeted lint fixes for modified GUI files
26. ☐ Run mypy; resolve new type issues (avoid large refactors)

## Batch 8 — Docs & Release Notes
27. ☐ Update fast-path plan with completion markers
28. ☐ Draft `GATE_GUI_RELEASE_NOTES_DRAFT.md`
29. ☐ README experimental flag note
30. ☐ Update checklist statuses

## Stretch / Optional (If Time Allows)
31. ☐ Simple auto metrics refresh (500ms) (ensure opt-in or negligible cost)
32. ☐ Basic error message label on menu for validation failures

-- END TODOS --
