# Unified VMT Refactoring Plan

*Generated on 2025-01-27*

## Executive Summary

This document provides a comprehensive, unified plan to refactor the two largest files in the VMT codebase: `debug_logger.py` (8.2K tokens, 1,610 lines) and `world.py` (5.9K tokens, 1,059 lines). The plan addresses shared concerns, eliminates duplication, and creates a cohesive architecture that improves maintainability while preserving performance and determinism.

## Current State Analysis

### Shared Problems
1. **Environment Variable Dependencies**: Both files heavily rely on `os.environ` for configuration
2. **Mixed Responsibilities**: Core logic mixed with logging, performance tracking, and configuration
3. **Monolithic Design**: Single classes handling multiple concerns
4. **Tight Coupling**: Direct dependencies between subsystems
5. **Verbose Documentation**: Excessive docstring repetition across both files

### File-Specific Issues

#### debug_logger.py
- Complex singleton pattern with extensive buffering logic
- Multiple event builders and parsing methods
- 1,610 lines in single class
- Complex state management with multiple buffer types

#### world.py
- Massive 400+ line step method
- Complex conditional logic based on environment variables
- Mixed simulation logic with logging and performance tracking
- Deep nesting and multiple execution branches

## Unified Refactoring Strategy

### Phase 1: Shared Infrastructure (Week 1)

#### Step 1.1: Create Unified Configuration System
**File**: `src/econsim/core/config.py`

```python
"""Unified configuration management for VMT."""

import os
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass

class LogLevel(Enum):
    CRITICAL = "CRITICAL"
    EVENTS = "EVENTS"
    PERIODIC = "PERIODIC"
    VERBOSE = "VERBOSE"

@dataclass
class VMTConfig:
    """Unified configuration for VMT simulation and logging."""
    
    # Simulation flags
    legacy_random: bool = False
    forage_enabled: bool = True
    trade_draft: bool = False
    trade_exec: bool = False
    debug_agent_modes: bool = False
    priority_trade: bool = False
    hash_neutral_trade: bool = False
    
    # Logging configuration
    log_level: LogLevel = LogLevel.VERBOSE
    log_categories: set = None
    log_format: str = "STRUCTURED_ONLY"
    bundle_trades: bool = False
    explanations: bool = False
    
    # Performance settings
    enable_respawn: bool = True
    enable_metrics: bool = True
    performance_log_interval: int = 1000
    
    @classmethod
    def from_environment(cls) -> "VMTConfig":
        """Create configuration from environment variables."""
        return cls(
            legacy_random=cls._get_bool_flag('ECONSIM_LEGACY_RANDOM', False),
            forage_enabled=cls._get_bool_flag('ECONSIM_FORAGE_ENABLED', True),
            trade_draft=cls._get_bool_flag('ECONSIM_TRADE_DRAFT', False),
            trade_exec=cls._get_bool_flag('ECONSIM_TRADE_EXEC', False),
            debug_agent_modes=cls._get_bool_flag('ECONSIM_DEBUG_AGENT_MODES', False),
            priority_trade=cls._get_bool_flag('ECONSIM_PRIORITY_TRADE', False),
            hash_neutral_trade=cls._get_bool_flag('ECONSIM_HASH_NEUTRAL_TRADE', False),
            log_level=cls._get_log_level(),
            log_categories=cls._get_enabled_categories(),
            log_format=os.environ.get('ECONSIM_LOG_FORMAT', 'STRUCTURED_ONLY'),
            bundle_trades=cls._get_bool_flag('ECONSIM_LOG_BUNDLE_TRADES', False),
            explanations=cls._get_bool_flag('ECONSIM_LOG_EXPLANATIONS', False),
            enable_respawn=cls._get_bool_flag('ECONSIM_ENABLE_RESPAWN', True),
            enable_metrics=cls._get_bool_flag('ECONSIM_ENABLE_METRICS', True),
            performance_log_interval=int(os.environ.get('ECONSIM_PERF_LOG_INTERVAL', '1000')),
        )
    
    @staticmethod
    def _get_bool_flag(env_var: str, default: bool) -> bool:
        """Get boolean flag from environment variable."""
        value = os.environ.get(env_var, '').lower()
        return value in ('1', 'true', 'yes', 'on')
    
    @staticmethod
    def _get_log_level() -> LogLevel:
        """Get log level from environment."""
        level_str = os.environ.get("ECONSIM_LOG_LEVEL", "VERBOSE").upper()
        try:
            return LogLevel(level_str)
        except ValueError:
            return LogLevel.VERBOSE
    
    @staticmethod
    def _get_enabled_categories() -> set:
        """Get enabled log categories."""
        categories = os.environ.get('ECONSIM_LOG_CATEGORIES', '').split(',')
        return {cat.strip() for cat in categories if cat.strip()}
    
    def get_execution_mode(self) -> str:
        """Determine execution mode based on flags."""
        if self.legacy_random:
            return 'random'
        elif self.forage_enabled and self.trade_draft:
            return 'unified'
        elif self.forage_enabled:
            return 'forage'
        else:
            return 'idle'
    
    def should_log_category(self, category: str) -> bool:
        """Check if category should be logged."""
        if not self.log_categories:
            return True
        return category in self.log_categories
```

#### Step 1.2: Create Shared Performance Tracking
**File**: `src/econsim/core/performance.py`

```python
"""Unified performance tracking for VMT."""

import time
from typing import Dict, Any, Optional
from collections import deque
from .config import VMTConfig

class PerformanceTracker:
    """Unified performance tracking for simulation and logging."""
    
    def __init__(self, config: VMTConfig):
        self.config = config
        self.step_times = deque(maxlen=100)
        self.last_log_step = 0
        self.total_steps = 0
        self.start_time = time.time()
    
    def track_step(self, step_num: int, start_time: float, end_time: float) -> None:
        """Track step performance metrics."""
        step_time = end_time - start_time
        self.step_times.append(step_time)
        self.total_steps = step_num
        
        # Log performance at intervals
        if step_num - self.last_log_step >= self.config.performance_log_interval:
            self._log_performance(step_num)
            self.last_log_step = step_num
    
    def _log_performance(self, step_num: int) -> None:
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
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        return {
            'fps': self.get_current_fps(),
            'avg_step_time': self.get_average_step_time(),
            'total_steps': self.total_steps,
            'uptime': time.time() - self.start_time
        }
    
    def reset(self) -> None:
        """Reset performance tracking."""
        self.step_times.clear()
        self.last_log_step = 0
        self.total_steps = 0
        self.start_time = time.time()
```

### Phase 2: Logging System Refactoring (Week 1-2)

#### Step 2.1: Create Logging Infrastructure
**File**: `src/econsim/gui/logging/__init__.py`

```python
"""Logging system for VMT GUI."""

from .logger import GUILogger
from .convenience import (
    get_gui_logger,
    log_agent_mode,
    log_trade,
    log_simulation,
    log_utility_change,
    log_performance,
    finalize_log_session
)
from .formatters import format_agent_id, format_delta

__all__ = [
    "GUILogger",
    "get_gui_logger",
    "log_agent_mode",
    "log_trade",
    "log_simulation", 
    "log_utility_change",
    "log_performance",
    "finalize_log_session",
    "format_agent_id",
    "format_delta"
]
```

#### Step 2.2: Create Modular Logging Components
**Files**: 
- `src/econsim/gui/logging/logger.py` (Simplified main logger)
- `src/econsim/gui/logging/event_builders.py` (Event construction)
- `src/econsim/gui/logging/buffers.py` (Message buffering)
- `src/econsim/gui/logging/parsers.py` (Message parsing)
- `src/econsim/gui/logging/file_manager.py` (File I/O)
- `src/econsim/gui/logging/formatters.py` (Formatting utilities)
- `src/econsim/gui/logging/convenience.py` (Global access functions)

### Phase 3: Simulation System Refactoring (Week 2-3)

#### Step 3.1: Create Simulation Infrastructure
**File**: `src/econsim/simulation/__init__.py`

```python
"""Simulation system for VMT."""

from .world import Simulation
from .execution_strategies import ExecutionStrategyFactory
from .step_components import StepComponentManager
from .performance_tracker import SimulationPerformanceTracker

__all__ = [
    "Simulation",
    "ExecutionStrategyFactory", 
    "StepComponentManager",
    "SimulationPerformanceTracker"
]
```

#### Step 3.2: Create Modular Simulation Components
**Files**:
- `src/econsim/simulation/execution_strategies.py` (Execution modes)
- `src/econsim/simulation/step_components.py` (Step execution)
- `src/econsim/simulation/performance_tracker.py` (Simulation-specific performance)

### Phase 4: Integration and Coordination (Week 3-4)

#### Step 4.1: Create Unified World Class
**File**: `src/econsim/simulation/world.py` (Refactored)

```python
"""Unified simulation coordinator with integrated logging."""

import random
import time
from typing import List, Optional
from ..core.config import VMTConfig
from ..core.performance import PerformanceTracker
from .execution_strategies import ExecutionStrategyFactory
from .step_components import StepComponentManager
from ..gui.logging import get_gui_logger

class Simulation:
    """Unified simulation coordinator with integrated logging and performance tracking."""
    
    def __init__(self, grid, agents, config: VMTConfig):
        """Initialize simulation with unified configuration."""
        self.grid = grid
        self.agents = agents
        self.config = config
        self.step_count = 0
        
        # Initialize components
        self.execution_strategy = ExecutionStrategyFactory.create(self, config)
        self.step_components = StepComponentManager(self, config)
        self.performance_tracker = PerformanceTracker(config)
        self.logger = get_gui_logger()
    
    def step(self, rng: random.Random, *, use_decision: bool = False):
        """Execute one simulation step with integrated logging and performance tracking."""
        start_time = time.time()
        
        # Execute the main simulation logic
        self.execution_strategy.execute(rng, use_decision)
        
        # Execute all step components
        self.step_components.execute_all(rng, self.step_count)
        
        # Track performance
        end_time = time.time()
        self.performance_tracker.track_step(self.step_count, start_time, end_time)
        
        # Log performance if needed
        if self.config.should_log_category("PERF"):
            self._log_step_performance(start_time, end_time)
        
        self.step_count += 1
    
    def _log_step_performance(self, start_time: float, end_time: float):
        """Log step performance metrics."""
        step_time = end_time - start_time
        fps = 1.0 / step_time if step_time > 0 else 0
        
        self.logger.log("PERF", 
            f"Step {self.step_count}: {step_time:.4f}s, FPS: {fps:.1f}", 
            self.step_count)
    
    def get_performance_stats(self) -> dict:
        """Get current performance statistics."""
        return self.performance_tracker.get_stats()
    
    def reset_performance_tracking(self):
        """Reset performance tracking."""
        self.performance_tracker.reset()
    
    @classmethod
    def from_config(cls, config: VMTConfig, agent_positions: Optional[List[tuple]] = None):
        """Create simulation from unified configuration."""
        # Implementation details...
        pass
```

#### Step 4.2: Update Main Debug Logger
**File**: `src/econsim/gui/debug_logger.py` (Refactored)

```python
"""Centralized GUI debug logging system for VMT EconSim.

Provides unified logging to timestamped files in gui_logs/ directory.
All debug output from simulation components should use this logging system
instead of direct print statements for better organization and GUI integration.
"""

# Import all functionality from new modules
from .logging.logger import GUILogger
from .logging.convenience import (
    get_gui_logger,
    log_agent_mode,
    log_trade,
    log_simulation,
    log_utility_change,
    log_performance,
    finalize_log_session
)
from .logging.formatters import format_agent_id, format_delta

# Maintain backward compatibility
__all__ = [
    "GUILogger",
    "get_gui_logger", 
    "log_agent_mode",
    "log_trade", 
    "log_simulation",
    "log_utility_change",
    "log_performance",
    "finalize_log_session",
    "format_agent_id",
    "format_delta"
]
```

## Implementation Timeline

### Week 1: Foundation
- [ ] Create unified configuration system (`core/config.py`)
- [ ] Create shared performance tracking (`core/performance.py`)
- [ ] Create logging infrastructure modules
- [ ] Update imports and dependencies
- [ ] Test configuration system

### Week 2: Logging System
- [ ] Implement all logging modules
- [ ] Create event builders and parsers
- [ ] Implement buffer management
- [ ] Create file I/O manager
- [ ] Test logging system components

### Week 3: Simulation System
- [ ] Create execution strategies
- [ ] Implement step components
- [ ] Create simulation performance tracker
- [ ] Refactor main Simulation class
- [ ] Test simulation components

### Week 4: Integration & Testing
- [ ] Integrate logging and simulation systems
- [ ] Update main debug_logger.py
- [ ] Create comprehensive unit tests
- [ ] Create integration tests
- [ ] Performance validation
- [ ] Documentation updates

## Expected Benefits

### Unified Architecture
- **Shared Configuration**: Single source of truth for all environment variables
- **Integrated Performance Tracking**: Unified performance monitoring across systems
- **Consistent Logging**: Standardized logging interface for all components
- **Reduced Duplication**: Eliminate duplicate configuration and performance code

### Code Quality Improvements
- **Reduced Complexity**: Break down monolithic files into focused modules
- **Better Separation of Concerns**: Clear boundaries between logging, simulation, and configuration
- **Improved Testability**: Isolated components easier to unit test
- **Enhanced Maintainability**: Modular design easier to understand and modify

### Performance Benefits
- **Unified Performance Tracking**: Single performance monitoring system
- **Reduced Memory Usage**: Smaller object graphs and shared components
- **Better Caching**: Isolated components can be optimized independently
- **Faster Imports**: Reduced circular dependencies

### Developer Experience
- **Unified Interface**: Single configuration system for all components
- **Consistent APIs**: Standardized interfaces across logging and simulation
- **Better Documentation**: Focused, modular documentation
- **Easier Extension**: New features can be added as new components

## Risk Mitigation

### Backward Compatibility
- Maintain all existing public APIs
- Preserve all convenience functions
- Keep same file structure for imports
- No breaking changes to existing code

### Performance Impact
- Benchmark before and after refactoring
- Maintain deterministic behavior
- Preserve existing performance characteristics
- Monitor logging overhead (<2% as specified)

### Testing Strategy
- Comprehensive unit tests for all new modules
- Integration tests for complete workflows
- Performance regression testing
- Determinism validation with existing tests

## Success Criteria

### Code Quality Metrics
- [ ] Reduce debug_logger.py from 1,610 lines to <200 lines
- [ ] Reduce world.py from 1,059 lines to <300 lines
- [ ] Create 10+ focused modules with single responsibilities
- [ ] Achieve 90%+ test coverage for new modules
- [ ] Maintain all existing functionality

### Performance Metrics
- [ ] No performance regression in logging overhead
- [ ] Maintain <2% logging overhead as specified
- [ ] Preserve deterministic behavior
- [ ] Maintain FPS targets (≥30 FPS, target ~60 FPS)

### Architecture Metrics
- [ ] Unified configuration system eliminates environment variable duplication
- [ ] Shared performance tracking reduces code duplication
- [ ] Modular design enables independent testing and optimization
- [ ] Clear separation of concerns improves maintainability

## Conclusion

This unified refactoring plan addresses both the debug logger and world.py files as part of a cohesive architecture. By creating shared infrastructure for configuration and performance tracking, we eliminate duplication while improving maintainability and testability.

The phased approach ensures minimal risk while delivering significant improvements to code organization, performance, and developer experience. The result will be a cleaner, more maintainable codebase that's easier to understand, test, and extend while maintaining the performance and determinism characteristics required by the VMT project.
