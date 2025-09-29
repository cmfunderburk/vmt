# World.py Refactoring Plan

*Generated on 2025-01-27*

## Overview

This document provides a detailed, step-by-step plan for refactoring `src/econsim/simulation/world.py` to address its complexity, improve maintainability, and enhance code organization while preserving determinism and performance characteristics.

## Current State Analysis

### File Statistics
- **Size**: 1,059 lines of code (5.9K tokens)
- **Complexity**: Massive step method with 400+ lines
- **Dependencies**: Heavy reliance on environment variables
- **Responsibilities**: Mixed simulation logic, logging, and performance tracking

### Key Issues
1. **Monolithic Step Method**: Single method handling multiple execution paths
2. **Environment Variable Dependencies**: Feature flags scattered throughout
3. **Mixed Responsibilities**: Simulation logic mixed with logging and performance tracking
4. **Complex Conditional Logic**: Deep nesting and multiple execution branches
5. **Tight Coupling**: Direct dependencies on multiple subsystems

## Refactoring Strategy

### Phase 1: Extract Feature Flag Management

#### Step 1.1: Create Feature Flags Module
**File**: `src/econsim/simulation/feature_flags.py`

```python
"""Centralized feature flag management for simulation."""

import os
from typing import Dict, Any


class FeatureFlags:
    """Manages all simulation feature flags from environment variables."""
    
    def __init__(self):
        self._flags = self._load_flags()
    
    def _load_flags(self) -> Dict[str, Any]:
        """Load all feature flags from environment variables."""
        return {
            'legacy_random': self._get_bool_flag('ECONSIM_LEGACY_RANDOM', False),
            'forage_enabled': self._get_bool_flag('ECONSIM_FORAGE_ENABLED', True),
            'trade_draft': self._get_bool_flag('ECONSIM_TRADE_DRAFT', False),
            'trade_exec': self._get_bool_flag('ECONSIM_TRADE_EXEC', False),
            'debug_agent_modes': self._get_bool_flag('ECONSIM_DEBUG_AGENT_MODES', False),
            'priority_trade': self._get_bool_flag('ECONSIM_PRIORITY_TRADE', False),
            'hash_neutral_trade': self._get_bool_flag('ECONSIM_HASH_NEUTRAL_TRADE', False),
        }
    
    def _get_bool_flag(self, env_var: str, default: bool) -> bool:
        """Get boolean flag from environment variable."""
        value = os.environ.get(env_var, '').lower()
        return value in ('1', 'true', 'yes', 'on')
    
    @property
    def legacy_random(self) -> bool:
        """Whether to use legacy random walk mode."""
        return self._flags['legacy_random']
    
    @property
    def forage_enabled(self) -> bool:
        """Whether foraging is enabled."""
        return self._flags['forage_enabled']
    
    @property
    def trade_draft(self) -> bool:
        """Whether trade drafting is enabled."""
        return self._flags['trade_draft']
    
    @property
    def trade_exec(self) -> bool:
        """Whether trade execution is enabled."""
        return self._flags['trade_exec']
    
    @property
    def debug_agent_modes(self) -> bool:
        """Whether to debug agent modes."""
        return self._flags['debug_agent_modes']
    
    @property
    def priority_trade(self) -> bool:
        """Whether priority trading is enabled."""
        return self._flags['priority_trade']
    
    @property
    def hash_neutral_trade(self) -> bool:
        """Whether hash-neutral trading is enabled."""
        return self._flags['hash_neutral_trade']
    
    def get_execution_mode(self) -> str:
        """Determine the execution mode based on flags."""
        if self.legacy_random:
            return 'random'
        elif self.forage_enabled and self.trade_draft:
            return 'unified'
        elif self.forage_enabled:
            return 'forage'
        else:
            return 'idle'
```

#### Step 1.2: Update World.py Imports
**File**: `src/econsim/simulation/world.py`

```python
# Add import
from .feature_flags import FeatureFlags
```

#### Step 1.3: Replace Environment Variable Checks
Replace all `os.environ.get()` calls with `self.feature_flags` property access.

### Phase 2: Extract Execution Strategies

#### Step 2.1: Create Execution Strategies Module
**File**: `src/econsim/simulation/execution_strategies.py`

```python
"""Execution strategies for different simulation modes."""

import random
from typing import List, Optional
from .agent import Agent
from .grid import Grid
from .trade import TradeIntent


class ExecutionStrategy:
    """Base class for simulation execution strategies."""
    
    def __init__(self, simulation):
        self.simulation = simulation
    
    def execute(self, rng: random.Random, use_decision: bool = False):
        """Execute the simulation step."""
        raise NotImplementedError


class RandomWalkStrategy(ExecutionStrategy):
    """Handles random walk execution mode."""
    
    def execute(self, rng: random.Random, use_decision: bool = False):
        """Execute random walk for all agents."""
        for agent in self.simulation.agents:
            agent.random_walk(rng, self.simulation.grid)


class ForageStrategy(ExecutionStrategy):
    """Handles foraging execution mode."""
    
    def execute(self, rng: random.Random, use_decision: bool = False):
        """Execute foraging for all agents."""
        for agent in self.simulation.agents:
            agent.forage_step(rng, self.simulation.grid)


class UnifiedSelectionStrategy(ExecutionStrategy):
    """Handles unified selection execution mode."""
    
    def execute(self, rng: random.Random, use_decision: bool = False):
        """Execute unified selection for all agents."""
        # Collect all possible actions
        actions = self._collect_actions(rng, use_decision)
        
        # Sort by utility and execute
        actions.sort(key=lambda x: (-x.utility_delta, x.distance, x.x, x.y))
        
        # Execute actions
        self._execute_actions(actions, rng)
    
    def _collect_actions(self, rng: random.Random, use_decision: bool) -> List:
        """Collect all possible actions from agents."""
        actions = []
        
        for agent in self.simulation.agents:
            if use_decision:
                agent_actions = agent.decide_actions(rng, self.simulation.grid)
            else:
                agent_actions = agent.get_available_actions(rng, self.simulation.grid)
            
            actions.extend(agent_actions)
        
        return actions
    
    def _execute_actions(self, actions: List, rng: random.Random):
        """Execute the collected actions."""
        for action in actions:
            action.execute(rng, self.simulation.grid)


class IdleStrategy(ExecutionStrategy):
    """Handles idle execution mode."""
    
    def execute(self, rng: random.Random, use_decision: bool = False):
        """Execute idle mode - no agent actions."""
        pass


class ExecutionStrategyFactory:
    """Factory for creating execution strategies."""
    
    @staticmethod
    def create(simulation, feature_flags) -> ExecutionStrategy:
        """Create appropriate execution strategy based on feature flags."""
        if feature_flags.legacy_random:
            return RandomWalkStrategy(simulation)
        elif feature_flags.forage_enabled and feature_flags.trade_draft:
            return UnifiedSelectionStrategy(simulation)
        elif feature_flags.forage_enabled:
            return ForageStrategy(simulation)
        else:
            return IdleStrategy(simulation)
```

#### Step 2.2: Update World.py to Use Strategies
**File**: `src/econsim/simulation/world.py`

```python
# Add imports
from .execution_strategies import ExecutionStrategyFactory

# In Simulation.__init__:
def __init__(self, grid: Grid, agents: List[Agent], config: SimConfig):
    # ... existing initialization ...
    self.feature_flags = FeatureFlags()
    self.execution_strategy = ExecutionStrategyFactory.create(self, self.feature_flags)

# Replace the massive step method:
def step(self, rng: random.Random, *, use_decision: bool = False):
    """Execute one simulation step."""
    start_time = time.time()
    
    # Execute the main simulation logic
    self.execution_strategy.execute(rng, use_decision)
    
    # Handle trade execution if enabled
    if self.feature_flags.trade_exec:
        self._execute_trades(rng)
    
    # Handle respawn if enabled
    if self.config.enable_respawn:
        self._handle_respawn(rng)
    
    # Update metrics
    if self.config.enable_metrics:
        self._update_metrics()
    
    # Log performance if needed
    self._log_performance(start_time)
```

### Phase 3: Extract Step Components

#### Step 3.1: Create Step Components Module
**File**: `src/econsim/simulation/step_components.py`

```python
"""Modular components for simulation step execution."""

import random
import time
from typing import List, Optional
from .agent import Agent
from .grid import Grid
from .trade import TradeIntent
from .metrics import Metrics


class StepComponent:
    """Base class for step execution components."""
    
    def __init__(self, simulation):
        self.simulation = simulation
    
    def execute(self, rng: random.Random, step_num: int):
        """Execute the component for this step."""
        raise NotImplementedError


class TradeExecutionComponent(StepComponent):
    """Handles trade execution logic."""
    
    def execute(self, rng: random.Random, step_num: int):
        """Execute trades if enabled."""
        if not self.simulation.feature_flags.trade_exec:
            return
        
        # Collect trade intents
        intents = self._collect_trade_intents()
        
        # Execute at most one trade per step
        if intents:
            trade = self._select_trade(intents, rng)
            if trade:
                trade.execute(rng, self.simulation.grid)
    
    def _collect_trade_intents(self) -> List[TradeIntent]:
        """Collect trade intents from agents."""
        intents = []
        for agent in self.simulation.agents:
            agent_intents = agent.get_trade_intents()
            intents.extend(agent_intents)
        return intents
    
    def _select_trade(self, intents: List[TradeIntent], rng: random.Random) -> Optional[TradeIntent]:
        """Select one trade to execute."""
        if not intents:
            return None
        
        # Sort by utility and select first
        intents.sort(key=lambda x: (-x.utility_delta, x.seller_id, x.buyer_id))
        return intents[0]


class RespawnComponent(StepComponent):
    """Handles resource respawn logic."""
    
    def execute(self, rng: random.Random, step_num: int):
        """Handle resource respawn if enabled."""
        if not self.simulation.config.enable_respawn:
            return
        
        self.simulation.grid.respawn_resources(rng)


class MetricsComponent(StepComponent):
    """Handles metrics collection."""
    
    def execute(self, rng: random.Random, step_num: int):
        """Update metrics if enabled."""
        if not self.simulation.config.enable_metrics:
            return
        
        self.simulation.metrics.update_step(step_num, self.simulation.agents, self.simulation.grid)


class PerformanceComponent(StepComponent):
    """Handles performance tracking and logging."""
    
    def __init__(self, simulation):
        super().__init__(simulation)
        self.step_times = []
        self.last_log_step = 0
    
    def execute(self, rng: random.Random, step_num: int):
        """Track performance metrics."""
        # This would be called with timing information from the main step method
        pass
    
    def track_step(self, step_num: int, start_time: float, end_time: float):
        """Track step performance."""
        step_time = end_time - start_time
        self.step_times.append(step_time)
        
        # Log performance every 1000 steps
        if step_num - self.last_log_step >= 1000:
            self._log_performance(step_num)
            self.last_log_step = step_num
    
    def _log_performance(self, step_num: int):
        """Log performance statistics."""
        if not self.step_times:
            return
        
        avg_time = sum(self.step_times) / len(self.step_times)
        fps = 1.0 / avg_time if avg_time > 0 else 0
        
        print(f"Step {step_num}: Avg step time: {avg_time:.4f}s, FPS: {fps:.1f}")
        self.step_times.clear()


class StepComponentManager:
    """Manages all step components."""
    
    def __init__(self, simulation):
        self.simulation = simulation
        self.components = self._create_components()
    
    def _create_components(self) -> List[StepComponent]:
        """Create all step components."""
        return [
            TradeExecutionComponent(self.simulation),
            RespawnComponent(self.simulation),
            MetricsComponent(self.simulation),
            PerformanceComponent(self.simulation),
        ]
    
    def execute_all(self, rng: random.Random, step_num: int):
        """Execute all components."""
        for component in self.components:
            component.execute(rng, step_num)
```

#### Step 3.2: Update World.py to Use Components
**File**: `src/econsim/simulation/world.py`

```python
# Add imports
from .step_components import StepComponentManager

# In Simulation.__init__:
def __init__(self, grid: Grid, agents: List[Agent], config: SimConfig):
    # ... existing initialization ...
    self.step_components = StepComponentManager(self)

# Update the step method:
def step(self, rng: random.Random, *, use_decision: bool = False):
    """Execute one simulation step."""
    start_time = time.time()
    
    # Execute the main simulation logic
    self.execution_strategy.execute(rng, use_decision)
    
    # Execute all step components
    self.step_components.execute_all(rng, self.step_count)
    
    # Track performance
    end_time = time.time()
    self.step_components.components[-1].track_step(self.step_count, start_time, end_time)
    
    self.step_count += 1
```

### Phase 4: Extract Performance Tracking

#### Step 4.1: Create Performance Tracker Module
**File**: `src/econsim/simulation/performance_tracker.py`

```python
"""Performance tracking and monitoring for simulation."""

import time
from typing import List, Optional
from collections import deque


class PerformanceTracker:
    """Handles performance monitoring and logging."""
    
    def __init__(self, log_interval: int = 1000):
        self.log_interval = log_interval
        self.step_times = deque(maxlen=100)  # Keep last 100 step times
        self.last_log_step = 0
        self.total_steps = 0
    
    def track_step(self, step_num: int, start_time: float, end_time: float):
        """Track step performance metrics."""
        step_time = end_time - start_time
        self.step_times.append(step_time)
        self.total_steps = step_num
        
        # Log performance at intervals
        if step_num - self.last_log_step >= self.log_interval:
            self._log_performance(step_num)
            self.last_log_step = step_num
    
    def _log_performance(self, step_num: int):
        """Log performance statistics."""
        if not self.step_times:
            return
        
        avg_time = sum(self.step_times) / len(self.step_times)
        fps = 1.0 / avg_time if avg_time > 0 else 0
        min_time = min(self.step_times)
        max_time = max(self.step_times)
        
        print(f"Performance at step {step_num}:")
        print(f"  Avg step time: {avg_time:.4f}s")
        print(f"  FPS: {fps:.1f}")
        print(f"  Min time: {min_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")
        print(f"  Total steps: {self.total_steps}")
    
    def get_current_fps(self) -> float:
        """Get current FPS based on recent step times."""
        if not self.step_times:
            return 0.0
        
        avg_time = sum(self.step_times) / len(self.step_times)
        return 1.0 / avg_time if avg_time > 0 else 0.0
    
    def get_average_step_time(self) -> float:
        """Get average step time in seconds."""
        if not self.step_times:
            return 0.0
        
        return sum(self.step_times) / len(self.step_times)
    
    def reset(self):
        """Reset performance tracking."""
        self.step_times.clear()
        self.last_log_step = 0
        self.total_steps = 0
```

#### Step 4.2: Update World.py to Use Performance Tracker
**File**: `src/econsim/simulation/world.py`

```python
# Add import
from .performance_tracker import PerformanceTracker

# In Simulation.__init__:
def __init__(self, grid: Grid, agents: List[Agent], config: SimConfig):
    # ... existing initialization ...
    self.performance_tracker = PerformanceTracker()

# Update the step method:
def step(self, rng: random.Random, *, use_decision: bool = False):
    """Execute one simulation step."""
    start_time = time.time()
    
    # Execute the main simulation logic
    self.execution_strategy.execute(rng, use_decision)
    
    # Execute all step components
    self.step_components.execute_all(rng, self.step_count)
    
    # Track performance
    end_time = time.time()
    self.performance_tracker.track_step(self.step_count, start_time, end_time)
    
    self.step_count += 1
```

### Phase 5: Simplify Main Simulation Class

#### Step 5.1: Clean Up World.py
**File**: `src/econsim/simulation/world.py`

```python
"""Simplified simulation coordinator."""

import random
import time
from typing import List, Optional
from .grid import Grid
from .agent import Agent
from .config import SimConfig
from .feature_flags import FeatureFlags
from .execution_strategies import ExecutionStrategyFactory
from .step_components import StepComponentManager
from .performance_tracker import PerformanceTracker


class Simulation:
    """Simplified simulation coordinator."""
    
    def __init__(self, grid: Grid, agents: List[Agent], config: SimConfig):
        """Initialize simulation with components."""
        self.grid = grid
        self.agents = agents
        self.config = config
        self.step_count = 0
        
        # Initialize components
        self.feature_flags = FeatureFlags()
        self.execution_strategy = ExecutionStrategyFactory.create(self, self.feature_flags)
        self.step_components = StepComponentManager(self)
        self.performance_tracker = PerformanceTracker()
    
    def step(self, rng: random.Random, *, use_decision: bool = False):
        """Execute one simulation step."""
        start_time = time.time()
        
        # Execute the main simulation logic
        self.execution_strategy.execute(rng, use_decision)
        
        # Execute all step components
        self.step_components.execute_all(rng, self.step_count)
        
        # Track performance
        end_time = time.time()
        self.performance_tracker.track_step(self.step_count, start_time, end_time)
        
        self.step_count += 1
    
    def get_performance_stats(self) -> dict:
        """Get current performance statistics."""
        return {
            'fps': self.performance_tracker.get_current_fps(),
            'avg_step_time': self.performance_tracker.get_average_step_time(),
            'total_steps': self.performance_tracker.total_steps
        }
    
    def reset_performance_tracking(self):
        """Reset performance tracking."""
        self.performance_tracker.reset()
    
    @classmethod
    def from_config(cls, config: SimConfig, agent_positions: Optional[List[tuple]] = None):
        """Create simulation from configuration."""
        # ... existing implementation ...
        pass
```

## Implementation Timeline

### Week 1: Foundation
- [ ] Create `feature_flags.py` module
- [ ] Update `world.py` to use feature flags
- [ ] Test feature flag functionality
- [ ] Update existing tests

### Week 2: Execution Strategies
- [ ] Create `execution_strategies.py` module
- [ ] Implement all strategy classes
- [ ] Update `world.py` to use strategies
- [ ] Test strategy execution

### Week 3: Step Components
- [ ] Create `step_components.py` module
- [ ] Implement all component classes
- [ ] Update `world.py` to use components
- [ ] Test component execution

### Week 4: Performance & Cleanup
- [ ] Create `performance_tracker.py` module
- [ ] Simplify main `Simulation` class
- [ ] Update all tests
- [ ] Performance validation
- [ ] Documentation updates

## Testing Strategy

### Unit Tests
- Test each feature flag independently
- Test each execution strategy in isolation
- Test each step component separately
- Test performance tracker functionality

### Integration Tests
- Test complete simulation step execution
- Test feature flag combinations
- Test performance characteristics
- Test determinism preservation

### Performance Tests
- Benchmark before and after refactoring
- Validate FPS targets (≥30 FPS, target ~60 FPS)
- Check memory usage
- Verify deterministic behavior

## Risk Mitigation

### Backward Compatibility
- Maintain existing public APIs
- Use deprecation warnings for internal changes
- Provide migration guides for any breaking changes

### Performance Impact
- Benchmark each phase of refactoring
- Maintain deterministic behavior
- Preserve existing performance characteristics
- Monitor FPS throughout implementation

### Testing Strategy
- Comprehensive unit tests for new components
- Integration tests for refactored systems
- Performance regression testing
- Determinism validation

## Expected Benefits

### Code Quality
- **Reduced Complexity**: Smaller, focused classes with single responsibilities
- **Improved Testability**: Isolated components easier to unit test
- **Better Maintainability**: Clear separation of concerns
- **Enhanced Readability**: Simplified logic flow

### Performance
- **Reduced Memory Usage**: Smaller object graphs
- **Faster Imports**: Reduced circular dependencies
- **Better Caching**: Isolated components can be optimized independently

### Developer Experience
- **Easier Debugging**: Clear component boundaries
- **Simpler Extension**: New features can be added as new components
- **Better Documentation**: Focused, concise documentation
- **Reduced Cognitive Load**: Smaller files easier to understand

## Conclusion

This refactoring plan addresses the core issues in `world.py` while maintaining backward compatibility and performance characteristics. The proposed changes will significantly improve code maintainability, readability, and extensibility while reducing the cognitive load for developers working with the codebase.

The implementation should be done incrementally to minimize risk and ensure that each phase can be validated before proceeding to the next. Each phase includes comprehensive testing to ensure no regressions are introduced.
