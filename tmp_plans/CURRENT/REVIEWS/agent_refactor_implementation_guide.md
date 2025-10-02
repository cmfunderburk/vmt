# Agent Refactor: Comprehensive Implementation Guide

**Date**: October 2, 2025  
**Status**: Ready for Implementation  
**Goal**: Refactor 972-line Agent monolith into maintainable component architecture

---

## Executive Summary

This guide provides complete implementation details for refactoring the Agent class through 3 phases over ~13 days. All critical architectural decisions have been resolved, with only minor validations remaining.

**Success Criteria**:
- Agent class reduced from 972 → 400-500 lines
- All 210+ existing tests pass
- Performance monitoring (informational, non-blocking)
- Hash stability deferred until Phase 3 completion
- 1-day feature flag testing per component

**Key Architectural Decisions**:
- Mode management: Hybrid (agent.mode authoritative, state machine validates)
- Inventory mutation: Strict in-place only (never rebind dicts)
- Trading cooldowns: Deterministic state table with lower ID tie-break
- Serialization: Flatten component state (no versioning)
- Performance: Informational monitoring only (non-blocking)
- Feature flags: 1-day testing, rapid cleanup

---

## Phase 1: Safe Extractions (Days 1-5)

### Phase 1.1: Movement Component (Days 1-3)

#### Day 1: Implementation
**Create Component Structure**:
```bash
mkdir -p src/econsim/simulation/components/movement
touch src/econsim/simulation/components/__init__.py
```

**File**: `src/econsim/simulation/components/movement/__init__.py`
```python
"""Movement component for agent spatial navigation."""
from .core import AgentMovement
from .utils import manhattan_distance, calculate_meeting_point

__all__ = ["AgentMovement", "manhattan_distance", "calculate_meeting_point"]
```

**File**: `src/econsim/simulation/components/movement/core.py`
```python
"""Agent movement component for spatial navigation and pathfinding."""

from __future__ import annotations
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...grid import Grid

Position = tuple[int, int]

class AgentMovement:
    """Handles all agent movement operations with deterministic pathfinding."""
    
    def __init__(self, agent_id: int):
        self.agent_id = agent_id
    
    def move_random(self, current_pos: Position, grid: 'Grid', rng: random.Random) -> Position:
        """
        Move one step randomly in 4-neighborhood or stay put.
        
        Determinism: Uses fixed move list order, RNG only for selection.
        """
        x, y = current_pos
        moves = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]
        dx, dy = rng.choice(moves)
        nx, ny = x + dx, y + dy
        
        if 0 <= nx < grid.width and 0 <= ny < grid.height:
            return (nx, ny)
        return current_pos
    
    def move_toward_target(self, current_pos: Position, target: Position) -> Position:
        """
        Move one step toward target using greedy pathfinding.
        
        Tie-break: Horizontal priority if abs(dx) > abs(dy).
        """
        x, y = current_pos
        tx, ty = target
        
        if (x, y) == (tx, ty):
            return current_pos
        
        dx = tx - x
        dy = ty - y
        
        # Greedy: horizontal priority if abs(dx) > abs(dy)
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

**File**: `src/econsim/simulation/components/movement/utils.py`
```python
"""Spatial utility functions."""

def manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """Calculate Manhattan distance between two points."""
    return abs(x1 - x2) + abs(y1 - y2)

def calculate_meeting_point(pos1: tuple[int, int], pos2: tuple[int, int]) -> tuple[int, int]:
    """Calculate midpoint between two positions for meeting."""
    x1, y1 = pos1
    x2, y2 = pos2
    return (x1 + x2) // 2, (y1 + y2) // 2
```

**File**: `src/econsim/simulation/agent_flags.py` (create)
```python
"""Feature flags for agent refactor rollout."""

import os
from typing import Dict

def get_refactor_flags() -> Dict[str, bool]:
    """Get current refactor feature flag values."""
    return {
        "movement": os.environ.get("ECONSIM_AGENT_MOVEMENT_REFACTOR", "0") == "1",
        "events": os.environ.get("ECONSIM_AGENT_EVENTS_REFACTOR", "0") == "1",
        "inventory": os.environ.get("ECONSIM_AGENT_INVENTORY_REFACTOR", "0") == "1",
        "trading": os.environ.get("ECONSIM_AGENT_TRADING_REFACTOR", "0") == "1",
        "selection": os.environ.get("ECONSIM_AGENT_SELECTION_REFACTOR", "0") == "1",
        "state_machine": os.environ.get("ECONSIM_AGENT_STATE_MACHINE_REFACTOR", "0") == "1",
    }

def is_refactor_enabled(component: str) -> bool:
    """Check if specific refactor component is enabled."""
    flags = get_refactor_flags()
    return flags.get(component, False)
```

**Integration with Agent** (agent.py):
```python
from .agent_flags import is_refactor_enabled
from .components.movement import AgentMovement

class Agent:
    def __post_init__(self):
        # ... existing initialization ...
        
        if is_refactor_enabled("movement"):
            self._movement = AgentMovement(self.id)
    
    def move_random(self, grid: Grid, rng: random.Random) -> None:
        """Move one step randomly in 4-neighborhood or stay put."""
        if is_refactor_enabled("movement"):
            new_pos = self._movement.move_random((self.x, self.y), grid, rng)
            self.x, self.y = new_pos
        else:
            # LEGACY: Existing implementation
            x, y = self.x, self.y
            moves = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]
            dx, dy = rng.choice(moves)
            nx, ny = x + dx, y + dy
            if 0 <= nx < grid.width and 0 <= ny < grid.height:
                self.x, self.y = nx, ny
```

**Unit Tests** (`tests/unit/components/test_movement.py`):
```python
"""Unit tests for AgentMovement component."""

import pytest
import random
from unittest.mock import Mock
from src.econsim.simulation.components.movement import AgentMovement

class TestAgentMovement:
    def test_move_random_within_bounds(self):
        movement = AgentMovement(agent_id=1)
        grid = Mock(width=10, height=10)
        rng = random.Random(42)
        
        pos = movement.move_random((5, 5), grid, rng)
        assert 0 <= pos[0] < 10
        assert 0 <= pos[1] < 10
    
    def test_move_toward_target_horizontal_priority(self):
        movement = AgentMovement(agent_id=1)
        pos = movement.move_toward_target((2, 2), (5, 3))
        assert pos == (3, 2)  # Horizontal first
    
    def test_deterministic_movement_sequence(self):
        movement = AgentMovement(agent_id=1)
        grid = Mock(width=10, height=10)
        
        rng1 = random.Random(12345)
        rng2 = random.Random(12345)
        
        pos1 = pos2 = (5, 5)
        for _ in range(10):
            pos1 = movement.move_random(pos1, grid, rng1)
            pos2 = movement.move_random(pos2, grid, rng2)
            assert pos1 == pos2
```

#### Day 2: Testing & Validation
**Actions**:
1. Set `ECONSIM_AGENT_MOVEMENT_REFACTOR=1`
2. Run full test suite: `pytest -q`
3. Run performance benchmark: `make perf`
4. Verify movement behavior matches legacy (spot checks)

**Success Criteria**:
- [ ] All 210+ tests pass
- [ ] Performance report generated (informational)
- [ ] Movement component unit tests pass
- [ ] No behavioral regressions observed

#### Day 3: Flag Removal
**Actions**:
1. Remove flag checks from `agent.py`
2. Delete legacy movement code paths
3. Remove `"movement"` from `agent_flags.py`
4. Commit: `agent: movement component extraction complete (flag removed)`

---

### Phase 1.2: Event Emitter Consolidation (Days 3-5)

#### Day 3: Implementation
**File**: `src/econsim/simulation/components/event_emitter/core.py`
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
        """Emit agent mode change event."""
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
```

#### Day 4-5: Testing, Validation, Flag Removal
(Same pattern as Phase 1.1)

---

## Phase 2: Core Logic Refactoring (Days 5-11)

### Phase 2.1: Inventory Component (Days 5-7)

#### Day 5: Implementation
**File**: `src/econsim/simulation/components/inventory/core.py`
```python
"""
Agent inventory management with dual storage system.

CRITICAL INVARIANT: This component MUST mutate self.carrying and 
self.home_inventory dictionaries IN PLACE. Never rebind these references.
The Agent class exposes these dicts via aliases for backward compatibility,
and rebinding would break the alias connection.

Correct:   self.carrying["good1"] = 0
Incorrect: self.carrying = {"good1": 0, "good2": 0}
"""

from typing import Dict
from ...preferences.base import Preference
from ...constants import EPSILON_UTILITY

class AgentInventory:
    """Manages agent's carrying and home inventory with utility calculations."""
    
    def __init__(self, preference: Preference):
        # Create dicts ONCE - NEVER rebind these
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
        """Get current bundle (good1, good2) from total wealth."""
        total_good1 = float(self.carrying["good1"] + self.home_inventory["good1"])
        total_good2 = float(self.carrying["good2"] + self.home_inventory["good2"])
        return total_good1, total_good2
    
    def current_utility(self) -> float:
        """Calculate current utility from total wealth."""
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
        # ✅ CRITICAL: In-place mutation only
        for key in list(self.carrying.keys()):
            if self.carrying[key] > 0:
                self.home_inventory[key] += self.carrying[key]
                self.carrying[key] = 0
                moved = True
        return moved
    
    def withdraw_all(self) -> bool:
        """Move all home inventory into carrying. Returns True if withdrawn."""
        moved = False
        # ✅ CRITICAL: In-place mutation only
        for key in list(self.home_inventory.keys()):
            if self.home_inventory[key] > 0:
                self.carrying[key] += self.home_inventory[key]
                self.home_inventory[key] = 0
                moved = True
        return moved
    
    def collect_resource(self, resource_type: str) -> None:
        """Add resource to carrying inventory."""
        # ✅ CRITICAL: In-place mutation only
        if resource_type == "A":
            self.carrying["good1"] += 1
        elif resource_type == "B":
            self.carrying["good2"] += 1
```

**Agent Integration**:
```python
class Agent:
    def __post_init__(self):
        # ... existing initialization ...
        
        if is_refactor_enabled("inventory"):
            self._inventory = AgentInventory(self.preference)
            # CRITICAL: Set up aliases (not copies!)
            object.__setattr__(self, "carrying", self._inventory.carrying)
            object.__setattr__(self, "home_inventory", self._inventory.home_inventory)
            object.__setattr__(self, "inventory", self._inventory.inventory)
```

**Unit Tests** (mutation invariant):
```python
def test_inventory_alias_identity_preserved():
    """Verify dict objects maintain identity through operations."""
    agent = create_test_agent()
    
    carrying_id = id(agent.carrying)
    home_id = id(agent.home_inventory)
    
    # Perform operations
    agent.carrying["good1"] = 5
    agent.deposit()
    agent.withdraw_all()
    
    # Verify identity preserved
    assert id(agent.carrying) == carrying_id
    assert id(agent.home_inventory) == home_id
```

---

### Phase 2.2: Trading Partner Component (Days 7-9)

#### Day 7: Implementation
**File**: `src/econsim/simulation/components/trading_partner/core.py`
```python
"""Agent trading partner management and coordination."""

from __future__ import annotations
from typing import Optional, Dict, List, Tuple, TYPE_CHECKING
from ..movement.utils import manhattan_distance, calculate_meeting_point
from ...constants import default_PERCEPTION_RADIUS

if TYPE_CHECKING:
    from ...agent import Agent

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
        """Find other agents within perception radius, sorted deterministically."""
        candidates = []
        for other_agent in all_agents:
            if other_agent.id == self.agent_id:
                continue
            
            distance = manhattan_distance(agent_pos[0], agent_pos[1], other_agent.x, other_agent.y)
            if distance <= default_PERCEPTION_RADIUS:
                candidates.append((other_agent, distance))
        
        # Deterministic sort: distance, then position
        candidates.sort(key=lambda x: (x[1], x[0].x, x[0].y))
        return candidates
    
    def can_pair_with(self, other_agent: "Agent") -> bool:
        """Check if pairing is allowed (no cooldowns, both available)."""
        if self.trade_cooldown > 0:
            return False
        if other_agent.id in self.partner_cooldowns:
            return False
        if self.trade_partner_id is not None:
            return False
        if other_agent._trading_partner.trade_partner_id is not None:
            return False
        return True
    
    def establish_pairing(self, agent_pos: Position, other_agent: "Agent") -> None:
        """
        Establish mutual pairing with deterministic ordering.
        Lower agent.id processes first.
        """
        meeting_point = calculate_meeting_point(agent_pos, (other_agent.x, other_agent.y))
        
        self.trade_partner_id = other_agent.id
        self.meeting_point = meeting_point
        
        other_agent._trading_partner.trade_partner_id = self.agent_id
        other_agent._trading_partner.meeting_point = meeting_point
    
    def end_trading_session(self, other_agent: "Agent") -> None:
        """End trading session with per-partner cooldowns."""
        # Set per-partner cooldown (20 steps)
        self.partner_cooldowns[other_agent.id] = 20
        other_agent._trading_partner.partner_cooldowns[self.agent_id] = 20
        
        # Clear state (general cooldown = 3)
        self.clear_trade_partner()
        other_agent._trading_partner.clear_trade_partner()
    
    def clear_trade_partner(self) -> None:
        """Clear trade partner state with general cooldown."""
        self.trade_partner_id = None
        self.meeting_point = None
        self.is_trading = False
        self.trade_cooldown = 3
    
    def update_cooldowns(self) -> None:
        """Decrement all cooldowns by 1."""
        if self.trade_cooldown > 0:
            self.trade_cooldown -= 1
        
        for partner_id in list(self.partner_cooldowns.keys()):
            self.partner_cooldowns[partner_id] -= 1
            if self.partner_cooldowns[partner_id] <= 0:
                del self.partner_cooldowns[partner_id]
```

---

### Phase 2.3: Target Selection Strategies (Days 9-11)

#### Day 9: Implementation
**Note**: Leontief prospecting is **REMOVED** per architectural decision.

**File**: `src/econsim/simulation/components/target_selection/base.py`
```python
"""Base classes for target selection strategies."""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from ...grid import Grid
    from ....preferences.base import Preference

Position = tuple[int, int]

@dataclass
class TargetCandidate:
    """Structured result from target selection."""
    position: Position
    delta_u_raw: float
    distance: int
    kind: str  # 'resource' or 'pairing'
    aux: dict  # Optional metadata

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
    ) -> Optional[TargetCandidate]:
        """Select the best target for the agent."""
        pass
```

**File**: `src/econsim/simulation/components/target_selection/resource_selection.py`
```python
"""Resource target selection strategy."""

from typing import Optional, Tuple, TYPE_CHECKING
from .base import TargetSelectionStrategy, TargetCandidate
from ...constants import default_PERCEPTION_RADIUS
from ..movement.utils import manhattan_distance

if TYPE_CHECKING:
    from ...grid import Grid
    from ....preferences.base import Preference

Position = tuple[int, int]

class ResourceTargetStrategy(TargetSelectionStrategy):
    """Strategy for selecting resource targets based on utility maximization."""
    
    def select_target(
        self,
        agent_pos: Position,
        current_bundle: Tuple[float, float],
        preference: 'Preference',
        grid: 'Grid',
        **kwargs
    ) -> Optional[TargetCandidate]:
        """Find highest utility resource within perception radius."""
        best_candidate = None
        best_priority = None  # (-delta_u_adj, distance, x, y)
        
        # Deterministic iteration
        iterator = getattr(grid, 'iter_resources_sorted', grid.iter_resources)()
        
        for rx, ry, rtype in iterator:
            distance = manhattan_distance(agent_pos[0], agent_pos[1], rx, ry)
            if distance > default_PERCEPTION_RADIUS:
                continue
            
            # Calculate utility gain
            delta_u = self._calculate_delta_utility(current_bundle, rtype, preference)
            
            # Apply distance discount
            delta_u_adj = delta_u / (1 + 0.1 * distance * distance)
            
            # Canonical priority tuple
            priority = (-delta_u_adj, distance, rx, ry)
            
            if best_priority is None or priority < best_priority:
                best_priority = priority
                best_candidate = TargetCandidate(
                    position=(rx, ry),
                    delta_u_raw=delta_u,
                    distance=distance,
                    kind='resource',
                    aux={'resource_type': rtype}
                )
        
        return best_candidate
    
    def _calculate_delta_utility(self, bundle: Tuple[float, float], rtype: str, pref: 'Preference') -> float:
        """Calculate utility gain from collecting resource."""
        g1, g2 = bundle
        if rtype == "A":
            new_bundle = (g1 + 1, g2)
        else:
            new_bundle = (g1, g2 + 1)
        return pref.utility(new_bundle) - pref.utility(bundle)
```

---

## Phase 3: Advanced Patterns (Days 11-13)

### Phase 3.1: Mode State Machine (Days 11-13)

**File**: `src/econsim/simulation/components/mode_state_machine.py`
```python
"""Agent mode state machine with explicit transitions and validation."""

from enum import Enum
from typing import Optional, TYPE_CHECKING
from .event_emitter import AgentEventEmitter

if TYPE_CHECKING:
    from ...observability.registry import ObserverRegistry
    from ...observability.event_buffer import StepEventBuffer

class AgentMode(Enum):
    FORAGE = "FORAGE"
    RETURN_HOME = "RETURN_HOME"
    IDLE = "IDLE"
    MOVE_TO_PARTNER = "MOVE_TO_PARTNER"

class AgentModeStateMachine:
    """Validates mode transitions and emits events; does NOT own mode state."""
    
    # Valid transitions map
    VALID_TRANSITIONS = {
        AgentMode.FORAGE: {AgentMode.RETURN_HOME, AgentMode.IDLE, AgentMode.MOVE_TO_PARTNER},
        AgentMode.RETURN_HOME: {AgentMode.FORAGE, AgentMode.IDLE},
        AgentMode.IDLE: {AgentMode.FORAGE, AgentMode.MOVE_TO_PARTNER, AgentMode.RETURN_HOME},
        AgentMode.MOVE_TO_PARTNER: {AgentMode.IDLE, AgentMode.FORAGE, AgentMode.RETURN_HOME}
    }
    
    def __init__(self, agent_id: int, initial_mode: AgentMode):
        self.agent_id = agent_id
        self.current_mode = initial_mode  # Mirror of agent.mode
        self._event_emitter = AgentEventEmitter(agent_id)
    
    def is_valid_transition(self, from_mode: AgentMode, to_mode: AgentMode) -> bool:
        """Check if transition is valid (non-destructive check)."""
        if from_mode == to_mode:
            return True
        return to_mode in self.VALID_TRANSITIONS.get(from_mode, set())
    
    def emit_mode_change(
        self,
        old_mode: str,
        new_mode: str,
        reason: str,
        step_number: int,
        observer_registry: Optional['ObserverRegistry'],
        event_buffer: Optional['StepEventBuffer']
    ) -> None:
        """Emit mode change event."""
        self._event_emitter.emit_mode_change(
            old_mode, new_mode, reason, step_number, observer_registry, event_buffer
        )
```

---

## Hash Contract & Determinism

### Fields Participating in Hash

**Spatial State**:
- `x`, `y`, `home_x`, `home_y`, `target`

**Inventory State**:
- `carrying["good1"]`, `carrying["good2"]`
- `home_inventory["good1"]`, `home_inventory["good2"]`

**Mode State**:
- `mode` (enum value)

**Trading State** (if trading enabled):
- `trade_partner_id`, `meeting_point`

**Identity**:
- `id`

### Hash-EXCLUDED Fields
- All `_component` instances (`_movement`, `_inventory`, etc.)
- All `_debug_*` and `_perf_*` fields
- `unified_task` (internal cache)
- Trade metrics

### Serialization Pattern
```python
def serialize(self) -> dict:
    """Serialize agent state - components are flattened."""
    return {
        "id": self.id,
        "x": self.x, "y": self.y,
        "home_x": self.home_x, "home_y": self.home_y,
        "carrying": dict(self.carrying),  # Alias exposes component data
        "home_inventory": dict(self.home_inventory),
        "mode": self.mode.value,
        "target": self.target,
        "trade_partner_id": self.trade_partner_id,
        "meeting_point": self.meeting_point,
        # Components NOT serialized
    }
```

---

## Testing Strategy

### Unit Tests (Per Component)
```
tests/unit/components/
├── test_movement.py
├── test_inventory.py
├── test_trading_partner.py
├── test_event_emitter.py
├── test_target_selection.py
└── test_mode_state_machine.py
```

### Integration Tests
```
tests/integration/
├── test_agent_component_integration.py
├── test_snapshot_compatibility.py
└── test_performance_monitoring.py
```

### Hash Equivalence Tests
```python
def test_hash_equivalence_pre_post_refactor():
    """Verify determinism hash unchanged after refactor."""
    # Correct API: simulation.metrics_collector.determinism_hash()
    hash_baseline = sim1.metrics_collector.determinism_hash()
    hash_refactored = sim2.metrics_collector.determinism_hash()
    assert hash_baseline == hash_refactored
```

### Mutation Invariant Tests
```python
def test_inventory_alias_identity_preserved():
    """Critical: Verify dict identity maintained."""
    agent = create_test_agent()
    carrying_id = id(agent.carrying)
    
    agent.carrying["good1"] = 5
    agent.deposit()
    agent.withdraw_all()
    
    assert id(agent.carrying) == carrying_id
```

---

## Performance Monitoring (Informational)

**Protocol**: 5-sample median, 2% observation threshold
- 1 warmup run (discarded)
- 5 measurement runs
- Report changes >2% (informational only)
- **Does NOT block merges**

**Micro-Benchmark Targets** (informational guidelines):
- Movement: <0.5µs per move
- Inventory: <1.0µs per operation
- Target selection: <150µs per scan (12x12 grid)

---

## Feature Flag Lifecycle

**Day 1**: Implement with `ECONSIM_AGENT_<COMPONENT>_REFACTOR=0`
**Day 2**: Enable flag=1, run full validation
**Day 3**: Remove flag + delete legacy code

**Example**:
```bash
# Day 2
export ECONSIM_AGENT_MOVEMENT_REFACTOR=1
pytest -q && make perf

# Day 3
# Remove flag checks, delete legacy code
git commit -m "agent: movement component complete (flag removed)"
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Hash drift | Deferred enforcement; flatten serialization; components don't add hash fields |
| Performance regression | Informational monitoring only; non-blocking |
| Alias breakage | Strict in-place mutation contract; identity tests |
| Event ordering | Single emission via AgentEventEmitter |
| Circular imports | TYPE_CHECKING; no runtime imports of Agent |

---

## Documentation Requirements

Each component file must include:
```python
"""
Component docstring.

CRITICAL INVARIANT: [If applicable]
- Specific invariants this component must maintain
- Example: "Never rebind self.carrying"

HASH CONTRACT: [If applicable]
- Which fields participate in determinism hash
- Which fields are excluded
"""
```

---

## Success Validation Checklist

**Per Phase**:
- [ ] All 210+ tests pass
- [ ] Performance report generated (informational)
- [ ] Component unit tests pass (>90% coverage)
- [ ] Integration tests pass
- [ ] Feature flag removed after 1 day

**Final (After Phase 3)**:
- [ ] Agent class reduced to 400-500 lines
- [ ] All components extracted and tested
- [ ] Hash stabilization pass complete (using `sim.metrics_collector.determinism_hash()`)
- [ ] Baseline `determinism_hashes.json` regenerated
- [ ] Documentation updated

---

## Commit Message Templates

**Component Extraction**:
```
agent: extract <component> (flag=0, day 1 of 3)

- New component: components/<name>/
- Feature flag: ECONSIM_AGENT_<NAME>_REFACTOR
- Legacy path preserved
```

**Flag Removal**:
```
agent: <component> complete (flag removed, cleanup)

- Removed ECONSIM_AGENT_<NAME>_REFACTOR flag
- Deleted legacy code path
- Reduced agent.py by ~N lines
```

---

**Status**: Ready for Phase 1 implementation. See companion checklist for progress tracking.

