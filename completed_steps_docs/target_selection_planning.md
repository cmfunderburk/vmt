# Unified Target Selection Planning

## Overview

Proposal to make unified target selection the default agent decision logic, replacing the current system of separated decision paths. Instead of branching between foraging-only, trading-only, and combined logic, agents always use unified target selection with individual behaviors gated by their respective flags. This eliminates artificial precedence rules and creates cleaner architecture.

## Current Architecture Analysis

The current system has **separated decision paths**:
1. **Foraging-only**: `agent.step_decision()` handles resource targeting via `select_target()`
2. **Trading-only**: `_handle_bilateral_exchange_movement()` handles agent-to-agent targeting
3. **Both enabled**: Sequential processing with "foraging first" precedence (agents who collect are excluded from trading that tick)

### Current Flow (Complex Branching)
```
Simulation.step():
  if forage_enabled and not trade_enabled:
    # Foraging-only path
    for agent in agents: agent.step_decision(grid)
  elif trade_enabled and not forage_enabled:
    # Trading-only path  
    for agent in agents: _handle_bilateral_exchange_movement(agent, rng)
  elif both_enabled:
    # Complex combined path with precedence
    for agent in agents:
      collected = agent.step_decision(grid)  # Foraging first
      if collected: foraged_ids.add(agent.id)
    # Later: Trade logic excludes foragers
    filtered_agents = [ag for ag in coloc_agents if ag.id not in foraged_ids]
  else:
    # Neither enabled - return home logic
```

### Proposed Unified Flow
```
Simulation.step():
  for agent in agents:
    # Always use unified target selection
    agent.select_unified_target(grid, other_agents)
    agent.pursue_target()  # Handles both resources and trade partners
```

## Proposed Unified Approach

### Core Concept
The unified target selection becomes the default agent decision logic. Each agent scans for both resources and trade partners within perception radius, then selects the opportunity with the highest **distance-discounted utility gain**. This accounts for travel costs by applying an inverse square law discount to utility gains based on Manhattan distance. Individual behaviors (foraging, trading) are simply skipped when their flags are disabled, rather than requiring separate decision paths. Once a target is selected, the agent carries out that task and is unavailable for target selection by other agents until task completion.

### Benefits
1. **Architectural simplicity**: Unified path is the default, with behaviors conditionally included rather than requiring separate branching logic
2. **Eliminates artificial precedence**: No more "foraging first" - utility drives all decisions
3. **More realistic economic behavior**: Agents choose the most valuable opportunity regardless of type
4. **Cleaner flag handling**: Flags simply gate candidate inclusion rather than switching entire decision systems
5. **Better resource allocation**: Prevents agents from "missing" better opportunities due to system-level precedence rules

## Implementation Strategy

### Phase 1: Unified Target Selection Function
Create a new method `Agent.select_unified_target(grid, agents)` that serves as the primary decision logic:
- **Conditional scanning**: Include resources if `FORAGE_ENABLED`, include agents if `TRADE_ENABLED`
- **Distance-discounted utility evaluation**: Calculate travel-cost-adjusted utility gain for all candidates:
  - **Base utility gain**: 
    - Resources: `ΔU_base = U(carrying + resource) - U(carrying)`
    - Trade partners: `ΔU_base ≈ marginal_utility_gain_from_optimal_trade(partner)`
  - **Distance discount**: `ΔU_discounted = ΔU_base / (1 + k*distance²)` where `k` is GUI-configurable scaling constant
  - **Profitable targets only**: Filter to candidates with `ΔU_base > 0` before applying distance discount
  - **Selection criterion**: Choose target with highest `ΔU_discounted` among profitable candidates
- **Deterministic tiebreaks**: When `ΔU_discounted` values are equal, use `(x, y)` for resources, `agent_id` for agents
- **Graceful degradation**: If no profitable candidates found, return None to trigger return-home logic
- Returns unified target type (resource position or agent id) or None

### Phase 2: Unified Movement & Commitment
- Add agent state to track commitment: `current_task: Optional[Union[ResourceTarget, TradeTarget]]`
- Make agents unavailable for targeting while committed
- Task completion triggers new target selection

### Phase 3: Integration & Flag Management
Replace the current branching logic in `world.py` with unified path as the default. The unified target selection becomes the primary decision logic, with individual behaviors simply skipped when their respective flags are disabled:

**Unified Decision Flow** (with spatial indexing):
```python
# Pre-compute spatial index once per step O(agents)
agent_spatial_index = AgentSpatialGrid(grid.width, grid.height)
for agent in agents:
    agent_spatial_index.add_agent(agent.x, agent.y, agent)

for agent in agents:
    # Unified target selection with spatial optimization
    candidate_resources = scan_resources_in_radius(grid, agent.pos, PERCEPTION_RADIUS) if FORAGE_ENABLED else []
    candidate_agents = agent_spatial_index.get_agents_in_radius(agent.x, agent.y, PERCEPTION_RADIUS) if TRADE_ENABLED else []
    
    # Filter to profitable candidates only
    profitable_targets = []
    for target in (candidate_resources + candidate_agents):
        base_utility_gain = calculate_utility_gain(target)
        if base_utility_gain > 0:  # Only consider profitable targets
            profitable_targets.append((base_utility_gain, target))
    
    # Calculate distance-discounted utility for profitable candidates
    scored_targets = []
    for base_gain, target in profitable_targets:
        distance = manhattan_distance(agent.pos, target.pos)
        discounted_utility = base_gain / (1 + k * distance²)  # k from GUI (0-10 range)
        scored_targets.append((discounted_utility, target))
    
    # Select best target (highest discounted utility)
    best_target = max(scored_targets, key=lambda x: x[0]) if scored_targets else None
    
    if best_target:
        agent.pursue_target(best_target[1])
    else:
        # No profitable targets found - return home or idle
        agent.return_home_or_idle()
```

**Flag Behavior Matrix**:
- **Both enabled**: Full unified comparison between resources and trade partners
- **Foraging only**: Only resources considered in target selection
- **Trading only**: Only agents considered in target selection  
- **Both disabled**: No targets found → return home/idle logic triggers

This approach eliminates the current artificial branching and makes the unified path the architectural default rather than a special case.

## Key Design Decisions Needed

### 1. Trade Utility Estimation
**Question**: How to calculate expected ΔU from trading with a partner before actually meeting them?

**Options**:
- Simple heuristic: assume optimal 1-for-1 swap based on current inventories
- More sophisticated: estimate based on preference types if known
- Conservative: use minimum expected gain to avoid overestimating trade value

### 2. Commitment Duration
**Question**: How long should agents remain committed to a target?

**Options**:
- Until resource collected OR trade completed OR target becomes unavailable
- Add timeout for unreachable targets
- Allow commitment breaking if significantly better opportunity appears

### 3. Distance Discount Function (Decided)
**Chosen approach**: `ΔU_discounted = ΔU_base / (1 + k*distance²)` (inverse square law with scaling)

**Implementation details**:
- **Scaling constant `k`**: GUI-configurable parameter in right panel (text input)
  - Higher `k` = stronger distance penalty, more local behavior
  - Lower `k` = weaker distance penalty, agents willing to travel farther
  - Default value: `k = 0.0` (may tune later based on testing)
- **Profitable targets only**: Filter candidates to `ΔU_base > 0` before distance discounting
- **Tiebreaks**: When `ΔU_discounted` values are equal, use `(x, y)` for resources, `agent_id` for agents

### 4. Implementation Decisions (Finalized)

**Distance scaling**: Use `k` scaling constant in `ΔU_discounted = ΔU_base / (1 + k*distance²)`
- **GUI integration**: Add text input control in right panel for `k` parameter
- **Default value**: Start with `k = 0.0`
- **Range**: 0.0 to 10.0 (0 = no distance penalty, 10 = strong local behavior)
- **Real-time updates**: Changes apply immediately without simulation restart

**Profitable targets only**: Filter candidates to `ΔU_base > 0` before distance discounting
- **Rationale**: Eliminates clearly bad choices, simplifies decision space
- **Implementation**: Two-stage filtering process as shown in unified decision flow

**Distance function**: Stick with inverse square law
- **Rationale**: Provides reasonable diminishing returns, familiar mathematical behavior
- **Special case**: When `k = 0`, formula becomes `ΔU_discounted = ΔU_base` (pure utility maximization, no distance penalty)
- **Future**: Can revisit alternatives if behavioral tuning needs different characteristics

**Backward compatibility**: Single-behavior modes must use same distance-discounted utility logic
- **Foraging-only**: Apply `ΔU_base / (1 + k*distance²)` to resources only
- **Trading-only**: Apply `ΔU_base / (1 + k*distance²)` to agents only
- **Critical**: This changes existing behavior - determinism tests will need updates

### 5. Determinism Preservation
**Requirements**:
- Maintain stable iteration order over agents and resources  
- Ensure unified target scanning is deterministic
- Keep existing test contracts intact (will need updates for new selection logic)
- Preserve hash parity when features disabled

## Implementation Questions

### 1. Implementation Strategy
Since unified targeting becomes the architectural default rather than an optional feature, the implementation approach changes:

**Direct Integration**:
- Replace existing branching logic with unified path
- Use existing `ECONSIM_FORAGE_ENABLED` and `ECONSIM_TRADE_*` flags to gate candidate inclusion
- Preserve backward compatibility by ensuring disabled behaviors produce identical results to current system

**Migration Benefits**:
- Simpler codebase with single decision path
- Existing flags continue to work as expected
- No additional feature flag complexity
- Natural extension point for future opportunity types

### 2. Movement System Integration
How should we handle the **bilateral exchange movement system** that currently includes sophisticated pairing/pathfinding?

**Options**:
- Keep the existing sophisticated movement for trade targets
- Simplify to match resource targeting (greedy movement)
- Hybrid approach based on distance/complexity

**Current bilateral system**: 6-tier decision logic (perception → pairing → pathfinding → co-location → trading → cooldowns)

### 3. Performance Solution: Spatial Indexing (Decided)
**Chosen approach**: Implement spatial indexing for agents to maintain O(agents + resources) complexity while preserving full economic logic.

**Spatial indexing strategy**:
- **Pre-compute agent spatial grid** once per simulation step: O(agents)
- **Agent lookup by radius** becomes O(1) average case using grid cells
- **Maintains full economic realism**: All agents within perception radius are evaluated
- **Deterministic**: Consistent spatial lookups, no sampling randomness

**Implementation approach**:
```python
# In world.py - build spatial index once per step
agent_spatial_index = AgentSpatialGrid(self.grid.width, self.grid.height)
for agent in self.agents:
    agent_spatial_index.add_agent(agent.x, agent.y, agent)

# Each agent uses indexed lookup O(1) average case
for agent in self.agents:
    nearby_agents = agent_spatial_index.get_agents_in_radius(
        agent.x, agent.y, PERCEPTION_RADIUS
    )
    target = agent.select_unified_target(self.grid, nearby_agents)
```

**Performance benefits**:
- **Total complexity**: O(agents + resources) per step (maintains current bound)
- **Eliminates O(agents²)**: No more all-pairs agent scanning
- **Leverages existing patterns**: Similar to current resource grid indexing
- **Scalable**: Performance degrades gracefully with agent density

## Current Code Integration Points

### Files to Modify
- `agent.py`: Add unified target selection method, update existing `select_target()` to use distance-discounted utility
- `world.py`: Modify step logic for unified path, add agent spatial index construction
- `simulation/spatial.py`: **New file** - implement `AgentSpatialGrid` class for O(1) agent lookups
- `simulation/config.py`: Add distance scaling parameter `k` to SimConfig with real-time update capability
- `gui/`: Add text input control for distance scaling parameter in right panel (range 0-10, immediate effect)
- `simulation/constants.py`: Add default value for distance scaling constant
- Tests: **Update existing determinism tests** for new selection logic, add unified targeting tests, add spatial indexing tests

### Existing Methods to Consider
- `Agent.select_target()`: Current resource-only targeting
- `Simulation._handle_bilateral_exchange_movement()`: Current trade-only targeting
- `Agent.step_decision()`: Current movement execution

### Environment Variables
The unified approach uses existing flags to gate behavior inclusion:
- `ECONSIM_FORAGE_ENABLED`: Controls whether resources are included in target candidates
- `ECONSIM_TRADE_*`: Controls whether agents are included in target candidates
- **No new flag needed**: Unified targeting becomes the default path, with existing flags controlling what gets evaluated

## Determinism Requirements (VMT Constraints)

From copilot instructions, must preserve (with modifications for distance-discounted utility):
- **Updated selection criterion**: Highest distance-discounted utility `ΔU_base / (1 + k*distance²)` among profitable targets
- **GUI parameter**: Distance scaling constant `k` configurable in right panel
- **Deterministic tiebreaks**: When discounted utilities equal, use `(x, y)` for resources, `agent_id` for agents  
- Stable resource iteration (`iter_resources_sorted`)
- Original agent list order resolves contests
- **O() complexity maintained**: O(agents + resources) via spatial indexing
- No hidden randomness
- Metrics hash contract (trade metrics excluded)

**Breaking change**: This fundamentally alters target selection logic from `(-ΔU, distance, x, y)` tiebreaks to distance-discounted utility. All single-behavior modes (foraging-only, trading-only) will also use the new logic, requiring determinism test updates.

## Spatial Indexing Design

### AgentSpatialGrid Implementation
**Purpose**: Enable O(1) average-case lookups of agents within perception radius, eliminating O(agents²) complexity.

**Design approach**:
```python
class AgentSpatialGrid:
    def __init__(self, width: int, height: int, cell_size: int = 1):
        self.width = width
        self.height = height
        self.cell_size = cell_size  # Always 1 for exact spatial indexing
        self.grid: Dict[Tuple[int, int], List[Agent]] = {}
    
    def add_agent(self, x: int, y: int, agent: Agent) -> None:
        cell_x, cell_y = x // self.cell_size, y // self.cell_size
        self.grid.setdefault((cell_x, cell_y), []).append(agent)
    
    def get_agents_in_radius(self, x: int, y: int, radius: int) -> List[Agent]:
        # Check cells that intersect with radius
        candidates = []
        cell_radius = (radius + self.cell_size - 1) // self.cell_size  # Ceiling division
        center_cell_x, center_cell_y = x // self.cell_size, y // self.cell_size
        
        for dx in range(-cell_radius, cell_radius + 1):
            for dy in range(-cell_radius, cell_radius + 1):
                cell = (center_cell_x + dx, center_cell_y + dy)
                if cell in self.grid:
                    candidates.extend(self.grid[cell])
        
        # Filter to actual radius (Manhattan distance)
        return [agent for agent in candidates 
                if abs(agent.x - x) + abs(agent.y - y) <= radius]
```

**Performance analysis**:
- **Build time**: O(agents) per step
- **Query time**: O(agents_in_radius) average case, bounded by perception radius
- **Memory**: O(agents) additional storage
- **Total complexity**: O(agents + resources) maintained

**Integration with existing patterns**:
- Mirrors current resource grid indexing approach
- Builds on VMT's existing spatial data structures
- Deterministic iteration order preserved through consistent cell processing

## Next Steps (Updated for Spatial Indexing)

1. **Spatial Indexing Implementation**: Create `AgentSpatialGrid` class for O(1) agent lookups by radius
2. **GUI Integration**: Add distance scaling parameter `k` to right panel with text input (range 0-10, default 1.0, real-time updates)
3. **Agent.select_target() Migration**: Update existing method to use distance-discounted utility for single-behavior modes
4. **World.py Integration**: Modify step logic to build agent spatial index once per step, pass to unified target selection
5. **Determinism Test Updates**: Update existing tests for new selection logic (breaking change)
6. **Prototype**: Implement Phase 1 unified target selection function with spatial indexing
7. **Performance Testing**: Validate FPS maintains ≥30 (preferably ~62) with spatial indexing overhead
8. **Documentation**: Update API guide and copilot instructions

## Open Questions

### GUI & Configuration Questions (Decided)
1. **Distance scaling bounds**: Range `k` from 0 to 10.0 in GUI text input
   - `k = 0`: No distance penalty (pure utility maximization)
   - `k = 10`: Strong distance penalty (very local behavior)
2. **Default `k` value**: Start with `k = 1.0`, may tune later based on testing
3. **GUI responsiveness**: `k` changes apply immediately (no simulation restart required)

### Spatial Indexing Implementation Questions (Decided)
4. **Grid cell size**: Use `cell_size = 1` for exact spatial indexing
   - **Rationale**: Memory is not a constraint, provides most accurate spatial partitioning
   - **Benefits**: Minimal false positives, exact radius filtering, O(1) lookups
5. **Index rebuild frequency**: Rebuild spatial index every step
   - **Rationale**: Simplifies implementation, handles agent movement correctly, fits O(agents) budget
   - **Implementation**: Clear and repopulate `AgentSpatialGrid` each simulation step
6. **Memory vs. speed tradeoff**: Hash-based implementation using `Dict[Tuple[int, int], List[Agent]]`
   - **Rationale**: Efficient for sparse agent distributions, aligns with existing VMT patterns
   - **Benefits**: O(1) average case lookups, minimal memory overhead for unoccupied cells
7. **Distance² calculation cost**: Use optimized inline Manhattan distance² calculation
   - **Rationale**: Computational cost negligible compared to utility calculations
   - **Implementation**: Inline `(abs(dx) + abs(dy))**2` to avoid function call overhead

### Trade Utility Estimation Questions (Expanded)

#### 7. Conservative vs Optimistic Trade Utility Estimation (DECIDED: Conservative)
**Critical for unified target selection**: Trade utility estimates directly compete with resource collection utilities, so accuracy affects economic realism.

**VMT Recommendation**: **Conservative approach** for several reasons:
- **Avoids overcommitment**: Prevents agents from traveling far for trades that don't materialize
- **Realistic expectations**: Better matches human economic behavior (loss aversion)
- **System stability**: Reduces oscillation between trade targets
- **Determinism friendly**: Simpler calculations with fewer edge cases

**Implementation**:
```python
def estimate_trade_utility_conservative(self, partner: Agent) -> float:
    """Conservative estimate - assume worst-case beneficial trade"""
    my_inventory = self.carrying
    partner_inventory = partner.carrying  # Observable within perception
    
    # Find minimal beneficial swap
    best_gain = 0.0
    for my_good_type, my_count in my_inventory.items():
        if my_count > 0:
            for partner_good_type, partner_count in partner_inventory.items():
                if partner_count > 0 and partner_good_type != my_good_type:
                    # Conservative: assume only 1-for-1 swap possible
                    gain = self.marginal_utility(partner_good_type) - self.marginal_utility(my_good_type)
                    best_gain = max(best_gain, gain)
    
    return best_gain * 0.8  # 20% pessimism factor for uncertainty
```

#### 8. Handling Utility Estimation Mismatches (DECIDED: Timeout + Re-evaluation)
**Problem**: Agent selects trade partner based on estimated utility, but actual trade produces different value (or fails entirely).

**VMT Recommendation**: **Timeout and re-evaluation** because:
- **Minimal complexity**: Fits existing agent state patterns
- **Deterministic**: No learning state that affects hash contracts
- **Performance friendly**: Simple step counter, no complex re-calculation
- **Aligns with existing cooldown patterns**: Similar to current bilateral exchange behavior

**Implementation**:
```python
# In unified target selection
if agent.current_target_type == "trade" and agent.steps_pursuing_target > MAX_PURSUIT_STEPS:
    # Re-evaluate if trade is taking too long to materialize
    agent.abandon_target()
    # Next step will re-run unified target selection
```

#### 9. Agent Availability Broadcasting (DECIDED: Passive Observation)
**VMT Recommendation**: **Passive observation only** because:
- **Maintains existing patterns**: Builds on current perception-based visibility
- **Deterministic**: No additional signaling state to track
- **O() compliant**: No broadcast overhead or additional data structures
- **Realistic**: Mirrors real-world trading where you assess partners by visible cues
- **Hash contract safe**: Uses existing observable state only

**Implementation**:
```python
# Agents observe visible information only
def estimate_trade_utility(self, partner: Agent) -> float:
    if not partner.is_available_for_trade():  # Cooldown, etc.
        return 0.0
    
    visible_inventory = partner.carrying  # Observable within perception
    return self._calculate_mutual_benefit(self.carrying, visible_inventory)
```

#### 10. Interaction with Existing Cooldown System (DECIDED: Reuse Existing Logic)
**VMT Recommendation**: **Reuse existing cooldown logic exactly** to maintain consistency between unified and trading-only modes. The cooldown system is already well-tuned and tested.

**Integration approach**:
```python
def scan_available_trade_partners(self, nearby_agents: List[Agent]) -> List[Agent]:
    available = []
    for agent in nearby_agents:
        # Filter using existing bilateral exchange availability logic
        if (agent != self and 
            agent.trade_cooldown_remaining == 0 and
            not agent.is_currently_trading and
            not agent.is_committed_to_other_target()):
            available.append(agent)
    
    return available
```

**Cooldown timing decisions (DECIDED)**:
- **Target becomes unavailable**: Agent should gracefully abandon and re-select
- **Self goes on cooldown**: Should complete current pursuit (don't abandon mid-journey)
- **Cooldown duration consistency**: Use existing bilateral exchange cooldown values

#### 11. Multiple Agents Targeting Same Trade Partner (DECIDED: First-Come-First-Served)
**VMT Recommendation**: **First-come-first-served** because:
- **Minimal complexity**: No additional reservation state or conflict resolution
- **Deterministic**: Agent arrival order determined by existing movement system
- **Matches existing patterns**: Similar to current resource collection (first to arrive gets it)
- **Performance friendly**: No additional bookkeeping or conflict resolution overhead
- **Realistic**: Mirrors real-world trading where timing matters

**Implementation**:
```python
# When agent reaches trade target
def attempt_trade_with_target(self, target_agent: Agent) -> bool:
    if target_agent.is_available_for_trade():
        # Proceed with existing bilateral exchange logic
        return self.initiate_bilateral_trade(target_agent)
    else:
        # Target no longer available - abandon and re-select next step
        self.abandon_current_target()
        return False
```

The losing agents simply re-run unified target selection on the next step, potentially finding other good opportunities that opened up.

### Test Migration Questions (Expanded & Critical)

#### 12. Determinism Test Updates - Breaking Change Management (DECIDED: Update All Reference Hashes)
**Critical impact**: Distance-discounted utility fundamentally changes target selection logic from tiebreak-based to utility-based primary criterion.

**VMT Recommendation**: 
- **Update all reference hashes deliberately** with `k=1.0` as new baseline
- **Document the breaking change** in commit message and gate documentation
- **Add regression tests** comparing single vs unified behavior modes
- **Validate metric hash contract** still excludes trade metrics as intended

**Tests requiring hash updates**:
1. **All existing determinism tests** in `tests/unit/test_determinism.py`
2. **Agent movement tests** that verify specific target selection
3. **Simulation snapshot tests** that capture agent decision states

**Migration strategy**:
```python
# Phase 1: Update reference hashes with k=1.0 default
def test_determinism_foraging_distance_discounted():
    """Updated determinism test for distance-discounted foraging"""
    config = SimConfig(distance_scaling_factor=1.0)
    # New reference hash for distance-discounted behavior
    expected_hash = "NEW_HASH_POST_DISTANCE_DISCOUNTING"
    assert sim.get_metrics().determinism_hash() == expected_hash

# Phase 2: Add k=0 tests to verify pure utility behavior
def test_determinism_no_distance_penalty():
    """Verify k=0 produces pure utility maximization"""
    config = SimConfig(distance_scaling_factor=0.0)

# Phase 3: Add spatial indexing determinism tests  
def test_spatial_indexing_determinism():
    """Verify AgentSpatialGrid produces consistent agent ordering"""
```

#### 13. Backward Compatibility Validation - Single-Behavior Mode Verification (DECIDED: Economic Equivalence Testing)
**Critical requirement**: Single-behavior modes must produce economically equivalent results with distance-discounted utility.

**VMT Recommendation**:
- **Economic behavior validation**: Test that distance discounting produces intuitive economic decisions
- **Boundary condition testing**: Verify k=0 (pure utility) and k=10 (highly local) work correctly
- **Smooth transition validation**: Ensure no abrupt behavioral changes across k values
- **Performance equivalence**: Single-behavior modes should maintain current FPS performance

**Validation test strategy**:
```python
def test_single_behavior_economic_equivalence():
    """Verify single-behavior modes make economically sensible decisions"""
    
    # Test 1: High k should prefer nearby lower-utility resources
    config_high_k = SimConfig(distance_scaling_factor=5.0, trade_enabled=False)
    sim_high_k = run_scenario(config_high_k, scenario="nearby_low_vs_distant_high_utility")
    assert_prefers_nearby_resources(sim_high_k)
    
    # Test 2: k=0 should prefer highest utility regardless of distance  
    config_no_distance = SimConfig(distance_scaling_factor=0.0, trade_enabled=False)
    sim_no_distance = run_scenario(config_no_distance, scenario="nearby_low_vs_distant_high_utility")
    assert_prefers_highest_utility_resources(sim_no_distance)

def test_behavioral_continuity():
    """Verify smooth behavioral transition across k values"""
    k_values = [0.0, 0.5, 1.0, 2.0, 5.0, 10.0]
    # Verify smooth transitions: higher k → shorter distances, potentially lower total utility
```

#### 14. Spatial Indexing Determinism - AgentSpatialGrid Consistency (DECIDED: Strict Determinism Testing)
**Critical requirement**: Spatial indexing must produce identical results across runs while maintaining O(agents+resources) complexity.

**VMT Recommendation**:
- **Strict determinism testing**: Multiple runs must produce identical spatial query results
- **Equivalence validation**: Spatial indexing must find same agents as direct scan
- **Cell boundary testing**: Verify consistent behavior at grid cell boundaries  
- **Agent ordering preservation**: Maintain original agent list order within cells

**Determinism challenges**:
1. **Hash table iteration order**: Python dict iteration must be deterministic
2. **Cell processing order**: Must be consistent across spatial queries
3. **Agent ordering within cells**: Must preserve original agent list ordering
4. **Distance filtering stability**: Equal-distance agents must maintain relative order

**Test implementation**:
```python
def test_spatial_indexing_determinism():
    """Verify AgentSpatialGrid produces consistent results across multiple runs"""
    for run in range(10):  # Multiple runs
        agents = create_test_scenario()
        spatial_index = AgentSpatialGrid(40, 40, cell_size=1)
        # Build and query index
        query_results = perform_spatial_queries(spatial_index, agents)
        
        if run == 0:
            reference_results = query_results
        else:
            assert query_results == reference_results, f"Spatial index non-deterministic on run {run}"

def test_spatial_index_vs_direct_scan_equivalence():
    """Verify spatial indexing produces same results as direct O(n²) scan"""
    # Compare spatial indexing vs current bilateral exchange direct scan
    # Both methods should find identical agents within perception radius
```

#### 15. Performance Regression Testing (DECIDED: Defer Until Post-Implementation)
**Scope change**: Defer comprehensive performance testing until unified target selection implementation is complete.

**Rationale**: 
- **Implementation-first approach**: Focus on core functionality and determinism before optimization analysis
- **Comprehensive evaluation**: Performance testing should be part of broader complexity analysis of all agent decision systems
- **Reduced scope creep**: Avoid premature optimization during architectural transition
- **Future integration**: Will be included in comprehensive agent decision complexity evaluation

**Deferred scope**:
- Spatial indexing overhead vs. O(agents²) elimination benchmarks
- Memory usage analysis of AgentSpatialGrid
- FPS regression testing across various agent/resource counts
- Integration with existing VMT performance harness (`make perf`)

**Post-implementation evaluation plan**:
1. Complete unified target selection implementation
2. Validate determinism and economic behavior
3. Conduct comprehensive agent decision complexity analysis
4. Include spatial indexing performance as part of broader optimization review