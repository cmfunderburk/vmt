"""Embedded Pygame Widget with Delta-Based Rendering

Simplified pygame widget that uses visual deltas for rendering instead of complex simulation reconstruction.
"""

from __future__ import annotations

import pygame
from PyQt6.QtCore import QRect, QTimer
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QWidget

from ..visual.delta_controller import DeltaPlaybackController
from ..visual.visual_delta import VisualState


class EmbeddedPygameWidget(QWidget):
    """Pygame widget with delta-based rendering for visual playback."""
    
    SURFACE_SIZE = (600, 600)
    FRAME_INTERVAL_MS = 16  # ~60 FPS target
    
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        delta_controller: DeltaPlaybackController = None,
    ) -> None:
        super().__init__(parent)
        
        # Store delta controller for visual playback
        self.delta_controller: DeltaPlaybackController = delta_controller
        
        # Widget state
        self._surface: pygame.Surface | None = None
        self._closed = False
        self._frame = 0
        self._last_rendered_step = -1
        
        # Initialize pygame if needed
        self._init_pygame()
        
        # Create surface
        self._surface = pygame.Surface(self.SURFACE_SIZE, pygame.SRCALPHA)
        
        # Setup timer for updates
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(self.FRAME_INTERVAL_MS)
    
    def _init_pygame(self) -> None:
        """Initialize pygame if not already initialized."""
        if not pygame.get_init():
            pygame.init()
    
    def _on_tick(self) -> None:
        """Handle timer tick for frame updates."""
        if getattr(self, "_surface", None) is not None:
            # Only update if we have a delta controller and it's not playing
            # (to avoid race conditions with delta controller callbacks)
            if self.delta_controller and not self.delta_controller.is_playing():
                self._update_scene()
            elif not self.delta_controller:
                # Fallback for when no delta controller is set
                self._update_scene()
            
            if not getattr(self, "_closed", False):
                self.update()  # trigger paintEvent
        self._frame += 1
    
    def _update_scene(self) -> None:
        """Update pygame scene with visual delta data."""
        # Skip rendering if widget closed or surface gone
        if getattr(self, "_closed", False):
            return
        surf = getattr(self, "_surface", None)
        if surf is None:
            return
        try:
            import pygame as _pg_guard2
            if not _pg_guard2.get_init():
                return
        except Exception:
            return
        
        # Optional fast headless bypass for CI stress
        import os as _os_fast
        if _os_fast.environ.get("ECONSIM_HEADLESS_RENDER") == "1":
            return
        
        # Clear background
        surf.fill((30, 30, 35))
        
        # Render visual state if delta controller is available
        if self.delta_controller:
            try:
                current_step = self.delta_controller.get_current_step()
                
                # Only update if step changed (avoid unnecessary rendering)
                if self._last_rendered_step != current_step:
                    visual_state = self.delta_controller.get_visual_state()
                    if visual_state:
                        self._render_visual_state(surf, visual_state)
                        self._last_rendered_step = current_step
            except Exception as e:
                print(f"Warning: Error rendering visual state: {e}")
        
        self._frame += 1
    
    def _render_visual_state(self, surf, visual_state: VisualState) -> None:
        """Render visual state to pygame surface."""
        w, h = self.SURFACE_SIZE
        
        # Calculate cell size based on reasonable grid dimensions
        grid_width = 20  # Default grid width
        grid_height = 20  # Default grid height
        
        # Determine cell size to fit grid in surface
        cell_w = max(2, w // grid_width)
        cell_h = max(2, h // grid_height)
        cell_size = min(cell_w, cell_h)
        cell_w = cell_h = cell_size
        
        # Resource color map
        RES_COLORS = {
            "A": (240, 240, 60),  # yellowish
            "B": (60, 200, 255),  # cyan
        }
        
        # Draw resources
        for x, y, resource_type in visual_state.get_resource_list():
            if resource_type:
                color = RES_COLORS.get(str(resource_type), (200, 200, 200))
                pygame.draw.rect(surf, color, pygame.Rect(x * cell_w, y * cell_h, cell_w, cell_h))
        
        # Draw agents
        for agent_id, x, y, carrying in visual_state.get_agent_list():
            # Agent color based on carrying items
            if carrying:
                agent_color = (100, 255, 100)  # Green when carrying
            else:
                agent_color = (100, 100, 255)  # Blue when empty
            
            # Draw agent as circle
            center_x = x * cell_w + cell_w // 2
            center_y = y * cell_h + cell_h // 2
            radius = max(2, min(cell_w, cell_h) // 3)
            pygame.draw.circle(surf, agent_color, (center_x, center_y), radius)
    
    def _trigger_update(self) -> None:
        """Force an immediate update of the pygame rendering."""
        # Clear last rendered step to force refresh
        self._last_rendered_step = -1
        # Force immediate repaint
        self.update()
    
    def update_for_step(self, step: int) -> None:
        """Update pygame rendering for a specific step."""
        if self._last_rendered_step != step:
            self._last_rendered_step = -1  # Force refresh
            self._update_scene()
            self.update()  # Trigger paintEvent
    
    def paintEvent(self, event):  # type: ignore[override]
        """Handle paint event - convert pygame surface to QImage."""
        surf = getattr(self, "_surface", None)
        if surf is None:
            return
        
        # Convert pygame surface to QImage
        w, h = surf.get_size()
        data = pygame.image.tostring(surf, "RGBA")
        qimage = QImage(data, w, h, QImage.Format.Format_RGBA8888)
        
        # Paint the image
        painter = QPainter(self)
        painter.drawImage(QRect(0, 0, w, h), qimage)
        painter.end()
    
    def closeEvent(self, event):  # type: ignore[override]
        """Handle close event - cleanup pygame resources."""
        try:
            self._closed = True
            if hasattr(self, "_timer"):
                self._timer.stop()
            if hasattr(self, "_surface"):
                self._surface = None
        except Exception:
            pass
        super().closeEvent(event)
