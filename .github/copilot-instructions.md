## VMT EconSim – Concise AI Agent Guide (Oct 2025)
Goal: Maintain a deterministic educational micro‑economics sim (PyQt6 + Pygame) while iterating safely. Economic coherence > cosmetic frame sameness. Never add rollback/ghost state to “preserve hashes.” If you change ordering, RNG draw count, tie‑break keys, or big‑O, add/update tests first.

Core loop (single thread): PyQt6 QTimer (~16ms) → `Simulation.step(ext_rng)` → `StepExecutor` pipeline (Movement → Collection → Trading → Metrics → Respawn) → Pygame blit → Qt paint. Core: `src/econsim/simulation/`; GUI & launcher: `src/econsim/tools/launcher/` + `src/econsim/gui/`.

Primary workflow: `make venv && source vmt-dev/bin/activate` → `make launcher`. Run tests: `pytest -q`. Perf check: `make perf`. Determinism baseline: see `baselines/determinism_hashes.json` (refresh only with rationale). Headless: `QT_QPA_PLATFORM=offscreen SDL_VIDEODRIVER=dummy make launcher`.

Construct sims ONLY via factory:
```python
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
cfg = SimConfig(grid_size=(12,12), seed=123, enable_respawn=True, enable_metrics=True)
sim = Simulation.from_config(cfg, agent_positions=[(0,0)])
```

Determinism invariants (do not violate):
1. Iterate resources only through `Grid.iter_resources_sorted()`.
2. Selection tie key: `(-ΔU, distance, x, y)`; trade priority key: `(-ΔU, seller_id, buyer_id, give_type, take_type)`.
3. Preserve original agent list order each step (no resorting mid‑step).
4. External RNG passed into `step` stays separate from internal `_rng` (no extra / reordered draws).
5. At most one executed trade per step when trade execution enabled.

Architecture pattern: Add new per‑step logic as a handler in `simulation/execution/handlers/` subclassing `BaseStepHandler`; never re‑inflate `Simulation.step()`. Handlers use `StepContext` (immutable view) and return `StepResult` objects aggregated by `StepExecutor`.

Decision system: unified distance‑discounted utility (ΔU' = ΔU / (1 + k*d²)); ignore non‑positive ΔU early; keep complexity O(agents + visible_resources). Avoid quadratic partner scans.

Events & observability: Emit via `observability/events.py`. Simulation must not call GUI widgets directly. Logging overhead target <2% per step.

Mode changes: Always call `agent._set_mode(new_mode, reason, observer_registry, step_number)` (never direct assignment) to ensure `AgentModeChangeEvent`. Audit `world.py` for any remaining raw assignments before edits.

Performance guardrails: Per‑step O(n). No large per‑frame allocations. Movement handler budget ≲3ms typical. After altering selection, movement, or trading internals run `make perf` and compare against `baselines/performance_baseline.json`.

Hash & schema: Append‑only for dataclasses / snapshot / trade tuples. Determinism hash excludes trade & debug metrics. If a legit behavioral change alters the hash: (a) add/adjust a focused test, (b) regenerate baseline with concise commit message (WHAT + WHY).

Feature flags in active use: `ECONSIM_FORAGE_ENABLED`, `ECONSIM_TRADE_DRAFT`, `ECONSIM_TRADE_EXEC`, optional debug `ECONSIM_DEBUG_AGENT_MODES`, `ECONSIM_HEADLESS_RENDER`. Legacy `ECONSIM_LEGACY_RANDOM` and `use_decision` args are being purged—remove, don’t preserve.

Active cleanup focus (Phase A): eliminate legacy random mode artifacts (flags, test scaffolds, `use_decision=False` params) and migrate any stray mode assignments to `_set_mode`. When you touch a file containing legacy remnants, opportunistically remove them (ensure tests green).

Common pitfalls to avoid: resorting agents inside a step; iterating unsorted resource containers; generating >1 trade execution per step; hidden RNG draws; quadratic partner scans; per‑frame big list/dict rebuilds; GUI calls from simulation; silent inventory rewrites for “visual parity.”

Key files to inspect first: `simulation/world.py` (orchestration), `simulation/execution/step_executor.py` (pipeline), `simulation/execution/handlers/` (per‑phase logic), `simulation/agent.py` (decision & mode), `simulation/grid.py` (spatial indexing), `simulation/trade.py` (bilateral exchange), `observability/events.py` (event types), `metrics.py` (hashing rules), `tools/launcher/` (GUI launcher & scenarios).

Extension checklist before merging: (1) tests all pass, (2) perf within baseline, (3) invariants above unchanged (or explicitly updated with tests + baseline refresh), (4) new metrics excluded from hash unless justified, (5) any new mode transitions emit events, (6) no new nondeterministic iteration sources.

Unsure? Add a focused determinism or perf test rather than speculative refactor. Commit message format: `component: concise change (perf/determinism impact, hash stable|updated)`.

Feedback welcome—if a constraint blocked a legitimate improvement, document rationale in PR and reference updated tests.