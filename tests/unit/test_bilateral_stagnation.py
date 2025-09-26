import os
import random

from econsim.simulation.world import Simulation
from econsim.simulation.config import SimConfig
from econsim.simulation.agent import Agent, AgentMode
from econsim.preferences.cobb_douglas import CobbDouglasPreference


def build_sim(two_agents=True):
    # Minimal grid with no resources (forage disabled path only)
    cfg = SimConfig(
        grid_size=(5,5),
        initial_resources=[],
        perception_radius=8,
        respawn_target_density=0.0,
        respawn_rate=0.0,
        max_spawn_per_tick=0,
        seed=42,
        enable_respawn=False,
        enable_metrics=False,
        viewport_size=320,
    )
    if two_agents:
        agents = [
            Agent(id=0, x=2, y=2, preference=CobbDouglasPreference(alpha=0.5)),
            Agent(id=1, x=2, y=2, preference=CobbDouglasPreference(alpha=0.5)),
        ]
    else:
        agents = [Agent(id=0, x=2, y=2, preference=CobbDouglasPreference(alpha=0.5))]
    sim = Simulation(grid=None, agents=[], config=None)  # type: ignore[arg-type]
    # Use factory for consistent wiring
    sim = Simulation.from_config(cfg, preference_factory=lambda i: CobbDouglasPreference(alpha=0.5), agent_positions=[(2,2),(2,2)] if two_agents else [(2,2)])
    return sim


def test_stagnation_forces_return_home_and_deposit(monkeypatch):
    os.environ['ECONSIM_FORAGE_ENABLED'] = '0'
    os.environ['ECONSIM_TRADE_DRAFT'] = '1'
    os.environ['ECONSIM_TRADE_EXEC'] = '1'

    sim = build_sim(two_agents=True)

    # Seed inventories so that only one meaningful trade occurs then deltas fall below MIN_TRADE_DELTA
    a0, a1 = sim.agents
    a0.carrying['good1'] = 3
    a0.carrying['good2'] = 1
    a1.carrying['good1'] = 1
    a1.carrying['good2'] = 3

    # External RNG (unused for decision path but required by API)
    ext_rng = random.Random(7)

    # Run until no intents produced (filtered) and stagnation triggers forced return
    forced_triggered = False
    max_steps = 400
    for _ in range(max_steps):
        sim.step(ext_rng, use_decision=True)
        a0_mode = a0.mode
        a1_mode = a1.mode
        # Detect forced return: agent flagged RETURN_HOME with force_deposit_once
        if (getattr(a0, 'force_deposit_once', False) or getattr(a1, 'force_deposit_once', False)) and (a0_mode == AgentMode.RETURN_HOME or a1_mode == AgentMode.RETURN_HOME):
            forced_triggered = True
            break
    assert forced_triggered, 'Expected stagnation to trigger a forced return-home sequence'

    # Capture pre-home inventory totals for later comparison
    pre_home_totals = [sum(a.home_inventory.values()) for a in (a0, a1)]

    # Advance until deposit clears force_deposit_once (should become IDLE with inventories banked)
    for _ in range(50):
        sim.step(ext_rng, use_decision=True)
        if not getattr(a0, 'force_deposit_once', False) and not getattr(a1, 'force_deposit_once', False):
            break

    # After forced deposit, agents should not be stuck in perpetual trade (either no intents or minimal churn)
    intents_post = sim.trade_intents or []
    assert len(intents_post) == 0 or all(getattr(t, 'delta_utility', 0.0) > 0 for t in intents_post)

    # Home inventories should have increased for at least one agent after deposit
    post_home_totals = [sum(a.home_inventory.values()) for a in (a0, a1)]
    assert any(post_home_totals[i] > pre_home_totals[i] for i in range(2)), 'Expected at least one agent to deposit goods'

    # Clean env
    os.environ.pop('ECONSIM_TRADE_DRAFT', None)
    os.environ.pop('ECONSIM_TRADE_EXEC', None)
    os.environ.pop('ECONSIM_FORAGE_ENABLED', None)
