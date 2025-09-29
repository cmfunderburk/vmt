## VMT Copilot Instructions (High-Signal, 2025-09)
Purpose: Let AI edits improve functionality without breaking determinism, performance, or educational clarity. Keep changes localized, append-only, and test-backed.

### 1. Immutable Frame Pipeline
`QTimer(16ms)` → `Simulation.step(ext_rng, use_decision)` → `_update_scene()` → `paintEvent()`. Do NOT add new timers/threads, blocking loops, or recreate the Pygame surface. No per‑pixel Python iteration; draw via existing blits.

### 2. Determinism Invariants (NEVER VIOLATE)
1. Resource ordering: only via `Grid.iter_resources_sorted()`.
2. Tie-break keys: resources `(-ΔU, distance, x, y)`; trade intents `(-ΔU, seller_id, buyer_id, give_type, take_type)` (priority flag path uses this; must not alter multiset).
3. Agent list order defines priority—never reorder in-place mid step.
4. RNG separation: caller-supplied `ext_rng` vs internal `Simulation._rng`; keep call counts stable (don’t sprinkle extra random draws).
5. Serialization & determinism hash: schemas are append-only; hash excludes trade-only + debug/overlay metrics. Do not reorder existing serialized fields.

### 3. Core Edit Surface (touch these, not clones)
`simulation/world.py` (orchestrator) · `simulation/agent.py` (unified selection & modes) · `simulation/grid.py` (spatial + sorted iteration) · `simulation/config.py` (factory) · `preferences/` (utility forms) · `gui/embedded_pygame.py` (single surface bridge) · launcher logic under `MANUAL_TESTS/enhanced_test_launcher_v2.py` & helpers (debug test shell). Avoid parallel “experimental_*.py” forks—extend canonical modules.

### 4. Unified Target Selection
Distance‑discounted utility: ΔU' = ΔU / (1 + k·d²). Single ranking merges resource pickups and (feature‑gated) trade intents. Maintain O(agents + visible resources); leverage spatial index—no nested full scans. Mixed-type ties: deterministic ordering preserved via existing tuple components; do not add ad hoc fields.

### 5. Bilateral Exchange (Feature-Gated)
Flags: `ECONSIM_TRADE_DRAFT=1` (enumerate), `ECONSIM_TRADE_EXEC=1` (execute ≤1 intent/step; implies draft). Priority tuple as above; enabling priority reorders only. Trade metrics & debug overlays are hash‑excluded. Foraging disabled + trade enabled triggers partner search / meeting workflow; stagnation rule: 100 idle-improvement steps → forced return_home deposit then idle.

### 6. Foraging & Idle Semantics
`ECONSIM_FORAGE_ENABLED=0` disables collection. If foraging + trading both disabled → agents idle in place (retain carrying inventory). When both on, collection precedes trade enumeration (collecting agent excluded from trade that tick).

### 7. Performance Guardrails
Target ~60–62 FPS; floor ≥30 (`make perf`). Per-step complexity O(agents+resources). Overlays read-only: keep added overlay cost <2% (avoid allocations in loops; reuse surfaces/fonts). Run `scripts/perf_stub.py` if touching draw or selection paths.

### 8. Safe Extension Checklist
Before commit: 1) `pytest -q` green 2) `make perf` acceptable 3) No new unordered iteration 4) Tie-break tuples untouched 5) New metrics either hash-excluded or determinism tests updated 6) Commit message: WHAT + WHY (+ PERF/DET note if relevant).

### 9. Common Pitfalls (AVOID)
Reordering agent list; alternate unsorted resource scans; extra RNG draws; per-frame allocations; blocking sleeps; modifying trade priority shape; adding hidden state to hash without tests; creating duplicate GUI surfaces.

### 10. Structural & Schema Rules
Append-only for snapshot/agent/grid/world serialization; never reorder or remove fields. One executed trade max per step (when exec flag on). Overlays must be state-neutral (visual only). Idle path must not mutate inventories except explicit stagnation deposit rule.

### 11. Minimal Factory Usage
```python
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
cfg = SimConfig(grid_size=(12,12), seed=123, distance_scaling_factor=1.5,
				enable_respawn=True, enable_metrics=True)
sim = Simulation.from_config(cfg, agent_positions=[(0,0)])
```

### 12. Primary Workflows
Development GUI (legacy simple shell): `make dev`. High-visibility debug launcher: `make launcher`. Tests: `pytest -q`. Performance spot check: `make perf`. Formatting/lint: `make format` / `make lint`. Prefer the factory; legacy manual wiring is deprecated.

### 13. When Unsure
Add/extend a determinism or performance test instead of guessing. Keep edits small; document rationale in commit body if touching selection, movement, or serialization.

Reference depth docs: `README.md` (current state), `ROADMAP_REVISED.md` (forward), existing tests (behavioral contracts). Stay within these guardrails for safe iteration.