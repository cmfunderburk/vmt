## VMT Copilot Instructions (Concise, Actionable, Gate 4)
Purpose: Immediate orientation for AI agents contributing to a PyQt6 desktop app embedding a Pygame surface with an injectable simulation layer (Gates 1–4 implemented: rendering, preferences, grid/agents, decision + overlays).

Architecture:
1. Single process / single Qt event loop. No threads, no while True loops.
2. `EmbeddedPygameWidget` (`src/econsim/gui/embedded_pygame.py`) owns a QTimer (~16 ms) updating an off-screen 320x240 Surface → RGBA bytes → `QImage` in `paintEvent`.
3. Simulation (Gate 3/4) is optional: object with `step(rng)` plus attributes `grid`, `agents`; grid exposes `iter_resources()`. Rendering overlays read these; keep interface minimal.
4. Preferences system (`src/econsim/preferences/`) provides uniform contract (`utility`, `update_params`, `serialize`) for Cobb-Douglas, Perfect Substitutes, Leontief; validated by tests.

Gate Workflow (MUST FOLLOW before pushing):
1. Draft `Gate_N_todos.md` (scope + acceptance criteria)  2. Create `GATE_N_CHECKLIST.md`  3. Align with stakeholder  4. Implement & update docs  5. Write `GATE_N_EVAL.md` (evidence + gaps)  6. THEN commit/push.

Core Commands (use Make targets): `make dev` (launch GUI) · `make test` (unit+perf guards) · `make lint` · `make format` · `make type` · `make perf` (quick FPS / synthetic).

Headless Pattern: If no DISPLAY set: ensure `SDL_VIDEODRIVER=dummy` and `QT_QPA_PLATFORM=offscreen` (see tests + `scripts/perf_stub.py`). Mirror in any new perf/test code.

Performance Guardrails: Baseline ~62 FPS; minimum acceptable ≥30 FPS. If regression: (a) check per-frame allocations (image conversion already minimal) (b) avoid enlarging Surface (c) confirm `FRAME_INTERVAL_MS` unchanged. Use: `python scripts/perf_stub.py --mode widget --duration 2 --json`.

Determinism & Decision Logic: Tests enforce identical agent trajectories and bounded decision overhead (competition, preference shift, epsilon bootstrap). Preserve tie-break order (−ΔU, distance, x, y) if touching selection code.

Safe Changes Examples: OK—add simulation parameter, new preference subclass + factory registration + tests, lightweight perf flag. NOT OK—introduce threads, blocking loops, expand widget into simulation orchestrator, un-gated scope creep.

Teardown Discipline: In widget `closeEvent`: stop QTimer, `pygame.quit()`. Any new resource: mirror this pattern and extend tests if needed.

Testing Conventions: Short loops using `app.processEvents()`. Probe protected attributes only in tests (e.g., `_frame`). Always set headless env vars early when adding a test that initializes Qt/Pygame.

Response Style for AI: Start with intent sentence, act immediately, summarize delta (Goal | Actions | Result | Next). Offer A/B options when ambiguity exists; avoid reprinting this file.

When Unsure: Default to smallest diff preserving current public surface; document deferrals in the appropriate Gate doc before implementing larger shifts.

Questions or edge tradeoffs: present concise options + recommendation.