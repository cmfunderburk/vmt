from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.agent import Agent
from econsim.simulation.grid import Grid
from econsim.simulation.world import Simulation


def test_epsilon_bootstrap_enables_initial_target():
    grid = Grid(6, 6, resources=[(2, 2, "A")])
    a = Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
    sim = Simulation(grid, [a])
    # Run decision mode explicitly
    import random

    rng = random.Random(0)
    for _ in range(10):
        sim.step(rng=rng)
        if a.carrying["good1"] > 0 or a.carrying["good2"] > 0:
            break
    assert (
        a.carrying["good1"] + a.carrying["good2"] >= 1
    ), "Agent should collect at least one resource with epsilon bootstrap"
