import os
import copy

from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
from econsim.preferences.cobb_douglas import CobbDouglasPreference


def build_sim(agent_positions, resources=(), k=0.0):
    cfg = SimConfig(
        grid_size=(8, 8),
        initial_resources=list(resources),
        perception_radius=8,
        seed=42,
        enable_respawn=False,
        enable_metrics=False,
        viewport_size=320,
        distance_scaling_factor=k,
    )
    # Provide preference factory to ensure deterministic identical preferences
    pref_factory = lambda i: CobbDouglasPreference(alpha=0.5)
    sim = Simulation.from_config(cfg, preference_factory=pref_factory, agent_positions=agent_positions)
    return sim


def _clone_sim(sim: Simulation) -> Simulation:
    # Shallow reserialize minimal state for determinism check (agents positions & inventories)
    cfg = sim.config
    new = Simulation.from_config(cfg, preference_factory=lambda i: sim.agents[i].preference, agent_positions=[(a.x, a.y) for a in sim.agents])
    # Copy inventories (carrying + home)
    for src, dst in zip(sim.agents, new.agents):
        dst.carrying.update(src.carrying)
        dst.home_inventory.update(src.home_inventory)
    return new


def test_unified_resource_selection_k0(monkeypatch):
    """Agent should select and collect nearest lexicographically winning resource under k=0 unified mode."""
    monkeypatch.setenv("ECONSIM_FORAGE_ENABLED", "1")
    monkeypatch.delenv("ECONSIM_TRADE_EXEC", raising=False)
    monkeypatch.delenv("ECONSIM_TRADE_DRAFT", raising=False)
    monkeypatch.setenv("ECONSIM_UNIFIED_SELECTION_ENABLE", "1")  # force unified path
    # Two resources: (1,0,'A') and (2,0,'B') – both equal base utility; tie by (-ΔU,dist,x,y) becomes (1,0)
    sim = build_sim(agent_positions=[(0, 0)], resources=[(1, 0, 'A'), (2, 0, 'B')], k=0.0)
    import random
    ext_rng = random.Random(123)
    sim.step(ext_rng)
    a = sim.agents[0]
    # After one step agent should have collected resource at (1,0)
    assert a.carrying.get('good1', 0) == 1, f"Expected collection of good1, carrying={a.carrying}"
    assert a.carrying.get('good2', 0) == 0


def test_unified_partner_pairing(monkeypatch):
    """Two agents with complementary inventories should pair under unified selection when trade enabled."""
    monkeypatch.setenv("ECONSIM_FORAGE_ENABLED", "1")
    monkeypatch.setenv("ECONSIM_TRADE_EXEC", "1")  # triggers unified without explicit enable
    monkeypatch.setenv("ECONSIM_UNIFIED_SELECTION_DISABLE", "0")
    sim = build_sim(agent_positions=[(0, 0), (3, 0)], resources=[], k=0.0)
    # Give each agent 2 units of a different good to create positive joint gain from swapping 1 unit
    # (After a swap both can approach a balanced bundle increasing Cobb-Douglas utility.)
    sim.agents[0].carrying['good1'] = 2
    sim.agents[1].carrying['good2'] = 2
    import random
    ext_rng = random.Random(999)
    sim.step(ext_rng)
    # Advance one more step to allow pairing convergence (first step may just move both toward each other)
    sim.step(ext_rng)
    a0, a1 = sim.agents
    # Accept either: active pairing, in-progress meeting, or completed trade resulting in balanced inventories
    paired = (a0.trade_partner_id == a1.id and a1.trade_partner_id == a0.id)
    converging = (a0.meeting_point is not None) or (a1.meeting_point is not None)
    balanced_swap = (a0.carrying.get('good1',0)==1 and a0.carrying.get('good2',0)==1 \
                     and a1.carrying.get('good1',0)==1 and a1.carrying.get('good2',0)==1)
    assert paired or converging or balanced_swap, (
        f"Expected pairing/meeting or post-trade balanced inventories; a0_partner={a0.trade_partner_id}, "
        f"a1_partner={a1.trade_partner_id}, a0_inv={a0.carrying}, a1_inv={a1.carrying}"
    )


def test_spatial_index_unified_determinism(monkeypatch):
    """Running one unified selection step from identical cloned states yields identical post-step agent snapshots."""
    monkeypatch.setenv("ECONSIM_FORAGE_ENABLED", "1")
    monkeypatch.setenv("ECONSIM_UNIFIED_SELECTION_ENABLE", "1")
    monkeypatch.delenv("ECONSIM_TRADE_EXEC", raising=False)
    sim = build_sim(agent_positions=[(0,0), (5,5), (2,1)], resources=[(1,0,'A'), (4,5,'B')], k=0.0)
    clone = _clone_sim(sim)
    import random
    r1 = random.Random(555)
    r2 = random.Random(555)
    sim.step(r1)
    clone.step(r2)
    snapshot1 = [(a.id, a.x, a.y, dict(a.carrying), a.trade_partner_id) for a in sim.agents]
    snapshot2 = [(a.id, a.x, a.y, dict(a.carrying), a.trade_partner_id) for a in clone.agents]
    assert snapshot1 == snapshot2, f"Determinism mismatch: {snapshot1} vs {snapshot2}"
