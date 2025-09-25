# GATE – Forage / Exchange Dual Gating Remediation Checklist

Status Legend: [ ] pending, [~] in progress, [x] done, [!] blocked

## Core Remediation Tasks
1. [ ] Autouse fixture: reset `ECONSIM_FORAGE_ENABLED` to '1' each test (prevent leakage).
2. [ ] Restore simulation stepping & movement (adjust `_on_tick` guards, ensure frame advances).
3. [ ] Investigate & fix decision-mode hash parity (draft vs exec).
4. [ ] Overlay alias `_show_overlay` → `show_overlay` (legacy test compatibility).
5. [ ] Ensure overlay draws (pixel diff > threshold); add deterministic marker only if needed.
6. [ ] Refcount / shutdown: ensure `pygame.get_init()` false after last widget close.
7. [ ] Re-run failing test modules individually; document results.
8. [ ] Full suite green twice consecutively (record run IDs / timestamps).
9. [ ] Perf sanity: run `scripts/perf_stub.py --mode widget --duration 2 --json tmp_perf_gating.json` (capture FPS, frame count).
10. [ ] Documentation updates: README + API_GUIDE gating matrix & precedence description.

## Validation Artifacts To Capture
- Decision movement restoration: before/after log (first 5 steps agent positions).
- Hash parity: print hashes (draft-only vs execution) pre-fix & post-fix.
- Overlay diff: percentage pixel change (expected ≥2%).
- Shutdown: log `_PYGAME_INIT_COUNT` before & after widget close.
- Perf: JSON snippet (fps_avg, frames, duration, agents/resources counts).

## Risk Mitigations
- Confirm no additional per-frame allocations introduced.
- Maintain determinism (stable ordering: tie-break key (-ΔU, distance, x, y)).
- Avoid modifying constants (`EPSILON_UTILITY`, `default_PERCEPTION_RADIUS`).

## Sign-off Criteria
- All checklist items 1–10 marked [x].
- No new failing tests introduced.
- Determinism hash unchanged for baseline scenarios (store comparison evidence hash list).
- README / API_GUIDE updated without altering unrelated sections.

---
Created: 2025-09-24
