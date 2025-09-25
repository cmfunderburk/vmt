# VMT EconSim: Essential Code Examples for Study

**Companion to Student Coder Learning Guide**  
**Date**: 2025-09-24

This document highlights specific code snippets from the VMT EconSim codebase that demonstrate important software engineering patterns and Python techniques. Study these examples to understand professional-level code organization.

---

## 🏗️ Architecture Patterns

### 1. **Factory Pattern with Registry** 
*File: `src/econsim/preferences/factory.py`*

```python
class PreferenceFactory:
    """Centralized creation of preference objects with type safety."""
    
    _registry: dict[str, type[Preference]] = {}

    @classmethod
    def register(cls, type_name: str, preference_class: type[Preference]) -> None:
        """Register a preference implementation for later creation."""
        if type_name in cls._registry:
            raise ValueError(f"Preference type '{type_name}' already registered")
        cls._registry[type_name] = preference_class

    @classmethod
    def create(cls, type_name: str, **kwargs) -> Preference:
        """Create instance by type name with parameter validation."""
        if type_name not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(f"Unknown preference type: {type_name}. Available: {available}")
        
        try:
            return cls._registry[type_name](**kwargs)
        except TypeError as e:
            raise ValueError(f"Invalid parameters for {type_name}: {e}") from e

# Auto-registration at module level
PreferenceFactory.register("cobb_douglas", CobbDouglasPreference)
PreferenceFactory.register("perfect_substitutes", PerfectSubstitutesPreference)
PreferenceFactory.register("leontief", LeontiefPreference)
```

**Why This Matters:**
- **Extensibility**: New preference types can be added without modifying existing code
- **Type Safety**: Registry enforces that only valid Preference subclasses are registered
- **Error Handling**: Clear error messages help with debugging
- **Auto-Registration**: Module loading automatically populates the registry

---

### 2. **Configuration with Validation**
*File: `src/econsim/simulation/config.py`*

```python
@dataclass(slots=True)
class SimConfig:
    """Immutable configuration with validation and sensible defaults."""
    
    grid_size: tuple[int, int]
    initial_resources: Sequence[ResourceEntry]
    perception_radius: int = 8
    respawn_target_density: float = 0.25
    respawn_rate: float = 0.1
    max_spawn_per_tick: int = 3
    seed: int = 0
    enable_respawn: bool = True
    enable_metrics: bool = True
    viewport_size: int = 320

    def validate(self) -> None:
        """Validate configuration with specific error messages."""
        gw, gh = self.grid_size
        if gw <= 0 or gh <= 0:
            raise ValueError("grid_size dimensions must be positive")
        
        if not (0.0 <= self.respawn_target_density <= 1.0):
            raise ValueError("respawn_target_density must be within [0,1]")
        
        if self.respawn_rate < 0:
            raise ValueError("respawn_rate must be non-negative")
        
        if not (320 <= self.viewport_size <= 800):
            raise ValueError("viewport_size must be within [320, 800]")
        
        # Validate each resource entry format
        for i, entry in enumerate(self.initial_resources):
            if len(entry) not in (2, 3):
                raise ValueError(f"Resource {i}: expected (x,y) or (x,y,type), got {entry}")
```

**Why This Matters:**
- **Data Classes**: Modern Python approach to configuration objects
- **Slots Optimization**: `slots=True` reduces memory usage for performance
- **Validation Pattern**: Centralized validation with specific, actionable error messages
- **Default Values**: Sensible defaults reduce API complexity for users

---

### 3. **State Machine with Enums**
*File: `src/econsim/simulation/agent.py`*

```python
class AgentMode(str, Enum):
    """Agent behavioral states with string values for debugging."""
    FORAGE = "forage"
    RETURN_HOME = "return_home"
    IDLE = "idle"

@dataclass(slots=True)
class Agent:
    id: int
    x: int
    y: int
    home_x: int
    home_y: int
    preference: Preference
    mode: AgentMode = AgentMode.FORAGE
    target: tuple[int, int] | None = None
    carrying: dict[str, int] = field(default_factory=lambda: {"good1": 0, "good2": 0})
    home_inventory: dict[str, int] = field(default_factory=lambda: {"good1": 0, "good2": 0})

    def step_decision(self, grid: Grid) -> None:
        """Execute one decision step based on current mode."""
        if self.mode == AgentMode.FORAGE:
            self._forage_step(grid)
        elif self.mode == AgentMode.RETURN_HOME:
            self._return_home_step(grid)
        # IDLE mode: do nothing (explicit no-op)

    def _forage_step(self, grid: Grid) -> None:
        """Handle foraging behavior with mode transitions."""
        # Find best resource target within perception radius
        best_target = self._find_best_target(grid)
        
        if best_target is None:
            self.mode = AgentMode.RETURN_HOME  # No resources found
            return
        
        # Move toward target and collect if reached
        self._move_toward(best_target)
        if (self.x, self.y) == best_target:
            if self._collect_at_position(grid):
                # Successfully collected, continue foraging
                self.target = None
            else:
                # Resource was taken by another agent, retarget
                self.target = None

    def _return_home_step(self, grid: Grid) -> None:
        """Handle return-to-home behavior with mode transitions."""
        home_pos = (self.home_x, self.home_y)
        self._move_toward(home_pos)
        
        if self.at_home():
            self.deposit()  # Transfer carrying -> home_inventory
            self.mode = AgentMode.FORAGE  # Resume foraging
```

**Why This Matters:**
- **Clear State Management**: Enum-based states prevent invalid state values
- **Explicit Transitions**: Mode changes are deliberate and traceable
- **Single Responsibility**: Each mode method handles only one behavior type
- **Deterministic Behavior**: Same inputs always produce same outputs

---

### 4. **Protocol-Based Dependency Injection**
*File: `src/econsim/gui/embedded_pygame.py`*

```python
class _SimulationProto(Protocol):
    """Minimal interface required by the GUI widget."""
    def step(self, rng: random.Random, *, use_decision: bool = False) -> None: ...

class EmbeddedPygameWidget(QWidget):
    """PyQt widget embedding Pygame with loose coupling to simulation."""
    
    def __init__(
        self,
        parent: QWidget | None = None,
        simulation: _SimulationProto | None = None,
        *,
        decision_mode: bool | None = None,
    ) -> None:
        super().__init__(parent)
        
        # Dependency injection - widget doesn't know about concrete simulation class
        self._simulation: _SimulationProto | None = simulation
        self._sim_rng = None  # Lazy initialization
        
        # Extract viewport size from injected simulation config
        viewport_size = 320  # Sensible default
        if simulation is not None:
            config = getattr(simulation, 'config', None)
            if config is not None:
                viewport_size = getattr(config, 'viewport_size', 320)
        
        self.SURFACE_SIZE = (viewport_size, viewport_size)
        
        # Environment-based configuration with precedence rules
        import os
        env_legacy = os.environ.get("ECONSIM_LEGACY_RANDOM") == "1"
        if decision_mode is not None:
            self._use_decision_default = bool(decision_mode)
        else:
            self._use_decision_default = not env_legacy

    def _on_tick(self) -> None:
        """Timer callback - steps simulation if available."""
        if self._simulation is not None:
            if self._sim_rng is None:  # Lazy RNG creation
                self._sim_rng = random.Random(12345)
            
            # Use injected simulation without knowing its concrete type
            self._simulation.step(self._sim_rng, use_decision=self._use_decision_default)
        
        self._update_scene()  # Always update display
        self.update()  # Trigger Qt repaint
```

**Why This Matters:**
- **Protocol Classes**: Define minimal interfaces without inheritance overhead
- **Dependency Injection**: Widget can work with any object that implements the protocol
- **Lazy Initialization**: Expensive resources created only when needed
- **Configuration Precedence**: Clear rules for how settings are determined
- **Graceful Degradation**: Works even without a simulation injected

---

### 5. **Factory Method with Conditional Assembly**
*File: `src/econsim/simulation/world.py`*

```python
@classmethod
def from_config(
    cls,
    config: SimConfig,
    preference_factory: Callable[[int], Preference],
    agent_positions: Sequence[tuple[int, int]]
) -> Simulation:
    """Factory method creating fully configured simulation from declarative config."""
    
    # Create and populate grid
    grid = Grid(config.grid_size[0], config.grid_size[1])
    for entry in config.initial_resources:
        x, y = entry[0], entry[1]
        resource_type = entry[2] if len(entry) > 2 else 'A'  # Default type
        grid.place_resource(x, y, resource_type)
    
    # Create agents with injected preferences
    agents = []
    for i, (home_x, home_y) in enumerate(agent_positions):
        agent = Agent(
            id=i,
            x=home_x, y=home_y,  # Start at home
            home_x=home_x, home_y=home_y,
            preference=preference_factory(i)  # Injected preference creation
        )
        agents.append(agent)
    
    # Create base simulation
    simulation = cls(
        grid=grid,
        agents=agents,
        config=config,
        _respawn_interval=getattr(config, 'respawn_interval', 1)
    )
    
    # Seed internal RNG from config
    if config.seed is not None:
        simulation._rng = random.Random(config.seed)
    
    # Conditionally attach optional components based on config flags
    if config.enable_respawn and hasattr(config, 'respawn_target_density'):
        from .respawn import RespawnScheduler
        simulation.respawn_scheduler = RespawnScheduler(
            target_density=config.respawn_target_density,
            respawn_rate=config.respawn_rate,
            max_spawn_per_tick=config.max_spawn_per_tick
        )
    
    if config.enable_metrics:
        from .metrics import MetricsCollector
        simulation.metrics_collector = MetricsCollector()
    
    return simulation
```

**Why This Matters:**
- **Factory Methods**: Complex object construction with proper initialization order
- **Functional Parameters**: Using callables to customize object creation without tight coupling
- **Conditional Assembly**: Different configurations without inheritance complexity
- **Defensive Defaults**: Graceful handling of missing configuration values
- **Hook Pattern**: Optional components can be attached without affecting core logic

---

## 🧪 Testing Patterns

### 6. **Determinism Testing**
*File: `tests/unit/test_determinism_hash.py`*

```python
def test_determinism_same_seed_same_hash():
    """Verify identical seeds produce identical simulation sequences."""
    
    def create_simulation(seed: int) -> Simulation:
        """Helper to create configured simulation."""
        cfg = SimConfig(
            grid_size=(8, 8),
            initial_resources=[(1, 1, 'A'), (3, 3, 'B'), (5, 5, 'A')],
            seed=seed,
            enable_metrics=True
        )
        return Simulation.from_config(
            cfg,
            preference_factory=lambda i: CobbDouglasPreference(alpha=0.5),
            agent_positions=[(0, 0), (2, 2)]
        )
    
    # Create two simulations with identical seeds
    sim1 = create_simulation(seed=42)
    sim2 = create_simulation(seed=42)
    
    # Run identical step sequences
    rng1 = random.Random(999)  # External RNG for legacy random walk
    rng2 = random.Random(999)  # Identical external state
    
    for _ in range(20):
        sim1.step(rng1, use_decision=True)
        sim2.step(rng2, use_decision=True)
    
    # Verify identical behavior via hash comparison
    hash1 = sim1.metrics_collector.determinism_hash()
    hash2 = sim2.metrics_collector.determinism_hash()
    
    assert hash1 == hash2, f"Determinism broken: {hash1} != {hash2}"

def test_determinism_position_change_changes_hash():
    """Verify different initial conditions produce different results."""
    
    # Same seed, different agent positions
    cfg = SimConfig(grid_size=(8, 8), initial_resources=[(4, 4, 'A')], seed=42)
    
    sim1 = Simulation.from_config(cfg, lambda i: CobbDouglasPreference(0.5), [(0, 0)])
    sim2 = Simulation.from_config(cfg, lambda i: CobbDouglasPreference(0.5), [(1, 1)])
    
    # Run same number of steps
    rng = random.Random(123)
    for _ in range(10):
        sim1.step(rng, use_decision=True)
        rng = random.Random(123)  # Reset RNG state
        sim2.step(rng, use_decision=True)
    
    # Different positions should produce different hashes
    assert sim1.metrics_collector.determinism_hash() != sim2.metrics_collector.determinism_hash()
```

**Why This Matters:**
- **Property-Based Testing**: Tests verify system properties (determinism) rather than specific outputs
- **Controlled Randomness**: Careful RNG state management ensures reproducible tests
- **Helper Functions**: Reduce test code duplication with clear factory methods
- **Assertion Messages**: Helpful failure messages aid in debugging when tests fail

---

### 7. **Performance Benchmarking**
*File: `tests/unit/test_perf_decision_throughput.py`*

```python
def test_decision_throughput_floor():
    """Ensure decision logic meets minimum performance requirements."""
    
    # Create realistic simulation for performance testing
    cfg = SimConfig(
        grid_size=(16, 16),
        initial_resources=[(x, y, 'A' if (x + y) % 2 else 'B') 
                          for x in range(0, 16, 2) 
                          for y in range(0, 16, 2)],  # Checkerboard pattern
        seed=42,
        enable_respawn=True,
        enable_metrics=True
    )
    
    sim = Simulation.from_config(
        cfg,
        preference_factory=lambda i: CobbDouglasPreference(alpha=0.5),
        agent_positions=[(0, 0), (1, 1), (14, 14), (15, 15)]  # Spread agents
    )
    
    rng = random.Random(999)
    
    # Measure performance of decision steps
    import time
    start_time = time.perf_counter()
    
    target_steps = 4000  # Minimum throughput requirement
    for _ in range(target_steps):
        sim.step(rng, use_decision=True)
    
    elapsed = time.perf_counter() - start_time
    steps_per_sec = target_steps / elapsed
    
    # Performance floor: must achieve at least 4000 steps/second
    min_throughput = 4000
    assert steps_per_sec >= min_throughput, (
        f"Decision throughput too slow: {steps_per_sec:.1f} steps/sec "
        f"(minimum: {min_throughput})"
    )
    
    print(f"✅ Decision throughput: {steps_per_sec:.1f} steps/sec")
```

**Why This Matters:**
- **Performance Regression Prevention**: Automated tests catch performance degradation
- **Realistic Test Data**: Use patterns similar to actual usage for accurate measurements
- **Clear Thresholds**: Specific performance requirements that must be met
- **Helpful Output**: Success messages provide actual performance metrics

---

## 🎯 Key Takeaways for Students

### **Code Organization Principles**
1. **Single Responsibility**: Each class and method has one clear purpose
2. **Dependency Injection**: Components receive their dependencies rather than creating them
3. **Configuration Over Coding**: Behavior controlled by declarative configuration
4. **Interface Segregation**: Small, focused interfaces reduce coupling

### **Python Best Practices**
1. **Type Hints**: Comprehensive type annotations improve code clarity and catch errors
2. **Data Classes**: Modern Python approach to data containers with validation
3. **Protocols**: Lightweight interfaces without inheritance overhead
4. **Error Handling**: Specific exception types with actionable error messages

### **Testing Excellence**
1. **Property Testing**: Verify system behaviors rather than specific outputs
2. **Performance Testing**: Automated prevention of performance regressions
3. **Determinism Testing**: Ensure complex systems produce consistent results
4. **Test Organization**: Focused test files that mirror source code structure

### **Professional Development**
1. **Incremental Development**: Features built in small, testable increments
2. **Quality Gates**: Automated validation of code quality, performance, and functionality
3. **Documentation**: Code that explains itself through clear naming and structure
4. **Extensibility**: Systems designed to accommodate future requirements

---

*💡 **Study Tip**: Start by reading through these examples, then trace through the execution flow in your debugger to see how the patterns work in practice!*