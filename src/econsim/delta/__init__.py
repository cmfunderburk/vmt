"""
Comprehensive Delta System for VMT EconSim

This package provides a unified system for recording and playing back all simulation
state changes, serving as a single source of truth for both visual rendering and
economic analysis.

Key Components:
- SimulationDelta: Main container for all state changes at a single step
- VisualDelta: Visual changes for pygame rendering
- Agent events: Movement, mode changes, inventory changes, etc.
- Resource events: Collections, spawns, depletions
- Economic events: Trades, decisions, utility calculations
- System events: Performance metrics, debug information
"""

from .data_structures import (
    SimulationDelta,
    VisualDelta,
    VisualState,
    # Agent events
    AgentMove,
    AgentModeChange,
    InventoryChange,
    TargetChange,
    UtilityChange,
    # Resource events
    ResourceCollection,
    ResourceSpawn,
    ResourceDepletion,
    # Economic events
    TradeEvent,
    TradeIntent,
    EconomicDecision,
    # System events
    PerformanceMetrics,
    DebugEvent,
)
from .serializer import DeltaSerializer, DeltaDebugger
from .recorder import ComprehensiveDeltaRecorder
from .playback_controller import ComprehensivePlaybackController

__all__ = [
    "SimulationDelta",
    "VisualDelta", 
    "VisualState",
    "AgentMove",
    "AgentModeChange",
    "InventoryChange",
    "TargetChange",
    "UtilityChange",
    "ResourceCollection",
    "ResourceSpawn",
    "ResourceDepletion",
    "TradeEvent",
    "TradeIntent",
    "EconomicDecision",
    "PerformanceMetrics",
    "DebugEvent",
    "DeltaSerializer",
    "DeltaDebugger",
    "ComprehensiveDeltaRecorder",
    "ComprehensivePlaybackController",
]
