# VMT API Guide

This guide documents how to use the simulation components with the Gate 6+ factory plus the legacy
manual wiring path (deprecated for new code). It reflects recent increments: alternating multi-type
respawn (A/B baseline), square grid cell rendering, agent metrics UI accessors, and randomized
non-overlapping agent home placement with on-grid home labels. Python 3.11+ assumed.

## 1. Core Concepts
- `Grid`: typed resource storage (A,B) at integer coordinates; deterministic iteration.
- `Agent`: preference-driven collector with carrying vs home inventory, decision or random movement. Each
    agent has a deterministic randomized home (non-overlapping) chosen once at session build; home cell is
    rendered with a small `H{id}` label in the bottom-left for spatial reference.
- `Simulation`: orchestrates agents + grid per step; optional hooks for respawn & metrics.
- `Preferences`: pluggable utility forms (Cobb-Douglas, Perfect Substitutes, Leontief) via factory.
- Hooks (manual wiring now): `RespawnScheduler`, `MetricsCollector`.
    - Respawn baseline now assigns random resource types A/B deterministically (no added complexity).

## 2. Factory Construction (Preferred – Gate 6)
```python
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation

# Define configuration (seed ensures deterministic respawn & future stochastic systems)
cfg = SimConfig(
    grid_size=(10, 10),
    initial_resources=[(2,2,'A'), (5,4,'B'), (7,1,'A')],
    perception_radius=8,
    respawn_target_density=0.25,
    respawn_rate=0.4,
    max_spawn_per_tick=3,
    seed=42,
    enable_respawn=True,
    enable_metrics=True,
)

# Provide agent spawn positions (minimal helper; future gates may add agent_count param)
agent_positions = [(0,0), (3,3)]
sim = Simulation.from_config(cfg, agent_positions=agent_positions)

import random
ext_rng = random.Random(999)  # legacy external RNG still required for random movement path
for _ in range(15):
    sim.step(ext_rng, use_decision=True)

if sim.metrics_collector:
    print("hash:", sim.metrics_collector.determinism_hash())
```

### Why Factory?
* Centralizes config + seed → reproducible builds.
* Auto-attaches respawn & metrics conditional on flags.
* Avoids test-only pokes into internal attributes (e.g. `_rng`).

## 3. Legacy Manual Decision-Mode Simulation (Deprecated)
```python
from econsim.simulation.grid import Grid
from econsim.simulation.agent import Agent
from econsim.simulation.world import Simulation
from econsim.preferences.cobb_douglas import CobbDouglasPreference
import random

# Resources typed: (x,y,type)
grid = Grid(10, 10, resources=[(2,2,'A'), (5,4,'B'), (7,1,'A')])
agents = [Agent(id=0, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))]

sim = Simulation(grid, agents)
rng = random.Random(42)
for _ in range(15):
    sim.step(rng, use_decision=True)  # explicit decision mode

# Inspect agent state
for a in sim.agents:
    print(a.id, a.pos, a.carrying, a.home_inventory)
```

## 4. Random Walk (Legacy Path)
```python
# Decision-based movement is now the only mode (legacy movement removed)
sim.step(rng)
```
Use only for baseline comparisons; Gate 6 will default UI to decision mode.

## 5. Wiring Respawn & Metrics (Manual Legacy Example)
```python
from econsim.simulation.respawn import RespawnScheduler
from econsim.simulation.metrics import MetricsCollector

sim.respawn_scheduler = RespawnScheduler(target_density=0.25, max_spawn_per_tick=3, respawn_rate=0.4)
sim.metrics_collector = MetricsCollector()

for step in range(60):
    sim.step(rng, use_decision=True)

print("determinism hash:", sim.metrics_collector.determinism_hash())
```
Notes:
* Hooks are inert unless explicitly assigned when bypassing the factory.
* Determinism hash covers agents + resources each step (ordering sensitive).
* Random resource type spawn (A/B) is handled internally by `RespawnScheduler` (baseline diversity).

## 6. Snapshot & Replay
```python
from econsim.simulation.snapshot import Snapshot

snap = Snapshot.from_sim(sim)
# Advance further
for _ in range(10):
    sim.step(rng, use_decision=True)
# Restore
restored = Snapshot.restore(snap)
```
Replay determinism currently validated via tests (e.g. hash parity).

## 7. Preferences via Factory
```python
from econsim.preferences import PreferenceFactory
ps = PreferenceFactory.create("perfect_substitutes", a=2.0, b=1.0)
cd = PreferenceFactory.create("cobb_douglas", alpha=0.6)
leo = PreferenceFactory.create("leontief", a=2.0, b=4.0)
print(cd.utility((3.0,5.0)))
```
Parameter validation raises `PreferenceError` on invalid input.

## 8. Determinism Guarantees (Do Not Break Lightly)
- Resource iteration order: `Grid.iter_resources_sorted()` used in target selection.
- Tie-break key: (−ΔU, distance, x, y).
- Agent list order conveys priority in simultaneous contests.
- Epsilon bootstrap (`EPSILON_UTILITY`) lifts zero bundles to avoid stall.
- Metrics hash canonical ordering: sorted agents + sorted resources.
- Respawn diversity: simple random A/B assignment (seed + spawn order fully determines types; no extra RNG draws).
- Agent home placement: deterministic `random.sample` of all grid cells using secondary RNG seeded with `seed+9973`.
    Changing the offset or introducing additional draws would alter home distribution for a given seed; gate any such change.

## 9. Performance Notes
- Frame target ~60 FPS (GUI path). Avoid enlarging 320x320 surface or adding per-tick allocations.
- Decision loop complexity: O(agents + visible resources). Respawn & metrics remain linear; random assignment adds O(1) per spawn.

## 10. Controller Introspection (Agent Metrics Accessors)
The GUI leverages read-only helper methods on `SimulationController` (exposed via the new UI path). They are pure and safe for overlays/testing:
```python
controller.list_agent_ids()            # -> list[int]
controller.agent_carry_bundle(aid)     # -> (good1:int, good2:int)
controller.agent_carry_utility(aid)    # -> float | None (utility of total wealth: carrying + home)
```
Properties:
* Deterministic ordering (sorted IDs)
* No mutation or RNG usage
* Utility computed from the agent's total wealth (carrying + home inventory)

## 11. Current Limitations
| Limitation | Impact | Planned Resolution |
|------------|--------|-------------------|
| Weighted multi-type respawn | Only simple A/B random assignment | Future strategy gate |
| GUI trade / production | Economic depth limited | Interaction & production gates |
| Utility contour overlays | Limited pedagogical visualization | Future overlay gate |
| No menus / overlays control | Hard-coded visuals | Gate 8 basic controls |
| Trading / production absent | Economic depth limited | Gates 7–9 sequencing |

## 12. Snapshot & Replay Integrity
Unchanged: snapshot excludes `RespawnScheduler` internal state; replay parity relies on reproducing spawn order. If future serialization includes scheduler state, include the random assignment state at the end of existing fields.

## 13. Experimental Bilateral Exchange Flags (Gate Bilateral2 Phase 3)
These flags control the prototype reciprocal bilateral exchange system. Default off preserves determinism hash.

| Flag | Effect | Notes |
|------|--------|-------|
| `ECONSIM_TRADE_DRAFT=1` | Enumerate per-cell trade intents (no execution) | Populates `simulation.trade_intents` for overlay/introspection. |
| `ECONSIM_TRADE_EXEC=1` | Execute at most one intent per step | Implies draft enumeration; updates trade metrics. |
| `ECONSIM_TRADE_GUI_INFO=1` | Overlay executed trade summary line | Pure rendering; no state mutation. |
| `ECONSIM_TRADE_PRIORITY_DELTA=1` | Order intents by (-ΔU, seller_id, buyer_id, give_type, take_type) | Optional; baseline keeps first element 0.0; hash-neutral when off. |
| `ECONSIM_TRADE_DEBUG_OVERLAY=1` | Show first few drafted intents + last executed | Set by GUI Debug Overlay checkbox (requires draft). |

Runtime GUI Integration:
* Start Menu checkbox sets all three active flags for initial session.
* Controls panel checkbox toggles all flags live; disabling clears any displayed intents.

Metrics Added (hash-excluded): `trade_intents_generated`, `trades_executed`, `trade_ticks`, `no_trade_ticks`, `realized_utility_gain_total`, `last_executed_trade`, `fairness_round` (advisory).

Design Invariants:
* Single trade per tick (current phase).
* Only carried goods are tradable; home inventory remains banked and immutable during trade execution.
* `delta_utility` becomes part of ordering only when `ECONSIM_TRADE_PRIORITY_DELTA=1` (negative combined delta as first key component).
* Multiset invariance: Dedicated test assures ordering-only effect.
* Test isolation: Autouse fixture clears `ECONSIM_TRADE_*` env vars each test.

Future Enhancements (flag-gated): fairness rotation index, multi-trade analysis, priority upgrade, pedagogical analytics overlays.

### 13.1 Foraging Enable Flag

| Flag | Effect | Notes |
|------|--------|-------|
| `ECONSIM_FORAGE_ENABLED=1` (default if unset) | Agents collect resources in decision mode | Standard behavior |
| `ECONSIM_FORAGE_ENABLED=0` | Disables collection logic | Agents either trade-only (if trade flags set) or idle (no forced home march/deposit) when trading disabled |

Disabling foraging sets explicit `0` (tests rely on explicitness; deletion treated as enabled fallback).

#### 13.1.1 Idle Path Semantics (Updated)
When both foraging and trading are disabled (`ECONSIM_FORAGE_ENABLED=0`, trade flags unset), agents now immediately remain idle in place. They no longer perform an automatic deterministic walk home and deposit their carried goods. This preserves existing carrying inventory across feature toggles and avoids unintended state mutation during instructional demonstrations.

Rationale:
* Inventory invariance while exploring feature combinations.
* Clear visual signal that all economic subsystems are inactive.
* Maintains O(agents) per-step cost (pure no-op path).

### 13.2 Combined Gating Matrix (Decision Mode)

| Forage | Draft | Exec | Behavior Summary |
|--------|-------|------|------------------|
| 0 | 0 | 0 | Idle (no movement/collection/deposit); no intents |
| 0 | 1 | 0 | Draft only; intents may be empty |
| 0 | 1 | 1 | Draft + single execution per step |
| 1 | 0 | 0 | Normal foraging (movement + collection) |
| 1 | 1 | 0 | Forage first; non-foraging agents (if any) may draft |
| 1 | 1 | 1 | Forage first; non-foraging agents may execute one trade |

Collectors (agents that successfully gathered a resource this step) are excluded from that same step's trade enumeration when both systems are active.

### 13.3 Executed Trade Highlight

Recent executed trade cell is outlined (pulsing deterministic color cycle) for 12 steps when overlays are visible. Purely visual; does not affect determinism hash.

### 13.4 Determinism Hash Parity (Deferred Adjustment)

Current hash includes carrying inventories; execution mutates them, so draft-only vs draft+execution runs diverge. A historical parity test is temporarily marked `xfail` while a future hash revision (e.g., isolating pre-trade canonical state or excluding carrying deltas under execution flag) is evaluated.

## 13. Troubleshooting
| Symptom | Cause | Fix |
|---------|-------|-----|
| Respawn not occurring | Scheduler not assigned / disabled flags | Ensure `enable_respawn=True` in factory or assign scheduler |
| Metrics hash empty | `MetricsCollector` missing or disabled | Attach collector instance |
| Agents idle immediately | No positive ΔU targets (all consumed) | Add resources or attach respawn |
| Unexpected divergence between runs | Tie-break logic altered | Revert ordering / verify sorted iteration |

## 13. Testing Reference
Representative tests (browse under `tests/unit/`):
- `test_decision_determinism.py` – identical trajectories across seeds.
- `test_competition.py` – deterministic contest resolution.
- `test_respawn_density.py` – density convergence & no overshoot.
- `test_respawn_type_diversity.py` – A/B alternation presence.
- `test_agent_metrics_ui.py` – controller accessor wiring into GUI.
- `test_determinism_hash.py` – hash stability vs divergence.

---
Last updated: 2025-09-24 (Bilateral Phase 3: priority flag + fairness_round, test isolation fixture).

## 14. Environment Variables
- `ECONSIM_NEW_GUI=1` – Launch the new Start Menu + panels shell (default for `make dev`).
- `ECONSIM_LEGACY_ANIM_BG=1` – Enable legacy animated background in the Pygame viewport (off by default).
- `ECONSIM_METRICS_AUTO=1` – Auto-refresh metrics panel. Optional: `ECONSIM_METRICS_AUTO_INTERVAL_MS` to override interval (min 250ms enforced).
- `ECONSIM_DEBUG_FPS=1` – Print `[FPS]` diagnostic lines once per second in the widget.

## 15. Start Menu Behavior
- Scenarios use decision-based agent behavior (legacy random movement has been removed).
- All simulations now use the unified decision system for consistent, deterministic agent behavior.
- Non-implemented scenarios (e.g., `bilateral_exchange`, `money_market`) are disabled in the dropdown with a “Not implemented yet” tooltip to avoid modal interruptions.
