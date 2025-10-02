"""Tie-break ordering test (Gate 4).

Validates that when multiple resource candidates yield identical positive
delta utility and identical distance, the agent's `select_target` resolves
deterministically using the documented ordering key:
    (-delta_u, distance, x, y)

Here we construct a symmetric scenario:
 - Agent at (0,0)
 - Two resources of different types placed at equal Manhattan distance 3:
       (3,0, 'A') and (0,3, 'B')
 - Cobb-Douglas alpha=0.5 => marginal gain from +1 of either good is identical
   when starting bundle is (0,0) (epsilon bootstrap lifts zeros equally).

Expectation: Both candidates produce identical delta_u and distance; ordering
falls through to lexicographic (x,y) -> (0,3) < (3,0) so target should be (0,3).

We assert the first selected target matches lexicographic ordering and that
after collecting it the agent can subsequently acquire the second resource.
"""

from __future__ import annotations

import random

from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.agent import Agent
from econsim.simulation.grid import Grid
from econsim.simulation.world import Simulation


def test_tiebreak_lexicographic_when_delta_and_distance_equal():
    grid = Grid(8, 8, resources=[(3, 0, "A"), (0, 3, "B")])
    agent = Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
    sim = Simulation(grid, [agent])
    rng = random.Random(0)

    # Advance one decision tick; agent should pick lexicographically smaller target (0,3)
    sim.step(rng)
    assert agent.target in {(0, 3), (3, 0)}  # sanity
    assert (
        agent.target == (0, 3)
    ), f"Expected lexicographic tie-break target (0,3); got {agent.target}"

    # Step until first collection happens (should be B at (0,3))
    for _ in range(10):
        sim.step(rng)
        if agent.carrying["good2"] >= 1 or agent.carrying["good1"] >= 1:
            if agent.carrying["good2"] >= 1:
                break
    assert agent.carrying["good2"] >= 1, "Agent should collect B first via tie-break ordering"

    # Continue until second resource collected
    for _ in range(20):
        sim.step(rng)
        if agent.carrying["good1"] >= 1 and agent.carrying["good2"] >= 1:
            break
    assert (
        agent.carrying["good1"] >= 1 and agent.carrying["good2"] >= 1
    ), "Agent should eventually collect both resources"
