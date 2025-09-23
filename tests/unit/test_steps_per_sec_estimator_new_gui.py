import os, time
from econsim.gui.session_factory import SessionFactory, SimulationSessionDescriptor


def _controller():
    desc = SimulationSessionDescriptor(
        name="sps",
        mode="continuous",
        seed=11,
        grid_size=(4,4),
        agents=1,
        density=0.1,
        enable_respawn=False,
        enable_metrics=False,
        preference_type="cobb_douglas",
        turn_auto_interval_ms=None,
    )
    return SessionFactory.build(desc)


def test_steps_per_second_estimator_progress():
    os.environ['ECONSIM_NEW_GUI'] = '1'
    ctrl = _controller()
    # Manually step a few times spaced out to create timestamps
    for _ in range(3):
        ctrl.manual_step()
        time.sleep(0.01)
    val = ctrl.steps_per_second_estimate()
    assert val > 0
