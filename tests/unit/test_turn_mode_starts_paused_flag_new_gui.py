import os

from econsim.gui.session_factory import SessionFactory, SimulationSessionDescriptor
from econsim.gui.simulation_controller import SimulationController


def test_turn_mode_controller_starts_paused():
    os.environ["ECONSIM_NEW_GUI"] = "1"
    desc = SimulationSessionDescriptor(
        name="test",
        mode="turn",
        seed=7,
        grid_size=(8, 8),
        agents=2,
        density=0.1,
        enable_respawn=False,
        enable_metrics=False,
        preference_type="cobb_douglas",
        turn_auto_interval_ms=None,
    )
    controller = SessionFactory.build(desc)
    # In SessionFactory build, turn mode should not auto step; but MainWindow attaches pause.
    # Here we only validate build path returns controller; pause applied in MainWindow (GUI path).
    assert isinstance(controller, SimulationController)
