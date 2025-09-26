## VMT Copilot Instructions (Concise High‑Signal Guide)
Purpose: Educational micro‑econ spatial sim (PyQt6 shell + ONE embedded Pygame Surface 320–800px). Non‑negotiables: deterministic replay, single `QTimer` frame loop, per‑step O(agents+resources), minimal allocations.

Frame Pipeline (DO NOT CHANGE): single QTimer (~16ms) → `Simulation.step(ext_rng, use_decision)` → `_update_scene` → `update()` → `paintEvent` (Surface→bytes→QImage→QPainter). Forbidden: extra timers/threads, sleeps, blocking loops, surface realloc/recreate, per‑pixel Python loops, layout/resize math changes.

Determinism Invariants:
1. Target tie-break key EXACT: (-ΔU, distance, x, y)
2. Stable resource iteration (`iter_resources_sorted`); original agent list order breaks contests
3. Constants frozen: `EPSILON_UTILITY`, `default_PERCEPTION_RADIUS`
4. Metrics hash contract (`simulation/metrics.py`) excludes trade + debug overlay metrics
5. RNG separation: external (legacy/random movement) vs internal `Simulation._rng` (respawn, homes, trade drafts)

Core Architecture: Dual GUI (Start Menu new path default `ECONSIM_NEW_GUI=1`; legacy when 0) sharing `EmbeddedPygameWidget` + `Simulation` (`simulation/world.py`). Factory: `Simulation.from_config(SimConfig, preference_factory, agent_positions=...)` seeds internal RNG, optional `RespawnScheduler`, `MetricsCollector`; homes via deterministic secondary seed (`seed+9973`). Preferences must be pure/stateless; register in `preferences/factory.py` + tests (validation, utility math, serialize round‑trip).

Feature Flags (environment):
* Foraging: `ECONSIM_FORAGE_ENABLED` (default 1). Off + no trade ⇒ agents idle, carrying preserved.
* Trading: `ECONSIM_TRADE_DRAFT`, `ECONSIM_TRADE_EXEC` (implies draft), `ECONSIM_TRADE_PRIORITY_DELTA` (reorder only; multiset invariant), `ECONSIM_TRADE_GUI_INFO`, `ECONSIM_TRADE_DEBUG_OVERLAY`, `ECONSIM_TRADE_HASH_NEUTRAL` (debug: restore carrying after hash).
* Unified selection (experimental combined resource/partner pass): auto‑enabled when decision+forage+trade exec unless `ECONSIM_UNIFIED_SELECTION_DISABLE=1`; can force with `ECONSIM_UNIFIED_SELECTION_ENABLE=1`.

Active Refactor (see `tmp_plans/CURRENT/target_selection_planning.md`): migrate to unified target selection as default decision path.
* Implement `Agent.select_unified_target` with distance‑discounted utility (`ΔU_base / (1 + k*distance²)`), deterministic tiebreaks ((x,y) for resources, agent id for partners), and profitability filter (`ΔU_base > 0`).
* Spatial indexing (`AgentSpatialGrid`) rebuilt each step keeps partner lookup O(agents); maintain append‑only determinism and avoid quadratic scans.
* Commitment model: agents hold `current_task` until resource collected/trade resolved or target invalidated; ensure bilateral movement hooks cooperate (stagnation/force deposit still honored).
* Config + GUI: add distance scaling constant `k` (0–10, default 0.0) with live updates; propagate through `SimConfig` + right panel control.
* Testing: update determinism hashes + behavior assertions for new selection ordering; cover single-mode (forage‑only/trade‑only) parity, unified path, and spatial index queries. Expect breaking changes to existing selection tests—refresh fixtures intentionally.

Bilateral Exchange (Phase 3): O(agents) partner search (`_handle_bilateral_exchange_movement`) → pairing → meeting point path → co‑location → (intent enumeration + at most one execution per step) → cooldowns (general + partner‑specific). Stagnation: 100 no‑improvement steps triggers one‑time forced deposit (`force_deposit_once`). Priority key when flag on: `(-delta_utility, seller_id, buyer_id, give_type, take_type)`. Trade metrics & fairness_round are hash‑excluded.

Complexity Discipline: NO global all‑pairs expansions beyond localized perception scans; any new algorithm must document O(n) behavior or be flag‑gated + perf tested. Avoid unordered containers for determinism paths.

Rendering Rules: Single surface; cell size = `min(surface_w//gw, surface_h//gh)` (no centering for remainder). Cache shared fonts only. Sprites from `vmt_sprites_pack_1/`; fallback rects acceptable. Overlays strictly read‑only (grid, IDs, homes, trade lines, executed‑trade highlight, selection).

Serialization / Snapshot: Append‑only field additions in `snapshot.py`, `world.py`, `agent.py`, `grid.py` — NEVER reorder or remove; update determinism tests & reference hashes explicitly.

Allowed Low‑Risk Contributions: new pure preference type; deterministic O(n) overlay; additional metrics (update hash contract + tests); respawn parameter plumbing; doc sync. Forbidden: tie‑break alteration, constant edits, adding randomness, extra timers/threads, unordered iteration where order matters, mutable preference state, silent hash schema change, per‑step quadratic scans.

Perf Expectations: ~62 FPS typical (floor ≥30). Validate with `make perf` or `python scripts/perf_stub.py --mode widget --duration 2 --json` (overlays <~2% overhead). Watch for regressions: surface realloc, object churn, logging in hot loop, accidental N^2 partner scans.

Testing & PR Flow: Run `make test lint type perf`. Any state or perf‑sensitive change: add/adjust unit test (determinism, perf guard, hash). PR summary: Goal | Changes | Tests/Perf | Result | Next. Keep diffs minimal.

Key Files Map: GUI embed `src/econsim/gui/embedded_pygame.py`; controller `gui/simulation_controller.py`; core sim `simulation/world.py`; agents `simulation/agent.py`; grid `simulation/grid.py`; trade `simulation/trade.py`; respawn `simulation/respawn.py`; metrics `simulation/metrics.py`; snapshot `simulation/snapshot.py`; preferences `preferences/*.py`; config `simulation/config.py`; perf harness `scripts/perf_stub.py`; tests `tests/unit/*`.

Teardown Integrity: `closeEvent` stops timer → `pygame.quit()` → `super().closeEvent(event)`; mirror for new subsystems (no lingering timers/threads/resources).

When Unsure: Read the relevant unit tests FIRST. If an invariant feels ambiguous, write/strengthen a test before refactor.