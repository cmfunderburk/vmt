import os

from econsim.gui.panels.metrics_panel import MetricsPanel
from econsim.gui.simulation_controller import SimulationController
from econsim.gui.session_factory import SimulationSessionDescriptor, SessionFactory
from PyQt6.QtWidgets import QApplication


def _controller():
    desc = SimulationSessionDescriptor(
        name="mtest",
        mode="turn",
        seed=42,
        grid_size=(4,4),
        agents=1,
        density=0.1,
        enable_respawn=False,
        enable_metrics=False,
        preference_type="cobb_douglas",
        turn_auto_interval_ms=None,
    )
    return SessionFactory.build(desc)


def test_metrics_panel_manual_update_labels():
    os.environ["ECONSIM_NEW_GUI"] = "1"
    app = QApplication.instance() or QApplication([])
    ctrl = _controller()
    panel = MetricsPanel(ctrl)
    # initial
    panel._update_values()
    t0 = panel.ticks_lbl.text()
    # advance steps manually
    ctrl.manual_step()
    panel._update_values()
    t1 = panel.ticks_lbl.text()
    assert t0 != t1
