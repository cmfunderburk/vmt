## VMT EconSim – AI Agent Quick Guide
Mission: Educational micro‑economic spatial simulation (PyQt6 + Pygame) where determinism and pedagogical clarity are absolute. Economic coherence > technical parity—trades must have real consequences, not ghost transactions. If a change alters ordering, RNG call counts, tie‑breaks, or per‑step complexity, pause and add/update tests before merging.

Architecture: Single thread. PyQt6 QTimer(16ms) → `Simulation.step(ext_rng, use_decision)` → handler pipeline → Pygame surface blit → Qt paint. Core modules under `src/econsim/simulation/`; GUI/launcher under `src/econsim/gui/` + `src/econsim/tools/launcher/`. Step decomposition via `StepExecutor` and handlers in `simulation/execution/`.

Canonical construction:
```python
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
cfg = SimConfig(grid_size=(12,12), seed=123, enable_respawn=True, enable_metrics=True)
sim = Simulation.from_config(cfg, agent_positions=[(0,0)])
```

Determinism invariants (DO NOT break): (1) Resources only via `Grid.iter_resources_sorted()`; (2) Selection tie key `(-ΔU, distance, x, y)`; trade tie key `(-ΔU, seller_id, buyer_id, give_type, take_type)`; (3) Preserve original agent list order inside a step; (4) External RNG passed into `step` distinct from internal `_rng`; do not add or reorder draws; (5) ≤1 trade executed per step when enabled.

Handler pipeline (Phase 2): `StepExecutor` runs 5 ordered handlers: MovementHandler → CollectionHandler → TradingHandler → MetricsHandler → RespawnHandler. Each returns structured metrics; no cross-handler side effects. DO NOT add logic back to `Simulation.step()`—place it in/behind appropriate handler.

Selection algorithm: Distance‑discounted utility ΔU' = ΔU / (1 + k·d²) ranking resources and trade intents in O(agents + visible resources). Never introduce quadratic partner scans; reject non‑positive ΔU early.

Feature flags (env): Movement fallback `ECONSIM_LEGACY_RANDOM=1`; Foraging off `ECONSIM_FORAGE_ENABLED=0`; Trading draft/exec `ECONSIM_TRADE_DRAFT=1`, `ECONSIM_TRADE_EXEC=1`; Headless render `ECONSIM_HEADLESS_RENDER=1`; Debug modes: `ECONSIM_DEBUG_AGENT_MODES=1`, `ECONSIM_DEBUG_FPS=1`.

Observability & logging: Use event system `src/econsim/observability/` (Phase 1 complete). Add new event types in `observability/events.py`; notify via registry—never direct GUI calls from simulation. Legacy `debug_logger` kept via adapter; avoid raw prints.

Performance guardrails: Keep per step O(n). Avoid new per‑frame allocations; reuse surfaces & fonts. Logging overhead must stay <~2%. Run `make perf` after impactful changes. Handler timing monitored; movement budget ≤3ms.

Schema/hash rules: Append‑only for dataclasses, snapshot records, trade tuples. Determinism hash excludes debug/trade metrics; altering hash demands updated baseline (`baselines/determinism_hashes.json`).

**CRITICAL: Economic coherence over hash parity.** Test suite validates authentic micro-economic behavior (real trade consequences, inventory persistence, behavioral impact). NO artificial state restoration or ghost transactions. Use `test_trade_economic_coherence.py` as model for trade-related testing.

Testing workflow: `make venv && source vmt-dev/bin/activate`; run `pytest -q`. Headless GUI tests require: `QT_QPA_PLATFORM=offscreen`, `SDL_VIDEODRIVER=dummy`. Always build simulations through `Simulation.from_config` in tests for reproducibility.

Launcher/TestRunner: Use `make launcher` for interactive educational scenarios; programmatic API via `from econsim.tools.launcher.test_runner import create_test_runner`. Add new scenario via config registry (`framework/test_configs.py`), not ad‑hoc scripts.

Safe extension checklist: (a) Tests green; (b) Perf within baseline; (c) No unordered iterations added; (d) Tie keys unchanged; (e) RNG call count stable; (f) New metrics either excluded from or integrated into hash + updated baseline; (g) Events emitted (not direct state mutation) for new mode changes; (h) **Economic coherence preserved** (trades have real consequences, behavioral authenticity maintained).

Common pitfalls: Resorting agents mid step, iterating raw resource dicts, multiple trades per step, silent RNG draws, quadratic partner searches, allocating big objects per frame, modifying inventories in rendering/observer code, **creating artificial parity mechanisms that undermine economic authenticity**.

Handler development: Inherit from `BaseStepHandler` in `simulation/execution/handlers/protocol.py`. Return structured metrics only; emit events for state changes; preserve deterministic ordering. See `MovementHandler`, `CollectionHandler` as examples.

Add events: Wrap any future `agent.mode = ...` inside an event creator (Phase 2 goal is full coverage). Future event targets: resource collection, trade execution, movement decisions.

Key files to study first: `simulation/world.py` (step pipeline), `simulation/execution/step_executor.py` (handler orchestration), `simulation/agent.py` (behavior + mode), `simulation/grid.py` (resource ordering), `observability/events.py` (extensible event types), `tools/launcher/framework/test_configs.py` (scenario definitions).

When unsure: Prefer adding a focused determinism or perf test over speculative refactor. Keep commits logically atomic with WHY in message (e.g., `selection: prune zero ΔU early (perf +1.2%, hash stable)`).

More depth: See `README.md`, `src/econsim/simulation/README.md`, and `docs/launcher_architecture.md`.

**Current Priority (Phase 2 Completion):** Complete handler implementation in `simulation/execution/handlers/` (trading, metrics, respawn). Enable full delegation in `Simulation.step()`. Preserve exact RNG patterns and ordering. Target: reduce `Simulation.step()` from 402 lines to <100 lines orchestration. Validate economic coherence, not hash parity.