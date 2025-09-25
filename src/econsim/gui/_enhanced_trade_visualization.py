"""Enhanced Trade Flow Visualization (Educational Phase 2).

Extends existing trade debug overlay with visual indicators, arrows, and educational enhancements.
Maintains performance discipline and feature-flag gating while adding student-friendly visualization.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable, Optional, Tuple, List
import os
import pygame
import math

@runtime_checkable
class _SurfaceLike(Protocol):  # minimal protocol for blit
    def blit(self, source: Any, dest: Any) -> Any: ...  # pragma: no cover

@runtime_checkable
class _FontLike(Protocol):  # minimal font protocol
    def render(self, text: str, antialias: bool, color: Any) -> Any: ...  # pragma: no cover

# Visual configuration
INTENT_ARROW_COLOR = (100, 150, 255)  # Light blue for draft intents
EXECUTED_ARROW_COLOR = (50, 255, 50)  # Green for executed trades
ARROW_WIDTH = 2
ARROW_HEAD_SIZE = 8
INTENT_HIGHLIGHT_COLOR = (255, 255, 100, 64)  # Semi-transparent yellow for agent highlighting

def _get_last_executed(simulation: Any) -> Optional[dict[str, Any]]:
    """Get last executed trade from metrics collector."""
    mc = getattr(simulation, 'metrics_collector', None)
    if mc is None:
        return None
    return getattr(mc, 'last_executed_trade', None)

def _get_agent_position(agent: Any) -> Optional[Tuple[int, int]]:
    """Get agent's grid position."""
    try:
        x = getattr(agent, 'x', None)
        y = getattr(agent, 'y', None)
        if x is not None and y is not None:
            return (int(x), int(y))
        return None
    except Exception:
        return None

def _draw_trade_arrow(surface: _SurfaceLike, 
                     start_pos: Tuple[int, int], 
                     end_pos: Tuple[int, int], 
                     color: Tuple[int, int, int],
                     width: int = ARROW_WIDTH) -> None:
    """Draw an arrow between two positions to represent a trade."""
    try:
        if not isinstance(surface, pygame.Surface):
            return
            
        # Calculate arrow direction
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 1:
            return
            
        # Normalize direction
        dx /= distance
        dy /= distance
        
        # Draw main arrow line
        pygame.draw.line(surface, color, start_pos, end_pos, width)
        
        # Calculate arrowhead
        head_length = min(ARROW_HEAD_SIZE, distance / 2)
        head_x = end_pos[0] - dx * head_length
        head_y = end_pos[1] - dy * head_length
        
        # Perpendicular vector for arrowhead wings
        perp_x = -dy * head_length * 0.5
        perp_y = dx * head_length * 0.5
        
        # Draw arrowhead
        head_points = [
            end_pos,
            (int(head_x + perp_x), int(head_y + perp_y)),
            (int(head_x - perp_x), int(head_y - perp_y))
        ]
        pygame.draw.polygon(surface, color, head_points)
        
    except Exception:
        pass

def _highlight_trading_agents(surface: _SurfaceLike,
                            agent_positions: List[Tuple[int, int]],
                            cell_w: int, 
                            cell_h: int) -> None:
    """Highlight cells containing agents involved in trades."""
    try:
        if not isinstance(surface, pygame.Surface):
            return
            
        highlight_surface = pygame.Surface((cell_w, cell_h), pygame.SRCALPHA)
        highlight_surface.fill(INTENT_HIGHLIGHT_COLOR)
        
        for x, y in agent_positions:
            surface.blit(highlight_surface, (x * cell_w, y * cell_h))
            
    except Exception:
        pass

def render_enhanced_trade_visualization(surface: _SurfaceLike, 
                                      font: _FontLike, 
                                      simulation: Any,
                                      cell_w: int,
                                      cell_h: int,
                                      show_arrows: bool = True,
                                      show_highlights: bool = True,
                                      *,
                                      x_offset: int = 4,
                                      y_offset: int = 4) -> None:
    """Render enhanced trade visualization with arrows and highlights.
    
    Args:
        surface: Pygame surface to draw on
        font: Font for text rendering
        simulation: Simulation instance with trade_intents and agents
        cell_w, cell_h: Cell dimensions for positioning
        show_arrows: Whether to draw trade intent arrows
        show_highlights: Whether to highlight trading agent cells
        x_offset, y_offset: Text overlay positioning
    """
    # Only render if trade features are enabled
    if os.environ.get("ECONSIM_TRADE_DRAFT") != "1":
        return
        
    intents = getattr(simulation, "trade_intents", None)
    agents = getattr(simulation, "agents", None)
    
    if not intents or not agents:
        return
        
    # Protocol runtime checks
    if not isinstance(surface, pygame.Surface):
        return
            
    try:
        # Build agent position lookup
        agent_positions: dict[Any, Tuple[int, int]] = {}
        for agent in agents:
            pos = _get_agent_position(agent)
            if pos is not None:
                agent_positions[getattr(agent, 'id', None)] = pos
        
        # Get last executed trade for highlighting
        last_exec = _get_last_executed(simulation)
        executed_signature = None
        if last_exec is not None:
            executed_signature = (
                last_exec.get('seller'),
                last_exec.get('buyer'),
                last_exec.get('give_type'),
                last_exec.get('take_type'),
            )
        
        # Collect positions of agents involved in trading
        trading_agent_positions: set[Tuple[int, int]] = set()
        
        # Draw trade intent arrows and collect positions
        if show_arrows and cell_w > 0 and cell_h > 0:
            for intent in intents:
                seller_id = getattr(intent, "seller_id", None)
                buyer_id = getattr(intent, "buyer_id", None)
                
                if seller_id in agent_positions and buyer_id in agent_positions:
                    seller_pos = agent_positions[seller_id]
                    buyer_pos = agent_positions[buyer_id]
                    
                    # Calculate center positions
                    start_pos = (
                        int(seller_pos[0] * cell_w + cell_w // 2),
                        int(seller_pos[1] * cell_h + cell_h // 2)
                    )
                    end_pos = (
                        int(buyer_pos[0] * cell_w + cell_w // 2),
                        int(buyer_pos[1] * cell_h + cell_h // 2)
                    )
                    
                    # Check if this is the executed trade
                    is_executed = executed_signature == (
                        seller_id, buyer_id, 
                        getattr(intent, "give_type", None), 
                        getattr(intent, "take_type", None)
                    )
                    
                    # Choose arrow color
                    color = EXECUTED_ARROW_COLOR if is_executed else INTENT_ARROW_COLOR
                    
                    # Draw the trade arrow
                    _draw_trade_arrow(surface, start_pos, end_pos, color)
                    
                    # Track positions for highlighting
                    if show_highlights:
                        trading_agent_positions.add(seller_pos)
                        trading_agent_positions.add(buyer_pos)
        
        # Highlight trading agent cells
        if show_highlights and trading_agent_positions and cell_w > 0 and cell_h > 0:
            _highlight_trading_agents(surface, list(trading_agent_positions), cell_w, cell_h)
        
        # Render text overlay (reuse existing debug overlay logic)
        from ._trade_debug_overlay import render_trade_debug
        render_trade_debug(surface, font, simulation, x_offset=x_offset, y_offset=y_offset)
        
    except Exception:
        # Graceful fallback - just render basic text overlay
        try:
            from ._trade_debug_overlay import render_trade_debug
            render_trade_debug(surface, font, simulation, x_offset=x_offset, y_offset=y_offset)
        except Exception:
            pass


__all__ = ["render_enhanced_trade_visualization"]