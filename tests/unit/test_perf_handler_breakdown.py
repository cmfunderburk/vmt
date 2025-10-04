from __future__ import annotations
import random, statistics
from econsim.simulation.world import Simulation
from econsim.simulation.grid import Grid
from econsim.simulation.agent import Agent
from econsim.simulation.respawn import RespawnScheduler
from econsim.preferences.cobb_douglas import CobbDouglasPreference

STEPS=120

def build(n_agents=25, n_resources=150):
    pref = CobbDouglasPreference(alpha=0.5)
    grid = Grid(50,40)
    for i in range(n_resources):
        x = (i * 13) % grid.width
        y = (i * 7) % grid.height
        grid.add_resource(x,y,"A" if i % 2 == 0 else "B")
    agents=[Agent(id=i,x=i%grid.width,y=(i*5)%grid.height,preference=pref) for i in range(n_agents)]
    return Simulation(grid=grid, agents=agents, config=None)


def capture(sim: Simulation):
    rng = random.Random(999)
    handler_timings=[]
    for _ in range(STEPS):
        sim.step(rng)
        mts = sim.last_step_metrics or {}
        handler_timings.append(mts.get('handler_timings', {}))
    # Aggregate average per handler
    agg={}
    for rec in handler_timings:
        for k,v in rec.items():
            agg.setdefault(k, []).append(v)
    return {k: statistics.mean(v) for k,v in agg.items()}


def test_handler_breakdown_snapshot():  # not a strict assertion; prints for investigation
    base = build()
    enhanced = build()
    # MetricsCollector removed - determinism testing will be handled by delta recorder in future
    enhanced.respawn_scheduler = RespawnScheduler(target_density=0.18, max_spawn_per_tick=40, respawn_rate=0.5)
    base_t = capture(base)
    enh_t = capture(enhanced)
    print("BASE", base_t)
    print("ENH", enh_t)
    # Ensure we captured something
    assert base_t and enh_t
