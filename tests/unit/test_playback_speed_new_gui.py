import os, time
import pytest

from econsim.gui.session_factory import SessionFactory, SimulationSessionDescriptor


def _build_controller(mode="turn"):
    desc = SimulationSessionDescriptor(
        name="playback",
        mode=mode,
        seed=42,
        grid_size=(6, 6),
        agents=1,
        density=0.2,
        enable_respawn=False,
        enable_metrics=True,
        preference_type="cobb_douglas",
        turn_auto_interval_ms=None,
    )
    return SessionFactory.build(desc)


def test_playback_speed_throttles_steps():
    os.environ["ECONSIM_NEW_GUI"] = "1"
    controller = _build_controller()
    # Start unpaused to allow auto-stepping
    controller.resume()
    controller.set_playback_tps(1.0)
    start = time.perf_counter()
    # Simulate widget tick loop calling _should_step_now; we mimic only scheduling logic.
    # We'll call the internal scheduling helper just like the widget does.
    stepped = 0
    # Run a tight loop for ~1.2s wall time to accumulate steps.
    while time.perf_counter() - start < 1.2:
        now = time.perf_counter()
        if controller._should_step_now(now):  # type: ignore[attr-defined]
            # emulate a single auto step
            import random
            rng = random.Random(999)
            controller.simulation.step(rng)
            controller._record_step_timestamp()  # type: ignore[attr-defined]
            stepped += 1
    # Expect roughly 1 step (allowing small jitter) but not more than 2.
    assert 0 < stepped <= 2

    # Increase speed to 2 tps and measure again.
    controller.set_playback_tps(2.0)
    stepped2 = 0
    start2 = time.perf_counter()
    while time.perf_counter() - start2 < 1.2:
        now = time.perf_counter()
        if controller._should_step_now(now):  # type: ignore[attr-defined]
            import random
            rng = random.Random(999)
            controller.simulation.step(rng)
            controller._record_step_timestamp()  # type: ignore[attr-defined]
            stepped2 += 1
    # At 2 tps over ~1.2s expect between 2 and 3 steps
    assert 1 < stepped2 <= 3
    # And more than at 1 tps
    assert stepped2 >= stepped
