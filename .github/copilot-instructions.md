## VMT Copilot Instructions (Gate 6 Integration Pass – 40‑Line Target)
Purpose: Rapid orientation for AI agents contributing to a PyQt6 desktop app embedding a 320x240 Pygame surface plus a deterministic spatial economic simulation (Gates 1–5 complete; Gate 6 = integration & minimal factory/overlay wiring).

### Core Architecture
1. Single Qt event loop (no threads/while True). Frame cadence: `QTimer` 16ms in `EmbeddedPygameWidget` (`src/econsim/gui/embedded_pygame.py`).
2. Rendering path: off-screen `pygame.Surface` → `pygame.image.tostring(..., 'RGBA')` → `QImage` in `paintEvent`. Do NOT resize surface or add per-frame heap churn.
3. Simulation tick: `Simulation.step(rng, use_decision=...)` in `simulation/world.py` with legacy random walk vs deterministic greedy decision (`Agent.step_decision`).
	• Widget defaults to decision mode; set env `ECONSIM_LEGACY_RANDOM=1` or pass `decision_mode=False` to revert for legacy tests.
4. Hooks (optional): `respawn_scheduler`, `metrics_collector`; attach only when present—logic must remain inert if absent.
5. Preferences: contract in `src/econsim/preferences/` (pure `utility(bundle)`; no mutation). Factory-driven creation via `PreferenceFactory`.
6. Factory (Gate 6): `Simulation.from_config(config, preference_factory, agent_positions)` seeds deterministic RNG, builds grid, conditionally wires hooks.

### Determinism & Invariants
• Target tie-break key EXACT: (−ΔU, distance, x, y). Never alter ordering semantics.
• Perception & epsilon: `default_PERCEPTION_RADIUS`, `EPSILON_UTILITY` in `simulation/constants.py`—retain bootstrap to avoid zero-utility stalls.
• Agent list index resolves simultaneous contests (see `test_competition`).
• Resource iteration order stable (sorted) – do not replace with set/dict iteration without ordering guarantee.

### Performance Guardrails
• Baseline ~62 FPS (floor ≥30). If regression: check (a) surface size (b) new allocations in `_on_tick`/`paintEvent` (c) blocking I/O or sleeps.
• Quick perf: `make perf` or `python scripts/perf_stub.py --mode widget --duration 2 --json`.
• Keep `FRAME_INTERVAL_MS` & `SURFACE_SIZE` unchanged unless explicitly gate-scoped.

### Complexity Constraints
• Any per-step feature O(agents + resources); avoid nested scans beyond current patterns.
• Hooks must early-exit fast when disabled (None check only).

### Testing & Headless
• Headless: if `DISPLAY` unset ensure `SDL_VIDEODRIVER=dummy` & `QT_QPA_PLATFORM=offscreen` (already handled in widget/tests—mirror in new scripts).
• Drive GUI in tests via `app.processEvents()` bursts; never spin custom loops.
• Access protected members only in tests (e.g. `_frame`, `_surface`).

### Gate Workflow (Enforced)
1. Create `Gate_N_todos.md` + `GATE_N_CHECKLIST.md` before coding.
2. Implement minimal diff; document deferrals in gate docs.
3. After completion write `GATE_N_EVAL.md` mapping criteria → evidence before push.

### Allowed vs Forbidden
OK: new preference subclass + tests; overlay toggle wiring; metrics extension via optional collector; small doc corrections.
NOT OK: threads, blocking loops, enlarging surface, changing tie-break or perception constants silently, mutating state inside `utility`.

### Teardown & Resource Safety
In widget `closeEvent`: stop `QTimer`, then `pygame.quit()`. Replicate sequence for any new managed subsystem.

### AI Contribution Style
State intent → act → summarize (Goal | Actions | Result | Next). When uncertain, give 2–3 smallest viable options with recommendation; never expand scope silently.

Forward plan details: see `ROADMAP_REVISED.md` (Gates 6–9) & top-level `README.md` for implemented vs pending matrix.