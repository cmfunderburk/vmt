# Initial Visual Demo Checklist — Turn Mode Visualization Enhancements

(Complete all items before declaring the initial visual demo baseline finalized.)

## Core Goals
- [x] Provide pedagogical, low-noise turn-based visualization
- [x] Support both manual stepping and automatic paced stepping
- [x] Preserve deterministic simulation state & hashes

## Feature Additions
- [x] Grid lines toggle (default on in turn mode)
- [x] Resource rendering (typed A/B colors reused)
- [x] Agent rendering (color encoding inventory balance)
- [x] Overlay HUD (turn count, remaining resources, per-agent inventory & utility)
- [x] Movement tails (configurable length; disable flag)
- [x] Recent move highlight (contrast tail head)
- [x] Fading collected resources (time-based alpha decay)
- [x] Deterministic density-based initial resource placement ( --density )
- [x] Respawn gating hook ( --respawn-every N )
- [x] Static background option (suppress legacy animated rectangle)
- [x] Play/Pause button (1 turn per second baseline) replacing mandatory key presses

## CLI / UX Flags
- [x] --turn-mode activates turn visualization features
- [x] --grid-lines (kept for explicit enabling outside default-on case)
- [x] --no-overlay disables HUD
- [x] --tail-length / --no-tails configure tails
- [x] --fade-ms controls resource fade duration
- [x] --density sets probabilistic placement (seeded for determinism)
- [x] --respawn-every sets respawn interval (0/omitted => none)
- [x] --pause-start respected (no initial auto-step when provided)

## Determinism Safeguards
- [x] Visual-only features do not alter decision path
- [x] Density placement seeded (matches supplied --seed)
- [x] Respawn scheduling tied to deterministic step counter

## Performance
- [x] Maintain ≥30 FPS with overlays/tails/fade active
- [x] No per-frame unbounded allocations (reuses surfaces / small lists only)

## Documentation
- [x] README updated (Turn Mode section & flags)
- [x] Internal code comments explain hooks (pre/post step callbacks)
- [x] Checklist added pre-eval

## Testing
- [x] Deterministic density test added
- [x] Existing decision/agent tests unchanged & passing
- [x] Smoke GUI run (headless) confirming no crash

## Exit Criteria
- [x] This checklist fully checked
- [x] Evaluation doc drafted (initial_visual_demo_eval.md)

-- END --
