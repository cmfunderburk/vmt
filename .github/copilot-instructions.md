## VMT EconSim – AI Agent Quick Guide
Mission: Educational micro‑economic spatial simulation (PyQt6 + Pygame) where determinism and pedagogical clarity are absolute. If a change can alter ordering, RNG call counts, tie‑breaks, or per‑step complexity, pause and add/update tests before merging.

Architecture: Single thread. PyQt6 QTimer(16ms) → `Simulation.step(ext_rng, use_decision)` → Pygame surface blit → Qt paint. Core modules under `src/econsim/simulation/`; GUI/launcher under `src/econsim/gui/` + `src/econsim/tools/launcher/`. No extra threads, sleeps, or per‑pixel loops.

Canonical construction:
```python
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
cfg = SimConfig(grid_size=(12,12), seed=123, enable_respawn=True, enable_metrics=True)
sim = Simulation.from_config(cfg, agent_positions=[(0,0)])
```

Determinism invariants (DO NOT break): (1) Resources only via `Grid.iter_resources_sorted()`; (2) Selection tie key `(-ΔU, distance, x, y)`; trade tie key `(-ΔU, seller_id, buyer_id, give_type, take_type)`; (3) Preserve original agent list order inside a step; (4) External RNG passed into `step` distinct from internal `_rng`; do not add or reorder draws; (5) ≤1 trade executed per step when enabled.

Selection algorithm: Distance‑discounted utility ΔU' = ΔU / (1 + k·d²) ranking resources and (flagged) trade intents in O(agents + visible resources). Never introduce quadratic partner scans; reject non‑positive ΔU early.

Feature flags (env): Movement fallback `ECONSIM_LEGACY_RANDOM=1`; Foraging off `ECONSIM_FORAGE_ENABLED=0`; Trading draft/exec `ECONSIM_TRADE_DRAFT=1`, `ECONSIM_TRADE_EXEC=1`; Headless render `ECONSIM_HEADLESS_RENDER=1`; Debug modes: `ECONSIM_DEBUG_AGENT_MODES=1`, `ECONSIM_DEBUG_FPS=1`.

Observability & logging: Use event system `src/econsim/observability/` (Phase 1 complete). Add new event types in `observability/events.py`; notify via registry—never direct GUI calls from simulation. Legacy `debug_logger` kept via adapter; avoid raw prints.

Performance guardrails: Keep per step O(n). Avoid new per‑frame allocations; reuse surfaces & fonts. Logging overhead must stay <~2%. Run `make perf` after impactful changes.

Schema/hash rules: Append‑only for dataclasses, snapshot records, trade tuples. Determinism hash excludes debug/trade metrics; altering hash demands updated baseline (`baselines/determinism_hashes.json`).

Testing workflow: `make venv && source vmt-dev/bin/activate`; run `pytest -q`. Headless GUI tests require: `QT_QPA_PLATFORM=offscreen`, `SDL_VIDEODRIVER=dummy`. Always build simulations through `Simulation.from_config` in tests for reproducibility.

Launcher/TestRunner: Use `make launcher` for interactive educational scenarios; programmatic API via `from econsim.tools.launcher.test_runner import create_test_runner`. Add new scenario via config registry (`framework/test_configs.py`), not ad‑hoc scripts.

Safe extension checklist: (a) Tests green; (b) Perf within baseline; (c) No unordered iterations added; (d) Tie keys unchanged; (e) RNG call count stable; (f) New metrics either excluded from or integrated into hash + updated baseline; (g) Events emitted (not direct state mutation) for new mode changes.

Common pitfalls: Resorting agents mid step, iterating raw resource dicts, multiple trades per step, silent RNG draws, quadratic partner searches, allocating big objects per frame, modifying inventories in rendering/observer code.

Add events: Wrap any future `agent.mode = ...` inside an event creator (Phase 2 goal is full coverage). Future event targets: resource collection, trade execution, movement decisions.

Key files to study first: `simulation/world.py` (step pipeline), `simulation/agent.py` (behavior + mode), `simulation/grid.py` (resource ordering), `observability/events.py` (extensible event types), `tools/launcher/framework/test_configs.py` (scenario definitions).

When unsure: Prefer adding a focused determinism or perf test over speculative refactor. Keep commits logically atomic with WHY in message (e.g., `selection: prune zero ΔU early (perf +1.2%, hash stable)`).

More depth: See `README.md`, `src/econsim/simulation/README.md`, and `docs/launcher_architecture.md`.

Active refactor (Phase 2 – Step Decomposition): `Simulation.step()` being split into handlers under `simulation/execution/` (movement, collection done; trading, metrics, respawn pending). Do NOT add new logic back into `Simulation.step`; place it in/behind a handler. Preserve ordering & RNG draw count while extracting. Any `agent.mode =` still outside observer flow should be routed via a helper that emits `AgentModeChangeEvent` (goal: 100% coverage before Phase 3). When touching trading: keep intent enumeration ordering stable, enforce ≤1 execution, and ensure economic coherence (trade execution has real consequences). If a handler addition changes timing or call count, add/adjust determinism + perf tests before merge.