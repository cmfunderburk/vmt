# Unified Target Selection Planning

## User Prompt

I'd like to switch focus and work on unifying the target selection decision when both bilateral exchange and foraging are enabled. Let's discuss options. My initial thought is to unify the target selection logic such that: when both foraging+bilateral exchange are enabled, the agent searches for both goods and agents to trade with; whichever is closest takes priority, tiebreaks based on marginal utility diff; once a target is selected, the agent should carry out that task and be unavailable for target selection by other agents until they have completed the task (i.e. finished trading with an agent or picked up a resource). Once completed, they restart the loop. What are your thoughts?

## LLM Response:
## Overview

Proposal to unify the target selection decision when both bilateral exchange and foraging are enabled. Current system has artificial separation between foraging and trading decisions, while unified approach would let agents choose the most valuable opportunity (resource or trade partner) based on marginal utility.

## Current Architecture Analysis

The current system has **separated decision paths**:
1. **Foraging-only**: `agent.step_decision()` handles resource targeting via `select_target()`
2. **Trading-only**: `_handle_bilateral_exchange_movement()` handles agent-to-agent targeting
3. **Both enabled**: Sequential processing with "foraging first" precedence (agents who collect are excluded from trading that tick)

### Current Flow (Both Systems Enabled)
```
Simulation.step():
  for agent in agents:
    collected = agent.step_decision(grid)  # Foraging
    if collected:
      foraged_ids.add(agent.id)
  
  # Later: Trade intent enumeration excludes agents in foraged_ids
  if both_systems_enabled and foraged_ids:
    filtered_agents = [ag for ag in coloc_agents if ag.id not in foraged_ids]
```

## Proposed Unified Approach

### Core Concept
When both foraging+bilateral exchange are enabled, the agent searches for both goods and agents to trade with; whichever is closest takes priority, with tiebreaks based on marginal utility difference. Once a target is selected, the agent carries out that task and is unavailable for target selection by other agents until task completion.

### Benefits
1. **Eliminates artificial precedence**: Currently foraging gets priority, but unified approach lets utility drive the decision
2. **More realistic economic behavior**: Agents choose the most valuable opportunity regardless of type
3. **Cleaner architecture**: Single decision function instead of separated logic paths
4. **Better resource allocation**: Prevents agents from "missing" better trading opportunities while pursuing low-value resources

## Implementation Strategy

### Phase 1: Unified Target Selection Function
Create a new method `Agent.select_unified_target(grid, agents)` that:
- Scans both resources and available agents within perception radius
- Calculates expected utility gain for each option:
  - **Resources**: `ΔU = U(carrying + resource) - U(carrying)`
  - **Trade partners**: `ΔU ≈ marginal_utility_gain_from_optimal_trade(partner)`
- Uses proposed tiebreak: `(-ΔU, distance, x, y)` for resources, `(-ΔU, distance, agent_id)` for agents
- Returns unified target type (resource position or agent id)

### Phase 2: Unified Movement & Commitment
- Add agent state to track commitment: `current_task: Optional[Union[ResourceTarget, TradeTarget]]`
- Make agents unavailable for targeting while committed
- Task completion triggers new target selection

### Phase 3: Integration & Flag Management
Replace the current branching logic in `world.py` with unified path when both systems enabled.

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

### 3. Tiebreak Details
**Question**: For trade targets, what's the full tiebreak key?

**Suggested**: `(-ΔU, distance, target_agent_id)` for consistency with resource tiebreaks `(-ΔU, distance, x, y)`

### 4. Determinism Preservation
**Requirements**:
- Maintain stable iteration order over agents and resources
- Ensure unified target scanning is deterministic
- Keep existing test contracts intact
- Preserve hash parity when features disabled

## Implementation Questions

### 1. Feature Flag Strategy
Should we implement this as a **feature flag initially** (`ECONSIM_UNIFIED_TARGETING=1`) to allow A/B testing against current behavior?

**Benefits**:
- Gradual rollout
- Performance comparison
- Regression testing
- Easier rollback if issues found

### 2. Movement System Integration
How should we handle the **bilateral exchange movement system** that currently includes sophisticated pairing/pathfinding?

**Options**:
- Keep the existing sophisticated movement for trade targets
- Simplify to match resource targeting (greedy movement)
- Hybrid approach based on distance/complexity

**Current bilateral system**: 6-tier decision logic (perception → pairing → pathfinding → co-location → trading → cooldowns)

### 3. Performance Considerations
The unified approach needs to scan both resources AND agents. Current complexity is O(agents + resources) per agent.

**Options**:
- Add spatial indexing for agents (like resources have grid-based lookup)
- Maintain the O(agents + resources) bound by limiting perception radius
- Pre-compute agent availability states
- Cache trade utility calculations

## Current Code Integration Points

### Files to Modify
- `agent.py`: Add unified target selection method
- `world.py`: Modify step logic for unified path
- `simulation/constants.py`: Add any new constants
- Tests: Add unified targeting tests

### Existing Methods to Consider
- `Agent.select_target()`: Current resource-only targeting
- `Simulation._handle_bilateral_exchange_movement()`: Current trade-only targeting
- `Agent.step_decision()`: Current movement execution

### Environment Variables
Current flags that would interact:
- `ECONSIM_FORAGE_ENABLED`: Controls resource collection
- `ECONSIM_TRADE_*`: Controls trading behavior
- Proposed: `ECONSIM_UNIFIED_TARGETING`: Enable unified approach

## Determinism Requirements (VMT Constraints)

From copilot instructions, must preserve:
- Target tie-break key EXACT: (-ΔU, distance, x, y)
- Stable resource iteration (`iter_resources_sorted`)
- Original agent list order resolves contests
- O(agents+resources) step complexity
- No hidden randomness
- Metrics hash contract (trade metrics excluded)

## Next Steps

1. **Design Review**: Finalize approach for trade utility estimation
2. **Prototype**: Implement Phase 1 unified target selection function
3. **Testing**: Create determinism tests for unified approach
4. **Integration**: Modify world.py step logic
5. **Performance**: Validate O(agents+resources) bound maintained
6. **Documentation**: Update API guide and copilot instructions

## Open Questions

1. Should trade utility estimation be conservative (underestimate) or optimistic?
2. How should we handle cases where estimated trade value doesn't materialize?
3. Should agents broadcast their availability/inventory for better trade estimation?
4. How does this interact with the existing cooldown system?
5. What happens when multiple agents target the same trade partner simultaneously?