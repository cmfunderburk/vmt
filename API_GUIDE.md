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
    - Respawn baseline now alternates resource types A ↔ B deterministically (no added complexity).

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
# Replace use_decision=True with use_decision=False (default) to employ legacy movement
sim.step(rng, use_decision=False)
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
* Alternating resource type spawn (A/B) is handled internally by `RespawnScheduler` (baseline diversity).

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
- Respawn diversity: simple alternating A/B sequence (seed + spawn order fully determines types; no extra RNG draws).
- Agent home placement: deterministic `random.sample` of all grid cells using secondary RNG seeded with `seed+9973`.
    Changing the offset or introducing additional draws would alter home distribution for a given seed; gate any such change.

## 9. Performance Notes
- Frame target ~60 FPS (GUI path). Avoid enlarging 320x320 surface or adding per-tick allocations.
- Decision loop complexity: O(agents + visible resources). Respawn & metrics remain linear; alternation adds O(1) per spawn.

## 10. Controller Introspection (Agent Metrics Accessors)
The GUI leverages read-only helper methods on `SimulationController` (exposed via the new UI path). They are pure and safe for overlays/testing:
```python
controller.list_agent_ids()            # -> list[int]
controller.agent_carry_bundle(aid)     # -> (good1:int, good2:int)
controller.agent_carry_utility(aid)    # -> float | None (utility of carrying bundle only)
```
Properties:
* Deterministic ordering (sorted IDs)
* No mutation or RNG usage
* Utility computed from current carrying goods only (home inventory excluded by design for immediate marginal context)

## 11. Current Limitations
| Limitation | Impact | Planned Resolution |
|------------|--------|-------------------|
| Weighted multi-type respawn | Only simple A/B alternation | Future strategy gate |
| GUI trade / production | Economic depth limited | Interaction & production gates |
| Utility contour overlays | Limited pedagogical visualization | Future overlay gate |
| No menus / overlays control | Hard-coded visuals | Gate 8 basic controls |
| Trading / production absent | Economic depth limited | Gates 7–9 sequencing |

## 12. Snapshot & Replay Integrity
Unchanged: snapshot excludes `RespawnScheduler` internal alternation flag; replay parity relies on reproducing spawn order. If future serialization includes scheduler state, include the alternation toggle at the end of existing fields.

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
Last updated: 2025-09-23 (Docs update: alternating respawn, controller accessors, agent metrics UI).
