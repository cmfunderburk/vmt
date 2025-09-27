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
* Unified selection (production default): auto‑enabled when decision+forage+trade exec unless `ECONSIM_UNIFIED_SELECTION_DISABLE=1`; can force with `ECONSIM_UNIFIED_SELECTION_ENABLE=1`.
* Debug/Development: `ECONSIM_DEBUG_FPS`, `ECONSIM_HEADLESS_RENDER`, `ECONSIM_LEGACY_ANIM_BG`, `ECONSIM_METRICS_AUTO`, `ECONSIM_LEGACY_RANDOM`, `ECONSIM_LOG_LEVEL`, `ECONSIM_LOG_FORMAT`.
* Debug categories: `ECONSIM_DEBUG_AGENT_MODES`, `ECONSIM_DEBUG_TRADES`, `ECONSIM_DEBUG_SIMULATION`, `ECONSIM_DEBUG_PHASES`, `ECONSIM_DEBUG_DECISIONS`, `ECONSIM_DEBUG_RESOURCES`, `ECONSIM_DEBUG_PERFORMANCE`, `ECONSIM_DEBUG_ECONOMICS`, `ECONSIM_DEBUG_SPATIAL`.

Unified Selection (Production Default): Successfully migrated to unified target selection as default decision path. All 210+ tests passing.
* `Agent.select_unified_target` with distance‑discounted utility (`ΔU_base / (1 + k*distance²)`), deterministic tiebreaks ((x,y) for resources, agent id for partners), profitability filter (`ΔU_base > 0`).
* `AgentSpatialGrid` O(n) rebuilt each step for partner lookup; append‑only determinism maintained.
* Distance scaling factor `k` (0–10, default 0.0) configurable via Start Menu Advanced panel + live Controls panel Decision Params updates.
* Leontief prospecting fallback integrated within unified path to preserve behavioral parity.
* Conservative bilateral trade delta heuristic (min directional marginal gains) prevents oscillatory trades.
* Mixed type tiebreaks: higher raw ΔU wins; if equal then lexical kind ordering (foraging < partner).
* Educational impact: Higher k emphasizes local behavior; k=0.0 allows global optimization; k=5.0+ strongly favors nearby targets.

Bilateral Exchange (Phase 3): O(agents) partner search (`_handle_bilateral_exchange_movement`) → pairing → meeting point path → co‑location → (intent enumeration + at most one execution per step) → cooldowns (general + partner‑specific). Stagnation: 100 no‑improvement steps triggers one‑time forced deposit (`force_deposit_once`). Priority key when flag on: `(-delta_utility, seller_id, buyer_id, give_type, take_type)`. Trade metrics & fairness_round are hash‑excluded.

Complexity Discipline: NO global all‑pairs expansions beyond localized perception scans; any new algorithm must document O(n) behavior or be flag‑gated + perf tested. Avoid unordered containers for determinism paths.

Rendering Rules: Single surface; cell size = `min(surface_w//gw, surface_h//gh)` (no centering for remainder). Cache shared fonts only. Sprites from `vmt_sprites_pack_1/`; fallback rects acceptable. Overlays strictly read‑only (grid, IDs, homes, trade lines, executed‑trade highlight, selection).

Serialization / Snapshot: Append‑only field additions in `snapshot.py`, `world.py`, `agent.py`, `grid.py` — NEVER reorder or remove; update determinism tests & reference hashes explicitly.

Manual Test Patterns (Current Technical Debt): All 7 tests in `MANUAL_TESTS/` share identical 3‑panel UI (debug log | pygame viewport | controls), phase transition logic, timer setup, and environment variable management — creating ~3000 lines of duplication. When adding manual tests: reuse existing patterns for consistency. For framework refactor (see `REFACTOR_PLAN.md`): extract `BaseManualTest`, `TestConfiguration` dataclass, `PhaseManager`, `DebugOrchestrator` — reduces new tests to ~30 lines vs 400 lines.

Allowed Low‑Risk Contributions: new pure preference type; deterministic O(n) overlay; additional metrics (update hash contract + tests); respawn parameter plumbing; doc sync; manual test framework extraction (high‑impact, low‑risk). Forbidden: tie‑break alteration, constant edits, adding randomness, extra timers/threads, unordered iteration where order matters, mutable preference state, silent hash schema change, per‑step quadratic scans.

Perf Expectations: ~62 FPS typical (floor ≥30). Validate with `make perf` or `python scripts/perf_stub.py --mode widget --duration 2 --json` (overlays <~2% overhead). Watch for regressions: surface realloc, object churn, logging in hot loop, accidental N^2 partner scans.

Testing & PR Flow: Run `make test-unit lint type perf`. Any state or perf‑sensitive change: add/adjust unit test (determinism, perf guard, hash). Manual GUI validation: `make manual-tests` (7 educational scenarios). PR summary: Goal | Changes | Tests/Perf | Result | Next. Keep diffs minimal.

Development Workflow: Virtual env `vmt-dev/`; entry point `make dev` (new GUI) or `ECONSIM_NEW_GUI=0 make dev` (legacy). Environment flags control features (see above). Live config via Controls panel; settings persist across GUI sessions. Factory construction via `Simulation.from_config()` preferred over manual wiring.

Debug System: Centralized logging via `src/econsim/gui/debug_logger.py` with environment flags (`ECONSIM_DEBUG_AGENT_MODES`, `ECONSIM_DEBUG_TRADES`, etc). Manual tests include debug panels with 250ms update timers. Use `log_phase_transition()`, `log_comprehensive()` for educational scenarios.

Manual Testing Framework: 7 educational scenarios in `MANUAL_TESTS/` (run via `make manual-tests` or individual `.py` files). Standard 6‑phase structure (900 turns): Both enabled (1‑200) → Forage only (201‑400) → Exchange only (401‑600) → Both disabled (601‑650) → Both enabled (651‑850) → Final disabled (851‑900). Phase transitions via environment variable management. Current tests have massive duplication (~400 lines each); refactor plan in `MANUAL_TESTS/REFACTOR_PLAN.md` proposes configuration‑driven approach with `TestConfiguration` dataclass + `BaseManualTest` framework.

Key Files Map: GUI embed `src/econsim/gui/embedded_pygame.py`; controller `src/econsim/gui/simulation_controller.py`; core sim `src/econsim/simulation/world.py`; agents `src/econsim/simulation/agent.py`; grid `src/econsim/simulation/grid.py`; spatial index `src/econsim/simulation/spatial.py`; trade `src/econsim/simulation/trade.py`; respawn `src/econsim/simulation/respawn.py`; metrics `src/econsim/simulation/metrics.py`; snapshot `src/econsim/simulation/snapshot.py`; preferences `src/econsim/preferences/*.py`; config `src/econsim/simulation/config.py`; perf harness `scripts/perf_stub.py`; tests `tests/unit/*`; manual tests `MANUAL_TESTS/*.py`.

Teardown Integrity: `closeEvent` stops timer → `pygame.quit()` → `super().closeEvent(event)`; mirror for new subsystems (no lingering timers/threads/resources).

Educational Context: This is a microeconomic simulation for teaching spatial resource allocation, agent decision-making, and exchange dynamics. Behavioral changes must be educationally meaningful and deterministically reproducible across classroom sessions.

When Unsure: Read the relevant unit tests FIRST. If an invariant feels ambiguous, write/strengthen a test before refactor.