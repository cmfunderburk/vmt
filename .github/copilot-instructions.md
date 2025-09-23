## VMT Copilot Instructions (Gate 5 Up-To-Date, 40‑Line Target)
Purpose: Fast orientation for coding agents contributing to a PyQt6 desktop app embedding a Pygame surface + deterministic economic simulation (Gates 1–5 complete: rendering, preferences, grid/agents, decision, respawn & metrics).

For forward scope sequencing (Gates 6–9) see `ROADMAP_REVISED.md`.

Architecture Snapshot:
1. Single Qt event loop, no threads, no while True; frame timing via `QTimer` (16 ms) in `EmbeddedPygameWidget` (`src/econsim/gui/embedded_pygame.py`).
2. Widget renders off-screen 320x240 `pygame.Surface` → RGBA bytes → `QImage` in `paintEvent`; do NOT enlarge surface or add per-frame allocations.
3. Simulation core: `Simulation.step(rng, use_decision=...)` orchestrates agents + grid hooks (respawn, metrics). Agents implement `step_decision` (greedy 1-step) & legacy `move_random` path.
4. Preferences (`src/econsim/preferences/`): uniform contract (`utility`, `update_params`, `serialize`, `deserialize`) with factory registry; tests rely on strict validation & determinism.
5. Grid stores typed resources in dict[(x,y)] -> {'A','B'} with stable `iter_resources_sorted()` for tie-break determinism.

Determinism & Invariants:
• Tie-break ordering for target selection: sort key (−ΔU, distance, x, y). Preserve exactly; tests assert identical trajectories.
• PERCEPTION_RADIUS & epsilon bootstrap (see `EPSILON_UTILITY`) avoid zero-utility stalls—retain logic when modifying decision code.
• Agent ordering (list index) confers priority in simultaneous contests (see `test_competition.py`).
• No mutation inside preference `utility`; must remain pure & fast.

Performance Guardrails:
• Baseline ~62 FPS; hard floor ≥30. Investigate regressions: (a) surface size (b) new allocations in tick/paint (c) accidental sleeps or blocking I/O.
• Use `make perf` or `python scripts/perf_stub.py --mode widget --duration 2 --json` for quick check.
• Keep `FRAME_INTERVAL_MS` and surface dimensions stable unless gate-scoped change approved.

Dynamics & Metrics (Gate 5):
• Respawn & metrics are optional hooks (`Simulation.respawn_scheduler`, `metrics_collector`) – isolate new logic behind presence checks; never break existing tests if absent.
• Any new per-step feature must be O(agents + resources) and avoid nested scans > current complexity.

Headless / Testing Pattern:
• If `DISPLAY` unset: set `SDL_VIDEODRIVER=dummy`, `QT_QPA_PLATFORM=offscreen` (tests & perf script already do this). Replicate in new test scripts.
• Drive GUI in tests via short loop `app.processEvents()`; never spin custom loops.
• Access protected members only in tests (e.g., `_frame`).

Workflow & Gating:
1. For new scope create `Gate_N_todos.md` + `GATE_N_CHECKLIST.md` before coding.
2. After implementation document evidence in `GATE_N_EVAL.md` before merge.
3. Keep changes smallest-surface; defer speculative abstractions (record deferral in gate docs).

Mandatory Gate Workflow (ENFORCE BEFORE ANY GIT PUSH):
1. Generate Todo List: `Gate_N_todos.md` (scope, acceptance criteria, step-by-step plan).
2. Create Checklist: derive actionable items into `GATE_N_CHECKLIST.md`.
3. Discuss & Agree: validate scope, risks, timeline with stakeholder BEFORE coding.
4. Execute Systematically: implement steps, updating todos & checklist status as you go.
5. Write Retrospective Eval: `GATE_N_EVAL.md` mapping each criterion to evidence; list gaps, risks, performance impact, technical debt, readiness.
6. ONLY THEN: git commit/push (after evaluation documents completion explicitly).
Violation = scope creep risk. Always document delivered vs promised, perf impact, debt, readiness for next gate.

Allowed vs Not Allowed:
• OK: add preference subclass + tests; add lightweight overlay toggle; extend metrics via optional collector.
• NOT OK: introduce threading, blocking loops, enlarge surface, change tie-break, mutate preference state mid-step.

Teardown Discipline: In `closeEvent` always stop QTimer then `pygame.quit()`. Mirror pattern for any new managed resource.

AI Response Style: Start with intent; act immediately; summarize (Goal | Actions | Result | Next). Offer concise options when ambiguous; default to smallest diff.

When Unsure: Present 2–3 minimal options + recommendation; never silently broaden scope.