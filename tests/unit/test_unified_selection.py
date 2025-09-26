import os
import random
import pytest

from econsim.simulation.world import Simulation
from econsim.simulation.grid import Grid
from econsim.simulation.agent import Agent
from econsim.preferences.cobb_douglas import CobbDouglasPreference


def make_world(agent_positions, resources):
    grid = Grid(20, 20, resources)
    agents = [
        Agent(id=i, x=x, y=y, preference=CobbDouglasPreference(alpha=0.5))
        for i, (x, y) in enumerate(agent_positions)
    ]
    return Simulation(grid=grid, agents=agents, config=None)


def test_unified_prefers_partner_when_better(monkeypatch):
    monkeypatch.setenv("ECONSIM_FORAGE_ENABLED", "1")
    monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
    monkeypatch.setenv("ECONSIM_TRADE_EXEC", "0")
    monkeypatch.setenv("ECONSIM_UNIFIED_SELECTION_ENABLE", "1")
    # Two agents close; place a far resource so partner is better
    world = make_world([(5,5), (7,5)], resources=[(15,15,'A')])
    rng = random.Random(0)
    world.step(rng, use_decision=True)
    a0 = world.agents[0]
    assert a0.current_unified_task is not None
    kind, payload = a0.current_unified_task
    assert kind == 'partner', f"Expected partner choice, got {a0.current_unified_task}"


def test_unified_prefers_resource_when_closer(monkeypatch):
    monkeypatch.setenv("ECONSIM_FORAGE_ENABLED", "1")
    monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
    monkeypatch.setenv("ECONSIM_TRADE_EXEC", "0")
    monkeypatch.setenv("ECONSIM_UNIFIED_SELECTION_ENABLE", "1")
    # Resource adjacent, partner farther -> resource chosen
    world = make_world([(5,5), (12,12)], resources=[(6,5,'A')])
    rng = random.Random(0)
    world.step(rng, use_decision=True)
    a0 = world.agents[0]
    assert a0.current_unified_task is not None
    kind, payload = a0.current_unified_task
    assert kind == 'resource', f"Expected resource choice, got {a0.current_unified_task}"


def test_unified_reservation(monkeypatch):
    monkeypatch.setenv("ECONSIM_FORAGE_ENABLED", "1")
    monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
    monkeypatch.setenv("ECONSIM_TRADE_EXEC", "0")
    monkeypatch.setenv("ECONSIM_UNIFIED_SELECTION_ENABLE", "1")
    # Three agents, only one nearby partner scenario; ensure not all pick same partner
    # Place a distant resource still within bounds so partner selection dominates
    world = make_world([(5,5),(7,5),(19,19)], resources=[(19,19,'A')])
    rng = random.Random(0)
    world.step(rng, use_decision=True)
    decisions = [a.current_unified_task for a in world.agents[:2]]
    # Both near each other; first should pick partner, second should fall back (None or partner with different id not possible)
    assert decisions[0] is not None
    # Second either None or resource (since partner reserved). It must not pick same partner id as first.
    first = decisions[0]
    second = decisions[1]
    if second is not None and second[0] == 'partner':
        assert second[1] != first[1], "Reservation failed: both paired to same partner"

