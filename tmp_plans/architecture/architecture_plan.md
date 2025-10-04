# VMT Codebase Architecture Restructure Plan

## Problem Statement

The current VMT codebase has grown organically and now suffers from several architectural issues that impact maintainability and extensibility:

### Current Issues

1. **Mixed Responsibilities**: The `simulation/` directory contains multiple distinct concerns:
   - Agent behavior and decision-making logic
   - Grid/spatial data structures and indexing
   - Step execution orchestration
   - Trading mechanics
   - Component architecture (inventory, trading partners, target selection)

2. **Unclear Boundaries**: Related functionality is scattered across multiple files:
   - Agent logic spans `agent.py`, `agent_mode_utils.py`, and `components/`
   - Grid/spatial logic is split between `grid.py`, `spatial.py`, and `world.py`
   - GUI code is distributed across `gui/` and `tools/launcher/`

3. **Tight Coupling**: Components have circular dependencies and unclear interfaces:
   - `world.py` orchestrates everything but doesn't clearly separate concerns
   - Agent components are tightly coupled to simulation state
   - GUI components directly import simulation internals

4. **Testing Complexity**: Current structure makes it difficult to:
   - Test individual components in isolation
   - Mock dependencies cleanly
   - Understand component boundaries

## Proposed Solution: Domain-Driven Restructure

### New Folder Structure

```
src/econsim/
├── gui/                    # All GUI components
│   ├── __init__.py
│   ├── launcher/           # Test launcher GUI
│   ├── widgets/            # Reusable GUI widgets
│   ├── analysis/           # Economic analysis displays
│   └── embedded/           # Embedded pygame components
└── simulation/             # Core simulation domain
    ├── __init__.py
    ├── agent/              # Agent behavior and decision-making
    │   ├── __init__.py
    │   ├── core.py         # Main Agent class
    │   ├── decision_making.py  # Unified selection pass logic
    │   ├── components/     # Agent sub-components
    │   │   ├── inventory/
    │   │   ├── trading_partner/
    │   │   └── target_selection/
    │   └── modes.py        # Agent mode management
    ├── world/              # Grid and spatial systems
    │   ├── __init__.py
    │   ├── grid.py         # Grid data structure
    │   ├── spatial.py      # Spatial indexing and queries
    │   ├── respawn.py      # Resource respawn logic
    │   └── coordinates.py  # Position utilities
    ├── logging/            # Recording and delta systems
    │   ├── __init__.py
    │   ├── delta/          # Current delta system
    │   ├── recorder.py     # Recording interfaces
    │   └── playback.py     # Playback engines
    ├── executor.py         # StepExecutor (renamed from step_executor.py)
    ├── coordinator.py      # Simulation coordinator (renamed from world.py)
    ├── config.py           # Simulation configuration
    ├── features.py         # Feature flags
    └── constants.py        # Simulation constants
```

## Detailed Migration Plan

### Phase 1: Agent Domain (`simulation/agent/`)

**Goal**: Consolidate all agent-related functionality into a cohesive domain.

**Files to Move/Create**:
- `simulation/agent.py` → `simulation/agent/core.py`
- `simulation/agent_mode_utils.py` → `simulation/agent/modes.py`
- `simulation/components/` → `simulation/agent/components/`
- Extract unified selection logic into `simulation/agent/decision_making.py`

**Key Responsibilities**:
- Agent state management (position, inventory, mode)
- Decision-making algorithms (target selection, trading)
- Component coordination (inventory, trading partners, target selection)
- Mode transitions and behavior

**Interface Design**:
```python
# simulation/agent/core.py
class Agent:
    def step_decision(self, world_state: WorldState) -> DecisionResult
    def select_target(self, world_state: WorldState) -> TargetChoice
    def execute_trade(self, partner: Agent, intent: TradeIntent) -> TradeResult

# simulation/agent/decision_making.py  
class UnifiedSelectionEngine:
    def select_best_action(self, agent: Agent, world_state: WorldState) -> ActionChoice
```

### Phase 2: World Domain (`simulation/world/`)

**Goal**: Isolate spatial and grid management from simulation orchestration.

**Files to Move/Create**:
- `simulation/grid.py` → `simulation/world/grid.py`
- `simulation/spatial.py` → `simulation/world/spatial.py`
- `simulation/respawn.py` → `simulation/world/respawn.py`
- Create `simulation/world/coordinates.py` for position utilities

**Key Responsibilities**:
- Grid data structure and resource management
- Spatial indexing and neighbor queries
- Resource spawning and respawn logic
- Position validation and boundary checking

**Interface Design**:
```python
# simulation/world/grid.py
class Grid:
    def get_resources_in_radius(self, center: Position, radius: int) -> List[Resource]
    def place_resource(self, position: Position, resource_type: str) -> bool
    def remove_resource(self, position: Position) -> bool

# simulation/world/spatial.py
class SpatialIndex:
    def find_agents_in_radius(self, center: Position, radius: int) -> List[Agent]
    def find_nearest_resources(self, center: Position, count: int) -> List[Resource]
```

### Phase 3: Simulation Domain (Core Files)

**Goal**: Focus on step execution orchestration and simulation coordination.

**Files to Move/Create**:
- `simulation/step_executor.py` → `simulation/executor.py`
- `simulation/world.py` → `simulation/coordinator.py`
- Keep: `config.py`, `features.py`, `constants.py`
- Move `trade.py` to `simulation/trading.py`

**Key Responsibilities**:
- Step execution orchestration
- Feature flag management
- Simulation configuration
- Trading system coordination
- Performance metrics collection

**Interface Design**:
```python
# simulation/executor.py
class SimulationExecutor:
    def execute_step(self, simulation_state: SimulationState) -> StepResult
    def collect_metrics(self) -> MetricsSnapshot

# simulation/coordinator.py
class SimulationCoordinator:
    def __init__(self, grid: Grid, agents: List[Agent], config: SimConfig)
    def step(self, rng: Random) -> SimulationStep
```

### Phase 4: GUI Domain (`gui/`)

**Goal**: Consolidate all GUI components under a single domain.

**Files to Move/Create**:
- `gui/` (existing) → `gui/analysis/`
- `tools/launcher/` → `gui/launcher/`
- `tools/widgets/` → `gui/widgets/`
- Move embedded pygame components to `gui/embedded/`

**Key Responsibilities**:
- Test launcher interface
- Economic analysis displays
- Reusable UI components
- Embedded simulation visualizations

### Phase 5: Logging Domain (`simulation/logging/`)

**Goal**: Consolidate all recording and playback functionality.

**Files to Move/Create**:
- `delta/` (existing) → `simulation/logging/delta/`
- Create `simulation/logging/recorder.py` for recording interfaces
- Create `simulation/logging/playback.py` for playback engines

**Key Responsibilities**:
- Delta recording and serialization
- Playback and state reconstruction
- Recording interface abstractions
- Performance monitoring

## Implementation Strategy

### Migration Approach

1. **Parallel Development**: Create a new `source/` folder alongside existing `src/` folder for incremental migration
2. **Interface Preservation**: Maintain existing public APIs during transition
3. **Dependency Injection**: Use dependency injection to decouple components
4. **Clear Boundaries**: Define explicit interfaces between domains
5. **Gradual Replacement**: Once fully migrated and tested, evaluate replacement of old `src/` folder

### New Source Structure

The implementation will create a parallel `source/` directory with the new architecture:

```
source/econsim/
├── gui/                    # All GUI components
└── simulation/             # Core simulation domain
    ├── agent/              # Agent behavior and decision-making
    ├── world/              # Grid and spatial systems
    └── logging/            # Recording and delta systems
```

This approach allows:
- **Zero Risk**: Original `src/` remains untouched during development
- **Incremental Testing**: Test new architecture alongside existing system
- **Gradual Migration**: Move functionality piece by piece
- **Rollback Safety**: Can abandon new structure if issues arise
- **Comparison Testing**: Run both systems in parallel for validation

### Dependency Management

**New Dependency Graph**:
```
simulation/agent/ → simulation/world/, preferences/
simulation/world/ → preferences/
simulation/logging/ → simulation/agent/, simulation/world/
gui/ → simulation/
```

**Key Principles**:
- No circular dependencies between domains
- Simulation subdomains (agent, world, logging) have clear interfaces
- GUI domain only depends on public simulation interfaces
- Logging domain is passive and doesn't affect simulation behavior
- All simulation logic contained within `simulation/` directory

### Interface Design Patterns

1. **Domain Services**: Each subdomain (agent, world, logging) exposes clear service interfaces
2. **Value Objects**: Use immutable data structures for cross-domain communication
3. **Event-Driven**: Use events for loose coupling between simulation subdomains
4. **Factory Pattern**: Centralized creation of simulation objects
5. **Facade Pattern**: Simulation coordinator provides unified interface to GUI

## Benefits of This Restructure

### Maintainability
- **Clear Separation of Concerns**: Each subdomain has a single, well-defined responsibility
- **Reduced Coupling**: Simulation subdomains depend only on interfaces, not implementations
- **Easier Testing**: Each subdomain can be tested in isolation
- **Logical Organization**: All simulation logic contained within `simulation/` directory

### Extensibility
- **Plugin Architecture**: New agent behaviors can be added within `simulation/agent/` without affecting other subdomains
- **Alternative Implementations**: Can swap out grid implementations or GUI frameworks
- **Feature Flags**: Easy to add new features without affecting existing simulation code
- **Modular Design**: Clear boundaries allow independent development of simulation subdomains

### Developer Experience
- **Intuitive Navigation**: Developers know exactly where to find simulation functionality within `simulation/` directory
- **Clear Dependencies**: Easy to understand how simulation subdomains interact
- **Focused Development**: Teams can work on different simulation subdomains independently
- **Consistent Structure**: All simulation code follows the same organizational pattern

## Migration Timeline

### Week 1-2: Agent Domain
- Create `source/econsim/simulation/agent/` structure
- Move agent files from `src/` to `source/` and refactor interfaces
- Update imports and dependencies
- Add comprehensive tests
- Validate against existing `src/` functionality

### Week 3-4: World Domain  
- Create `source/econsim/simulation/world/` structure
- Move grid and spatial files from `src/` to `source/`
- Refactor spatial indexing interfaces
- Update agent dependencies
- Cross-validate with existing system

### Week 5-6: Simulation Core Files
- Create core simulation files in `source/econsim/simulation/`
- Refactor step executor and coordinator in `source/`
- Update trading system integration
- Performance testing and optimization
- Parallel execution testing with `src/`

### Week 7-8: GUI Domain
- Create `source/econsim/gui/` structure
- Consolidate GUI components from `src/`
- Update launcher architecture
- UI testing and validation
- Feature parity verification

### Week 9-10: Logging Domain
- Create `source/econsim/simulation/logging/` structure
- Move delta system from `src/` to `source/`
- Refactor recording interfaces
- Integration testing
- Full system validation

### Week 11-12: Migration Completion
- Comprehensive testing of new `source/` architecture
- Performance benchmarking against `src/`
- Evaluation of migration success
- Decision on replacing `src/` with `source/`

## Risk Mitigation

### Breaking Changes
- **Parallel Development**: New `source/` folder allows zero-risk development
- **Backward Compatibility**: Maintain existing public APIs during migration
- **Gradual Rollout**: Move files incrementally with feature flags
- **Comprehensive Testing**: Full test suite must pass at each step
- **Validation Gates**: Each domain must pass validation before proceeding

### Performance Impact
- **Benchmarking**: Measure performance before and after each phase
- **Optimization**: Profile and optimize critical paths
- **Rollback Plan**: Ability to revert changes if performance degrades

### Team Coordination
- **Documentation**: Clear migration guide for team members
- **Code Reviews**: All changes require thorough review
- **Communication**: Regular updates on migration progress

## Next Steps

1. **Team Review**: Discuss this plan with the development team
2. **Create Source Structure**: Set up the new `source/econsim/` directory structure with nested simulation organization
3. **Prototype**: Create a small prototype of the new structure in `source/econsim/simulation/`
4. **Timeline Refinement**: Adjust timeline based on team capacity
5. **Tool Selection**: Choose migration tools and automation
6. **Begin Migration**: Start with the Agent domain within `simulation/agent/` as it has the clearest boundaries
7. **Validation Framework**: Establish testing framework to compare `src/` vs `source/`

## Migration Success Criteria

Before replacing `src/` with `source/`, the following must be validated:

- **Functional Parity**: All existing functionality works identically
- **Performance Parity**: No performance regression (≤5% tolerance)
- **Test Coverage**: 100% of existing tests pass
- **Integration Tests**: All integration scenarios work correctly
- **GUI Validation**: All UI components function properly
- **Documentation**: Complete API documentation for new structure

## Final Decision Process

After Week 11-12 completion:
1. **Comprehensive Testing**: Full regression test suite
2. **Performance Benchmarking**: Detailed performance comparison
3. **Code Quality Assessment**: Architecture quality metrics
4. **Team Evaluation**: Developer experience feedback
5. **Go/No-Go Decision**: Based on success criteria above

## Summary

This restructure will transform VMT from a monolithic simulation into a well-architected, maintainable, and extensible system with the following key improvements:

### Organizational Benefits:
- **Centralized Simulation Logic**: All simulation code contained within `simulation/` directory
- **Clear Subdomain Boundaries**: Agent, world, and logging concerns separated within simulation domain
- **Intuitive Navigation**: Developers immediately know where to find specific functionality
- **Scalable Architecture**: Easy to add new simulation features without affecting existing code

### Technical Benefits:
- **Zero Risk Migration**: Parallel development in `source/` folder preserves existing functionality
- **Modular Design**: Each simulation subdomain can be developed and tested independently
- **Clean Interfaces**: Clear contracts between simulation subdomains and GUI
- **Future-Proof**: Architecture supports growth and new requirements

This approach ensures zero risk to the existing codebase while providing a clear path to a more maintainable and extensible system.
