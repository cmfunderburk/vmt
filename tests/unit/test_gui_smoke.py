"""Smoke test for GUI scaffolding (headless friendly)."""
from __future__ import annotations

import os
import pytest


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