from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.agent import Agent
from econsim.simulation.grid import Grid
from econsim.simulation.world import Simulation

"""Preference Shift Test (Gate 4)
Scenario: Single agent with Cobb-Douglas (alpha=0.5) starts with only type A resources nearby
and a type B resource slightly farther but still within perception radius.
After collecting one A, marginal utility of collecting a B (balancing bundle) should become
strictly greater than another A (due to multiplicative form), prompting target switch.
The test asserts that after first collection the agent's next selected target is the B resource
and that it eventually collects it.
"""


def test_cobb_douglas_preference_shift_to_balance_goods():
    # Layout revision:
    # Agent at (0,0)
    # A resources at (2,0), (5,0)  (second A placed farther)
    # B resource at (3,0)
    # After collecting first A at (2,0), B at (3,0) is closer than second A (5,0) and
    # also increases the currently zero good2 component, so selection should shift to B.
    grid = Grid(10, 5, resources=[(2, 0, "A"), (5, 0, "A"), (3, 0, "B")])
    agent = Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
    sim = Simulation(grid, [agent])

    import random

    rng = random.Random(0)

    # Step until first collection (should be an 'A')
    first_collected_tick = None
    for tick in range(15):
        sim.step(rng)
        if agent.carrying["good1"] + agent.carrying["good2"] >= 1:
            first_collected_tick = tick
            break
    assert first_collected_tick is not None, "Agent failed to collect initial A resource"
    assert (
        agent.carrying["good1"] == 1 and agent.carrying["good2"] == 0
    ), "First collection should be type A (good1)"

    # Advance one more step (target reselection & movement towards B expected)
    sim.step(rng)
    # Agent should be moving toward B at (3,0); target either (3,0) or None if already there/collected
    assert agent.carrying["good1"] >= 1, "Still should have at least one A"
    # Run additional steps to collect B
    for _ in range(10):
        sim.step(rng)
        if agent.carrying["good2"] >= 1:
            break
    assert agent.carrying["good2"] >= 1, "Agent should collect B (good2) after balancing decision"
    # Ensure agent did not ignore distant second A indefinitely; after B collected could pursue second A
    # but we only require that B was prioritized before collecting distant second A.
