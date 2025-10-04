# VMT EconSim Copilot Quickstart (AI Agents)

Project: Educational microeconomic simulation with deterministic spatial agents (Python 3.11+, PyQt6, Pygame, NumPy). Determinism-first architecture; GUI decoupled via observers.

## Architecture at a glance
- Simulation core (`src/econsim/simulation/`): use `Simulation.from_config(SimConfig)` only. Key files: `world.py`, `agent.py`, `grid.py`, `config.py`, `trade.py`.
- Step pipeline (fixed order): Movement → Collection → Trading → Metrics → Respawn in `simulation/execution/handlers/`.
- Observer layer (`src/econsim/observability/`): events via `ObserverRegistry` (notify → flush_step → close). Observers: File, Educational, Performance, GUI.
- GUI (`src/econsim/gui/` + `src/econsim/tools/launcher/`): subscribes to observers; simulation has no GUI imports.

## Determinism rules (critical)
- Always sort iteration (e.g., `Grid.iter_resources_sorted()`, `sorted(agents, key=lambda a: a.id)`).
- All randomness through sanctioned RNG: `ext_rng` or `simulation._rng`; stable tie-breaks used throughout.
- Determinism guards live in `tests/integration/test_determinism_*.py`.

## Construction & example
```python
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
config = SimConfig(seed=42, grid_size=(50, 50), num_agents=20)
sim = Simulation.from_config(config)  # Mandatory factory
```

## Feature flags
Env vars checked in `SimulationFeatures.from_environment()`: `ECONSIM_FORAGE_ENABLED`, `ECONSIM_TRADE_DRAFT`, `ECONSIM_TRADE_EXECUTION`, `ECONSIM_BILATERAL_ENABLED`. Tests reset flags in `tests/conftest.py`.

## Preferences (pure O(1))
- Implemented in `src/econsim/preferences/` and built via `factory.build_preference(type, **params)`.
- Must implement: `utility(bundle)`, `serialize()`, `deserialize()`, `update_params(**kwargs)`; register in `factory.py:_REGISTRY`.
- Validate rigorously; raise `PreferenceError` on invalid params.

## Performance constraints
- Per-step complexity O(agents + resources); avoid quadratic scans.
- Use spatial index: `simulation._spatial_index.find_agents_in_radius()`.
- Target 60 FPS; run `make perf`. Regression threshold: <5% slowdown acceptable.

## Dev workflows
- `make venv && source vmt-dev/bin/activate`
- `make dev` (GUI) • `make launcher` (Enhanced test launcher)
- `make test-unit` • `make lint format type` • `make perf`

## Common pitfalls
- Direct `Simulation(...)` instantiation (breaks hooks/RNG) → use factory.
- Non-deterministic iteration over dict/set → always sorted.
- GUI dependencies inside simulation → use observers only.
- Multiple QTimers in GUI → single 16ms timer in `EmbeddedPygameWidget`.
- Preference side effects → keep `utility()` pure.

## Integration notes
- Simulation → GUI: events recorded by `GUIEventObserver`; GUI uses `DataTranslator` for display.
- Headless runs: loop `sim.step(sim._rng)`; no GUI required.

## Refactor context
- Canonical plan: `tmp_plans/CURRENT/CRITICAL/ACTIONABLE_REFACTORING_PLAN_V2.md`.
- Git checkpoints: `refactor-pre-phase{N}` / `refactor-post-phase{N}`; GUI may break after Phase 1 (expected). Quarantine tests in `tests/QUARANTINE/`.
# VMT EconSim Copilot Instructions

**Project:** Educational microeconomic simulation with deterministic spatial agent behavior  
**Stack:** Python 3.11+, PyQt6, Pygame, NumPy  
**Status:** Post-refactor (October 2025) - Observer pattern established, GUILogger eliminated

---

## Critical Architecture Principles

### 1. Determinism is Sacred
- **Never** introduce non-deterministic iteration (dict keys, set ordering)
- Use `Grid.iter_resources_sorted()` for resource iteration, `sorted()` for agent pairs
- All randomness goes through sanctioned RNG: `ext_rng` parameter or `simulation._rng`
- Tie-breaking uses stable keys: `(-delta_utility, distance, x, y)` or `(seller_id, buyer_id, give_type, take_type)`
- Hash validation in `MetricsCollector.record()` excludes trade/debug metrics
- See `tests/integration/test_determinism_*.py` for regression guards

### 2. Factory Construction is Mandatory
**Always** use `Simulation.from_config(config)` - **never** direct instantiation:
```python
# ✅ CORRECT
from econsim.simulation.config import SimConfig
config = SimConfig(seed=42, grid_size=(50, 50), num_agents=20)
sim = Simulation.from_config(config)

# ❌ NEVER DO THIS
sim = Simulation(grid=grid, agents=agents)  # Breaks determinism, skips hook attachment
```

Factory ensures: RNG initialization, observer registry, respawn scheduler, metrics collector, spatial index.

### 3. Observer Pattern for Decoupling
Simulation emits events through `ObserverRegistry` - no direct GUI/logging dependencies in `src/econsim/simulation/`:
- **Record events:** `observer.record_mode_change()`, `record_trade()`, `record_collection()` (raw data architecture)
- **Zero overhead:** Events stored as dicts, formatting deferred to GUI/analysis layers
- **Event lifecycle:** `notify(event)` → `flush_step(step)` → `close()`
- Observers: `FileObserver`, `EducationalObserver`, `PerformanceObserver`, `GUIEventObserver`
- See `src/econsim/observability/` for implementation

### 4. Step Decomposition Pipeline
`Simulation.step(ext_rng)` uses handler pattern (DO NOT modify step ordering):
```
StepExecutor.execute_step() →
  1. MovementHandler      # movement + foraging + mode transitions
  2. CollectionHandler    # legacy collection + decision diff metrics
  3. TradingHandler       # intent enumeration + optional execution
  4. MetricsHandler       # step timing, determinism hash
  5. RespawnHandler       # resource replenishment
```
Each handler in `src/econsim/simulation/execution/handlers/` returns metrics, modifies simulation state minimally.

### 5. Feature Flags Control Behavior
Environment variables gate experimental features (checked in `SimulationFeatures.from_environment()`):
- `ECONSIM_FORAGE_ENABLED=1` (default: foraging active)
- `ECONSIM_TRADE_DRAFT=1` (enumerate trade intents)
- `ECONSIM_TRADE_EXECUTION=1` (actually execute trades)
- `ECONSIM_BILATERAL_ENABLED=1` (overall bilateral trade system)
- Tests use `conftest.py` fixtures to clear flags between runs

### 6. Preference System (Pure Functions)
Preferences are **stateless, O(1) utility calculators** in `src/econsim/preferences/`:
- Factory pattern: `build_preference('cobb_douglas', alpha=0.6)`
- Must implement: `utility(bundle)`, `serialize()`, `deserialize(data)`, `update_params(**kwargs)`
- Validation raises `PreferenceError` on invalid params
- No side effects, no external dependencies, no I/O
- Register new types in `factory.py:_REGISTRY`

### 7. Performance Constraints
- **Per-step complexity:** O(agents + resources) - avoid quadratic scans
- **Target:** 60 FPS in GUI (≤16ms per step)
- Movement handler budget: ≤3ms average
- Run `make perf` to capture baselines: `tests/performance/baseline_capture.py`
- Regression threshold: <5% slowdown acceptable, >5% requires investigation

---

## Developer Workflows

### Daily Development Commands
```bash
make venv                    # Create vmt-dev environment (first time only)
source vmt-dev/bin/activate  # Activate environment
make dev                     # Launch GUI with new observer architecture
make launcher                # Launch enhanced test launcher (RECOMMENDED)
make test-unit              # Run 210+ unit/integration tests (~10s)
make lint format type       # Code quality checks
make perf                   # Capture performance baselines
```

### Testing Strategy
- **Unit tests:** `tests/unit/` - 210+ tests, ~10 seconds, runs on every commit
- **Integration tests:** `tests/integration/` - determinism guards, observer validation
- **Performance tests:** `tests/performance/` - baseline capture, regression detection
- **Manual tests:** `MANUAL_TESTS/` - 7 educational scenarios (900 turns each, phase-based)
  - Launch via `make launcher` → Gallery tab → select test card
  - Tests validate agent behavior across phase transitions (forage/trade/idle combinations)
- **Quarantine:** `tests/QUARANTINE/` - tests under review during refactoring (should be empty post-refactor)

### Git Workflow for Refactoring
**CRITICAL:** Follow git checkpoint strategy from `ACTIONABLE_REFACTORING_PLAN_V2.md`:
```bash
# Before starting any phase
git tag refactor-pre-phase0 -m "Before observer system cleanup"

# After phase complete and stable
git tag refactor-post-phase0 -m "Observer system clean"

# Rollback if needed
git checkout refactor-post-phase0  # Go to last stable checkpoint
```

**Checkpoint discipline:**
- Tag BEFORE any major breaking change
- Test thoroughly before creating "post" tag
- Never create "post" tag if tests failing
- Document all checkpoints in CHANGELOG.md

### Adding New Preferences
1. Create `src/econsim/preferences/my_type.py`:
```python
from .base import Preference, PreferenceError

class MyPreference(Preference):
    TYPE_NAME = "my_type"
    
    def __init__(self, param: float):
        if param <= 0:
            raise PreferenceError(f"param must be positive, got {param}")
        self.param = param
    
    def utility(self, bundle) -> float:
        x, y = self._normalize_bundle(bundle)
        return self.param * (x + y)
    
    def serialize(self) -> dict:
        return {"type": self.TYPE_NAME, "params": {"param": self.param}}
```
2. Register in `factory.py:_REGISTRY["my_type"] = MyPreference`
3. Add tests: `tests/unit/test_my_preference.py` (validation, utility, round-trip serialization)
4. Run: `make test-unit lint type`

---

## File Organization & Key Paths

### Simulation Core (No GUI Dependencies)
- `src/econsim/simulation/world.py` - `Simulation` dataclass, step orchestration
- `src/econsim/simulation/agent.py` - `Agent` class, decision logic, modes
- `src/econsim/simulation/grid.py` - Resource storage with deterministic iteration
- `src/econsim/simulation/config.py` - `SimConfig` dataclass, factory integration
- `src/econsim/simulation/execution/` - Step handlers (movement, collection, trading, metrics, respawn)
- `src/econsim/simulation/trade.py` - Bilateral trade primitives, intent enumeration

### Observer System (Decoupling Layer)
- `src/econsim/observability/registry.py` - `ObserverRegistry` for event distribution
- `src/econsim/observability/observers/` - Concrete implementations:
  - `file_observer.py` - High-performance JSONL logging
  - `educational_observer.py` - Behavioral insights, analytics
  - `performance_observer.py` - Performance monitoring
  - `gui_observer.py` - GUI event translation (uses raw data + `DataTranslator`)
- `src/econsim/observability/raw_data/` - Zero-overhead raw data recording

### GUI Layer (Depends on Simulation via Observer)
- `src/econsim/gui/embedded_pygame.py` - `EmbeddedPygameWidget` (PyQt6 + Pygame integration)
- `src/econsim/gui/controller.py` - `SimulationController` (pause, speed, feature toggles)
- `src/econsim/gui/panels/` - UI panels (agent inspector, metrics, overlays)
- `src/econsim/tools/launcher/` - Modern test launcher architecture
  - `app_window.py` - Main window with tabbed interface
  - `gallery.py` - Test gallery with visual cards
  - `framework/test_configuration.py` - Educational scenario definitions

### Testing & Analysis
- `tests/unit/` - Fast unit tests (preferences, agent, grid, handlers)
- `tests/integration/` - Determinism guards, observer validation
- `tests/performance/` - `baseline_capture.py` (7 scenarios), regression detection
- `MANUAL_TESTS/` - Educational scenarios (`test_1.py` through `test_7.py`)
- `baselines/` - Performance baselines, determinism hashes

---

## Common Pitfalls & How to Avoid

### ❌ Direct Simulation Instantiation
```python
sim = Simulation(grid=my_grid, agents=my_agents)  # Breaks everything
```
✅ **Always use factory:** `sim = Simulation.from_config(config)`

### ❌ Non-Deterministic Iteration
```python
for agent in agents_dict.values():  # Dict ordering is not guaranteed
for (x, y) in grid._resources:     # Set ordering is random
```
✅ **Use sorted iteration:** `for agent in sorted(agents, key=lambda a: a.id):`

### ❌ GUI Dependencies in Simulation
```python
# In simulation/world.py
from econsim.gui.widgets import StatusPanel  # NEVER
```
✅ **Use observer pattern:** Simulation emits events, GUI subscribes

### ❌ Adding New Timers to GUI
```python
self.my_timer = QTimer()
self.my_timer.timeout.connect(self._my_method)
self.my_timer.start(100)  # Creates second simulation loop
```
✅ **Single QTimer:** GUI uses ONE 16ms timer in `EmbeddedPygameWidget`, calls `simulation.step()`

### ❌ Mutating State in Preferences
```python
def utility(self, bundle):
    self.call_count += 1  # Preferences must be pure
    return self.alpha * x
```
✅ **Pure functions:** No side effects, no instance mutation in `utility()`

### ❌ Ignoring Performance Budget
```python
# In handler
for agent in simulation.agents:
    for other_agent in simulation.agents:  # O(n²) - FORBIDDEN
        compute_interaction(agent, other_agent)
```
✅ **Use spatial index:** `simulation._spatial_index.find_agents_in_radius()`

---

## Integration Points

### Simulation → GUI (via Observers)
1. Simulation calls `observer_registry.notify(event)`
2. `GUIEventObserver` records raw data (zero overhead)
3. GUI requests formatted data via `DataTranslator.translate_*()` (deferred processing)
4. DisplayUpdateBatcher batches GUI updates for performance

### CLI → Simulation (Headless Execution)
```python
from econsim.simulation import Simulation
from econsim.simulation.config import SimConfig

config = SimConfig(seed=42, grid_size=(50, 50), num_agents=20, max_steps=1000)
sim = Simulation.from_config(config)

for step in range(1000):
    sim.step(sim._rng)  # Headless execution
```

### Test Launcher → Simulation
- `framework/test_configuration.py` defines `TestConfiguration` objects
- `executor.py` launches tests with config via `EmbeddedPygameWidget`
- Phase-based scenarios control feature flags dynamically (see `phase_config_editor.py`)

---

## Active Refactoring Plan (CRITICAL)

**CANONICAL REFERENCE:** `tmp_plans/CURRENT/CRITICAL/ACTIONABLE_REFACTORING_PLAN_V2.md`  
**Status:** Clean Architecture Edition - Execution in Progress (October 2025)  
**Approach:** No backward compatibility, git checkpoints for safety, aggressive decoupling

### Current Phase Status
- **Phase 0 (IN PROGRESS):** Observer system cleanup - MUST complete before Phase 2
- **Phase 1 (PLANNED):** GUI/simulation decoupling - GUI WILL BREAK (expected and acceptable)
- **Phase 2 (PLANNED):** Output/playback architecture - rebuild GUI on clean foundation
- **Phases 3-6 (PLANNED):** Test cleanup, MANUAL_TESTS consolidation, preference extensions, docs

### Critical Refactoring Principles
1. **No backward compatibility** - All old saved outputs will be invalidated
2. **Git checkpoints** - `refactor-pre-phase{N}` and `refactor-post-phase{N}` tags for rollback
3. **Temporary breakage acceptable** - GUI will be non-functional after Phase 1 until Phase 2 complete
4. **Clean architecture over convenience** - Building on solid foundation worth short-term disruption
5. **Schema unstable during refactor** - Output schema marked "dev", can change freely

### When Working on Refactor
- Check `tmp_plans/CURRENT/CRITICAL/ACTIONABLE_REFACTORING_PLAN_V2.md` for detailed step-by-step instructions
- Create git checkpoints BEFORE starting new phases
- Phase 0 must complete before Phase 2 (output architecture depends on clean observers)
- If GUI is broken, check which phase is active (expected after Phase 1)
- Use quarantine workflow in `tests/QUARANTINE/` for uncertain test decisions

---

## Code Style & Conventions

- **Python 3.11+**, Black (line length 100), Ruff linting, MyPy type hints
- Type hints encouraged, avoid `Any` unless necessary
- Dataclasses with `slots=True` for simulation core
- Import guards: `if TYPE_CHECKING:` for circular dependencies
- Comments explain "why", not "what" (code should be self-documenting)
- Apache 2.0 license headers required for files >30 lines

### Commit Messages
- Imperative mood: "Add feature X" not "Added feature X"
- Reference plan docs when applicable: "launcher: extract gallery panel (Part2-G12)"
- Keep diffs minimal and focused

---

## Quick Reference

### Run Simulation
```bash
make dev              # GUI with observer pattern
make launcher         # Enhanced test launcher (modern interface)
```

### Testing
```bash
make test-unit        # All unit tests
pytest tests/unit/test_specific.py -v  # Single test file
make perf             # Performance baseline capture
```

---

## Getting Help

- **🔥 REFACTORING CONTEXT (CRITICAL):** `tmp_plans/CURRENT/CRITICAL/ACTIONABLE_REFACTORING_PLAN_V2.md` - **CANONICAL** development path
- **Architecture questions:** Check `README.md` and `src/econsim/simulation/README.md`
- **Performance issues:** Review `baselines/` and `tests/performance/`
- **Test failures:** Check `tests/QUARANTINE/README.md` for test review process
- **Observer system:** Read `src/econsim/observability/__init__.py` docstrings
- **Quarantine workflow:** `tests/QUARANTINE/QUARANTINE_NOTES.md` for uncertain test decisions

**Educational focus:** This is a teaching platform. Code clarity and deterministic behavior matter more than micro-optimizations. When in doubt, prioritize understandability and reproducibility.
