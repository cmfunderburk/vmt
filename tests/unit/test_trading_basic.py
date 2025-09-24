import random

from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
from econsim.preferences.cobb_douglas import CobbDouglasPreference


from typing import Tuple


def _build_sim(enable_trading: bool, a_inv: Tuple[int, int] = (1, 0), b_inv: Tuple[int, int] = (0, 1)):
    cfg = SimConfig(
        grid_size=(4,4),
        initial_resources=[],
        seed=42,
        enable_respawn=False,
        enable_metrics=True,
        enable_trading=enable_trading,
    )
    def pf(i: int):
        return CobbDouglasPreference(alpha=0.5)
    sim = Simulation.from_config(cfg, preference_factory=pf, agent_positions=[(1,1),(1,1)])
    # seed inventories into carrying
    sim.agents[0].carrying['good1'] = a_inv[0]
    sim.agents[0].carrying['good2'] = a_inv[1]
    sim.agents[1].carrying['good1'] = b_inv[0]
    sim.agents[1].carrying['good2'] = b_inv[1]
    return sim


def test_trading_basic_exchange():
    sim = _build_sim(True, a_inv=(1,0), b_inv=(0,1))
    rng = random.Random(7)
    sim.step(rng, use_decision=False)  # movement path (legacy) -> co-location remains
    # After one step they should have swapped if marginal utilities opposed (they are for symmetric CD with different holdings)
    a = sim.agents[0].carrying
    b = sim.agents[1].carrying
    assert a['good1'] == 0 and a['good2'] == 1
    assert b['good1'] == 1 and b['good2'] == 0


def test_trading_no_exchange_conditions():
    sim = _build_sim(True, a_inv=(1,0), b_inv=(1,0))
    rng = random.Random(7)
    sim.step(rng, use_decision=False)
    a = sim.agents[0].carrying
    b = sim.agents[1].carrying
    # No complementary holdings; no trade
    assert a['good1'] == 1 and a['good2'] == 0
    assert b['good1'] == 1 and b['good2'] == 0


def test_trading_hash_inert_when_disabled():
    sim_disabled = _build_sim(False, a_inv=(1,0), b_inv=(0,1))
    sim_enabled = _build_sim(True, a_inv=(1,0), b_inv=(0,1))
    rng1 = random.Random(7)
    rng2 = random.Random(7)
    sim_disabled.step(rng1, use_decision=False)
    sim_enabled.step(rng2, use_decision=False)
    # With trading disabled, inventories remain original; with trading enabled they swapped
    a_dis = sim_disabled.agents[0].carrying
    a_en = sim_enabled.agents[0].carrying
    assert a_dis['good1'] == 1 and a_dis['good2'] == 0
    assert a_en['good1'] == 0 and a_en['good2'] == 1


def test_trading_goods_conservation():
    sim = _build_sim(True, a_inv=(2,0), b_inv=(0,3))
    rng = random.Random(5)
    before_g1 = sum(a.carrying.get('good1',0) for a in sim.agents)
    before_g2 = sum(a.carrying.get('good2',0) for a in sim.agents)
    sim.step(rng, use_decision=False)
    after_g1 = sum(a.carrying.get('good1',0) for a in sim.agents)
    after_g2 = sum(a.carrying.get('good2',0) for a in sim.agents)
    assert before_g1 == after_g1
    assert before_g2 == after_g2
