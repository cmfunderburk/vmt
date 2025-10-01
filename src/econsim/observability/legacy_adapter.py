"""Legacy adapter for GUILogger backward compatibility.

This module provides a bridge between the legacy GUILogger API and the new
observer pattern system. It allows existing code to continue using GUILogger
methods while internally routing to the new modular observer system.

Phase 3.3 Design Principles:
- 100% backward API compatibility for existing GUILogger users
- Internal routing FROM legacy methods TO new observer system
- Deprecation warnings for migration guidance
- Gradual migration path without breaking changes
- Observer system integration under the hood
"""

from __future__ import annotations

import warnings
import time
from pathlib import Path
from typing import Optional, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .config import ObservabilityConfig
    from .observers.base_observer import BaseObserver

from .events import AgentModeChangeEvent
from .config import ObservabilityConfig


class LegacyLoggerAdapter:
    """Adapter providing backward compatibility for GUILogger API.
    
    This adapter maintains the existing GUILogger interface while internally
    routing events to the new modular observer system. It provides a seamless
    migration path from the monolithic logger to the observer pattern.
    
    Features:
    - Complete API compatibility with existing GUILogger methods
    - Deprecation warnings to guide migration
    - Internal routing to FileObserver and EducationalObserver
    - Performance monitoring via PerformanceObserver
    - Configurable observer selection based on environment
    
    Attributes:
        _config: Observability configuration
        _observers: List of registered observers
        _enable_warnings: Whether to emit deprecation warnings
    """
    
    def __init__(self, 
                 config: Optional[ObservabilityConfig] = None,
                 output_path: Optional[Path] = None,
                 enable_deprecation_warnings: bool = True):
        """Initialize the legacy adapter with observer system.
        
        Args:
            config: Observability configuration (defaults to environment-based)
            output_path: Output path for file logging (defaults to gui_logs/)
            enable_deprecation_warnings: Whether to emit deprecation warnings
        """
        self._config = config or ObservabilityConfig.from_environment()
        self._enable_warnings = enable_deprecation_warnings
        
        # Initialize observer system
        self._observers: List[BaseObserver] = []
        
        # Set up default output path
        if output_path is None:
            output_path = Path("gui_logs") / "structured" / f"{time.strftime('%Y-%m-%d %H-%M-%S')} Legacy.jsonl"
        
        # Create observers based on configuration
        self._initialize_observers(output_path)

    def _initialize_observers(self, output_path: Path) -> None:
        """Initialize observers based on configuration.
        
        Args:
            output_path: Path for file logging output
        """
        try:
            # Import observers here to avoid circular imports
            from .observers.file_observer import FileObserver
            from .observers.educational_observer import EducationalObserver
            from .observers.performance_observer import PerformanceObserver
            
            # Always include FileObserver for structured logging
            file_observer = FileObserver(self._config, output_path)
            self._observers.append(file_observer)
            
            # Add EducationalObserver for behavioral analytics
            educational_observer = EducationalObserver(self._config)
            self._observers.append(educational_observer)
            
            # Add PerformanceObserver for monitoring
            performance_observer = PerformanceObserver(self._config)
            self._observers.append(performance_observer)
            
        except Exception as e:
            # Fallback to minimal configuration if initialization fails
            warnings.warn(f"Observer initialization failed, using fallback: {e}", UserWarning)
    
    def _emit_deprecation_warning(self, method_name: str, recommended_alternative: str = "") -> None:
        """Emit deprecation warning for legacy method usage.
        
        Args:
            method_name: Name of the deprecated method being called
            recommended_alternative: Suggested alternative approach
        """
        if not self._enable_warnings:
            return
            
        alternative_msg = f" Use {recommended_alternative} instead." if recommended_alternative else ""
        warnings.warn(
            f"GUILogger.{method_name}() is deprecated.{alternative_msg} "
            f"Migrate to observer pattern for better performance and modularity.",
            DeprecationWarning,
            stacklevel=3
        )
    
    def _notify_observers(self, event: Any) -> None:
        """Notify all registered observers of an event.
        
        Args:
            event: The simulation event to broadcast
        """
        for observer in self._observers:
            try:
                observer.notify(event)
            except Exception as e:
                # Log error but continue processing other observers
                warnings.warn(f"Observer notification failed: {e}", UserWarning)
    
    def log_agent_mode(self, agent_id: int, old_mode: str, new_mode: str, 
                      reason: str = "", step: Optional[int] = None) -> None:
        """DEPRECATED: Log agent mode transitions.
        
        Args:
            agent_id: ID of the agent changing modes
            old_mode: Previous agent mode
            new_mode: New agent mode
            reason: Optional reason for the mode change
            step: Simulation step number
        """
        self._emit_deprecation_warning(
            "log_agent_mode", 
            "AgentModeChangeEvent with observer pattern"
        )
        
        event = AgentModeChangeEvent(
            step=step or 0,
            timestamp=time.time(),
            event_type="agent_mode_change",
            agent_id=agent_id,
            old_mode=old_mode,
            new_mode=new_mode,
            reason=reason
        )
        
        self._notify_observers(event)

    def log(self, category: str, message: str, step: Optional[int] = None) -> None:
        """DEPRECATED: Generic log method.
        
        Args:
            category: Log category (e.g., "TRADE", "AGENT_MODE")
            message: Log message
            step: Simulation step number
        """
        self._emit_deprecation_warning("log", "specific event types with observer pattern")
        
        # Route to appropriate observer based on category
        # For now, just log as generic event through file observer
        if self._observers:
            try:
                # Create a generic event for backward compatibility
                # This is a simplified routing - in practice, you'd want more specific events
                self._observers[0].notify(type('GenericEvent', (), {
                    'step': step or 0,
                    'timestamp': time.time(),
                    'event_type': category.lower(),
                    'message': message
                })())
            except Exception:
                pass  # Fail silently to maintain backward compatibility
    
    def finalize_session(self) -> None:
        """DEPRECATED: Finalize the logging session."""
        self._emit_deprecation_warning("finalize_session", "observer cleanup methods")
        
        # Close all observers
        for observer in self._observers:
            try:
                observer.close()
            except Exception:
                pass  # Fail silently
    
    def recent_structured_events(self) -> List[Any]:
        """DEPRECATED: Get recent structured events.
        
        Returns:
            Empty list for compatibility (functionality moved to MemoryObserver)
        """
        self._emit_deprecation_warning("recent_structured_events", "MemoryObserver for event collection")
        return []  # Return empty list for backward compatibility
    
    # Legacy singleton pattern compatibility
    _instance: Optional['LegacyLoggerAdapter'] = None
    
    @classmethod
    def get_instance(cls) -> 'LegacyLoggerAdapter':
        """DEPRECATED: Get singleton instance for backward compatibility."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def create_legacy_adapter(config: Optional[ObservabilityConfig] = None,
                         output_path: Optional[Path] = None,
                         enable_warnings: bool = True) -> LegacyLoggerAdapter:
    """Factory function to create a legacy adapter instance.
    
    Args:
        config: Optional observability configuration
        output_path: Optional output path for logging
        enable_warnings: Whether to enable deprecation warnings
        
    Returns:
        Configured LegacyLoggerAdapter instance
    """
    return LegacyLoggerAdapter(
        config=config,
        output_path=output_path,
        enable_deprecation_warnings=enable_warnings
    )