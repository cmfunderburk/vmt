import os

from econsim.gui.session_factory import SessionFactory, SimulationSessionDescriptor
from econsim.gui.simulation_controller import SimulationController


def test_start_paused_descriptor_controller_paused():
    os.environ["ECONSIM_NEW_GUI"] = "1"
    desc = SimulationSessionDescriptor(
        name="test",
        mode="continuous",
        seed=7,
        grid_size=(8, 8),
        agents=2,
        density=0.1,
        enable_respawn=False,
        enable_metrics=False,
        preference_type="cobb_douglas",
        turn_auto_interval_ms=None,
        start_paused=True,
    )
    controller = SessionFactory.build(desc)
    assert isinstance(controller, SimulationController)
    assert controller.is_paused(), "Controller should start paused when descriptor.start_paused=True"
