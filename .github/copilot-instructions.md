## VMT Copilot Instructions (High‑Signal, ~50 lines)
Context: Educational micro‑econ spatial sim. PyQt6 hosts ONE embedded Pygame Surface (320–800 squared). Prime directives: determinism, single QTimer frame loop, O(agents+resources) step, minimal per‑tick allocations.

Architecture: Dual GUI (Start Menu vs legacy) via `ECONSIM_NEW_GUI=1` (default); shared core: `EmbeddedPygameWidget` + `Simulation` (`simulation/world.py`). Post-Gate 6 with bilateral exchange Phase 3 completed.

Frame Pipeline (DO NOT ALTER): single `QTimer` (≈16ms) → `Simulation.step(ext_rng, use_decision)` (optional) → `_update_scene` → `update()` → `paintEvent` (Surface→bytes→`QImage`→`QPainter`). Forbidden: extra timers, threads, sleeps, blocking loops, surface reallocation, per‑pixel Python loops, resizing logic changes.

Determinism Invariants:
- Target tie-break key EXACT: (-ΔU, distance, x, y)
- Stable resource iteration (`iter_resources_sorted`); original agent list order resolves contests
- Frozen constants: `EPSILON_UTILITY`, `default_PERCEPTION_RADIUS`
- Metrics hash contract in `simulation/metrics.py` (trade + debug overlay metrics excluded)
- RNG separation: external RNG (legacy/random walk) vs internal `Simulation._rng` (respawn, homes, trade drafts). No hidden randomness.

Construction: Prefer `Simulation.from_config(SimConfig, preference_factory, agent_positions=...)`. Attaches deterministic `RespawnScheduler`, `MetricsCollector`; homes seeded via secondary RNG offset (`seed+9973`). Preferences are pure/stateless; register new ones in `preferences/factory.py` with tests (validation, utility math, serialize round‑trip).

Respawn: Alternating A↔B assignment; placement = uniform seeded shuffle of empty cells. Interval gating: `(step % interval)==0`; Off leaves scheduler inert. GUI dropdowns: Interval (Off,1,5,10,20) + Rate (10–100%).

Foraging Flag: `ECONSIM_FORAGE_ENABLED=0` disables resource collection. If trading also off → agents idle in place preserving carrying inventory (no implicit deposit). If trading on → agents may trade without new gathering (see bilateral system below).

Trading (Default ON in GUI): `ECONSIM_TRADE_DRAFT`, `ECONSIM_TRADE_EXEC`, `ECONSIM_TRADE_PRIORITY_DELTA`, `ECONSIM_TRADE_GUI_INFO`, `ECONSIM_TRADE_DEBUG_OVERLAY`. Bilateral exchange system with 6-tier decision logic: perception → pairing → pathfinding → co-location → trading → cooldowns. Only currently carried units exchange; home inventory immutable. At most one executed intent/step. Priority flag must ONLY reorder identical multiset of intents. Hash parity redesign pending; trade metrics excluded. Optional `ECONSIM_TRADE_HASH_NEUTRAL=1` restores carrying inventories post-hash (debug mode, not default). SimulationController toggles: `set_bilateral_enabled(bool)` manages flag cluster.

Bilateral Exchange Movement (forage disabled & trade enabled path): Sophisticated partner search in `Simulation._handle_bilateral_exchange_movement`: perception radius scan → availability filters (cooldowns, pairing) → meeting-point pathfinding → co-location trading → dual cooldown system. Utility-maximizing 1-for-1 goods swapping using marginal utility calculations. Stagnation tracking prevents infinite loops. Keep it O(agents); no global all-pairs beyond localized scan already implemented.

Rendering Rules:
- Preserve pipeline; no per-agent font objects (cache `_overlay_font`, `_paused_font`).
- Cell size = `min(surface_w//gw, surface_h//gh)`; no centering math for leftover margin.
- Sprites loaded from `vmt_sprites_pack_1/`; scaled each frame (acceptable); fallback to colored rects.
- Overlays (grid, IDs, homes, trade debug, executed-trade highlight) are read-only views.

Performance: Expect ~62 FPS; floor ≥30. Regressions usually = surface reallocations, object churn, logging, unordered scans. Validate: `make perf` or `python scripts/perf_stub.py --mode widget --duration 2 --json` (overlays <~2% overhead). Throughput + overlay regression tests enforce guardrails.

Serialization / Snapshot: When appending fields to `snapshot.py`, `world.py`, `agent.py`, `grid.py` APPEND ONLY; preserve ordering (hash & replay parity). Adjust determinism tests + reference hash deliberately.

Complexity Discipline: Per-step O(agents+resources). Prohibit pathfinding / all-pairs heuristics unless behind feature flag + perf test + documented rationale.

Allowed Quick Wins: New preference type; deterministic O(n) overlay; append metrics (hash-adjusted tests); respawn parameter plumbing; doc sync. Forbidden: tie-break changes, constant edits, extra timers/threads, hidden randomness, unordered iterations, mutable preference state, silent hash contract shifts.

Teardown: `closeEvent` → stop timer → `pygame.quit()` → `super().closeEvent(event)`; mirror for any new subsystems (no lingering timers).

Workflow Commands: install `pip install -e .[dev]`; run GUI `make dev`; legacy GUI `ECONSIM_NEW_GUI=0 make dev`; tests `make test`; lint `make lint`; types `make type`; perf `make perf`; legacy random walk `ECONSIM_LEGACY_RANDOM=1 make dev`; FPS debug `ECONSIM_DEBUG_FPS=1 make dev`.

Gate / PR Flow: Gate docs (`Gate_N_todos.md`, `GATE_N_CHECKLIST.md`, `GATE_N_EVAL.md`) → implement → PR: state intent + gate ref, minimal diff, add/adjust tests (determinism/perf if touched), run perf + hash, sync docs, concise summary (Goal | Actions | Result | Next). Avoid scope creep.

Key Files: GUI `gui/embedded_pygame.py`; controller `gui/simulation_controller.py`; core `simulation/world.py`, `agent.py`, `grid.py`; respawn `simulation/respawn.py`; trade `simulation/trade.py`; metrics `simulation/metrics.py`; snapshot `simulation/snapshot.py`; preferences `preferences/*.py`; config `simulation/config.py`; perf harness `scripts/perf_stub.py`; tests `tests/unit/*`.

When Unsure: Read the tests first. Any state-changing or perf-sensitive edit needs a test. If an invariant is ambiguous, propose/author a clarifying test before refactor.