import random
import time

from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.agent import Agent
from econsim.simulation.grid import Grid
from econsim.simulation.world import Simulation

# Performance guardrails (lightweight, not a full benchmark):
# - Ensure we can execute >= N decision steps per second for a modest scenario.
# - Scenario: 20 agents, 120 resources, 200 ticks.
# - We assert a soft floor on steps/second to catch gross regressions.
#   Chosen threshold conservative to reduce flakiness in CI.

MIN_STEPS_PER_SECOND = 2000  # empirical conservative floor (tune if noisy)


def _build_scenario():
    # Grid 40x40 with scattered resources (types alternating)
    resources: list[tuple[int, int, str]] = []
    for i in range(120):
        x = (i * 7) % 40
        y = (i * 11) % 40
        rtype = "A" if i % 2 == 0 else "B"
        resources.append((x, y, rtype))
    grid = Grid(40, 40, resources=resources)
    agents: list[Agent] = []
    for i in range(20):
        agents.append(
            Agent(id=i, x=i % 10, y=(i * 3) % 10, preference=CobbDouglasPreference(alpha=0.5))
        )
    return Simulation(grid, agents)


def test_decision_mode_step_throughput():
    sim = _build_scenario()
    rng = random.Random(123)
    ticks = 200
    start = time.perf_counter()
    for _ in range(ticks):
        sim.step(rng)
    duration = time.perf_counter() - start
    steps_per_sec = ticks / duration if duration > 0 else float("inf")
    # Soft assertion with headroom
    assert (
        steps_per_sec >= MIN_STEPS_PER_SECOND
    ), f"Decision mode throughput regression: {steps_per_sec:.1f} < {MIN_STEPS_PER_SECOND} steps/sec"


# Micro benchmark for marginal decision cost (single agent target selection overhead)
# We measure average time per select_target call and assert it's below a threshold.
MAX_SELECT_TARGET_MICRO_SECONDS = 3000  # 3 ms per call upper bound (very lenient)


def test_select_target_micro_overhead():
    sim = _build_scenario()
    agent = sim.agents[0]
    grid = sim.grid
    iterations = 200
    start = time.perf_counter()
    for _ in range(iterations):
        # Force reselection state
        agent.target = None
        agent.select_target(grid)
    duration = time.perf_counter() - start
    avg_us = (duration / iterations) * 1e6
    assert (
        avg_us <= MAX_SELECT_TARGET_MICRO_SECONDS
    ), f"select_target average {avg_us:.1f}us exceeds {MAX_SELECT_TARGET_MICRO_SECONDS}us threshold"
