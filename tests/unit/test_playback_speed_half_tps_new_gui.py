import os

from econsim.gui.session_factory import SessionFactory, SimulationSessionDescriptor


def _build_controller():
    desc = SimulationSessionDescriptor(
        name="half_tps",
        mode="turn",
        seed=7,
        grid_size=(5, 5),
        agents=1,
        density=0.2,
        enable_respawn=False,
        enable_metrics=True,
        preference_type="cobb_douglas",
        turn_auto_interval_ms=None,
    )
    return SessionFactory.build(desc)


def test_half_tps_schedule_allows_step_every_two_seconds():
    os.environ["ECONSIM_NEW_GUI"] = "1"
    controller = _build_controller()
    controller.resume()
    controller.set_playback_tps(0.5)  # one step every 2s

    # Instead of waiting wall time, we emulate time progression by directly calling the scheduling helper
    # with synthetic timestamps. This isolates logic and avoids flakiness.
    t = 0.0
    stepped = 0
    # First call at t=0 should step.
    if controller._should_step_now(t):  # type: ignore[attr-defined]
        stepped += 1
    # Calls before 2.0s should not trigger additional steps.
    for t in [0.1, 0.5, 1.0, 1.5, 1.9]:
        assert not controller._should_step_now(t)  # type: ignore[attr-defined]
    # At exactly 2.0 (or beyond) next step should occur.
    if controller._should_step_now(2.0):  # type: ignore[attr-defined]
        stepped += 1
    # No new step until >=4.0
    for t in [2.1, 3.0, 3.9]:
        assert not controller._should_step_now(t)  # type: ignore[attr-defined]
    if controller._should_step_now(4.0):  # type: ignore[attr-defined]
        stepped += 1

    # We expect exactly 3 granted steps at t=0,2,4 in this synthetic progression.
    assert stepped == 3
