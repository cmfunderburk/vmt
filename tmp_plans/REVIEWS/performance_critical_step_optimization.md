# Performance-Critical Step Method Optimization Plan

## Problem Statement

The current step handler architecture, while excellent for maintainability and testability, introduces **45% performance regression** due to:

- **5x method call overhead** (5 handlers vs 1 monolithic method)
- **~10 object creations per step** (StepContext, StepResult objects)
- **Feature flag parsing overhead** every step
- **Metrics aggregation overhead** across handlers

This is **unacceptable for a critical performance component** where the simulation step method is called thousands of times per second.

## Design Principles

### Primary: Performance First
- **Minimize method call overhead** - prefer inline logic over handler dispatch
- **Eliminate object creation** - reuse objects, use direct variable access
- **Cache feature flags** - parse environment variables once, not every step
- **Direct metrics** - avoid dictionary aggregation overhead

### Secondary: Maintainability & Extensibility
- **Modular organization** - separate concerns into focused methods within the same class
- **Clear separation** - movement, collection, trading, respawn, metrics as distinct sections
- **Testable components** - individual methods can be unit tested
- **Extensible design** - new features can be added as new methods without breaking existing logic

## Implementation Strategy

### Phase 1: Consolidate into Optimized Step Method
1. **Create `src/econsim/simulation/step_executor.py`** - new optimized step execution module
2. **Consolidate handler logic** - merge all 5 handlers into a single optimized step method
3. **Eliminate object creation** - use direct variable access instead of StepContext/StepResult
4. **Cache feature flags** - parse environment variables once per simulation, not per step
5. **Direct metrics collection** - use simple variables instead of dictionary aggregation

### Phase 2: Maintain Handler Interface for Testing
1. **Keep handler classes** - for unit testing individual components
2. **Add test mode** - allow switching between optimized and handler modes
3. **Preserve testability** - individual methods can still be tested in isolation

### Phase 3: Performance Validation
1. **Benchmark comparison** - measure against canonical baseline
2. **Profile optimization** - identify remaining bottlenecks
3. **Validate determinism** - ensure behavioral preservation

## Detailed Implementation Plan

### 1. Create Optimized Step Executor Module

```python
# src/econsim/simulation/step_executor.py
class OptimizedStepExecutor:
    """High-performance step executor with minimal overhead."""
    
    def __init__(self, simulation):
        self.simulation = simulation
        # Cache feature flags once per simulation
        self._cached_features = None
        self._features_dirty = True
    
    def execute_step(self, rng: random.Random) -> Dict[str, Any]:
        """Execute one simulation step with minimal overhead."""
        # Direct variable access - no object creation
        step_num = self.simulation._steps + 1
        
        # Cached feature flag access
        if self._features_dirty:
            self._cached_features = self._parse_feature_flags()
            self._features_dirty = False
        
        # Direct metrics collection
        metrics = {
            'agents_moved': 0,
            'resources_collected': 0,
            'trades_executed': 0,
            'mode_changes': 0
        }
        
        # Inline execution of all handlers
        self._execute_movement(step_num, rng, metrics)
        self._execute_collection(step_num, metrics)
        self._execute_trading(step_num, rng, metrics)
        self._execute_respawn(step_num, rng, metrics)
        self._execute_metrics(step_num, metrics)
        
        return metrics
```

### 2. Consolidate Handler Logic

**Movement Logic** (from MovementHandler):
```python
def _execute_movement(self, step_num: int, rng: random.Random, metrics: Dict[str, Any]) -> None:
    """Execute movement logic with minimal overhead."""
    forage_enabled = self._cached_features['forage_enabled']
    unified_disabled = self._cached_features['unified_disabled']
    
    if forage_enabled and not unified_disabled:
        # Unified selection pass
        foraged_ids = set()
        self.simulation._unified_selection_pass(rng, foraged_ids, step_num)
        metrics['agents_moved'] = len(self.simulation.agents)
        self.simulation._transient_foraged_ids = foraged_ids
    elif forage_enabled:
        # Decision mode
        for agent in self.simulation.agents:
            collected = agent.step_decision(self.simulation.grid, step_num)
            if collected:
                metrics['agents_moved'] += 1
    else:
        # No forage mode
        self._handle_no_forage_movement(step_num, rng, metrics)
```

**Collection Logic** (from CollectionHandler):
```python
def _execute_collection(self, step_num: int, metrics: Dict[str, Any]) -> None:
    """Execute resource collection with minimal overhead."""
    # Direct collection logic without handler overhead
    for agent in self.simulation.agents:
        if agent.mode == AgentMode.FORAGE and agent.target:
            # Collection already handled in movement, just count
            pass
```

### 3. Feature Flag Caching

> **Note:** This step would implement feature flag caching using environment variables, but we plan to rethink this approach in the near future. The long-term goal is to move away from environment variables as the primary means of controlling simulation behavior, in favor of a more explicit and testable configuration system.

### 4. Maintain Testability

```python
# Keep handler classes for testing
class MovementHandler:
    def execute(self, context: StepContext) -> StepResult:
        """Handler interface for testing."""
        # Implementation for unit tests
        
# Add test mode to simulation
class Simulation:
    def __init__(self, ..., use_optimized_step: bool = True):
        if use_optimized_step:
            self._step_executor = OptimizedStepExecutor(self)
        else:
            self._step_executor = StepExecutor(handlers)  # Legacy handler mode
```
> **Note:** Once the optimized step executor is verified to match all test and performance requirements, immediately remove the legacy handler classes and all compatibility code. The simulation should always use the optimized step execution path.

## Expected Performance Impact

### Optimizations Applied:
- **Eliminate 5 method calls** → Single method execution
- **Eliminate ~10 object creations** → Direct variable access
- **Cache feature flags** → Parse once per simulation
- **Direct metrics** → No dictionary aggregation
- **Inline logic** → No handler dispatch overhead

### Expected Results:
- **Target: 95%+ of canonical baseline performance**
- **Maintain: All existing functionality and determinism**
- **Preserve: Testability through handler interface**
- **Enable: Easy feature addition through modular methods**

## Implementation Timeline

1. **Day 1**: Create OptimizedStepExecutor module and consolidate movement logic
2. **Day 2**: Consolidate collection, trading, and respawn logic
3. **Day 3**: Add metrics collection and feature flag caching
4. **Day 4**: Performance testing and validation
5. **Day 5**: Integration testing and determinism validation

## Risk Mitigation

- **Preserve handler interface** for testing and fallback
- **Maintain exact RNG call patterns** for determinism
- **Keep feature flag compatibility** for existing behavior
- **Add performance regression tests** to prevent future issues

## Success Criteria

- **Performance**: Achieve 95%+ of canonical baseline (999.3 steps/sec)
- **Determinism**: Pass all existing determinism tests
- **Functionality**: Maintain all existing feature flag combinations
- **Testability**: Preserve unit test coverage through handler interface
- **Maintainability**: Keep code organized and extensible despite optimization

This approach prioritizes performance while maintaining the architectural benefits of the refactor through careful organization and preserved testing interfaces.
