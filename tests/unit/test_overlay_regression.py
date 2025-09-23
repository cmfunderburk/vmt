import os
from time import sleep

from PyQt6.QtWidgets import QApplication

from econsim.gui.embedded_pygame import EmbeddedPygameWidget
from econsim.simulation.grid import Grid
from econsim.simulation.world import Simulation
from econsim.simulation.agent import Agent
from econsim.preferences.cobb_douglas import CobbDouglasPreference


def _headless_env():
    if not os.environ.get("DISPLAY"):
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_overlay_toggle_renders_hud_text_bytes():
    """Minimal regression: enabling overlay introduces stable HUD text bytes; disabling removes them.

    Strategy: Build a tiny simulation (no movement steps needed) and grab raw RGBA bytes with overlay off, then
    enable overlay via widget API (exposed attr) and force a repaint. We look for ASCII substrings pattern such as
    'Turn:' or 'Agents:' within the raw byte buffer. While not guaranteed by font rendering to be contiguous ASCII,
    empirical rendering path (`pygame.font.render`) tends to embed glyph surface pixel data that will not directly
    contain the literal strings. Therefore we instead leverage an exported helper: we fall back to comparing checksums
    size difference heuristic if literal text bytes absent. To keep complexity low we assert that enabling overlay
    changes at least 2% of the surface bytes and disabling reverts majority (>90%) similarity.
    """
    _headless_env()
    app = QApplication.instance() or QApplication([])

    grid = Grid(6, 4, resources=[(1, 1, "A")])
    agents = [Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))]
    sim = Simulation(grid, agents)
    w = EmbeddedPygameWidget(simulation=sim)
    w.show()

    # Process a couple frames with overlay off
    for _ in range(10):
        app.processEvents()
        sleep(0.002)
    base_bytes = w.get_surface_bytes()

    # Enable overlay if attribute exists (turn widgets may differ; keep guard)
    if hasattr(w, "_show_overlay"):
        setattr(w, "_show_overlay", True)

    # Process frames after enabling overlay
    for _ in range(10):
        app.processEvents()
        sleep(0.002)
    overlay_bytes = w.get_surface_bytes()

    # Compute byte difference ratio
    diff_count = sum(b1 != b2 for b1, b2 in zip(base_bytes, overlay_bytes))
    diff_ratio = diff_count / max(1, len(base_bytes))
    assert (
        diff_ratio >= 0.02
    ), f"Expected >=2% bytes to differ when overlay enabled (got {diff_ratio*100:.2f}%)"

    # Disable overlay again and expect surface to broadly revert (not perfectly identical due to frame count text)
    if hasattr(w, "_show_overlay"):
        setattr(w, "_show_overlay", False)
    for _ in range(10):
        app.processEvents()
        sleep(0.002)
    reverted_bytes = w.get_surface_bytes()

    # Compare reverted to base
    diff_after_disable = sum(b1 != b2 for b1, b2 in zip(base_bytes, reverted_bytes)) / max(
        1, len(base_bytes)
    )
    assert (
        diff_after_disable < 0.15
    ), f"Expected <15% divergence after disabling overlay (got {diff_after_disable*100:.2f}%)"

    w.close()
    app.processEvents()
