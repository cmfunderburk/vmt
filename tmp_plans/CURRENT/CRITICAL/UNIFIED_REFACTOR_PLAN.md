# VMT EconSim Refactoring Implementation Plan

**Target**: `src/econsim/simulation/` + `src/econsim/gui/debug_logger.py`  
**Scope**: Decompose monolithic components, eliminate circular dependencies, preserve determinism

## Problems Addressed

- Monolithic `Simulation.step()` (450+ lines) and `GUILogger` class (2500+ lines)
- Circular dependency: simulation layer imports GUI debug logger
- Scattered environment flag handling across multiple modules
- Singleton patterns preventing unit testing
- O(n log n) operations in simulation critical path

## Architecture Goals

- Break simulation → GUI dependency via observer pattern
- Decompose `Simulation.step()` into focused, testable handlers
- Replace monolithic logger with modular observers
- Centralize environment flag management
- Preserve deterministic behavior and educational features

## Implementation Phases

| Phase | Risk | Dependencies | Key Deliverables |
|-------|------|--------------|------------------|
| **Phase 0**: Baseline Capture | LOW | None | Determinism hashes, performance baselines, safety nets |
| **Phase 1**: Observer Foundation | LOW | Phase 0 | Observer protocol, event system, configuration consolidation |
| **Phase 2**: Step Decomposition | MEDIUM | Phase 1 | Step executor framework, handler implementations |
| **Phase 3**: Logger Refactoring | HIGH | Phase 1 | Modular observers, buffer system, legacy migration |
| **Phase 4**: Integration | MEDIUM | Phase 2,3 | Factory integration, validation suite |

**Critical**: Complete each phase before starting the next. No parallel work on coupled components.

---

## Phase 0: Baseline Capture

**Objective**: Establish validation framework before making changes.

### Deliverables

1. **Determinism Hash Capture**
   ```bash
   pytest -q --capture-determinism-hash > baselines/determinism_reference.txt
   ```

2. **Performance Baseline**
   - First implement comprehensive performance test for current testrunner system
   - Benchmark `Simulation.step()` performance across all 7 educational test scenarios
   - Capture steps/second metrics for each scenario configuration
   ```bash
   # After implementing performance test:
   python tests/performance/baseline_capture.py > baselines/performance_baseline.json
   ```

3. **Golden Log Capture**
   ```bash
   ECONSIM_DEBUG_AGENT_MODES=1 ECONSIM_DEBUG_TRADES=1 python scripts/golden_log_capture.py
   ```

4. **Safety Net Tests**
   - Create `tests/integration/test_refactor_safeguards.py`
   - Add targeted tests around `Simulation.step()` and `GUILogger` APIs
   - Verify all tests pass

### Completion Criteria
- All existing tests pass with captured reference hashes
- **Comprehensive performance test implemented and baseline captured** for current testrunner
- Golden debug logs saved for comparison  
- Safety net integration tests implemented and passing

---

## Phase 1: Observer Foundation

**Objective**: Break simulation → GUI dependency via observer pattern.

### Step 1.1: Core Event System & Observer Protocol

**Implementation**:
```python
# NEW: src/econsim/observability/
├── __init__.py           # Public API exports
├── events.py             # Event data models 
├── observers.py          # Observer protocol and base classes
├── config.py             # Centralized observability configuration  
└── registry.py           # Observer registration system
```

**Key Components**:
1. **Event Protocol**:
```python
@dataclass(frozen=True)
class SimulationEvent:
    step: int
    timestamp: float
    event_type: str

@dataclass(frozen=True)
class AgentModeChangeEvent(SimulationEvent):
    agent_id: int
    old_mode: str
    new_mode: str
    reason: str = ""
```

2. **Observer Interface**:
```python
class SimulationObserver(Protocol):
    def notify(self, event: SimulationEvent) -> None: ...
    def flush_step(self, step: int) -> None: ...
    def close(self) -> None: ...
```

### Step 1.2: Configuration Consolidation & Registry

**Implementation**:
```python
# NEW: src/econsim/simulation/features.py
@dataclass
class SimulationFeatures:
    """Centralized simulation feature flag management."""
    legacy_random_movement: bool
    forage_enabled: bool
    trade_draft_enabled: bool
    trade_execution_enabled: bool
    
    @classmethod
    def from_environment(cls) -> 'SimulationFeatures': ...

# NEW: src/econsim/observability/config.py  
@dataclass
class ObservabilityConfig:
    """Centralized observability configuration."""
    agent_mode_logging: bool
    trade_logging: bool
    behavioral_aggregation: bool
    
    @classmethod
    def from_environment(cls) -> 'ObservabilityConfig': ...
```

### Step 1.3: Simulation Integration & Legacy Adapter

**Implementation**:
```python
# MODIFY: src/econsim/simulation/world.py
from ..observability.registry import ObserverRegistry

class Simulation:
    def __init__(self, config: SimConfig, observers: List[SimulationObserver] = None):
        self._observer_registry = ObserverRegistry()
        if observers:
            for observer in observers:
                self._observer_registry.register(observer)

# NEW: src/econsim/observability/legacy_adapter.py
class LegacyLoggerAdapter(BaseObserver):
    """Backward compatibility for existing debug_logger API."""
    
    def __init__(self, gui_logger: 'GUILogger'):
        self._gui_logger = gui_logger
        
    def notify(self, event: SimulationEvent) -> None:
        # Route events to existing GUILogger methods
        if isinstance(event, AgentModeChangeEvent):
            self._gui_logger.log_agent_mode_change(...)
```

### Completion Criteria
- Observer protocol defined with type safety
- All environment flags centralized in feature managers  
- Simulation integration with zero behavioral changes
- Legacy adapter maintains 100% API compatibility
- All Phase 0 baselines still validate

---

## Phase 2: Step Decomposition

**Objective**: Decompose monolithic `Simulation.step()` into focused, testable components.

### Step 2.1: Step Executor Framework

**Implementation**:
```python
# NEW: src/econsim/simulation/execution/
├── __init__.py           # Public API
├── step_executor.py      # Main step coordination  
├── context.py            # Shared step context
└── handlers/             # Individual step handlers
    ├── movement_handler.py
    ├── trading_handler.py
    ├── collection_handler.py
    ├── metrics_handler.py
    └── respawn_handler.py
```

**Key Architecture**:
```python
@dataclass
class StepContext:
    """Immutable context passed between handlers."""
    simulation: 'Simulation'
    step_number: int
    ext_rng: random.Random
    feature_flags: SimulationFeatures
    observer_registry: ObserverRegistry

class StepHandler(Protocol):
    def execute(self, context: StepContext) -> StepResult: ...

class StepExecutor:
    def __init__(self, handlers: List[StepHandler]):
        self._handlers = handlers
        
    def execute_step(self, context: StepContext) -> None:
        for handler in self._handlers:
            result = handler.execute(context)
            # Emit observer events based on result
```

### Step 2.2: Movement & Collection Handlers

**Implementation**:
```python
class MovementHandler:
    """Handles agent movement decisions and execution."""
    
    def execute(self, context: StepContext) -> StepResult:
        # Extract existing movement logic from Simulation.step()
        # Maintain exact same ordering and RNG call patterns
        # Emit AgentMoveEvent through observer registry
        pass

class CollectionHandler:
    """Handles resource collection with spatial optimization."""
    
    def execute(self, context: StepContext) -> StepResult:
        # Extract foraging logic with Grid.iter_resources_sorted()
        # Preserve distance-based tie-breaking  
        # Emit ResourceCollectionEvent
        pass
```

### Step 2.3: Trading & Metrics Handlers

**Implementation**:  
```python
class TradingHandler:
    """Handles bilateral trading intent enumeration and execution."""
    
    def execute(self, context: StepContext) -> StepResult:
        if not context.feature_flags.trade_draft_enabled:
            return StepResult.empty()
            
        # Phase 1: Enumerate all trading intents  
        intents = self._enumerate_trading_intents(context)
        
        # Phase 2: Execute single best intent (if execution enabled)
        if context.feature_flags.trade_execution_enabled and intents:
            executed_intent = self._execute_best_intent(intents, context)
            # Emit TradeExecutionEvent
            
        return StepResult(trade_metrics={"intents_count": len(intents)})
```

### Completion Criteria
- `Simulation.step()` method <100 lines (orchestration only)
- Each step handler <50 lines with single responsibility
- Identical deterministic behavior (hash verification against Phase 0)
- Performance overhead <1% vs baseline
- Component-level unit tests with >90% coverage

---

## Phase 3: Logger Refactoring

**Objective**: Decompose monolithic `GUILogger` into modular observer components.

### Step 3.1: Buffer System Architecture

**Implementation**:
```python
# NEW: src/econsim/observability/buffers/
├── __init__.py               # Buffer API exports
├── base.py                   # Abstract interfaces
├── event_buffer.py           # Basic event buffering  
├── behavioral_buffer.py      # Agent behavior aggregation
├── correlation_buffer.py     # Correlation tracking
└── buffer_manager.py         # Coordinated management
```

**Key Components**:
```python
class EventBuffer(ABC):
    """Abstract base for all event buffers."""
    
    @abstractmethod
    def add_event(self, event: SimulationEvent) -> None: ...
    
    @abstractmethod  
    def flush_step(self, step: int) -> List[Dict]: ...

class BehavioralAggregationBuffer(EventBuffer):
    """Aggregates agent behavioral data over configurable windows."""
    
    def __init__(self, window_size: int = 100):
        self._window_size = window_size
        self._agent_activities = defaultdict(lambda: defaultdict(int))
        
    def add_event(self, event: SimulationEvent) -> None:
        if isinstance(event, AgentModeChangeEvent):
            self._agent_activities[event.agent_id][event.new_mode] += 1
```

### Step 3.2: Observer Implementation

**Implementation**:
```python
# NEW: src/econsim/observability/observers/
├── file_observer.py          # File-based structured logging
├── memory_observer.py        # In-memory for testing
├── educational_observer.py   # Educational analytics  
└── performance_observer.py   # Performance monitoring
```

**File Observer**:
```python
class FileObserver(BaseObserver):
    """High-performance structured file logging."""
    
    def __init__(self, config: ObservabilityConfig, output_path: Path):
        super().__init__(config)
        self._output_path = output_path
        self._buffer_manager = BufferManager(config.buffer_size)
        self._file_handle = None
        
    def notify(self, event: SimulationEvent) -> None:
        if self.is_enabled(event.event_type):
            self._buffer_manager.add_event(event)
            
    def flush_step(self, step: int) -> None:
        events = self._buffer_manager.flush_step(step)
        self._write_events_batch(events)
```

### Step 3.3: Legacy Migration & Integration

**Implementation**:
```python
# MODIFY: src/econsim/gui/debug_logger.py
class GUILogger:
    """DEPRECATED: Legacy logger - use observer pattern instead."""
    
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "GUILogger is deprecated. Use FileObserver and EducationalObserver instead.",
            DeprecationWarning, 
            stacklevel=2
        )
        
        # Initialize with observer system under the hood
        self._config = ObservabilityConfig.from_environment()
        self._observers = [
            FileObserver(self._config, Path("logs/simulation.jsonl")),
            EducationalObserver(self._config)
        ]
        
    def log_agent_mode_change(self, agent_id: int, old_mode: str, new_mode: str, reason: str = "", step: int = None):
        """DEPRECATED: Use observer events instead."""
        event = AgentModeChangeEvent(
            step=step or 0,
            timestamp=time.time(), 
            event_type="agent_mode_change",
            agent_id=agent_id,
            old_mode=old_mode,
            new_mode=new_mode,
            reason=reason
        )
        
        for observer in self._observers:
            observer.notify(event)
```

### Completion Criteria
- GUILogger decomposed into <5 focused observer classes  
- All educational features preserved in observer pattern
- Performance overhead <5% for full behavioral aggregation
- Legacy API compatibility with deprecation warnings
- Buffer management separated from event processing

---

## Phase 4: Integration

**Objective**: Complete integration testing and performance validation.

### Step 4.1: Factory Integration

**Implementation**:
```python
# Enhanced factory integration
def from_config(cls, config: SimConfig, agent_positions: List[Tuple[int, int]] = None) -> 'Simulation':
    """Factory method with full observer integration."""
    
    # Configure observability
    obs_config = ObservabilityConfig.from_environment()
    observers = []
    
    if obs_config.file_logging_enabled:
        observers.append(FileObserver(obs_config, config.log_path))
        
    if obs_config.educational_analytics_enabled:
        observers.append(EducationalObserver(obs_config))
        
    # Create simulation with observers
    simulation = cls._create_simulation_components(config, agent_positions)
    simulation._observer_registry = ObserverRegistry()
    
    for observer in observers:
        simulation._observer_registry.register(observer)
        
    return simulation
```

### Step 4.2: Validation Suite
```python
class RefactorValidationSuite:
    """Comprehensive validation against Phase 0 baselines."""
    
    def validate_determinism(self) -> ValidationResult:
        """Verify identical hash outputs vs baseline."""
        
    def validate_performance(self) -> ValidationResult:  
        """Verify <2% performance regression vs baseline."""
        
    def validate_educational_features(self) -> ValidationResult:
        """Verify all educational outputs preserved."""
        
    def validate_api_compatibility(self) -> ValidationResult:
        """Verify legacy API still functional."""
```

### Completion Criteria
- All Phase 0 determinism hashes still validate
- Performance within 2% of baseline  
- All educational features functional
- Legacy compatibility layer working

---

## Validation Requirements

### Critical Checkpoints
- **Determinism Preservation**: Hash validation at every phase gate
- **Performance Monitoring**: Benchmark against Phase 0 baseline using new comprehensive performance test
- **Educational Continuity**: Verify all analytics features preserved
- **Backward Compatibility**: Legacy API functions without modification

### Success Criteria

**Code Quality**:
- No class >500 lines
- No method >50 lines  
- Single responsibility principle
- Dependency injection throughout

**Performance**:
- Simulation steps/second within 98% of baseline
- Observer overhead <2% for minimal logging
- Full behavioral aggregation <5% overhead
- Memory usage increase <10%

**Architecture**:  
- Zero simulation → GUI dependencies
- Component-level unit testing >90% coverage
- Observer pattern supports multiple backends

## Implementation Notes

### Phase Dependencies
- Complete each phase entirely before starting the next
- Validate all completion criteria before proceeding
- Run full test suite + determinism hash check between phases

### Risk Management
- **Highest Risk**: Phase 3 (logger decomposition) - proceed carefully
- **Rollback Strategy**: Each phase creates isolated changes that can be reverted
- **Performance Regression**: Stop and investigate if >2% performance loss detected

### Legacy Compatibility
- Maintain existing API during transition via adapter pattern
- Add deprecation warnings but keep functionality intact
- Plan 6-month migration timeline for downstream code