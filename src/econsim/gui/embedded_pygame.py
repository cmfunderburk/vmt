"""Embedded Pygame Widget (Gate 1 Stub)

Gate 1 scope: Demonstrate coexistence of PyQt6 event loop with a Pygame
off-screen Surface updated on a QTimer. This avoids native SDL window
embedding complexity while validating frame update + paint path.

Out-of-scope in Gate 1: agents, economics, grid logic, advanced rendering,
logging, threading.
"""

from __future__ import annotations

from time import perf_counter

import pygame
from PyQt6.QtCore import QRect, QTimer
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QWidget


class EmbeddedPygameWidget(QWidget):  # pragma: no cover (GUI, smoke tested separately)
    FRAME_INTERVAL_MS = 16  # ~60 FPS target
    SURFACE_SIZE = (320, 240)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
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

    # --- Frame Loop -----------------------------------------------------
    def _on_tick(self) -> None:
        self._update_scene()
        self.update()  # trigger paintEvent
        self._frame += 1
        now = perf_counter()
        if now - self._fps_last_report >= 1.0:
            fps = self._frame / (now - self._start)
            print(f"[Gate1] Frames={self._frame} AvgFPS={fps:.1f}")
            self._fps_last_report = now

    def _update_scene(self) -> None:
        # Simple color cycle + moving rectangle.
        w, h = self.SURFACE_SIZE
        phase = (self._frame // 5) % 255
        bg_color = (phase, 50, 255 - phase)
        self._surface.fill(bg_color)
        # Moving rectangle path
        rect_w, rect_h = 50, 30
        x = (self._frame * 3) % (w - rect_w)
        y = (self._frame * 2) % (h - rect_h)
        pygame.draw.rect(
            self._surface, (255 - phase, 200, phase), pygame.Rect(x, y, rect_w, rect_h)
        )

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


__all__ = ["EmbeddedPygameWidget"]
