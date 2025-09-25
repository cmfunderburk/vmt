## VMT Copilot Instructions (High‑Signal, ~50 lines)
Context: Educational micro‑econ spatial sim. PyQt6 shell embeds ONE Pygame Surface (configurable 320–800 square). Prime directives: determinism, single QTimer frame loop, O(agents+resources) step, minimal allocations.

Architecture: Dual GUI paths (new Start Menu vs legacy) behind `ECONSIM_NEW_GUI`. Shared core: `EmbeddedPygameWidget` rendering + `Simulation` model (`simulation/world.py`).

Core Frame Pipeline (DO NOT RESTRUCTURE): single `QTimer` (16ms) → optional `Simulation.step(ext_rng, use_decision)` → `_update_scene` (draw) → `update()` → `paintEvent` (Surface→bytes→`QImage`→`QPainter`). Forbidden: extra timers, sleeps, threads, while loops, surface resize policy changes, per-pixel Python loops, surface reallocation.

Determinism Invariants:
- Target tie-break key EXACT: (-ΔU, distance, x, y)
- Stable resource ordering (`iter_resources_sorted` where order matters); original agent list order resolves contests
- Frozen constants: `EPSILON_UTILITY`, `default_PERCEPTION_RADIUS`
- Metrics hash (`simulation/metrics.py`) = external contract (trade metrics & debug overlays excluded)
- RNG separation: external RNG (legacy movement param) vs internal `Simulation._rng` (respawn, homes, trade drafts). No hidden randomness.

Construction: Use `Simulation.from_config(SimConfig, preference_factory, agent_positions=...)`. Attaches optional `RespawnScheduler`, `MetricsCollector`, homes (secondary RNG seed+9973). Preferences are pure/stateless; register new ones in `preferences/factory.py` with tests (validation, utility math, serialize round trip).

Respawn & Interval: Alternating A↔B deterministic sequence; placement = seeded uniform shuffle of empty cells. Interval gating `(step % interval)==0`; Off leaves scheduler inert (still attached).

Respawn System: Dual control via GUI dropdowns. **Interval**: when respawn occurs (Off, 1,5,10,20 steps; default 20). **Rate**: percentage of deficit respawned (10%,25%,50%,75%,100%; default 100%). Maintains target density from start menu. Random A/B type assignment, uniform empty‑cell shuffle from internal RNG. Agent homes use secondary seed offset (`seed+9973`).

Trading (Feature-Gated): Flags `ECONSIM_TRADE_DRAFT`, `ECONSIM_TRADE_EXEC`, `ECONSIM_TRADE_PRIORITY_DELTA`, `ECONSIM_TRADE_GUI_INFO`, `ECONSIM_TRADE_DEBUG_OVERLAY`. Only units currently carried may be exchanged; home inventory immutable. Execution (at most one intent/step) mutates carrying bundles; related metrics excluded from determinism hash. Priority flag changes ordering only; multiset of intents must stay identical.

Foraging Enable Flag: `ECONSIM_FORAGE_ENABLED=0` disables collection; with trading off agents idle (do NOT auto-deposit) preserving inventories. With trading on they may trade without gathering. Behavior matrix lives in README; keep parity when extending logic.

Rendering Rules:
- Keep pipeline intact; no per-pixel Python mutation.
- Square cell sizing = min(surface_w//gw, surface_h//gh); leave extra margin unused (no centering math).
- Cache fonts (`_overlay_font`, `_paused_font`); no per-agent font objects.
- Sprite system: Loads sprites from `vmt_sprites_pack_1/` on init, scales to cell size per frame. Fallback to colored rectangles if loading fails.
- Overlays (grid, IDs, arrows, homes, trade debug) are read-only.

Performance: Typical ~62 FPS; floor ≥30. Investigate regressions: surface reallocations, per-frame object churn, logging, unintended list rebuilds. Validate via `make perf` or `python scripts/perf_stub.py --mode widget --duration 2 --json` (overlays <~2% overhead). Decision throughput + overlay regression tests guard.

Serialization / Snapshot: When adding fields to `snapshot.py`, `world.py`, `agent.py`, `grid.py` APPEND ONLY; preserve order for hash/replay parity. Update determinism tests & metrics hash deliberately.

Complexity Discipline: Per-step O(agents+resources). No all-pairs scans/pathfinding/heuristics without feature flag + perf test + documented justification.

Allowed Fast Path Changes: New preference type; deterministic overlay (O(n)); append metrics field (hash-adjusted + tests); respawn parameter plumbing; doc sync. Forbidden: tie-break edits, constant changes, extra timers, threads, hidden randomness, unordered iteration, mutable preference state, silent hash contract shifts.

Teardown: `closeEvent` → stop timer → `pygame.quit()` → `super().closeEvent(event)`. Mirror for new subsystems.

Workflow Commands: install `pip install -e .[dev]`; run GUI `make dev`; legacy GUI `ECONSIM_NEW_GUI=0 make dev`; tests `make test`; lint `make lint`; types `make type`; perf `make perf`; legacy random walk `ECONSIM_LEGACY_RANDOM=1 make dev`; FPS debug `ECONSIM_DEBUG_FPS=1 make dev`.

Gate / PR Flow: Gate doc trio (`Gate_N_todos.md`, `GATE_N_CHECKLIST.md`, `GATE_N_EVAL.md`) → execute → PR: state intent + gate ref, minimal diff, add/adjust tests (determinism/perf if touched), run perf + hash, sync docs, summarize (Goal | Actions | Result | Next). No scope creep.

Key Files: GUI `gui/embedded_pygame.py`, controller `gui/simulation_controller.py`; model `simulation/world.py`, `agent.py`, `grid.py`; respawn `simulation/respawn.py`; trade `simulation/trade.py`; metrics `simulation/metrics.py`; snapshot `simulation/snapshot.py`; preferences `preferences/*.py`; config `simulation/config.py`; perf harness `scripts/perf_stub.py`; tests `tests/unit/*`.

When Unsure: Read the test first. Any state-changing or performance-sensitive change requires a corresponding test. If an invariant seems ambiguous, propose a clarifying test before coding.