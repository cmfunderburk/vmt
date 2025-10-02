# Agent.py Refactoring Implementation Plan

**File**: `src/econsim/simulation/agent.py`  
**Date**: October 2, 2025  
**Implementation Strategy**: Phased extraction with determinism preservation  
**Target**: Reduce 972-line monolith to maintainable component architecture

## 🎯 Implementation Overview

This plan implements the refactoring strategy through **3 phases** over **8-13 weeks**, with each phase delivering working, tested code that maintains full backward compatibility and deterministic behavior.

### Success Criteria
- ✅ All 210+ existing tests pass without modification
- ✅ Performance within 2% of baseline (≥999.3 steps/sec mean)
- ✅ Determinism hash stability maintained
- ✅ Agent class reduced from 972 → ~400-500 lines
- ✅ Component test coverage >90%

## 📋 Phase 1: Safe Extractions (2-3 weeks)

### 1.1 AgentMovement Component Extraction

**Timeline**: Week 1-2  
**Risk**: Low  
**Lines Reduced**: ~50

#### Step 1.1.1: Create Movement Component Structure
```bash
# Create new component file
touch src/econsim/simulation/components/movement.py
touch src/econsim/simulation/components/__init__.py
```

**File**: `src/econsim/simulation/components/movement.py`
```python
"""Agent movement component for spatial navigation and pathfinding."""

from __future__ import annotations
import random
from typing import TYPE_CHECKING
from ..grid import Grid

if TYPE_CHECKING:
    pass

Position = tuple[int, int]

class AgentMovement:
    """Handles all agent movement operations with deterministic pathfinding."""
    
    def __init__(self, agent_id: int):
        self.agent_id = agent_id
    
    def move_random(self, current_pos: Position, grid: Grid, rng: random.Random) -> Position:
        """Move one step randomly in 4-neighborhood or stay put."""
        x, y = current_pos
        moves = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]
        dx, dy = rng.choice(moves)
        nx, ny = x + dx, y + dy
        if 0 <= nx < grid.width and 0 <= ny < grid.height:
            return (nx, ny)
        return current_pos
    
    def move_toward_target(self, current_pos: Position, target: Position) -> Position:
        """Move one step toward target using greedy pathfinding."""
        x, y = current_pos
        tx, ty = target
        
        if (x, y) == (tx, ty):
            return current_pos
            
        dx = tx - x
        dy = ty - y
        
        # Greedy: horizontal priority if abs(dx) > abs(dy) else vertical
        if abs(dx) > abs(dy):
            new_x = x + (1 if dx > 0 else -1)
            return (new_x, y)
        elif dy != 0:
            new_y = y + (1 if dy > 0 else -1)
            return (x, new_y)
        else:
            return current_pos
    
    def move_toward_meeting_point(self, current_pos: Position, meeting_point: Position) -> Position:
        """Move one step toward established meeting point."""
        return self.move_toward_target(current_pos, meeting_point)
```

#### Step 1.1.2: Integration with Agent Class
**File**: `src/econsim/simulation/agent.py`

Add import and component initialization:
```python
from .components.movement import AgentMovement

class Agent:
    # Add to __post_init__
    def __post_init__(self) -> None:
        # ... existing initialization ...
        self._movement = AgentMovement(self.id)
```

Replace existing movement methods:
```python
def move_random(self, grid: Grid, rng: random.Random) -> None:
    """Move one step randomly in 4-neighborhood or stay put."""
    new_pos = self._movement.move_random((self.x, self.y), grid, rng)
    self.x, self.y = new_pos

def move_toward_meeting_point(self, grid: "Grid") -> None:
    """Move one step toward the established meeting point."""
    if self.meeting_point is None:
        return
    
    new_pos = self._movement.move_toward_target((self.x, self.y), self.meeting_point)
    self.x, self.y = new_pos
```

Update `step_decision()` movement logic:
```python
# Replace movement section in step_decision()
if self.target is not None and (self.x, self.y) != self.target:
    old_pos = (self.x, self.y)
    new_pos = self._movement.move_toward_target(old_pos, self.target)
    self.x, self.y = new_pos
    # ... existing observer logging ...
```

#### Step 1.1.3: Testing and Validation
```bash
# Run full test suite
pytest -q

# Run performance baseline
make perf

# Check determinism hash
python -c "
import json
with open('baselines/determinism_hashes.json') as f:
    baseline = json.load(f)
# Run determinism test and compare
"
```

**Validation Checklist**:
- [ ] All 210+ tests pass
- [ ] Performance within 2% of baseline
- [ ] Determinism hash unchanged
- [ ] Movement component unit tests pass

### 1.2 Observer Event Consolidation

**Timeline**: Week 2  
**Risk**: Low  
**Lines Reduced**: ~30

#### Step 1.2.1: Create AgentEventEmitter
**File**: `src/econsim/simulation/components/event_emitter.py`
```python
"""Centralized event emission for agent actions."""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...observability.registry import ObserverRegistry
    from ...observability.event_buffer import StepEventBuffer

class AgentEventEmitter:
    """Handles all agent event emission with consistent error handling."""
    
    def __init__(self, agent_id: int):
        self.agent_id = agent_id
    
    def emit_mode_change(
        self, 
        old_mode: str, 
        new_mode: str, 
        reason: str,
        step_number: int,
        observer_registry: Optional['ObserverRegistry'] = None,
        event_buffer: Optional['StepEventBuffer'] = None
    ) -> None:
        """Emit agent mode change event with fallback handling."""
        if event_buffer is not None:
            event_buffer.queue_mode_change(self.agent_id, old_mode, new_mode, reason)
        elif observer_registry:
            from ...observability.events import AgentModeChangeEvent
            event = AgentModeChangeEvent.create(
                step=step_number,
                agent_id=self.agent_id,
                old_mode=old_mode,
                new_mode=new_mode,
                reason=reason
            )
            observer_registry.notify(event)
    
    def emit_resource_collection(
        self,
        x: int, 
        y: int, 
        resource_type: str,
        step: int,
        observer_registry: Optional['ObserverRegistry'] = None
    ) -> None:
        """Emit resource collection event."""
        if observer_registry:
            from ...observability.events import ResourceCollectionEvent
            event = ResourceCollectionEvent.create(
                step=step,
                agent_id=self.agent_id,
                x=x,
                y=y,
                resource_type=resource_type,
                amount_collected=1
            )
            observer_registry.notify(event)
    
    def emit_movement(self, old_pos: tuple[int, int], new_pos: tuple[int, int], step: int) -> None:
        """Emit movement event via global observer logger."""
        try:
            from ...observability.observer_logger import get_global_observer_logger
            logger = get_global_observer_logger()
            if logger:
                message = f"Agent {self.agent_id} moved from {old_pos} to {new_pos}"
                logger.log_spatial(message, step)
        except Exception:
            pass  # Don't break simulation if logging fails
```

#### Step 1.2.2: Replace Scattered Event Emission
Update `Agent` class to use centralized emitter:
```python
class Agent:
    def __post_init__(self) -> None:
        # ... existing initialization ...
        self._event_emitter = AgentEventEmitter(self.id)
    
    def _set_mode(self, new_mode: AgentMode, reason: str = "", observer_registry: Optional['ObserverRegistry'] = None, step_number: int = 0, event_buffer: Optional['StepEventBuffer'] = None) -> None:
        """Centralized mode setter that emits AgentModeChangeEvent."""
        if self.mode == new_mode:
            return
            
        old_mode = self.mode
        self._debug_log_mode_change(old_mode, new_mode, reason)
        self.mode = new_mode
        
        self._event_emitter.emit_mode_change(
            old_mode.value, new_mode.value, reason, step_number, observer_registry, event_buffer
        )
```

### 1.3 Simple Utility Method Extractions

**Timeline**: Week 2-3  
**Risk**: Very Low  
**Lines Reduced**: ~20

#### Step 1.3.1: Extract Mathematical Utilities
**File**: `src/econsim/simulation/components/utils.py`
```python
"""Utility functions for agent calculations."""

def manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """Calculate Manhattan distance between two points."""
    return abs(x1 - x2) + abs(y1 - y2)

def calculate_meeting_point(pos1: tuple[int, int], pos2: tuple[int, int]) -> tuple[int, int]:
    """Calculate midpoint between two positions."""
    x1, y1 = pos1
    x2, y2 = pos2
    return (x1 + x2) // 2, (y1 + y2) // 2
```

#### Step 1.3.2: Update Agent to Use Utilities
```python
from .components.utils import manhattan_distance, calculate_meeting_point

class Agent:
    def _manhattan(self, x1: int, y1: int, x2: int, y2: int) -> int:
        """Calculate Manhattan distance between two points."""
        return manhattan_distance(x1, y1, x2, y2)
    
    def calculate_meeting_point(self, other_agent: "Agent") -> Position:
        """Calculate the midpoint between this agent and another agent for meeting."""
        return calculate_meeting_point((self.x, self.y), (other_agent.x, other_agent.y))
```

## 📋 Phase 2: Core Logic Refactoring (4-6 weeks)

### 2.1 AgentInventory Component Extraction

**Timeline**: Week 4-5  
**Risk**: Medium  
**Lines Reduced**: ~80

#### Step 2.1.1: Create Inventory Component
**File**: `src/econsim/simulation/components/inventory.py`
```python
"""Agent inventory management with dual storage system."""

from __future__ import annotations
from typing import Dict
from ...preferences.base import Preference
from ..constants import EPSILON_UTILITY

class AgentInventory:
    """Manages agent's carrying and home inventory with utility calculations."""
    
    def __init__(self, preference: Preference):
        self.carrying: Dict[str, int] = {"good1": 0, "good2": 0}
        self.home_inventory: Dict[str, int] = {"good1": 0, "good2": 0}
        self.preference = preference
    
    @property
    def inventory(self) -> Dict[str, int]:
        """Backward compatibility alias for carrying inventory."""
        return self.carrying
    
    def carrying_total(self) -> int:
        """Return total number of goods currently being carried."""
        return sum(self.carrying.values())
    
    def current_bundle(self) -> tuple[float, float]:
        """Get current bundle (good1, good2) from total wealth (carrying + home inventory)."""
        total_good1 = float(self.carrying["good1"] + self.home_inventory["good1"])
        total_good2 = float(self.carrying["good2"] + self.home_inventory["good2"])
        return total_good1, total_good2
    
    def current_utility(self) -> float:
        """Calculate current utility from total wealth (carrying + home inventory)."""
        raw_bundle = self.current_bundle()
        # Apply epsilon augmentation for consistent evaluation
        if raw_bundle[0] == 0.0 or raw_bundle[1] == 0.0:
            bundle = (raw_bundle[0] + EPSILON_UTILITY, raw_bundle[1] + EPSILON_UTILITY)
        else:
            bundle = raw_bundle
        return self.preference.utility(bundle)
    
    def deposit_all(self) -> bool:
        """Move all carried goods into home inventory. Returns True if any deposited."""
        moved = False
        for k, v in list(self.carrying.items()):
            if v > 0:
                self.home_inventory[k] += v
                self.carrying[k] = 0
                moved = True
        return moved
    
    def withdraw_all(self) -> bool:
        """Move all home inventory goods into carrying. Returns True if withdrawn."""
        moved = False
        for k, v in list(self.home_inventory.items()):
            if v > 0:
                self.carrying[k] += v
                self.home_inventory[k] = 0
                moved = True
        return moved
    
    def total_inventory(self) -> Dict[str, int]:
        """Return combined carrying + home inventory without mutation."""
        if not self.carrying and not self.home_inventory:
            return {}
        combined: Dict[str, int] = dict(self.home_inventory)
        for k, v in self.carrying.items():
            if v:
                combined[k] = combined.get(k, 0) + v
        return combined
    
    def collect_resource(self, resource_type: str) -> None:
        """Add resource to carrying inventory."""
        if resource_type == "A":
            self.carrying["good1"] += 1
        elif resource_type == "B":
            self.carrying["good2"] += 1
    
    def serialize(self) -> Dict[str, any]:
        """Serialize inventory state."""
        return {
            "carrying": dict(self.carrying),
            "home_inventory": dict(self.home_inventory),
            "inventory": dict(self.carrying),  # legacy alias
        }
```

#### Step 2.1.2: Integration with Agent Class
```python
from .components.inventory import AgentInventory

class Agent:
    def __post_init__(self) -> None:
        # ... existing initialization ...
        self._inventory = AgentInventory(self.preference)
        # Expose inventory fields for backward compatibility
        object.__setattr__(self, "carrying", self._inventory.carrying)
        object.__setattr__(self, "home_inventory", self._inventory.home_inventory)
        object.__setattr__(self, "inventory", self._inventory.inventory)
    
    def carrying_total(self) -> int:
        """Return total number of goods currently being carried."""
        return self._inventory.carrying_total()
    
    def current_utility(self) -> float:
        """Calculate current utility from total wealth (carrying + home inventory)."""
        return self._inventory.current_utility()
    
    def _current_bundle(self) -> tuple[float, float]:
        """Get current bundle (good1, good2) from total wealth (carrying + home inventory)."""
        return self._inventory.current_bundle()
    
    def deposit(self) -> bool:
        """Move all carried goods into home inventory. Returns True if any deposited."""
        return self._inventory.deposit_all()
    
    def withdraw_all(self) -> bool:
        """Move all home inventory goods into carrying. Returns True if withdrawn."""
        return self._inventory.withdraw_all()
    
    def total_inventory(self) -> dict[str, int]:
        """Return combined carrying + home inventory without mutation."""
        return self._inventory.total_inventory()
```

#### Step 2.1.3: Update Resource Collection
```python
def collect(self, grid: Grid, step: int = -1, observer_registry: Optional['ObserverRegistry'] = None) -> bool:
    """Collect resource at current position if foraging enabled."""
    import os
    
    forage_enabled = os.environ.get("ECONSIM_FORAGE_ENABLED", "1") == "1"
    if not forage_enabled:
        return False
        
    rtype = grid.take_resource_type(self.x, self.y)
    if rtype is None:
        return False
    
    # Use inventory component for collection
    self._inventory.collect_resource(rtype)
    
    # Emit events
    self._event_emitter.emit_resource_collection(self.x, self.y, rtype, step, observer_registry)
    
    # Observer logger tracking
    if step >= 0:
        # ... existing observer logging logic ...
    
    return True
```

### 2.2 TradingPartner Component Extraction

**Timeline**: Week 5-6  
**Risk**: Medium  
**Lines Reduced**: ~100

#### Step 2.2.1: Create Trading Partner Component
**File**: `src/econsim/simulation/components/trading_partner.py`
```python
"""Agent trading partner management and coordination."""

from __future__ import annotations
from typing import Optional, Dict, List, Tuple, TYPE_CHECKING
from ..constants import default_PERCEPTION_RADIUS
from .utils import manhattan_distance, calculate_meeting_point

if TYPE_CHECKING:
    from ..agent import Agent

Position = tuple[int, int]

class TradingPartner:
    """Manages trading partner relationships, cooldowns, and meeting coordination."""
    
    def __init__(self, agent_id: int):
        self.agent_id = agent_id
        self.trade_partner_id: Optional[int] = None
        self.meeting_point: Optional[Position] = None
        self.is_trading: bool = False
        self.trade_cooldown: int = 0
        self.partner_cooldowns: Dict[int, int] = {}
        
        # Stagnation tracking
        self.last_trade_mode_utility: float = 0.0
        self.trade_stagnation_steps: int = 0
    
    def find_nearby_agents(self, agent_pos: Position, all_agents: List["Agent"]) -> List[Tuple["Agent", int]]:
        """Find other agents within perception radius for potential trading."""
        candidates = []
        for other_agent in all_agents:
            if other_agent.id == self.agent_id:  # Skip self
                continue
                
            distance = manhattan_distance(agent_pos[0], agent_pos[1], other_agent.x, other_agent.y)
            if distance <= default_PERCEPTION_RADIUS:
                candidates.append((other_agent, distance))
        
        # Sort by distance first, then by position for deterministic tiebreaking
        candidates.sort(key=lambda x: (x[1], x[0].x, x[0].y))
        return candidates
    
    def pair_with_agent(self, agent_pos: Position, other_agent: "Agent") -> None:
        """Establish mutual pairing with another agent for trading."""
        meeting_point = calculate_meeting_point(agent_pos, (other_agent.x, other_agent.y))
        
        self.trade_partner_id = other_agent.id
        self.meeting_point = meeting_point
        
        # Set up mutual pairing on other agent
        other_partner = other_agent._trading_partner
        other_partner.trade_partner_id = self.agent_id
        other_partner.meeting_point = meeting_point
    
    def clear_trade_partner(self) -> None:
        """Clear trade partner state without setting cooldowns."""
        self.trade_partner_id = None
        self.meeting_point = None
        self.is_trading = False
        self.trade_cooldown = 3  # General cooldown for immediate re-pairing
    
    def end_trading_session(self, partner: "Agent") -> None:
        """End trading session with partner and set per-partner cooldowns."""
        # Set per-partner cooldown to prevent immediate re-pairing
        self.partner_cooldowns[partner.id] = 20
        partner._trading_partner.partner_cooldowns[self.agent_id] = 20
        
        # Clear trade partner state for both agents
        self.clear_trade_partner()
        partner._trading_partner.clear_trade_partner()
    
    def update_partner_cooldowns(self) -> None:
        """Decrement all partner-specific cooldowns by 1."""
        for partner_id in list(self.partner_cooldowns.keys()):
            self.partner_cooldowns[partner_id] -= 1
            if self.partner_cooldowns[partner_id] <= 0:
                del self.partner_cooldowns[partner_id]
    
    def can_trade_with_partner(self, partner_id: int) -> bool:
        """Check if this agent can trade with a specific partner (no active cooldown)."""
        return partner_id not in self.partner_cooldowns
    
    def is_colocated_with(self, agent_pos: Position, other_agent: "Agent") -> bool:
        """Check if agent is on the same tile as another agent."""
        return agent_pos[0] == other_agent.x and agent_pos[1] == other_agent.y
```

#### Step 2.2.2: Integration with Agent Class
```python
from .components.trading_partner import TradingPartner

class Agent:
    def __post_init__(self) -> None:
        # ... existing initialization ...
        self._trading_partner = TradingPartner(self.id)
        
        # Expose trading fields for backward compatibility
        object.__setattr__(self, "trade_partner_id", self._trading_partner.trade_partner_id)
        object.__setattr__(self, "meeting_point", self._trading_partner.meeting_point)
        object.__setattr__(self, "is_trading", self._trading_partner.is_trading)
        object.__setattr__(self, "trade_cooldown", self._trading_partner.trade_cooldown)
        object.__setattr__(self, "partner_cooldowns", self._trading_partner.partner_cooldowns)
        object.__setattr__(self, "last_trade_mode_utility", self._trading_partner.last_trade_mode_utility)
        object.__setattr__(self, "trade_stagnation_steps", self._trading_partner.trade_stagnation_steps)
    
    def find_nearby_agents(self, all_agents: list["Agent"]) -> list[tuple["Agent", int]]:
        """Find other agents within perception radius for potential trading."""
        return self._trading_partner.find_nearby_agents((self.x, self.y), all_agents)
    
    def pair_with_agent(self, other_agent: "Agent") -> None:
        """Establish mutual pairing with another agent for trading."""
        self._trading_partner.pair_with_agent((self.x, self.y), other_agent)
        # Update exposed fields
        object.__setattr__(self, "trade_partner_id", self._trading_partner.trade_partner_id)
        object.__setattr__(self, "meeting_point", self._trading_partner.meeting_point)
    
    # ... similar updates for other trading methods ...
```

### 2.3 Target Selection Strategy Extraction

**Timeline**: Week 6-7  
**Risk**: High  
**Lines Reduced**: ~150

#### Step 2.3.1: Create Strategy Base Classes
**File**: `src/econsim/simulation/components/target_selection/__init__.py`
**File**: `src/econsim/simulation/components/target_selection/base.py`
```python
"""Base classes for target selection strategies."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ...grid import Grid
    from ...agent import Agent
    from ....preferences.base import Preference

Position = tuple[int, int]

class TargetSelectionStrategy(ABC):
    """Base class for agent target selection strategies."""
    
    @abstractmethod
    def select_target(
        self,
        agent_pos: Position,
        current_bundle: Tuple[float, float],
        preference: 'Preference',
        grid: 'Grid',
        **kwargs
    ) -> Optional[Position]:
        """Select the best target position for the agent."""
        pass

class ResourceTargetStrategy(TargetSelectionStrategy):
    """Strategy for selecting resource targets based on utility maximization."""
    
    def select_target(
        self,
        agent_pos: Position,
        current_bundle: Tuple[float, float],
        preference: 'Preference',
        grid: 'Grid',
        **kwargs
    ) -> Optional[Position]:
        """Find highest utility resource within perception radius."""
        from .resource_selection import ResourceSelector
        selector = ResourceSelector()
        pos, delta_u, key = selector.compute_best_resource_candidate(
            agent_pos, current_bundle, preference, grid
        )
        return pos

class LeontieProspectingStrategy(TargetSelectionStrategy):
    """Strategy for Leontief agents to find complementary resource pairs."""
    
    def select_target(
        self,
        agent_pos: Position,
        current_bundle: Tuple[float, float],
        preference: 'Preference',
        grid: 'Grid',
        **kwargs
    ) -> Optional[Position]:
        """Find best prospecting target for complementary bundle building."""
        if getattr(preference, 'TYPE_NAME', '') != 'leontief':
            return None
            
        from .leontief_prospecting import LeontieProspector
        prospector = LeontieProspector()
        return prospector.find_prospect_target(agent_pos, current_bundle, grid, preference)
```

#### Step 2.3.2: Extract Leontief Prospecting Algorithm
**File**: `src/econsim/simulation/components/target_selection/leontief_prospecting.py`
```python
"""Optimized Leontief prospecting algorithm for complementary resource collection."""

from __future__ import annotations
from typing import Dict, List, Tuple, Optional, TYPE_CHECKING
from ...constants import EPSILON_UTILITY, default_PERCEPTION_RADIUS
from ..utils import manhattan_distance

if TYPE_CHECKING:
    from ...grid import Grid
    from ....preferences.base import Preference

Position = tuple[int, int]

# A→good1, B→good2
RESOURCE_TYPE_TO_GOOD = {
    "A": "good1",
    "B": "good2",
}

class LeontieProspector:
    """Handles Leontief agent prospecting with optimized resource caching."""
    
    def find_prospect_target(
        self,
        agent_pos: Position,
        raw_bundle: Tuple[float, float],
        grid: 'Grid',
        preference: 'Preference'
    ) -> Optional[Position]:
        """Find best prospecting target using cached resource optimization."""
        best_prospect: Optional[Tuple[float, int, int, int]] = None  # (-score, dist, x, y)
        best_prospect_pos: Optional[Position] = None
        max_dist = default_PERCEPTION_RADIUS
        
        # Build resource cache for performance optimization
        resource_cache, position_to_type_cache = self._build_resource_cache(
            agent_pos, grid, max_dist
        )
        
        # Process each nearby resource position to find prospects
        for rtype, positions in resource_cache.items():
            for rx, ry in positions:
                dist_to_resource = manhattan_distance(agent_pos[0], agent_pos[1], rx, ry)
                
                good = RESOURCE_TYPE_TO_GOOD.get(rtype)
                if not good:
                    continue
                    
                prospect_score = self._calculate_prospect_score_cached(
                    (rx, ry), rtype, resource_cache, position_to_type_cache, 
                    raw_bundle, max_dist, preference
                )
                
                if prospect_score > 0.0:
                    key = (-prospect_score, dist_to_resource, rx, ry)
                    if best_prospect is None or key < best_prospect:
                        best_prospect = key
                        best_prospect_pos = (rx, ry)
        
        return best_prospect_pos
    
    def _build_resource_cache(
        self, 
        agent_pos: Position, 
        grid: 'Grid', 
        max_dist: int
    ) -> Tuple[Dict[str, List[Tuple[int, int]]], Dict[Tuple[int, int], str]]:
        """Build optimized resource cache for nearby resources."""
        resource_cache: Dict[str, List[Tuple[int, int]]] = {}
        position_to_type_cache: Dict[Tuple[int, int], str] = {}
        iterator = getattr(grid, "iter_resources_sorted", grid.iter_resources)()
        
        for rx, ry, rtype in iterator:
            dist_to_resource = manhattan_distance(agent_pos[0], agent_pos[1], rx, ry)
            if dist_to_resource > max_dist:
                continue
                
            if rtype not in resource_cache:
                resource_cache[rtype] = []
            resource_cache[rtype].append((rx, ry))
            position_to_type_cache[(rx, ry)] = rtype
        
        return resource_cache, position_to_type_cache
    
    # ... rest of prospecting implementation methods ...
```

## 📋 Phase 3: Advanced Patterns (2-4 weeks)

### 3.1 Mode State Machine Implementation

**Timeline**: Week 8-9  
**Risk**: Medium-High  
**Lines Reduced**: ~60

#### Step 3.1.1: Create Mode State Machine
**File**: `src/econsim/simulation/components/mode_state_machine.py`
```python
"""Agent mode state machine with explicit transitions and validation."""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from ..agent import AgentMode
from .event_emitter import AgentEventEmitter

if TYPE_CHECKING:
    from ...observability.registry import ObserverRegistry
    from ...observability.event_buffer import StepEventBuffer

class AgentModeStateMachine:
    """Manages agent mode transitions with validation and event emission."""
    
    def __init__(self, agent_id: int, initial_mode: AgentMode = AgentMode.FORAGE):
        self.agent_id = agent_id
        self.current_mode = initial_mode
        self._event_emitter = AgentEventEmitter(agent_id)
    
    def transition_to(
        self, 
        new_mode: AgentMode, 
        reason: str = "",
        observer_registry: Optional['ObserverRegistry'] = None,
        step_number: int = 0,
        event_buffer: Optional['StepEventBuffer'] = None
    ) -> bool:
        """Attempt mode transition with validation."""
        if not self._is_valid_transition(self.current_mode, new_mode):
            return False
            
        if self.current_mode == new_mode:
            return True  # No-op but valid
            
        old_mode = self.current_mode
        self.current_mode = new_mode
        
        self._event_emitter.emit_mode_change(
            old_mode.value, new_mode.value, reason, step_number, observer_registry, event_buffer
        )
        return True
    
    def _is_valid_transition(self, from_mode: AgentMode, to_mode: AgentMode) -> bool:
        """Validate if transition is allowed."""
        # Define valid transitions
        valid_transitions = {
            AgentMode.FORAGE: [AgentMode.RETURN_HOME, AgentMode.IDLE, AgentMode.MOVE_TO_PARTNER],
            AgentMode.RETURN_HOME: [AgentMode.FORAGE, AgentMode.IDLE],
            AgentMode.IDLE: [AgentMode.FORAGE, AgentMode.MOVE_TO_PARTNER, AgentMode.RETURN_HOME],
            AgentMode.MOVE_TO_PARTNER: [AgentMode.IDLE, AgentMode.FORAGE, AgentMode.RETURN_HOME]
        }
        
        return to_mode in valid_transitions.get(from_mode, [])
```

### 3.2 Command Pattern Implementation

**Timeline**: Week 9-10  
**Risk**: Medium  
**Lines Reduced**: ~40

#### Step 3.2.1: Create Command Base Classes
**File**: `src/econsim/simulation/components/commands/__init__.py`
**File**: `src/econsim/simulation/components/commands/base.py`
```python
"""Command pattern implementation for agent actions."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ...agent import Agent
    from ...grid import Grid

class AgentCommand(ABC):
    """Base class for agent action commands."""
    
    @abstractmethod
    def execute(self, agent: 'Agent', grid: 'Grid', **kwargs) -> Any:
        """Execute the command and return result."""
        pass
    
    @abstractmethod
    def can_execute(self, agent: 'Agent', grid: 'Grid', **kwargs) -> bool:
        """Check if command can be executed."""
        pass

class SelectTargetCommand(AgentCommand):
    """Command to select agent movement target."""
    
    def can_execute(self, agent: 'Agent', grid: 'Grid', **kwargs) -> bool:
        return agent.target is None or agent.mode not in (agent.AgentMode.FORAGE, agent.AgentMode.MOVE_TO_PARTNER)
    
    def execute(self, agent: 'Agent', grid: 'Grid', **kwargs) -> None:
        observer_registry = kwargs.get('observer_registry')
        step_number = kwargs.get('step_number', 0)
        agent.select_target(grid, observer_registry, step_number)

class MoveTowardTargetCommand(AgentCommand):
    """Command to move agent toward current target."""
    
    def can_execute(self, agent: 'Agent', grid: 'Grid', **kwargs) -> bool:
        return agent.target is not None and (agent.x, agent.y) != agent.target
    
    def execute(self, agent: 'Agent', grid: 'Grid', **kwargs) -> tuple[int, int]:
        old_pos = (agent.x, agent.y)
        new_pos = agent._movement.move_toward_target(old_pos, agent.target)
        agent.x, agent.y = new_pos
        return old_pos, new_pos
```

## 🧪 Testing Strategy Implementation

### Continuous Testing Framework

#### Test Structure
```
tests/
├── unit/
│   ├── components/
│   │   ├── test_movement.py
│   │   ├── test_inventory.py
│   │   ├── test_trading_partner.py
│   │   ├── test_target_selection/
│   │   │   ├── test_resource_selection.py
│   │   │   ├── test_leontief_prospecting.py
│   │   │   └── test_unified_selection.py
│   │   ├── test_mode_state_machine.py
│   │   └── test_commands.py
│   └── test_agent_integration.py
├── integration/
│   ├── test_agent_refactor_compatibility.py
│   └── test_performance_regression.py
└── regression/
    ├── test_determinism_preservation.py
    └── test_behavioral_equivalence.py
```

#### Key Test Implementation

**File**: `tests/unit/components/test_movement.py`
```python
"""Unit tests for AgentMovement component."""

import pytest
import random
from unittest.mock import Mock
from src.econsim.simulation.components.movement import AgentMovement

class TestAgentMovement:
    def test_move_random_within_bounds(self):
        movement = AgentMovement(agent_id=1)
        grid = Mock()
        grid.width = 10
        grid.height = 10
        rng = random.Random(42)  # Deterministic for testing
        
        pos = movement.move_random((5, 5), grid, rng)
        assert 0 <= pos[0] < 10
        assert 0 <= pos[1] < 10
    
    def test_move_toward_target_horizontal_priority(self):
        movement = AgentMovement(agent_id=1)
        
        # Target is further horizontally
        pos = movement.move_toward_target((2, 2), (5, 3))
        assert pos == (3, 2)  # Move horizontally first
    
    def test_move_toward_target_vertical_when_closer(self):
        movement = AgentMovement(agent_id=1)
        
        # Target is further vertically
        pos = movement.move_toward_target((2, 2), (3, 5))
        assert pos == (2, 3)  # Move vertically
    
    def test_deterministic_movement_sequence(self):
        """Test that movement sequence is deterministic."""
        movement = AgentMovement(agent_id=1)
        grid = Mock()
        grid.width = 10
        grid.height = 10
        
        # Same seed should produce same sequence
        rng1 = random.Random(12345)
        rng2 = random.Random(12345)
        
        pos1 = (5, 5)
        pos2 = (5, 5)
        
        for _ in range(10):
            pos1 = movement.move_random(pos1, grid, rng1)
            pos2 = movement.move_random(pos2, grid, rng2)
            assert pos1 == pos2
```

**File**: `tests/regression/test_determinism_preservation.py`
```python
"""Regression tests to ensure determinism is preserved during refactoring."""

import pytest
import json
from src.econsim.simulation.config import SimConfig
from src.econsim.simulation.world import Simulation

class TestDeterminismPreservation:
    def test_refactored_agent_determinism_hash(self):
        """Test that refactored agent produces same determinism hash as baseline."""
        # Load baseline hash
        with open('baselines/determinism_hashes.json') as f:
            baseline_hashes = json.load(f)
        
        # Run same scenarios with refactored agent
        for scenario_name, expected_hash in baseline_hashes.items():
            config = self._get_scenario_config(scenario_name)
            sim = Simulation.from_config(config)
            
            # Run simulation
            for _ in range(100):  # Standard test duration
                sim.step()
            
            # Compare hash
            actual_hash = sim.get_determinism_hash()
            assert actual_hash == expected_hash, f"Determinism broken for {scenario_name}"
    
    def _get_scenario_config(self, scenario_name: str) -> SimConfig:
        """Get configuration for named scenario."""
        # Implementation depends on scenario definitions
        pass
```

## 📊 Success Metrics and Validation

### Automated Validation Pipeline

#### Pre-commit Hooks
```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running refactor validation pipeline..."

# 1. Unit tests
echo "Running unit tests..."
pytest tests/unit/ -q || exit 1

# 2. Integration tests  
echo "Running integration tests..."
pytest tests/integration/ -q || exit 1

# 3. Performance baseline
echo "Checking performance baseline..."
make perf || exit 1

# 4. Determinism hash check
echo "Validating determinism..."
python scripts/check_determinism_hash.py || exit 1

echo "All validation checks passed!"
```

#### Continuous Integration
```yaml
# .github/workflows/refactor-validation.yml
name: Agent Refactor Validation

on: [push, pull_request]

jobs:
  validate-refactor:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        make venv
        source vmt-dev/bin/activate
        pip install -e .[dev]
    
    - name: Run full test suite
      run: |
        source vmt-dev/bin/activate
        pytest -q
    
    - name: Performance baseline check
      run: |
        source vmt-dev/bin/activate
        make perf
    
    - name: Determinism validation
      run: |
        source vmt-dev/bin/activate
        python scripts/validate_determinism.py
```

## 🚦 Risk Mitigation Strategy

### Rollback Plan
- **Feature flags** for each component extraction
- **Backward compatibility layers** during transition
- **Automatic rollback** if any validation fails
- **Component-level toggles** for gradual rollout

### Critical Path Protection
- **Performance benchmarking** at each step
- **Hash validation** after each component extraction  
- **Full test suite** execution before any commit
- **Peer review** for high-risk extractions

## 📅 Timeline and Milestones

| Week | Phase | Milestone | Validation |
|------|-------|-----------|------------|
| 1-2  | 1.1   | AgentMovement extracted | Tests pass, performance stable |
| 2    | 1.2   | Observer consolidation | Event emission working |
| 2-3  | 1.3   | Utility extraction | Clean utility functions |
| 4-5  | 2.1   | AgentInventory extracted | Economic calculations stable |
| 5-6  | 2.2   | TradingPartner extracted | Bilateral exchange working |
| 6-7  | 2.3   | Target selection strategies | Performance critical algorithms stable |
| 8-9  | 3.1   | Mode state machine | Clean state transitions |
| 9-10 | 3.2   | Command pattern | Action decomposition complete |

## ✅ Final Success Criteria

- [ ] Agent class reduced from 972 → 400-500 lines
- [ ] All 210+ existing tests pass without modification
- [ ] Performance within 2% of baseline (≥999.3 steps/sec)
- [ ] Determinism hash completely stable
- [ ] Component test coverage >90%
- [ ] Clean architectural separation of concerns
- [ ] Maintainable, testable codebase
- [ ] Full backward compatibility preserved

This implementation plan provides a **systematic, risk-managed approach** to refactoring the Agent class while maintaining the strict requirements of the deterministic economic simulation platform.