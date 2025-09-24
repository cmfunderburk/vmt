## VMT Copilot Instructions (High‑Signal, ~45 lines)
Context: PyQt6 shell + fixed 320x240 Pygame Surface. Prime directives: determinism, single-frame pipeline, O(agents+resources) step.

Core Loop (do NOT restructure): `EmbeddedPygameWidget` owns ONE `QTimer` (16ms) → optional `Simulation.step(rng,use_decision)` → `_update_scene` → `update()` → `paintEvent` (Surface → bytes → `QImage` → `QPainter`). No extra timers, threads, while True, or Surface reallocation; do not change `SURFACE_SIZE` / `FRAME_INTERVAL_MS` without roadmap gate.

Determinism: Tie-break key exactly (-ΔU, distance, x, y). Sorted/stable resource iteration; agent list order resolves contests. Frozen constants: `EPSILON_UTILITY`, `default_PERCEPTION_RADIUS`. Metrics hash is contract—alter only with intentional test+doc update.

Preferred Construction: Use `Simulation.from_config(SimConfig, preference_factory, agent_positions=...)` (seeds RNG, wires optional `RespawnScheduler` + `MetricsCollector`). Preferences are pure stateless utility evaluators; register new ones in `preferences/factory.py` + tests (utility correctness, param validation, serialization round trip).

Hooks: `respawn_scheduler.step` & `metrics_collector.record` are optional O(n). New hook = single None check then return if absent. Alternating respawn (A↔B toggle) is deterministic, no extra RNG. Home placement: deterministic `seed+9973` sample; cached font draws `H{id}` once per frame (no per-agent font creation).

Performance Guardrails: Target ~62 FPS (floor ≥30). Diagnose: (1) Surface realloc? (2) per-frame object churn? (3) blocking I/O? Validate with `make perf` or `scripts/perf_stub.py --mode widget --duration 2 --json`. Overlays must cost <~2% FPS unless justified.

Rendering: Keep pipeline (`pygame.image.tostring(...,'RGBA')` → `QImage`). No per-pixel Python loops, dynamic surface sizes, or mid-frame scaling. Fonts cached (`_overlay_font`, `_paused_font`). Square cell sizing logic unchanged.

State Extension / Snapshot: Only append serialized fields (preserve order) in `snapshot.py` / `world.py`; update replay & hash tests to confirm parity for unchanged logic.

Complexity: Per-step stays linear; no new agent↔resource all-pairs scans. Experimental path/search logic requires feature flag + micro‑benchmark + gated approval.

Playback & Pacing: Controller logic (`simulation_controller.py`) governs throttling via `_should_step_now(now)`. No sleeps or alt timers. Turn mode starts paused (label invariant). Manual + auto step mix must match automatic hash (see tests).

Allowed: new preference, deterministic overlay (O(n)), metrics field append (with test update), minor doc sync. Forbidden: threads, extra timers, surface size change, silent tie-break/constant edits, mutable preference internals, hidden RNGs, unordered iteration.

Teardown: `closeEvent` order = stop timer → `pygame.quit()` → super. Mirror for any new subsystem.

Workflow Commands: Install `pip install -e .[dev]` | GUI `make dev` | Tests `make test` | Lint `make lint` | Types `make type` | Perf `make perf` | Legacy random walk `ECONSIM_LEGACY_RANDOM=1 make dev` | FPS debug `ECONSIM_DEBUG_FPS=1 make dev`.

Extension Steps (PR): 1) State intent & gate ref 2) Minimal diff 3) Tests + perf + hash check 4) Update docs/checklists 5) Summarize (Goal | Actions | Result | Next).

Adding Preference (quick): new class in `preferences/` → register in factory → tests (utility math, params, serialization) → no mutable state.

Landmarks: Loop `gui/embedded_pygame.py`; Controller `gui/simulation_controller.py`; Model: `simulation/world.py`, `grid.py`, `agent.py`; Respawn: `simulation/respawn.py`; Metrics: `simulation/metrics.py`; Snapshot: `simulation/snapshot.py`; Preferences: `preferences/*.py`; Config: `simulation/config.py`; Tests: `tests/unit/*`; Perf harness: `scripts/perf_stub.py`.

When Unsure: Read the specific test first; adjust code + corresponding test + docs atomically. Any untested change to determinism/perf is a regression.

Feedback welcome—flag unclear invariants so we can tighten these guardrails.