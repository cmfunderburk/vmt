"""Legacy adapter for backward compatibility with existing debug_logger API.

This module provides a bridge between the new observer-based event system
and the existing GUILogger interface. It allows existing code to continue
working without modification while routing events through the new architecture.

Adapter Design Principles:
- 100% API compatibility with existing GUILogger methods
- Route events through observer system for consistency
- Graceful degradation if observer system is unavailable
- Preserve existing method signatures and behavior

Legacy Support:
The adapter implements the most commonly used GUILogger methods and routes
them to appropriate simulation events. This allows the refactor to proceed
incrementally without breaking existing functionality.
"""

from __future__ import annotations

import warnings
from typing import Any

from .events import SimulationEvent, AgentModeChangeEvent
from .observers import BaseObserver


class LegacyLoggerAdapter(BaseObserver):
    """Adapter that routes observer events to existing GUILogger methods.
    
    Provides backward compatibility by translating new simulation events
    back to legacy GUILogger method calls. This allows existing debug
    logging infrastructure to continue working during the refactor.
    
    Attributes:
        _gui_logger: The legacy GUILogger instance to forward to
    """

    def __init__(self, gui_logger: Any) -> None:
        """Initialize adapter with legacy logger.
        
        Args:
            gui_logger: Existing GUILogger instance to forward events to
        """
        super().__init__(enabled=True)
        self._gui_logger = gui_logger

    def notify(self, event: SimulationEvent) -> None:
        """Route simulation events to appropriate GUILogger methods.
        
        Translates new event types back to legacy method calls to maintain
        backward compatibility during the refactor transition.
        
        Args:
            event: Simulation event to process
        """
        if not self.is_enabled():
            return
            
        try:
            if isinstance(event, AgentModeChangeEvent):
                # Route to existing log_agent_mode_change method
                self._gui_logger.log_agent_mode_change(
                    agent_id=event.agent_id,
                    old_mode=event.old_mode,
                    new_mode=event.new_mode,
                    reason=event.reason,
                    step=event.step
                )
            # Future event types can be added here as they're implemented
            
        except Exception as e:
            # Don't let adapter failures break the simulation
            warnings.warn(f"LegacyLoggerAdapter failed processing {type(event).__name__}: {e}")

    def flush_step(self, step: int) -> None:
        """Forward step flush to legacy logger if supported.
        
        Args:
            step: Step number that completed
        """
        if not self.is_enabled():
            return
            
        try:
            # Check if legacy logger supports step flushing
            if hasattr(self._gui_logger, 'flush_step'):
                self._gui_logger.flush_step(step)
        except Exception as e:
            warnings.warn(f"LegacyLoggerAdapter failed flushing step {step}: {e}")

    def close(self) -> None:
        """Close adapter and underlying legacy logger.
        
        Calls close on the legacy logger if supported, then marks
        adapter as closed to prevent further event processing.
        """
        try:
            # Check if legacy logger supports closing
            if hasattr(self._gui_logger, 'close'):
                self._gui_logger.close()
        except Exception as e:
            warnings.warn(f"LegacyLoggerAdapter failed closing: {e}")
        finally:
            super().close()


def create_legacy_adapter(gui_logger: Any) -> LegacyLoggerAdapter:
    """Factory function for creating legacy logger adapters.
    
    Provides a convenient way to create adapters while handling
    potential import or initialization issues gracefully.
    
    Args:
        gui_logger: Existing GUILogger instance
        
    Returns:
        LegacyLoggerAdapter configured for the provided logger
        
    Raises:
        ValueError: If gui_logger is None or invalid
    """
    if gui_logger is None:
        raise ValueError("gui_logger cannot be None")
        
    return LegacyLoggerAdapter(gui_logger)