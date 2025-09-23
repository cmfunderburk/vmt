import os
import time
import pytest

from econsim.gui.session_factory import SessionFactory, SimulationSessionDescriptor


def _build_controller():
    desc = SimulationSessionDescriptor(
        name="test",
        mode="turn",  # turn mode implies we will manually step (paused by MainWindow; here just manual)
        seed=123,
        grid_size=(8, 8),
        agents=2,
        density=0.2,
        enable_respawn=False,
        enable_metrics=True,
        preference_type="cobb_douglas",
        turn_auto_interval_ms=None,
    )
    return SessionFactory.build(desc)


def test_manual_step_increments_ticks_and_hash_cache_invalidated():
    os.environ["ECONSIM_NEW_GUI"] = "1"
    controller = _build_controller()
    start_ticks = controller.ticks()
    h1 = controller.refresh_hash()
    controller.manual_step()
    assert controller.ticks() == start_ticks + 1
    # hash cache should be invalidated (determinism_hash should differ after refresh)
    h2 = controller.refresh_hash()
    assert h1 != h2 or h1 == "(metrics disabled)"


def test_manual_step_count():
    os.environ["ECONSIM_NEW_GUI"] = "1"
    controller = _build_controller()
    start_ticks = controller.ticks()
    controller.manual_step(count=5)
    assert controller.ticks() == start_ticks + 5


def test_hash_cache_stable_until_refresh():
    os.environ["ECONSIM_NEW_GUI"] = "1"
    controller = _build_controller()
    h1 = controller.refresh_hash()
    # Without new steps determinism_hash() should return cached
    h2 = controller.determinism_hash()
    assert h1 == h2
    # After a manual step cache invalidated
    controller.manual_step()
    h3 = controller.refresh_hash()
    if h1 != "(metrics disabled)":
        assert h3 != h1

