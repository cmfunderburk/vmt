"""Observability system for VMT EconSim simulation events.

This module provides the core observability infrastructure for tracking and logging
simulation events without creating circular dependencies. The observer pattern allows
the simulation layer to emit events while remaining decoupled from specific logging
or GUI implementations.

Key components:
- SimulationEvent: Base event class and concrete event types  
- SimulationObserver: Observer protocol for event handling
- ObserverRegistry: Registration and notification system
- ObservabilityConfig: Centralized configuration management

Usage:
    from econsim.observability import AgentModeChangeEvent, ObserverRegistry
    
    registry = ObserverRegistry()
    registry.register(my_observer)
    
    event = AgentModeChangeEvent(
        step=42, timestamp=time.time(), event_type="agent_mode_change",
        agent_id=0, old_mode="idle", new_mode="moving", reason="target_found"
    )
    registry.notify(event)
"""

from .events import SimulationEvent
from .observers import BaseObserver  
from .registry import ObserverRegistry
from .config import ObservabilityConfig
from .observer_logger import (
    ObserverLogger, get_observer_logger, 
    get_global_observer_logger, initialize_global_observer_logger
)
# PHASE 5.2: Serializers directory removed - using raw data architecture

__all__ = [
    # Core events (Phase 5.1 - Only base class preserved for type annotations)
    "SimulationEvent",
    # Core infrastructure
    "BaseObserver", 
    "ObserverRegistry",
    "ObservabilityConfig",
    # Observer-based logging
    "ObserverLogger",
    "get_observer_logger",
    "get_global_observer_logger",
    "initialize_global_observer_logger",
    # Raw data architecture (Phase 5.2 - Serializers removed for 100x performance)
]