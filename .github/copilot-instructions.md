## VMT Copilot Instructions (High‑Signal, ~50 lines)
Context: Educational micro‑econ spatial sim. PyQt6 shell embeds ONE fixed 320x240 Pygame Surface. Prime directives: determinism, single QTimer frame loop, O(agents+resources) step, minimal allocations.

Architecture: Dual GUI paths via feature flags. New GUI (`ECONSIM_NEW_GUI=1`) provides start menu + simulation controller stack. Legacy path creates minimal bootstrap window. Both share the core `EmbeddedPygameWidget` rendering pipeline.

Core Frame Pipeline (DO NOT RESTRUCTURE): `EmbeddedPygameWidget` owns a single `QTimer` (16ms) → optional `Simulation.step(ext_rng, use_decision)` → `_update_scene` (draw grid/resources/agents/overlays) → `update()` → `paintEvent` (Surface→bytes→`QImage`→`QPainter`). Forbidden: extra timers, while True loops, sleeps, threads, Surface reallocation, SURFACE_SIZE / FRAME_INTERVAL_MS changes.

Determinism Invariants:
- Target tie-break key EXACT: (-ΔU, distance, x, y)
- Stable resource order (`iter_resources_sorted` if order-sensitive); original agent list order resolves contests
- Frozen constants: `EPSILON_UTILITY`, `default_PERCEPTION_RADIUS`
- Metrics hash (see `simulation/metrics.py`) is external contract
- RNG separation: external RNG (legacy movement) vs internal `Simulation._rng` (respawn, hooks). No hidden randomness.

Construction Path: `Simulation.from_config(SimConfig, preference_factory, agent_positions=...)` seeds internal RNG + optional `RespawnScheduler` & `MetricsCollector`. Manual wiring only in legacy tests. Preferences are pure & stateless; register new types in `preferences/factory.py` with full tests (validation, utility math, serialize round trip).

Testing Strategy: Determinism via reproducible hash tests (`test_determinism_hash.py`), performance gates (`make perf`, acceptable floor ≥30 FPS), decision mode validation. All state-changing features require regression tests. Test structure mirrors src layout: `tests/unit/test_*.py`.

Respawn & Interval:
- Alternating resource types A↔B deterministic toggle + uniform seeded empty‑cell shuffle (removes positional bias)
- Interval gating: `(step % interval)==0`; GUI dropdown maps (Off→None, 1,2,5,10). Disabling leaves scheduler attached but inert.
- Agent homes: deterministic secondary RNG (`seed+9973`), non‑overlapping; home labels cached font.

Rendering Rules:
- Keep pipeline intact; no per-pixel Python mutation.
- Square cell sizing = min(surface_w//gw, surface_h//gh); leave extra margin unused (no centering math).
- Cache fonts (`_overlay_font`, `_paused_font`); no per-agent font objects.

GUI / Pacing:
- `simulation_controller.py` decides stepping via `_should_step_now`; paused start yields identical hash if resumed at same step sequence.
- Overlays panel toggles (grid, agent IDs, target arrows, home labels) are render-only—must not mutate state.

Performance Guardrails:
- Typical ~62 FPS; acceptable floor ≥30. Diagnose drops: Surface realloc? Per-frame list/build? Logging?
- Validate: `make perf` or `python scripts/perf_stub.py --mode widget --duration 2 --json`. Overlays <~2% overhead.

State / Serialization:
- When extending `snapshot.py`, `world.py`, `agent.py`, `grid.py`: APPEND fields only; preserve order for hash/replay parity; adjust determinism tests accordingly.

Complexity Discipline:
- Per-step O(agents+resources). No all-pairs scans, pathfinding, or heuristic planning without feature flag + perf test.

Allowed Fast Path: new preference type, deterministic overlay (O(n)), append metrics field (with tests), respawn/overlay parameter plumbing, minor doc sync. Forbidden: threads, extra timers, silent tie-break edits, constant changes, mutable preference state, unordered iteration, hidden RNG.

Teardown Order: `closeEvent` → stop timer → `pygame.quit()` → `super().closeEvent(event)`; mirror for new subsystems.

Workflow Commands: install `pip install -e .[dev]`; run GUI `make dev`; tests `make test`; lint `make lint`; types `make type`; perf `make perf`; legacy random walk `ECONSIM_LEGACY_RANDOM=1 make dev`; FPS debug `ECONSIM_DEBUG_FPS=1 make dev`.

Gate Workflow (Before Push): Create `Gate_N_todos.md` + `GATE_N_CHECKLIST.md` → stakeholder agreement → execute steps → `GATE_N_EVAL.md` retrospective (criteria→evidence, perf/debt/risks) → only then commit. No silent scope creep.

PR Flow: (1) State intent + gate ref (2) Minimal diff (3) Add/adjust tests (determinism/perf if touched) (4) Perf + hash check (5) Sync docs (6) Summarize (Goal | Actions | Result | Next).

Quick Preference Add: new class in `preferences/` (`TYPE_NAME`, `utility`, validation, serialize/deserialize) → register in `factory.py` → tests (math, edge params, round trip) → no runtime mutation.

Key Files: GUI loop `gui/embedded_pygame.py`; Controller `gui/simulation_controller.py`; Model `simulation/world.py`, `agent.py`, `grid.py`; Respawn `simulation/respawn.py`; Metrics `simulation/metrics.py`; Snapshot `simulation/snapshot.py`; Preferences `preferences/*.py`; Config `simulation/config.py`; Tests `tests/unit/*`; Perf harness `scripts/perf_stub.py`.

When Unsure: read the test covering the area first. Any untested determinism/perf change = regression. If an invariant seems ambiguous, pause and propose a clarifying test before expanding scope.