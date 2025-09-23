"""Embedded Pygame Widget (Gate 1 Stub)

Gate 1 scope: Demonstrate coexistence of PyQt6 event loop with a Pygame
off-screen Surface updated on a QTimer. This avoids native SDL window
embedding complexity while validating frame update + paint path.

Out-of-scope in Gate 1: agents, economics, grid logic, advanced rendering,
logging, threading.
"""

from __future__ import annotations

from time import perf_counter
from typing import Protocol
import random  # for simulation RNG typing

import pygame
from PyQt6.QtCore import QRect, QTimer
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QWidget


class _SimulationProto(Protocol):  # pragma: no cover - typing helper only
    def step(self, rng: random.Random, *, use_decision: bool = False) -> None: ...


class EmbeddedPygameWidget(QWidget):  # pragma: no cover (GUI, smoke tested separately)
    FRAME_INTERVAL_MS = 16  # ~60 FPS target
    SURFACE_SIZE = (320, 240)
    _sim_rng: random.Random | None  # lazily-created RNG for simulation

    def __init__(
        self,
        parent: QWidget | None = None,
        simulation: _SimulationProto | None = None,
        *,
        decision_mode: bool | None = None,
    ) -> None:
        super().__init__(parent)
        # Optional injected simulation (Gate 3). Avoid hard dependency to keep
        # earlier tests stable. If provided, it must expose step(rng) with a
        # deterministic RNG argument. We'll internally manage a Random instance.
        self._simulation: _SimulationProto | None = simulation
        self._sim_rng = None  # set in first tick if simulation provided
        # Cache decision mode default (Gate 6 integration finalization):
        # Precedence: explicit constructor param > env flag > default True.
        # Env flag ECONSIM_LEGACY_RANDOM=1 forces legacy random walk.
        import os as _os  # local alias to avoid top-level changes
        env_legacy = _os.environ.get("ECONSIM_LEGACY_RANDOM") == "1"
        if decision_mode is not None:
            self._use_decision_default = bool(decision_mode)
        else:
            self._use_decision_default = not env_legacy
        # Set SDL video driver for headless environments before pygame.init()
        import os

        if not os.environ.get("DISPLAY"):
            os.environ["SDL_VIDEODRIVER"] = "dummy"

        pygame.init()
        # Always set a display mode to ensure Surface creation works
        try:
            pygame.display.set_mode((1, 1))  # Minimal display mode
        except pygame.error:
            pass  # Continue if display setup fails

        # Off-screen surface (no window). Create without convert_alpha() if needed
        try:
            self._surface = pygame.Surface(self.SURFACE_SIZE).convert_alpha()
        except pygame.error:
            self._surface = pygame.Surface(self.SURFACE_SIZE)  # Fallback without alpha
        self._frame = 0
        self._start = perf_counter()
        self._fps_last_report = self._start
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)  # type: ignore[arg-type]
        self._timer.start(self.FRAME_INTERVAL_MS)
        self.setMinimumSize(*self.SURFACE_SIZE)
        # Bundle 3 forthcoming enhancement flags (kept simple for forward compatibility)
        self.show_grid_lines = False
        self.show_overlay = False
        self._overlay_font = None  # lazy init
        # When True, disable legacy animated background & moving rectangle for pedagogical clarity
        self.static_background = False
        # External overlay state container (set by controller / GUI). If absent, all False.
        try:
            from .overlay_state import OverlayState  # local import to avoid mandatory dependency elsewhere
            self.overlay_state: "OverlayState | None" = OverlayState()
        except Exception:  # pragma: no cover - defensive import guard
            self.overlay_state = None

    # --- Frame Loop -----------------------------------------------------
    def _on_tick(self) -> None:
        # Step simulation first (if present) using a lazily-created RNG.
        if self._simulation is not None:
            import random

            if self._sim_rng is None:
                # Seed based on start time fractional part for repeatable session if needed.
                self._sim_rng = random.Random(12345)
            # If a SimulationController is attached (parent chain), check pause state
            controller = getattr(self, "_controller_ref", None)
            paused = False
            if controller is not None:
                try:
                    paused = controller.is_paused()  # type: ignore[attr-defined]
                except Exception:
                    paused = False
            if not paused:
                try:
                    self._simulation.step(self._sim_rng, use_decision=self._use_decision_default)
                    if controller is not None:
                        try:
                            controller._record_step_timestamp()  # type: ignore[attr-defined]
                        except Exception:
                            pass
                except Exception as exc:  # pragma: no cover - defensive
                    print(f"[SimulationWarning] Step error: {exc}")
        self._update_scene()
        self.update()  # trigger paintEvent
        self._frame += 1
        now = perf_counter()
        if now - self._fps_last_report >= 1.0:
            fps = self._frame / (now - self._start)
            print(f"[Gate1] Frames={self._frame} AvgFPS={fps:.1f}")
            self._fps_last_report = now

    def _update_scene(self) -> None:
        # Background
        w, h = self.SURFACE_SIZE
        if self.static_background:
            self._surface.fill((30, 30, 35))  # neutral dark
        else:
            phase = (self._frame // 5) % 255
            bg_color = (phase, 50, 255 - phase)
            self._surface.fill(bg_color)
            # Legacy moving rectangle (kept only when not static)
            rect_w, rect_h = 50, 30
            x = (self._frame * 3) % (w - rect_w)
            y = (self._frame * 2) % (h - rect_h)
            pygame.draw.rect(
                self._surface, (255 - phase, 200, phase), pygame.Rect(x, y, rect_w, rect_h)
            )
        # Overlay simulation elements if a compatible simulation is attached (Gate 4 visual aid)
        sim = self._simulation
        if sim is not None:
            grid = getattr(sim, "grid", None)
            agents = getattr(sim, "agents", None)
            if grid is not None and agents is not None and hasattr(grid, "iter_resources"):
                # Scaling: map simulation grid to surface; simple uniform scale (integer) or fallback 1.
                gw = getattr(grid, "width", 1)
                gh = getattr(grid, "height", 1)
                # Determine cell size (fit entire grid). Ensure >=2 pixels for visibility when possible.
                cell_w = max(2, w // max(1, gw))
                cell_h = max(2, h // max(1, gh))
                # Optional grid lines - phase out legacy flag in favor of overlay_state.show_grid
                overlay_state = getattr(self, "overlay_state", None)
                use_grid = False
                if overlay_state is not None:
                    use_grid = getattr(overlay_state, "show_grid", False)
                else:
                    use_grid = getattr(self, "show_grid_lines", False)
                if use_grid:
                    line_color = (40, 40, 40)
                    # Vertical lines
                    for gx in range(gw + 1):
                        x_pix = gx * cell_w
                        pygame.draw.line(self._surface, line_color, (x_pix, 0), (x_pix, gh * cell_h), 1)
                    # Horizontal lines
                    for gy in range(gh + 1):
                        y_pix = gy * cell_h
                        pygame.draw.line(self._surface, line_color, (0, y_pix), (gw * cell_w, y_pix), 1)
                # Resource color map
                RES_COLORS = {
                    "A": (240, 240, 60),  # yellowish
                    "B": (60, 200, 255),  # cyan
                }
                # Draw resources
                try:
                    for rx, ry, rtype in grid.iter_resources():  # type: ignore[attr-defined]
                        color = RES_COLORS.get(rtype, (200, 200, 200))
                        pygame.draw.rect(
                            self._surface,
                            color,
                            pygame.Rect(rx * cell_w, ry * cell_h, cell_w, cell_h),
                        )
                except Exception:  # pragma: no cover - defensive
                    pass
                # Draw agents (small squares with outline) - deterministic order
                sorted_agents = list(sorted(agents, key=lambda a: getattr(a, "id", 0)))
                for agent in sorted_agents:
                    ax = getattr(agent, "x", 0)
                    ay = getattr(agent, "y", 0)
                    inv = getattr(agent, "carrying", {})
                    # Agent color shifts slightly with carried balance (good1 vs good2)
                    g1 = float(inv.get("good1", 0))
                    g2 = float(inv.get("good2", 0))
                    total = g1 + g2 + 1e-6
                    mix = g1 / total
                    r = int(255 * (1 - mix))
                    b = int(255 * mix)
                    agent_color = (r, 40, b)
                    rect = pygame.Rect(ax * cell_w, ay * cell_h, cell_w, cell_h)
                    pygame.draw.rect(self._surface, agent_color, rect)
                    # Outline for visibility
                    pygame.draw.rect(self._surface, (20, 20, 20), rect, 1)
                # Overlay HUD (legacy full stats) + Phase A overlays (agent IDs / target arrow)
                if getattr(self, "show_overlay", False) or (
                    overlay_state is not None and (overlay_state.show_agent_ids or overlay_state.show_target_arrow)
                ):
                    try:
                        if self._overlay_font is None:
                            pygame.font.init()
                            self._overlay_font = pygame.font.Font(None, 14)
                        font = self._overlay_font
                        # HUD lines only if legacy show_overlay flag set
                        if getattr(self, "show_overlay", False):
                            step_count = getattr(sim, "_count", 0)
                            remaining = 0
                            try:
                                remaining = sum(1 for _ in grid.iter_resources())  # type: ignore[arg-type]
                            except Exception:
                                pass
                            lines: list[str] = [f"Turn: {step_count}", f"Resources: {remaining}"]
                            for agent in sorted_agents:
                                carry = getattr(agent, "carrying", {})
                                home = getattr(agent, "home_inventory", {})
                                g1c = carry.get("good1", 0)
                                g2c = carry.get("good2", 0)
                                g1h = home.get("good1", 0)
                                g2h = home.get("good2", 0)
                                pref = getattr(agent, "preference", None)
                                util_val = None
                                try:
                                    if pref is not None and hasattr(pref, "utility"):
                                        goods_map = {"good1": g1c + g1h, "good2": g2c + g2h}
                                        util_val = pref.utility(goods_map)  # type: ignore[arg-type]
                                except Exception:
                                    util_val = None
                                if util_val is not None:
                                    lines.append(
                                        f"A{getattr(agent,'id',0)} pos=({getattr(agent,'x',0)},{getattr(agent,'y',0)}) carry=({g1c},{g2c}) home=({g1h},{g2h}) U={util_val:.2f}"
                                    )
                                else:
                                    lines.append(
                                        f"A{getattr(agent,'id',0)} pos=({getattr(agent,'x',0)},{getattr(agent,'y',0)}) carry=({g1c},{g2c}) home=({g1h},{g2h})"
                                    )
                            # Render lines
                            y_off = 4
                            for txt in lines:
                                surf = font.render(txt, True, (250, 250, 250))
                                shadow = font.render(txt, True, (0, 0, 0))
                                self._surface.blit(shadow, (5, y_off + 1))
                                self._surface.blit(surf, (4, y_off))
                                y_off += surf.get_height() + 2
                        # Agent IDs / target arrows from overlay_state
                        if overlay_state is not None:
                            for agent in sorted_agents:
                                ax = getattr(agent, "x", 0)
                                ay = getattr(agent, "y", 0)
                                if overlay_state.show_agent_ids:
                                    label_surf = font.render(f"A{getattr(agent,'id',0)}", True, (255, 255, 255))
                                    self._surface.blit(label_surf, (ax * cell_w + 2, ay * cell_h + 2))
                                if overlay_state.show_target_arrow:
                                    tgt = getattr(agent, "_target", None) or getattr(agent, "target", None)
                                    if isinstance(tgt, tuple) and len(tgt) == 2:
                                        tx, ty = tgt
                                        sx = ax * cell_w + cell_w // 2
                                        sy = ay * cell_h + cell_h // 2
                                        ex = tx * cell_w + cell_w // 2
                                        ey = ty * cell_h + cell_h // 2
                                        pygame.draw.line(self._surface, (255, 255, 0), (sx, sy), (ex, ey), 1)
                    except Exception:
                        pass

    # --- Paint Path ------------------------------------------------------
    def paintEvent(self, event):  # type: ignore[override]
        # Convert surface -> QImage without scaling.
        width, height = self.SURFACE_SIZE
        raw_bytes = pygame.image.tostring(self._surface, "RGBA")
        image = QImage(raw_bytes, width, height, QImage.Format.Format_RGBA8888)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.drawImage(QRect(0, 0, self.width(), self.height()), image)
        painter.end()

    # --- Teardown --------------------------------------------------------
    def closeEvent(self, event):  # type: ignore[override]
        if self._timer.isActive():
            self._timer.stop()
        if pygame.get_init():
            pygame.quit()
        super().closeEvent(event)

    # --- Testing Helpers (non-public) ------------------------------
    def get_surface_bytes(self) -> bytes:
        """Return raw RGBA bytes of the current surface (test/diagnostic helper)."""
        return pygame.image.tostring(self._surface, "RGBA")


__all__ = ["EmbeddedPygameWidget"]
