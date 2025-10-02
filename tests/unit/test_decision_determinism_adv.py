import random
from typing import Any

from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.agent import Agent
from econsim.simulation.grid import Grid
from econsim.simulation.world import Simulation


def snapshot(
    sim: Simulation,
) -> list[
    tuple[
        str,
        tuple[int, int],
        tuple[int, int] | None,
        tuple[tuple[str, int], ...],
        tuple[tuple[str, int], ...],
    ]
]:
    return [
        (
            a.mode.value,
            a.pos,
            a.target,
            tuple(sorted(a.carrying.items())),
            tuple(sorted(a.home_inventory.items())),
        )
        for a in sim.agents
    ]


def build_sim(seed: int):
    # deterministic resource layout
    resources = [
        (2, 2, "A"),
        (4, 1, "B"),
        (5, 5, "A"),
        (1, 4, "B"),
        (3, 3, "A"),
    ]
    grid = Grid(8, 8, resources=resources)
    pref = CobbDouglasPreference(alpha=0.55)
    agents = [
        Agent(id=0, x=0, y=0, preference=pref),
        Agent(id=1, x=7, y=7, preference=pref),
    ]
    return Simulation(grid, agents)


def test_decision_determinism_adv():
    sim1 = build_sim(1)
    sim2 = build_sim(1)
    rng1 = random.Random(123)  # only relevant if fallback random path used
    rng2 = random.Random(123)
    states1: list[Any] = []
    states2: list[Any] = []
    steps = 30
    for _ in range(steps):
        sim1.step(rng1)
        sim2.step(rng2)
        states1.append(snapshot(sim1))
        states2.append(snapshot(sim2))
    assert states1 == states2
    # At least one collection happened (resource count decreased)
    remaining = sim1.grid.resource_count()
    assert remaining < 5
