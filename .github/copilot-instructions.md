## VMT Copilot Instructions (Post Gate 6)
Concise high-signal guide for AI agents working on a PyQt6 desktop app embedding a fixed 320x240 Pygame surface + deterministic spatial economic simulation.

### 1. Core Loop & Rendering (Do NOT Break)
1. Single Qt event loop; frame pacing via `QTimer` 16 ms inside `EmbeddedPygameWidget` (`src/econsim/gui/embedded_pygame.py`). No while True, no extra threads.
2. Render pipeline: off-screen `pygame.Surface` → `pygame.image.tostring(...,'RGBA')` → `QImage` in `paintEvent`. Keep surface size + pixel format constant; never allocate new surface per frame.
3. Simulation step invoked from timer: `Simulation.step(rng, use_decision=...)` (world). Widget default = decision mode; legacy random walk only when env `ECONSIM_LEGACY_RANDOM=1` or widget param `decision_mode=False`.

### 2. Determinism Invariants (Must Stay Exact)
Tie-break ordering key: (−ΔU, distance, x, y). Do not alter sign, field order, or append fields.
Stable resource iteration (sorted) & agent list order decide conflicts (`tests/unit` competition test). Do not introduce unordered structures.
Epsilon bootstrap constants: `EPSILON_UTILITY`, `default_PERCEPTION_RADIUS` in `simulation/constants.py`—unchanged unless gate-scoped.
Metrics determinism: hash from `metrics_collector` must remain identical for unchanged scenarios; update tests if and only if intentional model change.

### 3. Construction Pattern
Use `Simulation.from_config(SimConfig, preference_factory, agent_positions)` for new scenarios—this seeds RNG, wires optional `respawn_scheduler` & `metrics_collector`, and enforces defaults. Direct `Simulation(...)` only for legacy tests or narrow probes.
Preferences: pure `utility(bundle)` (no mutation); defined in `src/econsim/preferences/*`. Register new subclasses via `PreferenceFactory` with minimal diff + tests.

### 4. Optional Hooks (Remain Inert When Absent)
`respawn_scheduler` and `metrics_collector` are attached conditionally; any extension must be O(agents + resources) per tick and early-exit with a single None check.

### 5. Performance Guardrails
Baseline: ~62 FPS (floor ≥30). If regression, first inspect: (a) surface reallocation (b) per-frame Python object churn in `_on_tick` / `paintEvent` (c) blocking I/O / sleeps.
Quick perf commands: `make perf` or `python scripts/perf_stub.py --mode widget --duration 2 --json`.
Do not change `FRAME_INTERVAL_MS`, `SURFACE_SIZE` without explicit gate rationale.

### 6. Snapshot / Replay & Testing
Snapshot + restore parity (hash match) used for determinism validation. Maintain serialization shape when adding state (extend, don’t reorder existing keys if dict-based).
GUI/headless tests drive events via `app.processEvents()` bursts—never spin custom loops or sleeps. Headless safety: ensure new scripts mirror existing env guard (`SDL_VIDEODRIVER=dummy`, `QT_QPA_PLATFORM=offscreen` when `DISPLAY` absent).
Access protected members only inside tests (e.g., `_surface`, `_frame`). Keep new introspection helpers lightweight and documented.

### 7. Complexity & Algorithmic Limits
Per-step work must remain O(agents + resources). Avoid nested all-pairs scans or pathfinding explosions. If evaluating new search logic, gate with feature flag + micro-benchmark.

### 8. Allowed vs Forbidden
Allowed: new preference type + tests; small overlay or metrics extensions; deterministic factory config additions; doc sync; low-overhead visualization toggle.
Forbidden: threads / custom loops; enlarging surface; silent change to tie-break or perception constants; mutating preference internal state during `utility`; unordered iteration replacing deterministic order.

### 9. Teardown Discipline
`closeEvent`: stop timer before `pygame.quit()`. Replicate ordering for any added subsystem (stop → dispose → quit). No lingering timers after window close.

### 10. Contribution Style (Expectations)
State intent → perform minimal diff → summarize (Goal | Actions | Result | Next). Offer 2–3 smallest options when ambiguity exists. Never widen scope without an explicit gate or user request.

### 11. Quick Command Index
Env setup: `pip install -e .[dev]`
Run GUI: `make dev`
Run tests: `make test` (determinism, competition, respawn, metrics, snapshot, overlay, perf)
Perf sample: `python scripts/perf_stub.py --mode widget --duration 2 --json`
Legacy random walk: `ECONSIM_LEGACY_RANDOM=1 make dev`

### 12. When Extending
Add new state? Update snapshot & determinism test; keep backward order. Add preference? Provide serialize/deserialize + parameter validation test. Add overlay? Prove negligible FPS impact (<~2% diff) or document rationale.

Forward plan reference: `ROADMAP_REVISED.md` (active gates) and top-level `README.md` (implemented vs pending matrix).