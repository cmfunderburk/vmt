from econsim.simulation.grid import Grid
from econsim.simulation.world import Simulation
from econsim.simulation.config import SimConfig

"""Competition test (Gate 4):
Two agents equidistant from a single resource. Deterministic path should cause exactly
one agent to collect it; the other must retarget (become IDLE or RETURN_HOME or pick
another resource if available). We seed an additional resource to verify retargeting.
"""


def test_competition_single_resource_resolution():
    # Grid with two resources so loser can retarget second one (B)
    _ = Grid(7, 7, resources=[(3, 3, "A"), (5, 5, "B")])  # legacy construction kept for narrative
    cfg = SimConfig(
        grid_size=(7, 7),
        initial_resources=[(3, 3, "A"), (5, 5, "B")],
        perception_radius=8,
        respawn_target_density=0.0,
        respawn_rate=0.0,
        max_spawn_per_tick=0,
        seed=0,
        enable_respawn=False,
        enable_metrics=False,
    )
    sim = Simulation.from_config(cfg, agent_positions=[(0,3),(6,3)])
    # Access agents constructed by factory (ids 0,1)
    a1, a2 = sim.agents[0], sim.agents[1]

    import random

    rng = random.Random(0)

    # Step until first resource collected
    collected_tick = None
    for tick in range(10):
        sim.step(rng)
        a_collected = (a1.carrying["good1"] + a1.carrying["good2"]) > 0
        b_collected = (a2.carrying["good1"] + a2.carrying["good2"]) > 0
        if a_collected or b_collected:
            collected_tick = tick
            break
    assert collected_tick is not None, "One agent should collect the contested resource"

    # Exactly one collected so far
    total_collected = (
        a1.carrying["good1"] + a1.carrying["good2"] + a2.carrying["good1"] + a2.carrying["good2"]
    )
    assert total_collected == 1, "Only one resource should have been collected at this point"

    # Advance a few more ticks so loser retargets toward remaining resource (5,5)
    for _ in range(12):
        sim.step(rng)
        if sim.grid.resource_count() == 0:
            break

    # Both resources should eventually be collected
    assert (
        sim.grid.resource_count() == 0
    ), "Both resources should be collected after continued decision steps"
    # Total goods carried should be 2 (one each or both by one agent acceptable, but no duplication)
    total_collected = (
        a1.carrying["good1"] + a1.carrying["good2"] + a2.carrying["good1"] + a2.carrying["good2"]
    )
    assert (
        total_collected == 2
    ), "Total collected goods should equal number of resources originally present"

    # Deterministic tie-break should select a consistent winner (document expectation)
    # With current tie-break (-delta_u, dist, x, y) and identical preferences/dist,
    # lower x coordinate of resource candidate influences only via later tiebreak; agents are symmetric.
    # Movement ordering (agent list order) confers priority. Assert stable winner id for contested resource.
    winner_first = 1 if a1.carrying["good1"] + a1.carrying["good2"] >= 1 else 2
    assert (
        winner_first == 1
    ), "Agent 1 should deterministically win the first contested collection given ordering"
