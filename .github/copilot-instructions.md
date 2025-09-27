## VMT Copilot Instructions (Concise High‑Signal Guide)
Purpose: Educational micro‑econ spatial sim (PyQt6 shell + ONE embedded Pygame Surface 320–800px). Non‑negotiables: deterministic replay, single `QTimer` frame loop, per‑step O(agents+resources), minimal allocations.

Frame Pipeline (DO NOT CHANGE): single QTimer (~16ms) → `Simulation.step(ext_rng, use_decision)` → `_update_scene` → `update()` → `paintEvent` (Surface→bytes→QImage→QPainter). Forbidden: extra timers/threads, sleeps, blocking loops, surface realloc/recreate, per‑pixel Python loops, layout/resize math changes.

Determinism Invariants:
1. Target tie-break key EXACT: (-ΔU, distance, x, y)
2. Stable resource iteration (`iter_resources_sorted`); original agent list order breaks contests
3. Constants frozen: `EPSILON_UTILITY`, `default_PERCEPTION_RADIUS`
4. Metrics hash contract (`simulation/metrics.py`) excludes trade + debug overlay metrics
5. RNG separation: external (legacy/random movement) vs internal `Simulation._rng` (respawn, homes, trade drafts)

Project Structure: Python 3.11+ package with PyQt6/pygame deps, virtual env `vmt-dev/`. Entry points: `main.py` (dual GUI system), enhanced test launcher in `MANUAL_TESTS/enhanced_test_launcher_v2.py` (canonical dev interface), unit tests in `tests/unit/` (210+ tests). Core modules: `simulation/world.py` (coordinator), `gui/embedded_pygame.py` (rendering), `preferences/*.py` (economic models), `simulation/agent.py` (behavior).

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

Enhanced Test Framework (Current Reality): `MANUAL_TESTS/enhanced_test_launcher_v2.py` is the **primary development interface** (1153 lines) with visual test launcher, comparison mode, and tabbed interface. Framework components in `MANUAL_TESTS/framework/` (`test_configs.py`, `base_test.py`, `phase_manager.py`, `ui_components.py`, `simulation_factory.py`). **Major technical debt**: 7 educational tests (`test_*_baseline_simple.py`, `test_*_framework_version.py`) share ~3000 lines of duplicated code for identical 6‑phase UI structure. **ACTIVE REFACTOR IN PROGRESS**: Comprehensive restructuring planned per `tmp_plans/CURRENT/CRITICAL_REVIEW_AND_REORG_PLAN_ENHANCED_TESTS.md` to extract monolithic launcher into proper package structure under `src/econsim/tools/launcher/` (main VMT user environment) with console scripts, XDG data directories, and programmatic test runner APIs. Current implementation has brittle path hacks, subprocess coupling, and repo-polluting data locations that need resolution.

Allowed Low‑Risk Contributions: new pure preference type; deterministic O(n) overlay; additional metrics (update hash contract + tests); respawn parameter plumbing; doc sync; manual test framework extraction (high‑impact, low‑risk). **REFACTOR CONTEXT**: Current session focuses on comprehensive launcher framework restructuring - prioritize work supporting the migration to `src/econsim/tools/launcher/` package structure (main VMT user environment). Forbidden: tie‑break alteration, constant edits, adding randomness, extra timers/threads, unordered iteration where order matters, mutable preference state, silent hash schema change, per‑step quadratic scans.

Perf Expectations: ~62 FPS typical (floor ≥30). Validate with `make perf` or `python scripts/perf_stub.py --mode widget --duration 2 --json` (overlays <~2% overhead). Watch for regressions: surface realloc, object churn, logging in hot loop, accidental N^2 partner scans.

Testing & PR Flow: Run `make test-unit lint type perf`. Any state or perf‑sensitive change: add/adjust unit test (determinism, perf guard, hash). Manual GUI validation: `make manual-tests` (7 educational scenarios). PR summary: Goal | Changes | Tests/Perf | Result | Next. Keep diffs minimal.

Development Workflow: **ALWAYS activate virtual environment first**: `source vmt-dev/bin/activate` (create with `make venv` if missing). Primary workflows:
* `make enhanced-tests` – **canonical development interface** with visual test launcher, optimized logging (compact format), tabbed UI including test gallery, config editor, batch runner, bookmarks, and custom test management. **CRITICAL**: This is the authoritative development version; functionality not used here will be deprecated in future refactoring.
* `make dev` – basic GUI (Start Menu → scenario selection) - **legacy interface, use sparingly**
* `make test-unit lint type perf` – full validation pipeline
* `pytest -q` – run 210+ automated tests
* `python scripts/perf_stub.py` – performance benchmarking

Debug System: Centralized logging via `src/econsim/gui/debug_logger.py` with environment flags (`ECONSIM_DEBUG_AGENT_MODES`, `ECONSIM_DEBUG_TRADES`, etc). Enhanced test launcher auto-configures educational logging. Manual tests include debug panels with 250ms update timers. Use `log_phase_transition()`, `log_comprehensive()` for educational scenarios.



Key Files Map: GUI embed `src/econsim/gui/embedded_pygame.py`; controller `src/econsim/gui/simulation_controller.py`; core sim `src/econsim/simulation/world.py`; agents `src/econsim/simulation/agent.py`; grid `src/econsim/simulation/grid.py`; spatial index `src/econsim/simulation/spatial.py`; trade `src/econsim/simulation/trade.py`; respawn `src/econsim/simulation/respawn.py`; metrics `src/econsim/simulation/metrics.py`; snapshot `src/econsim/simulation/snapshot.py`; preferences `src/econsim/preferences/*.py`; config `src/econsim/simulation/config.py`; perf harness `scripts/perf_stub.py`; tests `tests/unit/*`; manual tests `MANUAL_TESTS/*.py`.

Teardown Integrity: `closeEvent` stops timer → `pygame.quit()` → `super().closeEvent(event)`; mirror for new subsystems (no lingering timers/threads/resources).

Educational Context: This is a microeconomic simulation for teaching spatial resource allocation, agent decision-making, and exchange dynamics. Behavioral changes must be educationally meaningful and deterministically reproducible across classroom sessions.

**CRITICAL REFACTOR CONTEXT (September 2025)**: The project is undergoing comprehensive restructuring of the enhanced test framework. Current session goals:
1. **Deprecation Path**: Features not accessible via `make enhanced-tests` are candidates for removal in future refactoring passes
2. **Package Migration**: Moving from monolithic `MANUAL_TESTS/enhanced_test_launcher_v2.py` (1153 lines) to proper package structure under `src/econsim/tools/launcher/` (main VMT user environment)
3. **Technical Debt Resolution**: Addressing ~3000 lines of duplicated test code, brittle path hacks, subprocess coupling, and repo-polluting data locations
4. **Planned Phases**: Framework extraction → launcher factoring → programmatic runner → test registry centralization → XDG data migration → console scripts + packaging
5. **Architecture Target**: Console script `econsim-launcher` (or `vmt-launcher`), proper imports (no `sys.path` hacks), appdata directories, programmatic test APIs

Code Quality Standards: Python 3.11+, Black formatting (line-length 100), Ruff linting, MyPy type checking. Use `make format lint type` before commits. All state changes require corresponding unit tests in `tests/unit/`. Performance-sensitive changes must pass `make perf` regression tests.

When Unsure: Read the relevant unit tests FIRST. If an invariant feels ambiguous, write/strengthen a test before refactor. The `tests/unit/` directory contains 80+ test files covering determinism, performance, GUI integration, and economic behavior patterns.