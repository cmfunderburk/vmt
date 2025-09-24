## VMT Copilot Instructions (High‑Signal, ~55 lines)
Context: Educational microeconomic sim: PyQt6 shell + fixed 320x240 off‑screen Pygame Surface. Prime directives: determinism, single-frame pipeline, O(agents+resources) step cost, minimal object churn.

Core Render/Step Loop (DO NOT RESTRUCTURE): `EmbeddedPygameWidget` owns ONE `QTimer` (16 ms) → optional `Simulation.step(ext_rng, use_decision)` → `_update_scene` (draw resources, agents, overlays) → `update()` → `paintEvent` (Surface→bytes→`QImage`→`QPainter`). No additional timers, threads, sleeps, while True loops, or Surface re-allocation. Do not change `SURFACE_SIZE` / `FRAME_INTERVAL_MS` without roadmap approval.

Determinism Invariants:
- Target selection tie-break key EXACT: (-ΔU, distance, x, y).
- Resource iteration stable (use `iter_resources_sorted` if order matters); agent list order breaks contests.
- Frozen constants: `EPSILON_UTILITY`, `default_PERCEPTION_RADIUS` (decision scan), perception radius parameterization deferred.
- Metrics hash (see `simulation/metrics.py`) is a public contract; change only with updated tests + docs.
- RNG separation: external RNG passed to `Simulation.step` for legacy movement; internal `Simulation._rng` seeds respawn + future systems (seed = config.seed). No hidden RNGs.

Preferred Construction Path: `Simulation.from_config(SimConfig, preference_factory, agent_positions=...)` seeds internal RNG, attaches optional `RespawnScheduler` & `MetricsCollector`. Only use manual wiring in legacy tests. Preferences are pure stateless utility evaluators (see `preferences/*.py`). Register new preference types in `preferences/factory.py`; provide tests: parameter validation, utility math, serialize/deserialize round trip.

Hooks & Respawn:
- `respawn_scheduler.step(grid, rng, step_index)` & `metrics_collector.record(step, sim)` are optional; always guard with a single None check.
- Respawn: deterministic alternating resource types A↔B + uniform seeded empty-cell shuffle (no positional bias). Interval gating: `(step % interval)==0` (pure arithmetic) controlled by GUI dropdown; interval None/<=0 disables without detaching scheduler.
- Agent home placement: deterministic `seed+9973` secondary RNG; home labels cached font once per session.

Rendering Constraints:
- Keep pipeline: `pygame.image.tostring(surface,'RGBA')` → `QImage` → `QPainter.drawImage` (no scaling loops, no per-pixel Python).
- Square cell sizing logic (min dimension) — do not re-center or introduce dynamic surfaces.
- Cache fonts (`_overlay_font`, `_paused_font`); no per-agent font creation.

Performance Guardrails:
- Target ~62 FPS (acceptable floor ≥30). Diagnose drops: (1) surface realloc? (2) per-frame allocations (fonts, large lists) (3) blocking I/O/log spam.
- Use `make perf` or `python scripts/perf_stub.py --mode widget --duration 2 --json` to validate. Overlays should add <~2% overhead.

State / Serialization:
- When extending snapshot/state (`simulation/snapshot.py`, `world.py`, `agent.py`, `grid.py`), only APPEND new serialized fields; preserve order for hash/replay parity. Update determinism & replay tests accordingly.

Complexity Discipline:
- Per-step must remain O(agents + resources). No all-pairs scans or heuristic pathfinding without feature flag + micro-benchmark + perf test. Greedy 1-step movement only.

Playback & Pacing:
- `simulation_controller.py` handles pacing via `_should_step_now(now)` and `is_paused()`. No sleeps. Start-paused sessions must produce identical hashes after identical step sequences.

Allowed (fast path): new preference type, deterministic overlay (O(n)), append metrics field (update tests), minor doc sync, respawn/overlay parameter plumbing. Forbidden: threads, extra timers, surface size change, silent tie-break or constant edits, mutable internal state in preferences, unordered iteration, hidden randomness.

Teardown Order: `closeEvent` → stop timer → `pygame.quit()` → `super().closeEvent(event)`. Mirror this sequence for any new subsystem teardown.

Workflow Commands: install `pip install -e .[dev]`; GUI `make dev`; tests `make test`; lint `make lint`; types `make type`; perf `make perf`; legacy random walk `ECONSIM_LEGACY_RANDOM=1 make dev`; FPS debug `ECONSIM_DEBUG_FPS=1 make dev`.

Extension / PR Flow: (1) State intent + gate ref (2) Minimal diff (3) Add/adjust tests (determinism/perf if touched) (4) Run perf + hash check (5) Update docs/checklists (6) Summarize (Goal | Actions | Result | Next).

Quick Preference Add: create class in `preferences/` (define `TYPE_NAME`, `utility`, validation, `serialize/deserialize`) → register in `factory.py` → tests (math correctness, param edge cases, serialization) → no runtime mutation.

Key Landmarks: GUI loop `gui/embedded_pygame.py`; Controller `gui/simulation_controller.py`; Core model: `simulation/world.py`, `grid.py`, `agent.py`; Respawn: `simulation/respawn.py`; Metrics: `simulation/metrics.py`; Snapshot: `simulation/snapshot.py`; Preferences: `preferences/*.py`; Config: `simulation/config.py`; Tests: `tests/unit/*`; Perf harness: `scripts/perf_stub.py`.

When Unsure: Read the relevant test first; keep code+tests+docs synchronized in the same PR. Any untested determinism or performance change is a regression.

Feedback: If an invariant seems ambiguous (tie-break, hash scope, pacing), flag it and propose a clarifying test before enlarging behavior.