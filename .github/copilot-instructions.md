## VMT Copilot Instructions (Concise)
Purpose: Enable AI agents to modify the simulation without breaking determinism, performance, or educational clarity.

### 1. Immutable Core Pipeline
`QTimer(16ms)` → `Simulation.step(ext_rng, use_decision)` → `_update_scene()` → `paintEvent()`
Never add timers/threads/blocking loops or recreate the Pygame surface; no per‑pixel Python work.

### 2. Determinism Invariants (DO NOT BREAK)
1. Resource ordering: iterate via `Grid.iter_resources_sorted()` only.
2. Tie-break keys: resources `(-ΔU, distance, x, y)`; trades `(-ΔU, seller_id, buyer_id, give_type, take_type)`.
3. Agent list order = priority; never reorder in-place mid step.
4. RNG separation: external `ext_rng` param vs internal `Simulation._rng` (keep call counts stable).

### 3. Core Files (edit here, not ad hoc clones)
`simulation/world.py` (orchestrator) · `simulation/agent.py` (unified target selection) · `simulation/grid.py` (spatial + sorted iteration) · `simulation/config.py` (factory) · `preferences/factory.py` (utility forms) · `gui/embedded_pygame.py` (single surface bridge) · `gui/debug_logger.py` (structured logging) · launcher framework under `tools/launcher/` (TestRunner + configs).

### 4. Decision & Selection Pattern
Unified selection ranks resource pickups vs (flagged) trade intents using distance‑discounted utility: ΔU' = ΔU / (1 + k·d²). Maintain O(agents + visible resources). Use existing spatial index; do not introduce quadratic scans.

### 5. Performance Guardrails
Target ~60–62 FPS; ≥30 floor (`make perf`). O(n) per step (n=agents+resources). Overlays: pure read-only; keep <2% overhead. Reuse surfaces/fonts; avoid allocating inside tight loops.

### 6. Feature / Teaching Flags (Core)
`ECONSIM_LEGACY_RANDOM=1` (disable decision logic) · `ECONSIM_FORAGE_ENABLED=0` (no collection) · `ECONSIM_TRADE_DRAFT=1` / `ECONSIM_TRADE_EXEC=1` (prototype bilateral exchange) · `ECONSIM_DEBUG_AGENT_MODES=1` (mode logs). Combine carefully; idle semantics when both foraging & trading disabled.

### 6a. Debug Logging Flags (Structured System)
`ECONSIM_LOG_LEVEL={CRITICAL|EVENTS|PERIODIC|VERBOSE}` · `ECONSIM_LOG_FORMAT={COMPACT|STRUCTURED}` · `ECONSIM_LOG_CATEGORIES="TRADE,PERF,MODE"` (comma-separated) · `ECONSIM_LOG_EXPLANATIONS=1` (utility context) · `ECONSIM_LOG_DECISION_REASONING=1` (agent reasoning). Use `gui/debug_logger.py` builders; avoid direct print/logging calls.

### 7. Launcher & Programmatic Workflow
Primary entry: `make launcher` (uses TestRunner `create_test_runner()` + registry `ALL_TEST_CONFIGS`). Legacy GUI: `make dev` (maintenance only). For tests: extend `MANUAL_TESTS/framework/test_configs.py` registry, not ad hoc scripts. Use `SimConfig` factory pattern: `Simulation.from_config(cfg)` for deterministic setup.

### 8. Safe Extension Checklist
Before committing: (a) `pytest -q` (determinism + hash) (b) `make perf` (FPS) (c) ensure no new unordered iteration (d) verify tie-break keys untouched (e) added metrics either hash-excluded or tests updated (f) debug logging uses structured builders from `gui/debug_logger.py`.

### 9. Common Pitfalls
Reordering agents; injecting extra RNG draws; alternative resource scans; adding blocking sleeps; per-frame allocations in render loop; modifying trade ordering tuple shape.

### 10. Minimal Factory Example
```python
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
cfg = SimConfig(grid_size=(12,12), seed=123, distance_scaling_factor=1.5, enable_respawn=True, enable_metrics=True)
sim = Simulation.from_config(cfg, agent_positions=[(0,0)])
```

### 11. Structural Rules
Append-only: snapshot / agent / grid / world schemas. Do not retroactively reorder fields. New overlays must be state-neutral. One trade max per step when execution flag enabled.

### 12. Commit Message Pattern
Short imperative: WHAT + WHY + (optional) PERF/DET note. Example: "agent: cache distance map to cut selection O(n) → O(1) (no hash change)".

### 13. Pre-PR Quick Gate
1. `pytest -q` green  2. `make perf` within expected FPS  3. No mypy/flake regressions (if configured)  4. Hash unchanged unless intentionally extended  5. Updated docs if new flag / config added.

If unsure about a change touching ordering, add/extend a determinism test instead of guessing.

End of concise instructions – expand via `README.md` & `docs/` when deeper context needed.

If unsure about a change touching ordering, add/extend a determinism test instead of guessing.

End of concise instructions – expand via `README.md` & `docs/` when deeper context needed.