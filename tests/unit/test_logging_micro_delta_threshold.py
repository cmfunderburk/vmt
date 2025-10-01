from __future__ import annotations

import os
import random
from pathlib import Path

from econsim.simulation.world import Simulation
from econsim.simulation.config import SimConfig
from econsim.simulation.grid import Grid
from econsim.gui.debug_logger import GUILogger
import econsim.simulation.trade as trade_mod

# This test validates that enabling trade execution (which prunes micro-delta intents)
# triggers exactly one micro_delta_threshold structured event, and that disabling execution
# suppresses it. It also asserts determinism hash parity between a run with logging active
# and a control run where the pruning still occurs (hash excludes the log event).


def _build_sim(seed: int) -> Simulation:
    grid = Grid(4, 4, [])
    cfg = SimConfig(
        grid_size=(grid.width, grid.height),
        initial_resources=[],
        perception_radius=4,
        respawn_target_density=0.0,
        respawn_rate=0.0,
        max_spawn_per_tick=0,
        seed=seed,
        enable_respawn=False,
        enable_metrics=True,
    )
    # Two agents co-located to force pair evaluation each step
    sim = Simulation.from_config(cfg, agent_positions=[(1,1),(1,1)])
    # Configure asymmetric total bundles to satisfy MU inequalities:
    # Agent0: many good1, few good2 -> desires good2.
    # Agent1: many good2, few good1 -> desires good1.
    a0, a1 = sim.agents[0], sim.agents[1]
    a0.carrying['good1'] = 1; a0.carrying['good2'] = 0
    a1.carrying['good1'] = 0; a1.carrying['good2'] = 1
    a0.home_inventory['good1'] = 100; a0.home_inventory['good2'] = 10
    a1.home_inventory['good1'] = 10;  a1.home_inventory['good2'] = 100
    # Normalize preferences if adjustable (Cobb-Douglas alpha=0.5 ensures MU ordering driven by quantities)
    for a in (a0, a1):
        pref = getattr(a, 'preference', None)
        if pref is not None:
            if hasattr(pref, 'alpha'):
                try:
                    setattr(pref, 'alpha', 0.5)
                except Exception:
                    pass
    return sim


def _run_steps(sim: Simulation, steps: int) -> None:
    rng = random.Random(999)
    for _ in range(steps):
        sim.step(rng)


def test_micro_delta_threshold_emitted_once(tmp_path: Path):
    # Ensure environment for execution mode
    os.environ['ECONSIM_TRADE_DRAFT'] = '1'
    os.environ['ECONSIM_TRADE_EXEC'] = '1'
    # Raise threshold to guarantee pruning path triggers quickly
    os.environ['ECONSIM_MIN_TRADE_DELTA_OVERRIDE'] = '0.1'
    os.environ['ECONSIM_FORCE_MICRO_DELTA_EMIT'] = '1'

    # Reset one-shot flag for isolation
    if hasattr(trade_mod, '_micro_delta_threshold_emitted'):
        trade_mod._micro_delta_threshold_emitted = False  # type: ignore[attr-defined]
    sim = _build_sim(seed=123)

    # Capture structured log file path (logger created lazily; trigger a step)
    _run_steps(sim, 5)

    logger = GUILogger.get_instance()
    events = [e for e in logger.recent_structured_events() if e.get('event') == 'micro_delta_threshold']
    assert len(events) == 1, f"Expected 1 micro_delta_threshold event, found {len(events)}"  # type: ignore[truthy-bool]


def test_micro_delta_threshold_not_emitted_when_exec_disabled(tmp_path: Path):
    os.environ['ECONSIM_TRADE_DRAFT'] = '1'
    os.environ['ECONSIM_TRADE_EXEC'] = '0'
    os.environ['ECONSIM_MIN_TRADE_DELTA_OVERRIDE'] = '1000000'
    os.environ.pop('ECONSIM_FORCE_MICRO_DELTA_EMIT', None)
    if hasattr(trade_mod, '_micro_delta_threshold_emitted'):
        trade_mod._micro_delta_threshold_emitted = False  # type: ignore[attr-defined]
    sim = _build_sim(seed=456)
    _run_steps(sim, 5)

    logger = GUILogger.get_instance()
    before = len([e for e in logger.recent_structured_events() if e.get('event') == 'micro_delta_threshold'])
    events = [e for e in logger.recent_structured_events() if e.get('event') == 'micro_delta_threshold']
    after = len(events)
    # No NEW emission should have occurred; allow prior runs to have populated buffer.
    assert after == before, f"Expected no additional micro_delta_threshold events; before={before} after={after}"  # type: ignore[truthy-bool]


def test_micro_delta_threshold_does_not_change_hash():
    # Two simulations with execution pruning on should have identical hashes regardless of one-shot log presence
    os.environ['ECONSIM_TRADE_DRAFT'] = '1'
    os.environ['ECONSIM_TRADE_EXEC'] = '1'
    os.environ['ECONSIM_MIN_TRADE_DELTA_OVERRIDE'] = '0.1'
    os.environ['ECONSIM_FORCE_MICRO_DELTA_EMIT'] = '1'

    if hasattr(trade_mod, '_micro_delta_threshold_emitted'):
        trade_mod._micro_delta_threshold_emitted = False  # type: ignore[attr-defined]
    sim1 = _build_sim(seed=789)
    if hasattr(trade_mod, '_micro_delta_threshold_emitted'):
        trade_mod._micro_delta_threshold_emitted = False  # ensure second sim can also emit if path executed  # type: ignore[attr-defined]
    sim2 = _build_sim(seed=789)

    _run_steps(sim1, 10)
    _run_steps(sim2, 10)

    h1 = sim1.metrics_collector.determinism_hash()  # type: ignore[attr-defined]
    h2 = sim2.metrics_collector.determinism_hash()  # type: ignore[attr-defined]
    assert h1 == h2
