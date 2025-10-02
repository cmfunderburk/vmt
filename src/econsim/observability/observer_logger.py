"""Observer-based logging for the simulation.

This module provides ObserverLogger, which uses the observer pattern for
event distribution with environment variable-based filtering and performance
optimizations.

Design Principles:
- Pure observer pattern implementation (no GUI dependencies)
- Environment variable-based filtering
- Performance optimizations through event batching
- Graceful degradation when observers unavailable

Usage:
    from econsim.observability.observer_logger import ObserverLogger
    logger = ObserverLogger(observer_registry)
    logger.log("TRADE", "Agent trade executed", step=42)
"""

from __future__ import annotations

import os
from typing import Optional, Dict, Any, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .registry import ObserverRegistry

from .events import (
    DebugLogEvent, PerformanceMonitorEvent, AgentDecisionEvent, 
    ResourceEvent, AgentModeChangeEvent
)


class ObserverLogger:
    """Observer-based logging functionality.
    
    Uses the observer pattern for event distribution with environment 
    variable-based filtering and performance optimizations.
    
    Attributes:
        observer_registry: Registry for event distribution
        _step_context: Current simulation step for event attribution
        _debug_enabled: Whether debug output is enabled
    """
    
    def __init__(self, observer_registry: ObserverRegistry) -> None:
        """Initialize observer-based logger.
        
        Args:
            observer_registry: Registry to distribute events to observers
        """
        self.observer_registry = observer_registry
        self._step_context: Optional[int] = None
        self._debug_enabled = os.environ.get("ECONSIM_DEBUG_OBSERVERS", "0") == "1"
        
        # Cache environment variables for performance
        self._env_cache = {
            "debug_agent_modes": os.environ.get("ECONSIM_DEBUG_AGENT_MODES", "0") == "1",
            "debug_trades": os.environ.get("ECONSIM_DEBUG_TRADES", "0") == "1", 
            "debug_simulation": os.environ.get("ECONSIM_DEBUG_SIMULATION", "0") == "1",
            "debug_phases": os.environ.get("ECONSIM_DEBUG_PHASES", "0") == "1",
            "debug_decisions": os.environ.get("ECONSIM_DEBUG_DECISIONS", "0") == "1",
            "debug_resources": os.environ.get("ECONSIM_DEBUG_RESOURCES", "0") == "1",
            "debug_performance": os.environ.get("ECONSIM_DEBUG_PERFORMANCE", "0") == "1"
        }
    
    def set_step_context(self, step: int) -> None:
        """Set current simulation step for event attribution.
        
        Args:
            step: Current simulation step number
        """
        self._step_context = step
    
    def _get_step(self, step: Optional[int] = None) -> int:
        """Get step number for event, using context if not provided.
        
        Args:
            step: Explicit step number (None = use context)
            
        Returns:
            Step number for event attribution
        """
        return step if step is not None else (self._step_context or 0)
    
    def _should_log_category(self, category: str) -> bool:
        """Check if events of this category should be logged.
        
        Uses environment variables for conditional logging.
        
        Args:
            category: Event category to check
            
        Returns:
            True if this category should be logged
        """
        category_lower = category.lower()
        
        if "mode" in category_lower:
            return self._env_cache["debug_agent_modes"]
        elif "trade" in category_lower:
            return self._env_cache["debug_trades"]
        elif "simulation" in category_lower:
            return self._env_cache["debug_simulation"]
        elif "phase" in category_lower:
            return self._env_cache["debug_phases"]
        elif "decision" in category_lower:
            return self._env_cache["debug_decisions"]
        elif "resource" in category_lower:
            return self._env_cache["debug_resources"]
        elif "performance" in category_lower or "perf" in category_lower:
            return self._env_cache["debug_performance"]
        else:
            # Default: log if any debug mode is enabled
            return any(self._env_cache.values())
    
    # Core logging methods
    
    def log(self, category: str, message: str, step: Optional[int] = None) -> None:
        """Log a categorized debug message.
        
        Args:
            category: Log category (TRADE, MODE, ECON, etc.)
            message: Debug message text
            step: Optional simulation step
        """
        if not self._should_log_category(category):
            return
            
        event = DebugLogEvent.create(
            step=self._get_step(step),
            category=category,
            message=message
        )
        self.observer_registry.notify(event)
    
    def log_agent_mode(self, agent_id: int, old_mode: str, new_mode: str, 
                       reason: str = "", step: Optional[int] = None) -> None:
        """Log agent mode transition.
        
        Args:
            agent_id: ID of agent changing modes
            old_mode: Previous mode string
            new_mode: New mode string
            reason: Optional reason for change
            step: Optional simulation step
        """
        if not self._env_cache["debug_agent_modes"]:
            return
            
        event = AgentModeChangeEvent.create(
            step=self._get_step(step),
            agent_id=agent_id,
            old_mode=old_mode,
            new_mode=new_mode,
            reason=reason
        )
        self.observer_registry.notify(event)
    
    def log_trade(self, message: str, step: Optional[int] = None) -> None:
        """Log trade debug information.
        
        Args:
            message: Trade debug message
            step: Optional simulation step
        """
        if not self._env_cache["debug_trades"]:
            return
            
        event = DebugLogEvent.create(
            step=self._get_step(step),
            category="TRADE",
            message=message
        )
        self.observer_registry.notify(event)
    
    def log_simulation(self, message: str, step: Optional[int] = None) -> None:
        """Log simulation debug information.
        
        Args:
            message: Simulation debug message
            step: Optional simulation step
        """
        if not self._env_cache["debug_simulation"]:
            return
            
        event = DebugLogEvent.create(
            step=self._get_step(step),
            category="SIMULATION",
            message=message
        )
        self.observer_registry.notify(event)
    
    def log_agent_decision(self, agent_id: int, decision_type: str, details: str, 
                          step: Optional[int] = None) -> None:
        """Log agent decision-making details.
        
        Args:
            agent_id: ID of agent making decision
            decision_type: Type of decision being made
            details: Decision details and context
            step: Optional simulation step
        """
        if not self._env_cache["debug_decisions"]:
            return
            
        event = AgentDecisionEvent.create(
            step=self._get_step(step),
            agent_id=agent_id,
            decision_type=decision_type,
            decision_details=details
        )
        self.observer_registry.notify(event)
    
    def log_resource_event(self, event_type: str, position: Tuple[int, int], 
                          resource_type: str, agent_id: Optional[int] = None, 
                          step: Optional[int] = None) -> None:
        """Log resource-related events.
        
        Args:
            event_type: Type of resource event (pickup, spawn, etc.)
            position: Grid position of resource
            resource_type: Type of resource
            agent_id: Optional agent involved
            step: Optional simulation step
        """
        if not self._env_cache["debug_resources"]:
            return
            
        event = ResourceEvent.create(
            step=self._get_step(step),
            event_type_detail=event_type,
            position_x=position[0],
            position_y=position[1],
            resource_type=resource_type,
            agent_id=agent_id if agent_id is not None else -1
        )
        self.observer_registry.notify(event)
    
    def log_performance(self, message: str, step: Optional[int] = None) -> None:
        """Log performance metrics.
        
        Args:
            message: Performance message (steps/sec, timing, etc.)
            step: Optional simulation step
        """
        if not self._env_cache["debug_performance"]:
            return
        
        # Extract numeric value if possible for structured logging
        import re
        steps_per_sec_match = re.search(r'([0-9.]+) steps/sec', message)
        frame_time_match = re.search(r'([0-9.]+)ms frame', message)
        
        if steps_per_sec_match:
            metric_value = float(steps_per_sec_match.group(1))
            event = PerformanceMonitorEvent.create(
                step=self._get_step(step),
                metric_name="steps_per_sec",
                metric_value=metric_value,
                details=message
            )
        elif frame_time_match:
            metric_value = float(frame_time_match.group(1))
            event = PerformanceMonitorEvent.create(
                step=self._get_step(step),
                metric_name="frame_time_ms", 
                metric_value=metric_value,
                details=message
            )
        else:
            # Fall back to debug log event
            event = DebugLogEvent.create(
                step=self._get_step(step),
                category="PERFORMANCE",
                message=message
            )
        
        self.observer_registry.notify(event)
    
    # Additional convenience methods for common patterns
    
    def log_phase_transition(self, phase: int, turn: int, description: str) -> None:
        """Log phase transition events.
        
        Args:
            phase: Phase number
            turn: Turn/step number  
            description: Phase description
        """
        if not self._env_cache["debug_phases"]:
            return
            
        event = DebugLogEvent.create(
            step=turn,
            category="PHASE",
            message=f"Phase {phase}: {description}"
        )
        self.observer_registry.notify(event)
    
    def log_mode_switch(self, agent_id: int, old_mode: str, new_mode: str, 
                       context: str = "", step: Optional[int] = None) -> None:
        """Log mode switch (alias for log_agent_mode).
        
        Args:
            agent_id: ID of agent switching modes
            old_mode: Previous mode
            new_mode: New mode
            context: Additional context
            step: Optional simulation step
        """
        self.log_agent_mode(agent_id, old_mode, new_mode, context, step)
    
    def log_economics(self, message: str, step: Optional[int] = None) -> None:
        """Log economic system messages.
        
        Args:
            message: Economic system message
            step: Optional simulation step
        """
        event = DebugLogEvent.create(
            step=self._get_step(step),
            category="ECON",
            message=message
        )
        self.observer_registry.notify(event)
    
    def log_spatial(self, message: str, step: Optional[int] = None) -> None:
        """Log spatial/movement messages.
        
        Args:
            message: Spatial system message
            step: Optional simulation step
        """
        event = DebugLogEvent.create(
            step=self._get_step(step),
            category="SPATIAL",
            message=message
        )
        self.observer_registry.notify(event)
    
    def log_utility_change(self, agent_id: int, old_utility: float, new_utility: float,
                          reason: str = "", step: Optional[int] = None, good_type: str = "") -> None:
        """Log utility changes for agents.
        
        Args:
            agent_id: Agent whose utility changed
            old_utility: Previous utility value
            new_utility: New utility value  
            reason: Reason for change
            step: Optional simulation step
            good_type: Type of good involved
        """
        utility_delta = new_utility - old_utility
        details = f"Utility {old_utility:.2f} → {new_utility:.2f} (Δ{utility_delta:+.2f})"
        if reason:
            details += f" due to {reason}"
        if good_type:
            details += f" [{good_type}]"
            
        event = AgentDecisionEvent.create(
            step=self._get_step(step),
            agent_id=agent_id,
            decision_type="utility_change",
            decision_details=details,
            utility_delta=utility_delta
        )
        self.observer_registry.notify(event)
    
    # Builder methods for complex logging patterns
    
    def build_phase_transition(self, phase: int, turn: int, description: str) -> Tuple[str, Dict[str, Any], str]:
        """Build phase transition data (compatibility method).
        
        Returns tuple format expected by legacy code but creates observer event.
        
        Args:
            phase: Phase number
            turn: Turn number
            description: Phase description
            
        Returns:
            Tuple of (category, data, formatted_message)
        """
        self.log_phase_transition(phase, turn, description)
        
        return (
            "PHASE",
            {"phase": phase, "turn": turn, "description": description},
            f"Phase {phase} (Turn {turn}): {description}"
        )
    
    def emit_built_event(self, step: int, builder_result: Tuple[str, Dict[str, Any], str]) -> None:
        """Emit a built event (compatibility method).
        
        Args:
            step: Simulation step
            builder_result: Result from builder method
        """
        category, _, message = builder_result  # data not used in observer pattern
        event = DebugLogEvent.create(
            step=step,
            category=category,
            message=message
        )
        self.observer_registry.notify(event)
    
    # Tracking methods (behavioral analysis compatibility)
    
    def track_agent_retargeting(self, step: int, agent_id: int) -> None:
        """Track agent retargeting behavior.
        
        Args:
            step: Simulation step
            agent_id: Agent that retargeted
        """
        event = AgentDecisionEvent.create(
            step=step,
            agent_id=agent_id,
            decision_type="retargeting",
            decision_details="Agent changed target selection"
        )
        self.observer_registry.notify(event)
    
    # Performance and analysis methods
    
    def should_log_performance(self, step: int, steps_per_sec: float) -> bool:
        """Check if performance should be logged (compatibility method).
        
        Args:
            step: Current simulation step
            steps_per_sec: Current performance metric
            
        Returns:
            True if performance should be logged
        """
        # Simple threshold-based logging (can be enhanced)
        return steps_per_sec < 10.0 or step % 100 == 0
    
    # Registry management methods
    
    def get_observer_count(self) -> int:
        """Get number of registered observers.
        
        Returns:
            Number of observers that will receive events
        """
        return self.observer_registry.observer_count()
    
    def has_observers(self) -> bool:
        """Check if any observers are registered.
        
        Returns:
            True if events will be processed
        """
        return self.observer_registry.has_observers()


# Factory functions for easy integration

def get_observer_logger(observer_registry: ObserverRegistry) -> ObserverLogger:
    """Get an ObserverLogger instance.
    
    Factory function for creating observer loggers with consistent configuration.
    
    Args:
        observer_registry: Registry for event distribution
        
    Returns:
        Configured ObserverLogger instance
    """
    return ObserverLogger(observer_registry)


# Module-level singleton for global access
_global_logger: Optional[ObserverLogger] = None
_global_registry: Optional[ObserverRegistry] = None


def get_global_observer_logger() -> Optional[ObserverLogger]:
    """Get the global ObserverLogger instance.
    
    Returns:
        Global ObserverLogger instance or None if not initialized
    """
    return _global_logger


def initialize_global_observer_logger(observer_registry: ObserverRegistry) -> ObserverLogger:
    """Initialize the global ObserverLogger instance.
    
    Args:
        observer_registry: Registry for event distribution
        
    Returns:
        Initialized global ObserverLogger
    """
    global _global_logger, _global_registry
    
    _global_registry = observer_registry
    _global_logger = ObserverLogger(observer_registry)
    
    if os.environ.get("ECONSIM_DEBUG_OBSERVERS", "0") == "1":
        print("Global ObserverLogger initialized")
    
    return _global_logger


def reset_global_observer_logger() -> None:
    """Reset the global ObserverLogger (for testing)."""
    global _global_logger, _global_registry
    _global_logger = None
    _global_registry = None