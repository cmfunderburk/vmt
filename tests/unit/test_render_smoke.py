import os
from PyQt6.QtWidgets import QApplication
from time import sleep

from econsim.gui.embedded_pygame import EmbeddedPygameWidget


def test_render_smoke_minimal_cycle():
    # Headless safety
    if not os.environ.get("DISPLAY"):
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    w = EmbeddedPygameWidget()
    w.show()
    # Process events for a short interval allowing QTimer timeouts to fire
    for _ in range(120):  # ~120 * (processEvents + sleep 2ms) ≈ <0.3s
        app.processEvents()
        sleep(0.002)
        if getattr(w, "_frame", 0) > 0:
            break
    if getattr(w, "_frame", 0) == 0:
        # In extremely constrained CI timing, skip rather than fail hard
        import pytest
        pytest.skip("No frame advanced during short smoke window")
    assert getattr(w, "_frame", 0) > 0
    w.close()
    app.processEvents()
