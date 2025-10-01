## VMT EconSim – AI Coding Agent Guide (Concise)
Mission: Deterministic educational micro‑economics simulation (PyQt6 + Pygame). Absolute rule: economic coherence > cosmetic determinism. Never add ghost/rollback logic to “preserve hashes.” If you change ordering, RNG draws, tie‑breaks, or asymptotic step cost—stop and add/update tests first.

Core flow (single thread): PyQt6 QTimer (≈16ms) → `Simulation.step(ext_rng, use_decision)` → `StepExecutor` → ordered handlers → Pygame blit → Qt paint. Core code: `src/econsim/simulation/`; GUI + launcher: `src/econsim/gui/`, `src/econsim/tools/launcher/`.

Canonical construction:
```python
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
cfg = SimConfig(grid_size=(12,12), seed=123, enable_respawn=True, enable_metrics=True)
sim = Simulation.from_config(cfg, agent_positions=[(0,0)])
```

Determinism invariants (DO NOT break):
1. Resources only via `Grid.iter_resources_sorted()` / stable serialization
2. Selection tie key `(-ΔU, distance, x, y)`; trade tie key `(-ΔU, seller_id, buyer_id, give_type, take_type)`
3. Preserve original agent list order every step
4. External RNG passed to `step` separate from internal `_rng` (no extra / reordered draws)
5. ≤ 1 trade executed per step when execution enabled

Handler pipeline (Phase 2 complete): Movement → Collection → Trading → Metrics → Respawn. Put new per‑step logic in a handler (inherit `BaseStepHandler`), not back into `Simulation.step()`.

Selection / decision system: Distance‑discounted utility `ΔU' = ΔU / (1 + k*d^2)`; reject non‑positive ΔU early. Complexity must remain O(agents + visible_resources); avoid quadratic partner scans.

Feature flags (env): `ECONSIM_LEGACY_RANDOM=1` (fallback movement), `ECONSIM_FORAGE_ENABLED=0`, `ECONSIM_TRADE_DRAFT=1`, `ECONSIM_TRADE_EXEC=1`, `ECONSIM_HEADLESS_RENDER=1`, debug: `ECONSIM_DEBUG_AGENT_MODES=1`, `ECONSIM_DEBUG_FPS=1`.

Events & observability: Emit events via `observability/events.py`; never call GUI directly from simulation. Add collection/trade/mode events rather than inline prints. Keep logging overhead <2%.

Performance guardrails: Per‑step O(n). Movement handler budget ≤3ms typical. Avoid new large per‑frame allocations or hidden loops. Run `make perf` after impactful changes.

Hash & schema rules: Dataclasses / snapshot / trade tuples are append‑only. Determinism hash excludes debug & trade metrics; if legitimate behavioral change alters hash, refresh `baselines/determinism_hashes.json` with rationale.

Testing workflow: `make venv && source vmt-dev/bin/activate` then `pytest -q`. Headless GUI: set `QT_QPA_PLATFORM=offscreen` and `SDL_VIDEODRIVER=dummy`. Always construct sims with `Simulation.from_config` in tests.

Launcher / scenarios: `make launcher` (canonical). Programmatic test runner: `from econsim.tools.launcher.test_runner import create_test_runner`. Add scenarios via `tools/launcher/framework/test_configs.py` registry.

Safe extension checklist: tests green; perf within baseline; no new unordered iterations; tie keys unchanged; RNG draw count stable; new metrics either excluded from hash or baseline updated; events (not silent state mutation) for new mode changes; economic coherence preserved.

Common pitfalls: resorting agents mid‑step; iterating unsorted resource containers; multiple trades per step; silent RNG draws; quadratic partner scans; per‑frame big object creation; modifying inventories from rendering/observer code; adding parity hacks that undo real trades.

Where to look first: `simulation/world.py` (orchestration), `simulation/execution/step_executor.py`, handlers under `simulation/execution/handlers/`, `simulation/agent.py`, `simulation/grid.py`, `observability/events.py`, `simulation/trade.py` (enumeration + execution), `metrics.py` (hash + trade metrics).

When unsure: add a focused determinism or perf test instead of speculative refactor. Commit messages: concise WHAT + WHY (e.g. `selection: prune zero ΔU early (perf +1.2%, hash stable)`).

Current refinement focus: broaden event coverage (collection/trade execution), metrics fidelity, scaling perf validation, determinism baseline refresh tied to respawn cadence updates.