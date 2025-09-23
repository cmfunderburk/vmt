import os
from econsim.gui.panels.metrics_panel import MetricsPanel
from econsim.gui.session_factory import SimulationSessionDescriptor, SessionFactory
from PyQt6.QtWidgets import QApplication


def _controller():
    desc = SimulationSessionDescriptor(
        name='mclamp',
        mode='continuous',
        seed=5,
        grid_size=(4,4),
        agents=1,
        density=0.1,
        enable_respawn=False,
        enable_metrics=False,
        preference_type='cobb_douglas',
        turn_auto_interval_ms=None,
    )
    return SessionFactory.build(desc)


def test_metrics_interval_clamped():
    os.environ['ECONSIM_NEW_GUI'] = '1'
    os.environ['ECONSIM_METRICS_AUTO'] = '1'
    os.environ['ECONSIM_METRICS_AUTO_INTERVAL_MS'] = '50'
    app = QApplication.instance() or QApplication([])
    panel = MetricsPanel(_controller())
    assert panel._auto_interval_ms == 250
