## VMT Copilot Instructions (High-Signal Operational Guide)

Purpose: Educational microeconomic simulation (PyQt6 shell embedding a single Pygame surface). Absolute non‑negotiables: deterministic replay, single QTimer frame loop, O(n) per step (n=agents+resources), minimal allocations.

Core Frame Pipeline (DO NOT ALTER): One QTimer (~16ms) → `Simulation.step(ext_rng, use_decision)` → `_update_scene` → `update()` → `paintEvent` (surface→bytes→QImage→QPainter). Never add extra timers/threads, sleeps, blocking loops, surface reallocation, per‑pixel Python loops, or layout math changes.

Determinism Invariants:
1. Target tie-break EXACT key: `(-ΔU, distance, x, y)` (or documented trade key when trade priority flag on).
2. Stable resource ordering via `iter_resources_sorted`; never iterate a raw unordered collection for contests.
3. Frozen constants: `EPSILON_UTILITY`, `default_PERCEPTION_RADIUS`.
4. Hash contract in `simulation/metrics.py` excludes trade + debug overlays; do not add fields silently.
5. RNG split: external RNG param vs internal `Simulation._rng` (respawn, homes, trade drafts). No cross‑contamination.
6. Agent list order = processing & contest priority; never reorder in place.
7. Snapshot / serialization fields (`snapshot.py`, `world.py`, `agent.py`, `grid.py`) are append‑only; never reorder/remove.

Active Refactor (Phase 4 – Monolith Cleanup): Migrating launcher from legacy `MANUAL_TESTS/enhanced_test_launcher_v2.py` to modular package `src/econsim/tools/launcher/` (cards, gallery, tabs, registry, executor). Remaining task: remove obsolete fallback class + path hacks; new entry will become console script (`econsim-launcher`).

Performance Guardrails: Typical ~62 FPS; floor ≥30. Investigate if: extra allocations in step loop, added logging inside hot loops, N^2 partner/resource scans, surface re-creations, font reloads. Use `make perf` or `python scripts/perf_stub.py --mode widget --duration 2 --json` for quick checks. Overlays must remain read‑only & <~2% overhead.

Allowed Low-Risk Changes: New pure preference type (register + tests), deterministic O(n) overlay, additive metrics (update hash tests), respawn param plumbing, launcher modularization (no behavior drift), documentation sync.

Forbidden Changes: Tie-break semantics, core constants, randomness injection, extra timers/threads, unordered iteration where order matters, mutable preference state, silent serialization/hash schema edits, per‑step quadratic scans, breaking frame pipeline.

Unified Selection Path: Default decision logic (`Agent.select_unified_target`) uses distance‑discounted utility `ΔU_base/(1+k*dist^2)`, profitability filter `ΔU_base>0`, deterministic tiebreaks ((x,y) or partner id). Maintain O(n) `AgentSpatialGrid` rebuild each step; no caching that changes iteration determinism.

Trading / Exchange: Partner search O(agents); at most one execution per pair per step; stagnation fallback after 100 idle steps triggers single forced deposit. Priority key when enabled: `(-delta_utility, seller_id, buyer_id, give_type, take_type)`. Trade metrics & fairness_round remain hash‑excluded.

Rendering Rules: Exactly one Pygame surface; cell size = `min(surface_w//gw, surface_h//gh)` (no centering remainder). Cache fonts once; sprites from `vmt_sprites_pack_1/` (rect fallback OK). No per-frame surface recreation.

Development Workflow: Activate venv (`source vmt-dev/bin/activate`). Use: `make enhanced-tests` (canonical launcher), `make dev` (legacy GUI), `make test-unit lint type perf`, or `pytest -q`. Add tests for any state/ordering/perf changes before refactor. Run perf after modifying agent selection, trade, respawn, or rendering.

Logging & Debug: Central logger `gui/debug_logger.py`; enable categories via env (`ECONSIM_DEBUG_*`). Avoid verbose logs in frame loop. Use provided helper functions for phase transitions.

Key Modules: `simulation/world.py` (orchestrator), `simulation/agent.py`, `simulation/trade.py`, `simulation/metrics.py`, `simulation/snapshot.py`, `gui/embedded_pygame.py`, `preferences/factory.py`, `simulation/config.py`, launcher package (`tools/launcher/*`), perf harness `scripts/perf_stub.py`.

Safety Checklist Before PR: (1) determinism tests pass, (2) perf check no regression, (3) hash tests updated only for intentional additive fields, (4) no new unordered iterations, (5) single QTimer still sole driver, (6) serialization diffs append-only.

When Unsure: Read existing unit tests covering the target area first; mirror patterns. If changing ordering or adding metrics, extend tests concurrently—not after.

Educational Constraint: Any behavioral change must retain clarity for teaching spatial allocation & exchange; prefer explicit, documented heuristics over opaque optimizations.

If a desired change conflicts with an invariant above: halt, open a design note, and add a guarded feature flag + tests before proceeding.