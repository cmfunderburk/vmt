## VMT Copilot Instructions (High‑Signal, ~50 lines)
Educational micro‑econ spatial sim: PyQt6 shell embeds ONE fixed 320x240 Pygame Surface. Prime directives: determinism, single `QTimer`, per-step O(agents+resources), minimal allocations.

Frame Pipeline (DO NOT ALTER): `EmbeddedPygameWidget` owns sole `QTimer` (16ms) → optional `Simulation.step(ext_rng, use_decision)` → `_update_scene` (grid/resources/agents/overlays) → `update()` → `paintEvent` (Surface→bytes→`QImage`→`QPainter`). Forbidden: extra timers, loops, sleeps, threads, surface resize/reallocation, changing `SURFACE_SIZE` / `FRAME_INTERVAL_MS`.

Determinism Invariants:
* Target tie-break key EXACT: (-ΔU, distance, x, y)
* Stable resource order (grid serialize / iteration); agent list order resolves contests
* Constants frozen: `EPSILON_UTILITY`, `default_PERCEPTION_RADIUS`
* Metrics hash (`simulation/metrics.py`) = external contract
* RNG separation: external RNG (legacy movement) vs internal `Simulation._rng` (respawn & hooks). Never mix or add hidden randomness.

Construction: `Simulation.from_config(SimConfig, preference_factory, agent_positions=...)` seeds internal RNG + optional `RespawnScheduler` & `MetricsCollector`. Manual wiring only in legacy tests. Preferences are pure/stateless; register new types in `preferences/factory.py` with tests (validation, utility math, serialize round trip).

Respawn & Interval:
* Alternating A↔B via internal toggle + full empty‑cell seeded shuffle (eliminates positional bias)
* Interval gate: `(step % interval)==0` (GUI Off→None, 1,2,5,10). Disabling leaves scheduler attached but inert.
* Agent homes: deterministic secondary RNG (`seed+9973`), unique, labels cached font (no per-frame font alloc).

Rendering:
* Preserve pipeline; no per-pixel Python loops.
* Square cells = `min(surface_w//gw, surface_h//gh)`; unused margin stays blank (no centering math).
* Cache `_overlay_font` & `_paused_font`; no per-agent fonts.
* Overlays panel flags (grid, IDs, target arrows, home labels) are PURE RENDER—must not mutate state.

GUI / Pacing:
* `simulation_controller._should_step_now` governs throttled auto stepping (turns/sec). Paused start must yield identical hash when resumed at same step index.
* Manual stepping uses persistent RNG; mixing manual + auto must not change sequence ordering.

Performance Guardrails:
* Typical ~62 FPS; floor ≥30. Investigate drops: surface realloc? large per-frame allocations? logging?
* Validate: `make perf` or `python scripts/perf_stub.py --mode widget --duration 2 --json`. Overlays <~2% overhead.

State / Serialization:
* Extending `snapshot.py`, `world.py`, `agent.py`, `grid.py`: APPEND fields only; preserve order → hash & replay parity; update determinism tests.

Complexity Discipline:
* Each step O(agents + resources). Avoid all-pairs scans, pathfinding, heuristic planning unless behind feature flag + perf & determinism tests.

Allowed Fast Paths (low-risk): new preference type, deterministic overlay (O(n)), append metrics field (with tests), respawn/overlay parameter plumbing, doc sync. Forbidden: threads, extra timers, silent tie-break edits, constant changes, mutable preference objects, unordered iteration, new randomness.

Trading Fast Path (Gate 7): `enable_trading` adds co-location bilateral 1-unit swaps (O(agents) via single pass cell grouping). No new RNG, at most one trade per agent per step, inventories mutated before respawn/metrics, no snapshot/schema change.

Teardown: `closeEvent` → stop timer → `pygame.quit()` → `super().closeEvent(event)`; mirror sequence for any new subsystems.

Workflow Commands: install `pip install -e .[dev]`; GUI `make dev`; tests `make test`; lint `make lint`; types `make type`; perf `make perf`; legacy random walk `ECONSIM_LEGACY_RANDOM=1 make dev`; FPS debug `ECONSIM_DEBUG_FPS=1 make dev`.

PR Flow: (1) State intent + gate ref (2) Minimal diff (3) Add/adjust tests (determinism/perf if touched) (4) Perf + hash check (5) Sync docs (6) Summarize (Goal | Actions | Result | Next).

Gate Workflow (Mandatory Pre-Push): (1) Draft `Gate_N_todos.md` (scope, acceptance criteria, ordered steps) (2) Derive `GATE_N_CHECKLIST.md` (binary items) (3) Stakeholder agree & freeze scope (no silent creep) (4) Execute updating todos/checklist as you go (5) Write `GATE_N_EVAL.md` mapping each criterion → concrete evidence + perf impact + debt + residual risks + readiness (6) Only push after eval exists & reflects delivered vs promised. Always document deltas & performance impact.

Preference Add Recipe: new class in `preferences/` (`TYPE_NAME`, `utility`, validation, serialize/deserialize) → register in `factory.py` → tests (math edges, round trip) → no runtime mutation.

Key Files: GUI loop `gui/embedded_pygame.py`; Controller `gui/simulation_controller.py`; Model `simulation/world.py`, `agent.py`, `grid.py`; Respawn `simulation/respawn.py`; Metrics `simulation/metrics.py`; Snapshot `simulation/snapshot.py`; Preferences `preferences/*.py`; Config `simulation/config.py`; Tests `tests/unit/*`; Perf harness `scripts/perf_stub.py`.

When Unsure: read the test first. Any untested determinism/perf change = regression risk. If an invariant feels ambiguous, pause & propose a clarifying test before coding.