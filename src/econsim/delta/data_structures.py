"""
Comprehensive Delta Data Structures

Defines all data structures for recording complete simulation state changes.
Each delta represents all changes that occurred during a single simulation step.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any


# === VISUAL DELTA (for pygame rendering) ===

@dataclass(frozen=True)
class VisualDelta:
    """Represents visual changes at a single simulation step."""
    
    step: int
    agent_moves: List[Tuple[int, int, int, int, int]]  # (agent_id, old_x, old_y, new_x, new_y)
    agent_state_changes: List[Tuple[int, bool]]  # (agent_id, is_carrying)
    resource_changes: List[Tuple[int, int, Optional[str]]]  # (x, y, resource_type_or_None)
    
    def is_empty(self) -> bool:
        """Check if this delta has any changes."""
        return (len(self.agent_moves) == 0 and 
                len(self.agent_state_changes) == 0 and 
                len(self.resource_changes) == 0)
    
    def get_summary(self) -> str:
        """Get a human-readable summary of changes."""
        parts = []
        if self.agent_moves:
            parts.append(f"{len(self.agent_moves)} agent moves")
        if self.agent_state_changes:
            parts.append(f"{len(self.agent_state_changes)} state changes")
        if self.resource_changes:
            parts.append(f"{len(self.resource_changes)} resource changes")
        
        if parts:
            return f"Step {self.step}: {', '.join(parts)}"
        else:
            return f"Step {self.step}: No changes"


@dataclass
class VisualState:
    """Current visual state for pygame rendering."""
    
    step: int
    agent_positions: dict[int, Tuple[int, int]]  # agent_id -> (x, y)
    agent_states: dict[int, bool]  # agent_id -> is_carrying
    resource_positions: dict[Tuple[int, int], str]  # (x, y) -> resource_type
    grid_width: int = 20  # Default grid width
    grid_height: int = 20  # Default grid height
    
    def get_agent_list(self) -> List[Tuple[int, int, int, bool]]:
        """Get agents as list of (id, x, y, carrying)."""
        return [
            (agent_id, x, y, self.agent_states.get(agent_id, False))
            for agent_id, (x, y) in self.agent_positions.items()
        ]
    
    def get_resource_list(self) -> List[Tuple[int, int, str]]:
        """Get resources as list of (x, y, resource_type)."""
        return [
            (x, y, resource_type)
            for (x, y), resource_type in self.resource_positions.items()
        ]


# === AGENT EVENTS ===

@dataclass(frozen=True)
class AgentMove:
    """Records agent position changes."""
    agent_id: int
    old_x: int
    old_y: int
    new_x: int
    new_y: int
    reason: str  # "random", "target_seeking", "partner_seeking", etc.


@dataclass(frozen=True)
class AgentModeChange:
    """Records agent mode transitions."""
    agent_id: int
    old_mode: str
    new_mode: str
    reason: str
    utility_before: float
    utility_after: float


@dataclass(frozen=True)
class InventoryChange:
    """Records inventory changes (carrying or home)."""
    agent_id: int
    inventory_type: str  # "carrying" or "home"
    old_inventory: Dict[str, int]
    new_inventory: Dict[str, int]
    change_type: str  # "collect", "deposit", "withdraw", "trade_give", "trade_receive"


@dataclass(frozen=True)
class TargetChange:
    """Records target selection changes."""
    agent_id: int
    old_target: Optional[Tuple[int, int]]
    new_target: Optional[Tuple[int, int]]
    target_type: str  # "resource", "partner", "home", None
    selection_reason: str


@dataclass(frozen=True)
class UtilityChange:
    """Records utility calculations."""
    agent_id: int
    old_utility: float
    new_utility: float
    utility_delta: float
    calculation_context: str  # "mode_change", "collection", "trade", "deposit"


# === RESOURCE EVENTS ===

@dataclass(frozen=True)
class ResourceCollection:
    """Records resource collection events."""
    agent_id: int
    resource_type: str
    position_x: int
    position_y: int
    utility_gained: float


@dataclass(frozen=True)
class ResourceSpawn:
    """Records resource spawn events."""
    resource_type: str
    position_x: int
    position_y: int
    spawn_reason: str  # "respawn", "initial", "trade_drop"


@dataclass(frozen=True)
class ResourceDepletion:
    """Records resource depletion events."""
    resource_type: str
    position_x: int
    position_y: int
    depletion_reason: str  # "collected", "trade_consumed"


# === ECONOMIC EVENTS ===

@dataclass(frozen=True)
class TradeEvent:
    """Records executed trade events."""
    step: int
    seller_id: int
    buyer_id: int
    give_type: str
    take_type: int  # quantity
    trade_location_x: int
    trade_location_y: int
    seller_utility_before: float
    seller_utility_after: float
    buyer_utility_before: float
    buyer_utility_after: float
    trade_success_reason: str


@dataclass(frozen=True)
class TradeIntent:
    """Records trade intent events."""
    agent_id: int
    partner_id: int
    proposed_give: Dict[str, int]
    proposed_take: Dict[str, int]
    intent_type: str  # "proposal", "counter_proposal", "acceptance", "rejection"
    utility_estimate: float


@dataclass(frozen=True)
class EconomicDecision:
    """Records economic decision-making events."""
    agent_id: int
    decision_type: str  # "resource_selection", "trade_proposal", "mode_selection", "target_selection"
    decision_context: str
    alternatives_considered: List[Dict[str, Any]]
    chosen_alternative: Dict[str, Any]
    utility_before: float
    utility_after: float
    decision_time_ms: float
    position_context: Tuple[int, int]


# === SYSTEM EVENTS ===

@dataclass(frozen=True)
class PerformanceMetrics:
    """Records performance metrics for a simulation step."""
    step_duration_ms: float
    agents_processed: int
    resources_processed: int
    trades_attempted: int
    trades_executed: int
    memory_usage_mb: float


@dataclass(frozen=True)
class DebugEvent:
    """Records debug logging events."""
    event_type: str
    message: str
    agent_id: Optional[int]
    position: Optional[Tuple[int, int]]
    severity: str  # "debug", "info", "warning", "error"


# === MAIN DELTA CONTAINER ===

@dataclass(frozen=True)
class SimulationDelta:
    """Complete record of all state changes at a single simulation step."""
    
    # Step identification
    step: int
    visual_changes: VisualDelta  # Required field must come before optional fields
    timestamp: float = field(default_factory=time.time)
    
    # === AGENT STATE CHANGES ===
    agent_moves: List[AgentMove] = field(default_factory=list)
    agent_mode_changes: List[AgentModeChange] = field(default_factory=list)
    agent_inventory_changes: List[InventoryChange] = field(default_factory=list)
    agent_target_changes: List[TargetChange] = field(default_factory=list)
    agent_utility_changes: List[UtilityChange] = field(default_factory=list)
    
    # === RESOURCE STATE CHANGES ===
    resource_collections: List[ResourceCollection] = field(default_factory=list)
    resource_spawns: List[ResourceSpawn] = field(default_factory=list)
    resource_depletions: List[ResourceDepletion] = field(default_factory=list)
    
    # === ECONOMIC EVENTS ===
    trade_events: List[TradeEvent] = field(default_factory=list)
    trade_intents: List[TradeIntent] = field(default_factory=list)
    economic_decisions: List[EconomicDecision] = field(default_factory=list)
    
    # === SYSTEM EVENTS ===
    performance_metrics: Optional[PerformanceMetrics] = None
    debug_events: List[DebugEvent] = field(default_factory=list)
    
    def is_empty(self) -> bool:
        """Check if this delta has any changes."""
        return (self.visual_changes.is_empty() and
                len(self.agent_moves) == 0 and
                len(self.agent_mode_changes) == 0 and
                len(self.agent_inventory_changes) == 0 and
                len(self.agent_target_changes) == 0 and
                len(self.agent_utility_changes) == 0 and
                len(self.resource_collections) == 0 and
                len(self.resource_spawns) == 0 and
                len(self.resource_depletions) == 0 and
                len(self.trade_events) == 0 and
                len(self.trade_intents) == 0 and
                len(self.economic_decisions) == 0 and
                len(self.debug_events) == 0)
    
    def get_summary(self) -> str:
        """Get a human-readable summary of all changes."""
        parts = []
        
        # Visual changes
        if not self.visual_changes.is_empty():
            parts.append(self.visual_changes.get_summary())
        
        # Agent changes
        if self.agent_moves:
            parts.append(f"{len(self.agent_moves)} agent moves")
        if self.agent_mode_changes:
            parts.append(f"{len(self.agent_mode_changes)} mode changes")
        if self.agent_inventory_changes:
            parts.append(f"{len(self.agent_inventory_changes)} inventory changes")
        if self.agent_target_changes:
            parts.append(f"{len(self.agent_target_changes)} target changes")
        if self.agent_utility_changes:
            parts.append(f"{len(self.agent_utility_changes)} utility changes")
        
        # Resource changes
        if self.resource_collections:
            parts.append(f"{len(self.resource_collections)} resource collections")
        if self.resource_spawns:
            parts.append(f"{len(self.resource_spawns)} resource spawns")
        if self.resource_depletions:
            parts.append(f"{len(self.resource_depletions)} resource depletions")
        
        # Economic events
        if self.trade_events:
            parts.append(f"{len(self.trade_events)} trades executed")
        if self.trade_intents:
            parts.append(f"{len(self.trade_intents)} trade intents")
        if self.economic_decisions:
            parts.append(f"{len(self.economic_decisions)} economic decisions")
        
        # System events
        if self.debug_events:
            parts.append(f"{len(self.debug_events)} debug events")
        
        if parts:
            return f"Step {self.step}: {', '.join(parts)}"
        else:
            return f"Step {self.step}: No changes"
    
    def get_event_counts(self) -> Dict[str, int]:
        """Get counts of different event types."""
        return {
            "agent_moves": len(self.agent_moves),
            "agent_mode_changes": len(self.agent_mode_changes),
            "agent_inventory_changes": len(self.agent_inventory_changes),
            "agent_target_changes": len(self.agent_target_changes),
            "agent_utility_changes": len(self.agent_utility_changes),
            "resource_collections": len(self.resource_collections),
            "resource_spawns": len(self.resource_spawns),
            "resource_depletions": len(self.resource_depletions),
            "trade_events": len(self.trade_events),
            "trade_intents": len(self.trade_intents),
            "economic_decisions": len(self.economic_decisions),
            "debug_events": len(self.debug_events),
        }
