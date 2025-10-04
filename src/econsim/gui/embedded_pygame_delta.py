"""Embedded Pygame Widget with Delta-Based Rendering

Simplified pygame widget that uses visual deltas for rendering instead of complex simulation reconstruction.
"""

from __future__ import annotations

import os
import random
from typing import Optional
import pygame
from PyQt6.QtCore import QRect, QTimer
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QWidget

from ..delta.playback_controller import ComprehensivePlaybackController
from ..delta.data_structures import VisualState


class EmbeddedPygameWidget(QWidget):
    """Pygame widget with delta-based rendering for visual playback."""
    
    SURFACE_SIZE = (600, 600)
    FRAME_INTERVAL_MS = 16  # ~60 FPS target
    
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        delta_controller: Optional[ComprehensivePlaybackController] = None,
    ) -> None:
        super().__init__(parent)
        
        # Store delta controller for visual playback
        self.delta_controller: Optional[ComprehensivePlaybackController] = delta_controller
        
        # Widget state
        self._surface: pygame.Surface | None = None
        self._closed = False
        self._frame = 0
        self._last_rendered_step = -1
        
        # Sprite management
        self._sprites: dict[str, pygame.Surface] = {}
        self._agent_sprite_map: dict[int, str] = {}  # agent_id -> sprite_key
        
        # Initialize pygame if needed
        self._init_pygame()
        
        # Load sprites
        self._load_sprites()
        
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
            # Set a video mode to avoid "No video mode has been set" errors
            pygame.display.set_mode((1, 1), pygame.HIDDEN)
    
    def _load_sprites(self) -> None:
        """Load sprite images for agents and resources."""
        # Get the project root directory (assuming we're in src/econsim/gui/)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        
        # Load resource sprites
        resource_sprites = {
            'A': ('vmt_sprites_pack_1', 'resource_food_64.png'),    # Resource A = Food
            'B': ('vmt_sprites_pack_2', 'resource_tools_64.png')    # Resource B = Tools
        }
        
        for resource_type, (pack, sprite_file) in resource_sprites.items():
            sprite_path = os.path.join(project_root, pack, sprite_file)
            try:
                sprite = pygame.image.load(sprite_path)
                # Convert to RGBA for transparency support
                sprite = sprite.convert_alpha()
                self._sprites[f'resource_{resource_type}'] = sprite
                print(f"✅ Loaded resource sprite: {sprite_file} for type {resource_type}")
            except Exception as e:
                print(f"❌ Failed to load resource sprite {sprite_file}: {e}")
        
        # Load agent sprites from pack 2
        agent_sprite_files = [
            'agent_explorer_64.png',
            'agent_farmer_64.png', 
            'agent_green_64.png',
            'agent_miner_64.png',
            'agent_purple_64.png',
            'agent_trader_64.png'
        ]
        
        for sprite_file in agent_sprite_files:
            sprite_path = os.path.join(project_root, 'vmt_sprites_pack_2', sprite_file)
            try:
                sprite = pygame.image.load(sprite_path)
                # Convert to RGBA for transparency support
                sprite = sprite.convert_alpha()
                sprite_key = sprite_file.replace('_64.png', '')
                self._sprites[sprite_key] = sprite
                print(f"✅ Loaded agent sprite: {sprite_file}")
            except Exception as e:
                print(f"❌ Failed to load agent sprite {sprite_file}: {e}")
        
        print(f"📊 Loaded {len(self._sprites)} sprites total")
    
    def _assign_agent_sprites(self, visual_state: VisualState) -> None:
        """Assign truly random sprites to agents at playback time (visual concern only)."""
        agent_sprite_keys = [key for key in self._sprites.keys() if key.startswith('agent_')]
        
        # Only assign sprites if we have agent sprites loaded
        if not agent_sprite_keys:
            return
        
        for agent_id, x, y, carrying in visual_state.get_agent_list():
            if agent_id not in self._agent_sprite_map:
                # Assign a truly random sprite to this agent (independent of simulation)
                sprite_key = random.choice(agent_sprite_keys)
                self._agent_sprite_map[agent_id] = sprite_key
                print(f"🎭 Assigned random sprite {sprite_key} to agent {agent_id}")
    
    def _on_tick(self) -> None:
        """Handle timer tick for frame updates."""
        if getattr(self, "_surface", None) is not None:
            # Only update if we have a delta controller and it's not playing
            # (to avoid race conditions with delta controller callbacks)
            if self.delta_controller and not self.delta_controller.current_state.is_playing:
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
        """Render visual state to pygame surface using sprites."""
        w, h = self.SURFACE_SIZE
        
        # Calculate cell size based on reasonable grid dimensions
        grid_width = 20  # Default grid width
        grid_height = 20  # Default grid height
        
        # Determine cell size to fit grid in surface
        cell_w = max(2, w // grid_width)
        cell_h = max(2, h // grid_height)
        cell_size = min(cell_w, cell_h)
        cell_w = cell_h = cell_size
        
        # Assign sprites to agents if needed
        self._assign_agent_sprites(visual_state)
        
        # Draw resources using sprites
        for x, y, resource_type in visual_state.get_resource_list():
            if resource_type:
                sprite_key = f'resource_{resource_type}'
                if sprite_key in self._sprites:
                    # Use sprite
                    sprite = self._sprites[sprite_key]
                    # Scale sprite to fit cell size
                    scaled_sprite = pygame.transform.scale(sprite, (cell_w, cell_h))
                    surf.blit(scaled_sprite, (x * cell_w, y * cell_h))
                else:
                    # Fallback to colored rectangle
                    fallback_colors = {
                        "A": (240, 240, 60),  # yellowish for food
                        "B": (160, 160, 160), # grey for tools
                    }
                    color = fallback_colors.get(str(resource_type), (200, 200, 200))
                    pygame.draw.rect(surf, color, pygame.Rect(x * cell_w, y * cell_h, cell_w, cell_h))
        
        # Draw agents using sprites
        for agent_id, x, y, carrying in visual_state.get_agent_list():
            sprite_key = self._agent_sprite_map.get(agent_id)
            if sprite_key and sprite_key in self._sprites:
                # Use assigned sprite (no tinting)
                sprite = self._sprites[sprite_key]
                
                # Scale sprite to fit cell size
                scaled_sprite = pygame.transform.scale(sprite, (cell_w, cell_h))
                surf.blit(scaled_sprite, (x * cell_w, y * cell_h))
            else:
                # Fallback to colored circle (blue for all agents)
                agent_color = (100, 100, 255)  # Blue for all agents
                
                center_x = x * cell_w + cell_w // 2
                center_y = y * cell_h + cell_h // 2
                radius = max(2, min(cell_w, cell_h) // 3)
                pygame.draw.circle(surf, agent_color, (center_x, center_y), radius)
            
            # Draw agent ID label
            font_size = max(8, cell_size // 8)  # Scale font size with cell size
            try:
                font = pygame.font.Font(None, font_size)
                text_surface = font.render(str(agent_id), True, (255, 255, 255))  # White text
                
                # Position label at bottom-right of cell
                text_x = x * cell_w + cell_w - font_size
                text_y = y * cell_h + cell_h - font_size
                
                # Add black outline for better visibility
                outline_surface = font.render(str(agent_id), True, (0, 0, 0))  # Black outline
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx != 0 or dy != 0:  # Skip center pixel
                            surf.blit(outline_surface, (text_x + dx, text_y + dy))
                
                # Draw the white text on top
                surf.blit(text_surface, (text_x, text_y))
            except Exception:
                # Fallback if font rendering fails
                pass
    
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
