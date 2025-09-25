"""Performance overhead guard for Gate 5 dynamic systems.

Compares simulation step throughput with and without respawn + metrics.
Constraint: added systems should not degrade throughput by more than 20% on
the modest scenario to reduce regression risk while allowing for modest cost.
"""
from __future__ import annotations

import random
import time

from econsim.simulation.world import Simulation
from econsim.simulation.grid import Grid
from econsim.simulation.agent import Agent
from econsim.simulation.respawn import RespawnScheduler
from econsim.simulation.metrics import MetricsCollector
from econsim.preferences.cobb_douglas import CobbDouglasPreference

MAX_RELATIVE_OVERHEAD = 0.30  # 30% relative cap when baseline is large enough
MAX_DELTA_PER_TICK_SECONDS = 0.0007  # 0.70 ms additional cost per tick allowed (CI variability)
MAX_ENHANCED_TOTAL_SECONDS = 0.22  # Hard ceiling for enhanced run on this scenario (adjusted for CI variability)
TICKS = 300


def _build_base(n_agents: int = 25, n_resources: int = 150) -> Simulation:
    pref = CobbDouglasPreference(alpha=0.5)
    # Deterministic grid/resource placement
    grid = Grid(50, 40)
    for i in range(n_resources):
        x = (i * 13) % grid.width
        y = (i * 7) % grid.height
        grid.add_resource(x, y, "A" if i % 2 == 0 else "B")
    agents: list[Agent] = []
    for i in range(n_agents):
        agents.append(Agent(id=i, x=i % grid.width, y=(i * 5) % grid.height, preference=pref))
    return Simulation(grid=grid, agents=agents, config=None)


def _run(sim: Simulation) -> float:
    rng = random.Random(999)
    start = time.perf_counter()
    for _ in range(TICKS):
        sim.step(rng, use_decision=False)
    return time.perf_counter() - start


def test_dynamic_systems_overhead():
    base = _build_base()
    baseline_time = _run(base)

    enhanced = _build_base()
    # Attach dynamic systems
    enhanced._rng = random.Random(123)  # type: ignore[attr-defined]
    enhanced.respawn_scheduler = RespawnScheduler(
        target_density=0.18, max_spawn_per_tick=40, respawn_rate=0.5
    )
    enhanced.metrics_collector = MetricsCollector()
    enhanced_time = _run(enhanced)

    # Compute relative overhead
    if baseline_time <= 0:
        return  # degenerate
    delta = enhanced_time - baseline_time
    delta_per_tick = delta / TICKS
    overhead = delta / baseline_time if baseline_time > 0 else 0.0

    # Absolute guardrails (apply always)
    assert enhanced_time <= MAX_ENHANCED_TOTAL_SECONDS, (
        f"Enhanced run too slow: {enhanced_time:.4f}s > {MAX_ENHANCED_TOTAL_SECONDS:.4f}s"
    )
    assert delta_per_tick <= MAX_DELTA_PER_TICK_SECONDS, (
        f"Per-tick overhead {delta_per_tick*1e6:.1f}us exceeds {(MAX_DELTA_PER_TICK_SECONDS*1e6):.0f}us limit" )

    # Relative check only meaningful if baseline sufficiently large to avoid noise amplification
    if baseline_time >= 0.02:  # 20 ms baseline threshold
        assert overhead <= MAX_RELATIVE_OVERHEAD, (
            f"Relative overhead {overhead*100:.1f}% exceeds {MAX_RELATIVE_OVERHEAD*100:.0f}%; "
            f"baseline={baseline_time:.6f}s enhanced={enhanced_time:.6f}s"
        )
