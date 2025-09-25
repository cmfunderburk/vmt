from __future__ import annotations

import random

import pygame

from econsim.simulation.world import Simulation
from econsim.simulation.config import SimConfig
from econsim.simulation.agent import Agent
from econsim.gui._trade_debug_overlay import render_trade_debug, MAX_LINES


from typing import List, Tuple


def _build_sim(agent_positions: List[Tuple[int, int]]):
    cfg = SimConfig(
        grid_size=(6,6),
        initial_resources=[],
        perception_radius=6,
        respawn_target_density=0.0,
        respawn_rate=0.0,
        max_spawn_per_tick=0,
        seed=19,
        enable_respawn=False,
        enable_metrics=False,
    )
    return Simulation.from_config(cfg, agent_positions=agent_positions)


def test_overlay_renders_with_intents(monkeypatch) -> None:  # type: ignore[missing-annotations]
    monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
    sim = _build_sim([(0,0),(0,0),(0,0),(0,0)])
    # Ensure complementary goods to yield intents
    sim.agents[0].carrying['good1'] = 1
    sim.agents[1].carrying['good2'] = 1
    sim.agents[2].carrying['good1'] = 1
    sim.agents[3].carrying['good2'] = 1
    # Prevent movement
    monkeypatch.setattr(Agent, 'move_random', lambda self, grid, rng: None)
    rng = random.Random(2)
    sim.step(rng, use_decision=False)
    assert sim.trade_intents is not None and len(sim.trade_intents) > 0
    # Minimal pygame surface/font setup (off-screen)
    pygame.init()
    try:
        surface = pygame.Surface((200, 120))
        font = pygame.font.Font(None, 14)
        # Call overlay; should not raise
        render_trade_debug(surface, font, sim)
        # We can't easily assert pixel text presence without diff harness, but at least ensure bounded lines
    # Bounded by MAX_LINES (implicit via slicing inside overlay)
        # As a loose smoke check, re-call (idempotency) should not mutate intents or crash
        before_ids = [id(t) for t in sim.trade_intents]
        render_trade_debug(surface, font, sim)
        after_ids = [id(t) for t in sim.trade_intents]
        assert before_ids == after_ids
    finally:
        pygame.quit()


def test_overlay_noop_without_flag(monkeypatch) -> None:  # type: ignore[missing-annotations]
    monkeypatch.delenv("ECONSIM_TRADE_DRAFT", raising=False)
    sim = _build_sim([(0,0),(0,0)])
    sim.agents[0].carrying['good1'] = 1
    sim.agents[1].carrying['good2'] = 1
    monkeypatch.setattr(Agent, 'move_random', lambda self, grid, rng: None)
    rng = random.Random(4)
    sim.step(rng, use_decision=False)
    # Intents enumerated only when flag set; thus trade_intents should be empty or None
    assert not sim.trade_intents
    pygame.init()
    try:
        surface = pygame.Surface((200, 60))
        font = pygame.font.Font(None, 14)
        render_trade_debug(surface, font, sim)  # should be a noop
    finally:
        pygame.quit()
