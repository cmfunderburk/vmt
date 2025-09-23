import os
from econsim.gui.embedded_pygame import EmbeddedPygameWidget
from econsim.gui.session_factory import SessionFactory, SimulationSessionDescriptor
from PyQt6.QtWidgets import QApplication


def _controller():
    desc = SimulationSessionDescriptor(
        name='obase',
        mode='continuous',
        seed=7,
        grid_size=(4,4),
        agents=1,
        density=0.1,
        enable_respawn=False,
        enable_metrics=False,
        preference_type='cobb_douglas',
        turn_auto_interval_ms=None,
    )
    return SessionFactory.build(desc)


def test_overlay_off_static_background_stable():
    os.environ['ECONSIM_NEW_GUI'] = '1'
    app = QApplication.instance() or QApplication([])
    ctrl = _controller()
    w = EmbeddedPygameWidget(simulation=ctrl.simulation)
    w.static_background = True
    # Pause controller to prevent simulation state changes between frames
    ctrl.pause()
    # Simulate two ticks without overlays; sample first pixel RGBA
    w._on_tick()
    b1 = w.get_surface_bytes()
    w._on_tick()
    b2 = w.get_surface_bytes()
    # Each pixel = 4 bytes RGBA; compare first pixel
    assert b1[:4] == b2[:4]
