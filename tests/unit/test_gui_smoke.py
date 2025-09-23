"""Smoke test for new GUI scaffolding (headless friendly).

Skips if ECONSIM_NEW_GUI not enabled to avoid affecting legacy pipeline.
"""
from __future__ import annotations

import os
import pytest


@pytest.mark.skipif(os.environ.get("ECONSIM_NEW_GUI") != "1", reason="New GUI not enabled")
def test_session_factory_headless_import():
    # Basic import + descriptor build path
    from econsim.gui.session_factory import SimulationSessionDescriptor, SessionFactory
    desc = SimulationSessionDescriptor(
        name="baseline_decision",
        mode="continuous",
        seed=123,
        grid_size=(8, 8),
        agents=3,
        density=0.2,
        enable_respawn=True,
        enable_metrics=True,
        preference_type="cobb_douglas",
        turn_auto_interval_ms=None,
    )
    controller = SessionFactory.build(desc)
    assert controller.simulation is not None
    # Manually step a few times to exercise path
    for _ in range(3):
        controller.manual_step()
    # Hash retrieval (may be metrics enabled)
    _ = controller.determinism_hash()