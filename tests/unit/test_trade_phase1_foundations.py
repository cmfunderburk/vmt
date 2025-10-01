from __future__ import annotations

from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference
from econsim.preferences.leontief import LeontiefPreference
from econsim.preferences.helpers import marginal_utility
from econsim.simulation.agent import Agent
from econsim.simulation.world import Simulation
from econsim.simulation.config import SimConfig
from typing import List
from econsim.preferences.base import Preference


def test_total_inventory_aggregation():
    a = Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
    a.carrying['good1'] = 2
    a.carrying['good2'] = 1
    a.home_inventory['good1'] = 5
    a.home_inventory['good2'] = 0
    total = a.total_inventory()
    assert total == {'good1': 7, 'good2': 1}
    # Ensure original dicts not mutated by reading
    assert a.carrying['good1'] == 2
    assert a.home_inventory['good1'] == 5


def test_marginal_utility_determinism_across_preferences():
    carrying = {'good1': 1, 'good2': 2}
    home = {'good1': 3, 'good2': 0}
    prefs: List[Preference] = [
        CobbDouglasPreference(0.4),
        PerfectSubstitutesPreference(1.0),
        LeontiefPreference(0.5),
    ]
    for pref in prefs:
        first = marginal_utility(pref, carrying, home)
        second = marginal_utility(pref, carrying, home)
        assert first == second  # pure & deterministic
        # Keys sorted lexicographically
        assert list(first.keys()) == sorted(first.keys())


def test_metrics_placeholders_do_not_affect_hash():
    # Build a tiny simulation and step once; counters untouched
    cfg = SimConfig(
        grid_size=(4,4),
        initial_resources=[],
        perception_radius=4,
        respawn_target_density=0.0,
        respawn_rate=0.0,
        max_spawn_per_tick=0,
        seed=1,
        enable_respawn=False,
        enable_metrics=True,
    )
    sim = Simulation.from_config(cfg, agent_positions=[(0,0)])
    # Step with external RNG
    import random as _r
    ext_rng = _r.Random(123)
    sim.step(ext_rng)
    assert sim.metrics_collector is not None
    h_before = sim.metrics_collector.determinism_hash()
    # Modify counters manually (simulating future usage); hash must not change retroactively
    sim.metrics_collector.trade_intents_generated += 5  # type: ignore[attr-defined]
    sim.metrics_collector.trades_executed += 1  # type: ignore[attr-defined]
    h_after = sim.metrics_collector.determinism_hash()
    assert h_before == h_after
