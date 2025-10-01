"""Lightweight performance safeguard for decision-mode stepping.

The goal is to ensure a minimum raw decision step throughput independent of GUI
FPS variability. This guards against accidental O(N^2) or per-step heap churn
regressions introduced in decision logic or factory wiring.

Heuristic: Run 4,000 decision steps on a small grid with 25 resources and 12
agents. On typical CI (Python 3.11), this should complete well under 0.25s.
We assert a conservative floor of 4,000 steps/sec (i.e. runtime <1.0s) to keep
the test robust on slower shared runners while still catching major slowdowns.
"""

from __future__ import annotations

import time
import random

from econsim.simulation.grid import Grid
from econsim.simulation.world import Simulation
from econsim.simulation.agent import Agent
from econsim.preferences.cobb_douglas import CobbDouglasPreference

# NOTE: This test intentionally accesses the protected _rng attribute to avoid adding
# an extra public accessor solely for performance safeguards. We suppress the style
# warning via noqa comments (SLF001) with clear justification.


def test_decision_step_throughput_floor():
    pref = CobbDouglasPreference(alpha=0.5)
    grid = Grid(40, 30)
    # Seed resources in a simple pattern (no randomness needed)
    for i in range(25):
        grid.add_resource((i * 3) % 40, (i * 5) % 30)
    agents = [Agent(id=i, x=i % 40, y=(i * 2) % 30, preference=pref) for i in range(12)]
    sim = Simulation(grid, agents)

    steps = 4000
    start = time.perf_counter()
    # Use an independent deterministic RNG; internal RNG determinism is exercised elsewhere.
    rng = random.Random(12345)
    for _ in range(steps):
        sim.step(rng)
    elapsed = time.perf_counter() - start
    # Floor: must exceed 4000 steps/sec => elapsed < 1s for 4000 steps
    assert elapsed < 1.0, (
        f"Decision step throughput regression: {steps} steps took {elapsed:.3f}s (<1.0s expected)"
    )
    # Provide additional safety informational ratio
    steps_per_sec = steps / elapsed
    # Soft expectation (not asserted hard to avoid flakiness): typical > 15000 steps/sec
    if steps_per_sec < 6000:
        # This branch indicates a moderate slowdown worth inspecting but not a hard failure.
        # Could be logged or turned into a stricter assert in future gates.
        print(
            f"[PERF INFO] decision steps/sec lower than historical typical: {steps_per_sec:.0f}"  # noqa: T201
        )
