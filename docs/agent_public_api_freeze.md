# Agent Public API - Frozen for Refactor

**Date**: October 2, 2025  
**Status**: Pre-Refactor Baseline  
**Agent Class**: `src/econsim/simulation/agent.py`  
**Pre-Refactor LOC**: 972 lines (excluding comments)

---

## Purpose

This document freezes the public API surface of the Agent class before the Phase 1-3 refactor.
All methods and attributes listed here MUST remain callable/accessible with identical signatures
after the refactor completes to ensure backward compatibility.

**Compatibility Contract**: External code (handlers, world, tests) may call any method or access
any attribute listed below. The refactor must preserve these interfaces exactly.

---

## Public Methods (27 total)

### Movement & Spatial (7 methods)

#### `move_random(grid: Grid, rng: random.Random) -> None`
Move one step randomly in 4-neighborhood or stay put.

**Usage**: Called by movement handlers for IDLE mode random movement.

#### `move_toward_meeting_point(grid: Grid) -> None`
Move one step toward the established meeting point for trading.

**Usage**: Called when agent is in MOVE_TO_PARTNER mode.

#### `at_home() -> bool`
Check if agent is currently at their home position.

**Usage**: Frequently checked for deposit logic and mode transitions.

#### `pos -> Position` (property)
Get agent's current position as a `(x, y)` tuple.

**Returns**: `tuple[int, int]`

#### `find_nearby_agents(all_agents: list[Agent]) -> list[tuple[Agent, int]]`
Find other agents within perception radius for potential trading.

**Returns**: List of (agent, distance) tuples sorted deterministically.

#### `calculate_meeting_point(other_agent: Agent) -> Position`
Calculate the midpoint between this agent and another agent for meeting.

**Returns**: `tuple[int, int]` - Meeting point coordinates.

#### `is_colocated_with(other_agent: Agent) -> bool`
Check if this agent is on the same tile as another agent.

**Usage**: Used by trading system to verify agents are ready to trade.

---

### Inventory & Resources (7 methods)

#### `carrying_total() -> int`
Return total number of goods currently being carried.

**Usage**: Checked for carrying capacity limits and mode transitions.

#### `collect(grid: Grid, step: int = -1, observer_registry: Optional[ObserverRegistry] = None) -> bool`
Collect resource at current position if foraging enabled.

Maps resource types: A→good1, B→good2. Tracks acquisition for behavioral logging.

**Args**:
- `grid`: Grid for resource access
- `step`: Current step number for logging and events
- `observer_registry`: Event registry for resource collection events

**Returns**: `True` if resource collected, `False` otherwise.

#### `deposit() -> bool`
Move all carried goods into home inventory.

**Returns**: `True` if any goods deposited, `False` if carrying was empty.

**Critical**: Mutates `self.carrying` and `self.home_inventory` dicts IN PLACE (never rebinds).

#### `withdraw_all() -> bool`
Move all home inventory goods into carrying.

**Returns**: `True` if any goods withdrawn, `False` if home inventory was empty.

**Critical**: Mutates `self.carrying` and `self.home_inventory` dicts IN PLACE (never rebinds).

#### `maybe_deposit(observer_registry: Optional[ObserverRegistry] = None, step_number: int = 0) -> None`
Deposit carried goods at home and transition to appropriate mode.

**Behavioral transitions after deposit**:
- Both forage + exchange enabled: withdraw goods and continue foraging
- Only forage enabled: continue foraging (keep goods at home)
- Only exchange enabled: withdraw goods for trading
- Neither enabled: idle at home
- `force_deposit_once` override: deposit and idle (stagnation recovery)

**Args**:
- `observer_registry`: Event registry for mode change notifications
- `step_number`: Current step for event context

#### `maybe_withdraw_for_trading(observer_registry: Optional[ObserverRegistry] = None, step_number: int = 0) -> None`
Withdraw home inventory when at home for bilateral exchange mode.

**Args**:
- `observer_registry`: Event registry for mode change notifications
- `step_number`: Current step for event context

#### `total_inventory() -> dict[str, int]`
Return combined carrying + home inventory without mutation.

**Returns**: `{"good1": int, "good2": int}` (new dict, not an alias)

---

### Utility & Preferences (1 method)

#### `current_utility() -> float`
Calculate current utility from total wealth (carrying + home inventory).

**Usage**: Core to all target selection and trading decisions.

**Note**: Applies epsilon augmentation for zero-bundle edge cases.

---

### Decision & Target Selection (5 methods)

#### `select_target(grid: Grid, observer_registry: Optional[ObserverRegistry] = None, step_number: int = 0) -> None`
Select movement target based on current mode and available resources.

**Mode-Specific Behavior**:
- `RETURN_HOME`: Target home position
- `MOVE_TO_PARTNER`: Target meeting point
- `IDLE`: Stay idle if foraging disabled
- `FORAGE`: Find highest utility resource within perception radius

**Args**:
- `grid`: Grid for resource access and spatial queries
- `observer_registry`: Event registry for mode change notifications
- `step_number`: Current step for event context

**Side Effects**: Sets `self.target` and may change `self.mode`.

#### `select_unified_target(...)` 
*Note: Complex signature - see agent.py line 909 for full signature*

Unified target selection with distance discounting for both resources and trading partners.

**Usage**: Advanced selection logic used by world simulation.

#### `compute_best_resource_candidate(grid: Grid) -> tuple[Position | None, float, tuple[float,int,int,int] | None]`
Return best resource target `(position, delta_u, tie_key)` without mutating state.

**Returns**:
- `Position | None`: Target position or None if no positive ΔU resource found
- `float`: Delta utility value
- `tuple[float,int,int,int] | None`: Tie-breaking key `(-ΔU, distance, x, y)`

**Usage**: Called by selection logic; deterministic ordering guaranteed.

#### `step_decision(grid: Grid, observer_registry: Optional[ObserverRegistry] = None, step_number: int = 0) -> bool`
Perform one decision+movement+interaction step (without RNG).

**Returns**: `True` if resource was collected during this step.

**Usage**: Main agent step method called by handlers.

---

### Trading & Partnerships (7 methods)

#### `pair_with_agent(other_agent: Agent) -> None`
Establish mutual pairing with another agent for trading.

**Side Effects**: 
- Sets `self.trade_partner_id` and `other_agent.trade_partner_id`
- Calculates and sets meeting point for both agents

#### `clear_trade_partner() -> None`
Clear trade partner state without setting cooldowns.

**Side Effects**: Clears `trade_partner_id`, `meeting_point`, `is_trading` flag.

#### `end_trading_session(partner: Agent) -> None`
End trading session with partner and set per-partner cooldowns.

**Side Effects**:
- Sets 20-step per-partner cooldown
- Sets 3-step general trade cooldown
- Clears partner state on both agents

#### `update_partner_cooldowns() -> None`
Decrement all partner-specific cooldowns by 1.

**Usage**: Called each step to manage cooldown timers.

#### `can_trade_with_partner(partner_id: int) -> bool`
Check if this agent can trade with a specific partner (no active cooldown).

**Returns**: `True` if no cooldown active for that partner.

#### `attempt_trade_with_partner(other_agent: Agent, metrics_collector: Any = None, current_step: int = 0) -> bool`
**DEPRECATED**: Trade execution path - no longer executes trades.

**Returns**: Always returns `False`.

**Note**: Trade execution has moved to centralized handler system.

#### `is_colocated_with(other_agent: Agent) -> bool`
Check if this agent is on the same tile as another agent.

**Usage**: Verify trading partners are at meeting point.

---

### Serialization (1 method)

#### `serialize() -> Mapping[str, Any]`
Serialize agent state to dictionary for persistence and debugging.

**Returns**: Dictionary with keys:
- `id`, `x`, `y`, `home_x`, `home_y`
- `carrying`, `home_inventory`
- `mode`, `target`
- `trade_partner_id`, `meeting_point`
- Preference type and parameters

**Usage**: Snapshots, replays, debugging.

---

## Public Attributes (Direct Access)

### Identity
- `id: int` - Unique agent identifier (immutable after construction)

### Spatial State
- `x: int` - Current X coordinate
- `y: int` - Current Y coordinate
- `home_x: int` - Home position X coordinate (immutable)
- `home_y: int` - Home position Y coordinate (immutable)
- `target: Position | None` - Current movement target `(x, y)` or `None`

### Inventory (Dict Attributes - MUST be mutated in place)
- `carrying: dict[str, int]` - Currently carried goods `{"good1": int, "good2": int}`
- `home_inventory: dict[str, int]` - Goods stored at home `{"good1": int, "good2": int}`

**CRITICAL INVARIANT**: These dicts MUST be mutated in place. Never rebind these references.
```python
# ✅ CORRECT:
agent.carrying["good1"] = 5

# ❌ WRONG (breaks backward compatibility):
agent.carrying = {"good1": 5, "good2": 0}
```

### Behavioral State
- `mode: AgentMode` - Current behavioral mode (enum: FORAGE, RETURN_HOME, IDLE, MOVE_TO_PARTNER)
- `preference: Preference` - Preference function object for utility calculations

### Trading State
- `trade_partner_id: int | None` - ID of current trade partner or None
- `meeting_point: Position | None` - Established meeting coordinates `(x, y)` or None
- `is_trading: bool` - Flag indicating active trading session
- `trade_cooldown: int` - General cooldown timer (3 steps after any pairing ends)
- `partner_cooldowns: dict[int, int]` - Per-partner cooldown timers `{agent_id: steps_remaining}`

### Stagnation Tracking
- `force_deposit_once: bool` - Override flag for forced deposit (stagnation recovery)
- `last_trade_mode_utility: float` - Utility at start of trade mode (stagnation detection)
- `trade_stagnation_steps: int` - Steps spent in trade mode without utility gain

---

## Private Methods (Do NOT Call from External Code)

These methods are internal implementation details and may change during refactor:

- `_set_mode()` - Internal mode transition with event emission
- `_debug_log_mode_change()` - Debug logging for mode transitions
- `_track_target_change()` - Behavioral churn analysis
- `_manhattan()` - Manhattan distance calculation
- `_current_bundle()` - Get current bundle from total wealth
- `_try_leontief_prospecting()` - Prospecting logic (scheduled for removal)
- `_peek_resource_type_at()` - Non-destructive resource type check
- `_find_nearest_complement_resource()` - Helper for prospecting (scheduled for removal)

**Note**: Private methods (prefixed with `_`) may be removed, renamed, or refactored without notice.

---

## AgentMode Enum Values

```python
class AgentMode(str, Enum):
    FORAGE = "forage"
    RETURN_HOME = "return_home"
    IDLE = "idle"
    MOVE_TO_PARTNER = "move_to_partner"
```

**Complete**: These 4 modes cover all agent behavioral states. No additional modes exist.

---

## Backward Compatibility Validation

After refactor completion, the following tests MUST pass:

1. **Signature Compatibility**: All 27 public methods callable with documented signatures
2. **Attribute Access**: All public attributes readable/writable as documented
3. **Inventory Mutation**: `id(agent.carrying)` unchanged after operations
4. **Serialization Round-Trip**: `Agent(**agent.serialize())` produces equivalent agent
5. **Mode Transitions**: All documented mode values remain valid

---

## Refactor Notes

### Components Being Extracted
- **Movement**: `move_random()`, `move_toward_meeting_point()`, spatial utilities
- **Inventory**: `carrying`, `home_inventory`, `deposit()`, `withdraw_all()`, `carrying_total()`
- **Event Emitter**: Consolidates observer event emission
- **Trading Partner**: `pair_with_agent()`, partner cooldowns, meeting point logic
- **Target Selection**: `select_target()`, `compute_best_resource_candidate()`
- **Mode State Machine**: Mode transition validation and event emission

### Scheduled Removals
- `_try_leontief_prospecting()` - Prospecting feature being removed (see Section 5.6 of finalreview.md)
- `_find_nearest_complement_resource()` - Helper for prospecting (unused after removal)
- `attempt_trade_with_partner()` - Deprecated (already no-op, may be removed in cleanup)

---

**Frozen Date**: October 2, 2025  
**Review Status**: ✅ Complete  
**Next Review**: After Phase 3 completion (validate compatibility)

