# VMT API Guide (Interim – Pre Gate 6 Integration)

This guide documents how to use the existing economic simulation components **as they function today**.
A configuration factory and higher-level GUI integration will arrive in Gate 6. Until then, construction
is manual and explicit. All examples assume Python 3.11+.

## 1. Core Concepts
- `Grid`: typed resource storage (A,B) at integer coordinates; deterministic iteration.
- `Agent`: preference-driven collector with carrying vs home inventory, decision or random movement.
- `Simulation`: orchestrates agents + grid per step; optional hooks for respawn & metrics.
- `Preferences`: pluggable utility forms (Cobb-Douglas, Perfect Substitutes, Leontief) via factory.
- Hooks (manual wiring now): `RespawnScheduler`, `MetricsCollector`.

## 2. Minimal Decision-Mode Simulation
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

## 3. Random Walk (Legacy Path)
```python
# Replace use_decision=True with use_decision=False (default) to employ legacy movement
sim.step(rng, use_decision=False)
```
Use only for baseline comparisons; Gate 6 will default UI to decision mode.

## 4. Wiring Respawn & Metrics
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
- Hooks are inert unless explicitly assigned.
- Determinism hash covers agents + resources each step (ordering sensitive).

## 5. Snapshot & Replay
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

## 6. Preferences via Factory
```python
from econsim.preferences import PreferenceFactory
ps = PreferenceFactory.create("perfect_substitutes", a=2.0, b=1.0)
cd = PreferenceFactory.create("cobb_douglas", alpha=0.6)
leo = PreferenceFactory.create("leontief", a=2.0, b=4.0)
print(cd.utility((3.0,5.0)))
```
Parameter validation raises `PreferenceError` on invalid input.

## 7. Determinism Guarantees (Do Not Break Lightly)
- Resource iteration order: `Grid.iter_resources_sorted()` used in target selection.
- Tie-break key: (−ΔU, distance, x, y).
- Agent list order conveys priority in simultaneous contests.
- Epsilon bootstrap (`EPSILON_UTILITY`) lifts zero bundles to avoid stall.
- Metrics hash canonical ordering: sorted agents + sorted resources.

## 8. Performance Notes
- Frame target ~60 FPS (GUI path). Avoid enlarging 320x240 surface or adding per-tick allocations.
- Decision loop complexity: O(agents + visible resources). Keep respawn / metrics similarly linear.

## 9. Current Limitations
| Limitation | Impact | Planned Resolution |
|------------|--------|-------------------|
| No `Simulation.from_config` | Verbose manual wiring | Gate 6 factory |
| GUI default = random mode | Demo under-sells decision logic | Gate 6 flip default |
| Hooks not auto-applied | Respawn/metrics invisible to new users | Gate 6 config integration |
| No menus / overlays control | Hard-coded visuals | Gate 8 basic controls |
| Trading / production absent | Economic depth limited | Gates 7–9 sequencing |

## 10. Upcoming (Gate 6 Scope Preview)
- Factory applying seed, respawn, metrics, default decision mode.
- Minimal overlay toggle path exposed.
- Public API adoption in tests (remove private `_rng` & manual hook pokes).

## 11. Troubleshooting
| Symptom | Cause | Fix |
|---------|-------|-----|
| Respawn not occurring | Scheduler not assigned | Assign `RespawnScheduler` to `sim.respawn_scheduler` |
| Metrics hash empty | `MetricsCollector` missing or disabled | Attach collector instance |
| Agents idle immediately | No positive ΔU targets (all consumed) | Add resources or attach respawn |
| Unexpected divergence between runs | Tie-break logic altered | Revert ordering / verify sorted iteration |

## 12. Testing Reference
Representative tests (browse under `tests/unit/`):
- `test_decision_determinism.py` – identical trajectories across seeds.
- `test_competition.py` – deterministic contest resolution.
- `test_respawn_density.py` – density convergence & no overshoot.
- `test_determinism_hash.py` – hash stability vs divergence.

---
Last updated: 2025-09-23 (pre Gate 6 integration).
