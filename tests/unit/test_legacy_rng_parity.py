"""RNG parity between auto-stepping widget and controller manual stepping.

Ensures that when both paths use the same decision-based movement system and
the RNGs are seeded from the same simulation config seed, trajectories match.
"""
from __future__ import annotations

import os
from PyQt6.QtWidgets import QApplication

from econsim.simulation.world import Simulation
from econsim.simulation.config import SimConfig
from econsim.preferences.cobb_douglas import CobbDouglasPreference


def _build_pair(seed: int = 314159):
    # Minimal grid with no resources so decision mode would idle; legacy random will still move.
    cfg = SimConfig(grid_size=(6, 6), initial_resources=[], seed=seed, enable_respawn=False, enable_metrics=False)
    # Two identical sims with a single agent at (0,0)
    sim1 = Simulation.from_config(cfg, preference_factory=lambda i: CobbDouglasPreference(alpha=0.5), agent_positions=[(0, 0)])
    sim2 = Simulation.from_config(cfg, preference_factory=lambda i: CobbDouglasPreference(alpha=0.5), agent_positions=[(0, 0)])
    return sim1, sim2


def test_legacy_rng_parity_widget_vs_manual():
    # Ensure GUI can init in headless
    if not os.environ.get("DISPLAY"):
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication([])

    from econsim.gui.embedded_pygame import EmbeddedPygameWidget
    from econsim.gui.simulation_controller import SimulationController

    sim_manual, sim_auto = _build_pair()

    # Manual controller steps using its own RNG seeded from config.seed
    ctrl = SimulationController(sim_manual)

    # Auto widget steps using RNG seeded from sim.config.seed; force legacy movement
    w = EmbeddedPygameWidget(simulation=sim_auto)

    # Decision mode is always enabled (legacy mode removed)
    steps = 20
    for _ in range(steps):
        ctrl.manual_step()
        # Ensure widget also advances exactly once
        w._on_tick()  # type: ignore[attr-defined]

    # Compare positions of the single agent
    a1 = sim_manual.agents[0]
    a2 = sim_auto.agents[0]
    assert (a1.x, a1.y) == (a2.x, a2.y), "Legacy RNG parity failed between manual and widget stepping"
    assert sim_manual.steps == sim_auto.steps == steps
