import os
import random

from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
from econsim.preferences.cobb_douglas import CobbDouglasPreference


def build_sim(k: float) -> Simulation:
    cfg = SimConfig(
        grid_size=(10, 4),
        initial_resources=[(1, 0, 'A')],  # Nearby resource (distance 1)
        seed=123,
        enable_respawn=False,
        enable_metrics=False,
        viewport_size=320,
        distance_scaling_factor=k,
    )
    pref_factory = lambda i: CobbDouglasPreference(alpha=0.5)
    # Agent0 at origin, Agent1 far to the right (distance 4) carrying complementary goods for a strong trade delta
    sim = Simulation.from_config(cfg, pref_factory, agent_positions=[(0, 0), (4, 0)])
    # Inventories to create high trade incentive: agent0 has good1=2, agent1 has good2=2
    sim.agents[0].carrying['good1'] = 2
    sim.agents[1].carrying['good2'] = 2
    return sim


def _step_and_get_choice(sim: Simulation) -> tuple[str, object] | None:
    # Force unified selection path (trade exec implies trade enabled; foraging on)
    os.environ['ECONSIM_FORAGE_ENABLED'] = '1'
    os.environ['ECONSIM_TRADE_EXEC'] = '1'
    os.environ['ECONSIM_UNIFIED_SELECTION_DISABLE'] = '0'
    r = random.Random(999)
    sim.step(r)
    return sim.agents[0].current_unified_task


def test_distance_scaling_partner_discount_monotonic():
    """Partner discounted utility should decrease as k increases (distance penalty stronger)."""
    sim0 = build_sim(k=0.0)
    c0 = _step_and_get_choice(sim0)
    assert c0 is not None and c0[0] == 'partner', f"Expected partner at k=0, got {c0}"
    d0 = c0[1]['discounted']  # type: ignore[index]

    sim_big = build_sim(k=5.0)
    c5 = _step_and_get_choice(sim_big)
    assert c5 is not None and c5[0] == 'partner', f"Expected partner still chosen at k=5 for this setup, got {c5}"
    d5 = c5[1]['discounted']  # type: ignore[index]

    assert d5 < d0, f"Expected discounted partner score to decrease with higher k: k0={d0}, k5={d5}"
