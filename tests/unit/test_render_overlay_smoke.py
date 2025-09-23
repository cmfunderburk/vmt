import os
import random
from time import sleep

from PyQt6.QtWidgets import QApplication

from econsim.gui.embedded_pygame import EmbeddedPygameWidget
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.agent import Agent
from econsim.simulation.grid import Grid
from econsim.simulation.world import Simulation


def test_render_overlay_shows_variation():
    # Headless guards
    if not os.environ.get("DISPLAY"):
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    # Build a small simulation with decision mode off (widget currently calls legacy path)
    grid = Grid(8, 6, resources=[(1, 1, "A"), (3, 2, "B"), (5, 4, "A")])
    agents = [
        Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5)),
        Agent(id=2, x=7, y=5, preference=CobbDouglasPreference(alpha=0.5)),
    ]
    sim = Simulation(grid, agents)
    w = EmbeddedPygameWidget(simulation=sim)
    w.show()

    # Run a few frames (legacy random movement still moves agents; overlay should draw)
    rng = random.Random(0)
    # Manually step simulation a few times to diversify positions/resources consumed
    for _ in range(10):
        sim.step(rng, use_decision=False)
    # Process GUI frames
    for _ in range(60):
        app.processEvents()
        sleep(0.002)
        if getattr(w, "_frame", 0) >= 2:
            break
    # Capture raw pixel data twice to check difference (animation + overlay variability)
    raw1 = w.get_surface_bytes()
    # Advance more frames
    for _ in range(30):
        app.processEvents()
        sleep(0.002)
    raw2 = w.get_surface_bytes()
    # Basic pixel variance check
    assert (
        raw1 != raw2
    ), "Surface bytes should change across frames indicating overlay + animation rendering"
    w.close()
    app.processEvents()
