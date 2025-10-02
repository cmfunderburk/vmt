# VMT EconSim Platform

An educational microeconomic simulation featuring deterministic spatial agent behavior with PyQt6 GUI and modular observer-based architecture.

> This README reflects the **current state after Unified Refactor (October 2025): GUILogger elimination complete, observer pattern established, step decomposition operational, launcher architecture modernized**. See `.github/copilot-instructions.md` for development constraints.

## 1. Current Architecture (October 2025)

**Major Achievement**: Unified refactor complete with 85% technical debt reduction. GUILogger system (2593 lines) eliminated and replaced with modular observer pattern. Step execution decomposed from 450+ lines to focused handler pipeline.

**Canonical Development Interface**: `make launcher` - comprehensive test management with modular tabs, real-time health monitoring, and educational scenario configuration.

**Core Pipeline**: PyQt6 QTimer (16ms) → `Simulation.step(ext_rng)` → `StepExecutor` handlers (Movement → Collection → Trading → Metrics → Respawn) → Pygame render → Qt display

### 1.1 Completed Systems
- **Observer Pattern**: Modular event system with FileObserver, EducationalObserver, PerformanceObserver
- **Step Decomposition**: Handler pipeline (Movement, Collection, Trading, Metrics, Respawn)
- **Agent Component Architecture**: Modular agent design with 6 specialized components
- **Launcher Architecture**: Modern GUI with test gallery, configuration editor, batch runner
- **Deterministic Simulation**: Factory construction, sorted iteration, RNG separation
- **Bilateral Trading**: Feature-gated single-unit exchange with intent enumeration
- **Distance-Discounted Utility**: Configurable k parameter for local vs global optimization
- **Agent Wealth Accumulation**: Home inventory tracking with utility calculations
- **Real-time Visualization**: Configurable overlays, agent inspector, performance metrics

### 1.2 Agent Component Architecture (October 2025)

The Agent class has been refactored into a modular component architecture with 6 specialized components:

| Component | Responsibility | Key Features |
|-----------|----------------|--------------|
| **Movement** | Spatial navigation & pathfinding | Manhattan distance, collision avoidance, target tracking |
| **Event Emitter** | Observer pattern integration | Mode change events, resource collection events, structured logging |
| **Inventory** | Dual inventory management | Carrying + home inventories, mutation-safe operations |
| **Trading Partner** | Bilateral exchange coordination | Partner pairing, meeting points, cooldown management |
| **Target Selection** | Resource & partner targeting | Deterministic priority ordering, distance-discounted utility |
| **Mode State Machine** | Behavioral mode transitions | Valid transition validation, event emission integration |

**Architecture Benefits**:
- **Modularity**: Each component has a single responsibility
- **Testability**: Components can be tested in isolation
- **Maintainability**: Clear separation of concerns
- **Backward Compatibility**: Agent API preserved through component delegation
- **Performance**: Minimal overhead through efficient component integration

**Component Integration**:
```python
# Agent components are initialized in __post_init__
self._movement = AgentMovement(self.id)
self._event_emitter = AgentEventEmitter(self.id)
self._inventory = AgentInventory(self.preference)
self._trading_partner = TradingPartner(self.id)
self._target_selection = ResourceTargetStrategy()
self._mode_state_machine = AgentModeStateMachine(self.id)
```

## 2. Quick Start

```bash
# Setup development environment
make venv && source vmt-dev/bin/activate

# Primary development interface (canonical)
make launcher                         # Modern GUI with test gallery & configuration

# Alternative interfaces
make dev                             # DEPRECATED - legacy bootstrap GUI
pytest -q                           # Run 210+ tests for validation
make perf                           # Performance comparison vs baselines
make token                          # Generate LLM token usage report

# Headless execution for CI/testing
QT_QPA_PLATFORM=offscreen SDL_VIDEODRIVER=dummy make launcher
```

## 3. Simulation Construction (Required Pattern)

**ALWAYS use factory method** - never direct instantiation:

```python
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
import random

cfg = SimConfig(
    grid_size=(12,12),
    initial_resources=[(2,2,'A'), (4,5,'B')],
    perception_radius=8,
    seed=123,
    enable_respawn=True,
    enable_metrics=True,
    distance_scaling_factor=0.0  # k=0.0 for no distance penalty, k=5.0 for strong local behavior
)
sim = Simulation.from_config(cfg, agent_positions=[(0,0)])
ext_rng = random.Random(999)
for _ in range(40):
    sim.step(ext_rng)
print("hash=", sim.metrics_collector.determinism_hash())
```

## 4. Key Systems Overview

### 4.1 Observer Pattern Architecture
**Status**: GUILogger system eliminated (October 2025). Modular observer system operational.
- **FileObserver**: High-performance structured logging to files
- **EducationalObserver**: Behavioral analytics and educational insights  
- **PerformanceObserver**: Performance monitoring and optimization metrics
- **ObserverRegistry**: Centralized event distribution system

### 4.2 Bilateral Exchange System
**Status**: Feature-gated single-unit reciprocal trading with deterministic mechanics.
- **Intent Enumeration**: Draft trade proposals with utility calculations
- **Execution Pipeline**: Maximum one trade per step when enabled
- **Priority Sorting**: `(-ΔU, seller_id, buyer_id, give_type, take_type)` for determinism
- **Partner Search**: Meeting point system when foraging disabled

**Feature Flags** (environment-controlled):
- `ECONSIM_TRADE_DRAFT=1` – enumerate trade intents (no execution)
- `ECONSIM_TRADE_EXEC=1` – execute highest-priority intent per step
- `ECONSIM_DEBUG_AGENT_MODES=1` – log agent mode transitions

**Trading Mechanics**:
- One reciprocal unit swap per step maximum (good1 ↔ good2)
- Micro-delta filter: utility gains < 1e-5 discarded to prevent oscillation
- Deterministic priority: `(-ΔU, seller_id, buyer_id, give_type, take_type)`
- Partner search with meeting points when foraging disabled
- Economic coherence: persistent inventory changes affect future behavior

### 4.3 Unified Target Selection System
**Status**: Fully operational as default agent decision mechanism.

**Core Algorithm**: Distance-discounted utility evaluation
```
ΔU_discounted = ΔU_base / (1 + k × distance²)
```

**Key Features**:
- **Distance scaling factor (k)**: Configurable 0-10, live-adjustable in GUI
- **Deterministic tie-breaking**: `(-ΔU, distance, x, y)` for resources, `agent_id` for partners
- **Spatial indexing**: `AgentSpatialGrid` for O(agents+resources) complexity per step
- **Conservative trade heuristics**: Minimum directional marginal gains to prevent oscillation
- **Leontief prospecting**: Integrated fallback for complementarity preferences

**Performance**: 62+ FPS maintained, <2% spatial indexing overhead, all 210+ tests passing.

**GUI Integration**: 
- Start Menu: Initial k configuration in Advanced panel
- Controls Panel: Live k adjustment with immediate effect
- Visual feedback: Real-time target selection updates

## 5. Development Architecture

### 5.1 Launcher Architecture (Canonical Interface)
**Primary Entry Point**: `make launcher` - Modern GUI with modular design
- **TestRegistry**: Centralized configuration management for all scenarios
- **TestExecutor**: Programmatic execution with subprocess fallback
- **LauncherLogger**: Independent logging system (`launcher_logs/`)
- **Modular Tabs**: Gallery, comparison, history, batch runner, config editor
- **Health Monitoring**: Real-time status checks with actionable error reporting

### 5.2 Critical Determinism Invariants
1. **Resources**: iterate only via `Grid.iter_resources_sorted()`
2. **Agent selection**: preserve original list order within each step
3. **Trade priority**: `(-ΔU, seller_id, buyer_id, give_type, take_type)`
4. **RNG separation**: external `step(ext_rng)` vs internal `_rng`
5. **Execution limits**: maximum one trade per step when enabled

### 5.3 Performance & Baselines
- **Complexity**: O(n) per-step performance maintained
- **Determinism**: `baselines/determinism_hashes.json` - only refresh with rationale  
- **Performance**: `baselines/performance_baseline.json` - compare after algorithm changes
- **Hash invariant**: excludes trade & debug metrics for stability

## 6. Educational Features

### 6.1 Preference Types
- **Cobb-Douglas**: U(x, y) = x^α * y^(1-α) - diminishing marginal utility
- **Perfect Substitutes**: U(x, y) = a·x + b·y - constant marginal rate of substitution  
- **Leontief (Complements)**: U(x, y) = min(x/a, y/b) - fixed proportions consumption

### 6.2 Behavioral Demonstrations
- **Distance vs Utility Trade-offs**: Configurable k parameter shows local vs global optimization
- **Wealth Accumulation**: Agents build home inventory, demonstrating long-term economic behavior
- **Trading Dynamics**: Bilateral exchange with realistic partner search and meeting mechanics
- **Mode Transitions**: Observable agent states (idle, forage, return home, seek partner)

### 6.3 Real-time Visualization
- **Overlay System**: Toggleable grid lines, agent IDs, home labels, trade connections
- **Agent Inspector**: Individual agent state, inventories, utility calculations
- **Performance Metrics**: Real-time FPS, step counts, trade statistics
- **Debug Information**: Educational logging with reasoning explanations

## 7. Contributing & Development

**Development Workflow**: See `.github/copilot-instructions.md` for constraints and invariants.

**Pre-commit Checklist**:
1. All tests pass (`pytest -q`)
2. Performance within baseline (`make perf`)
3. Determinism invariants unchanged (or explicit test + baseline update)
4. New metrics hash-excluded unless justified
5. Mode transitions emit proper observer events

**Commit Format**: `component: concise change (perf/determinism impact, hash stable|updated)`

## 8. Reference Documentation

| Document | Purpose |
|----------|---------|
| `.github/copilot-instructions.md` | **Development constraints & architectural invariants** |
| `API_GUIDE.md` | Programmatic API usage examples |
| `docs/launcher_architecture.md` | Launcher system design and components |
| `docs/launcher_troubleshooting.md` | Development environment debugging |
| `baselines/` | Determinism & performance reference data |
| `llm_counter/` | LLM context optimization tools |

## 9. Key Terminology

| Term | Definition |
|------|------------|
| **Observer Pattern** | Event-driven architecture replacing monolithic GUILogger; FileObserver + EducationalObserver + PerformanceObserver |
| **StepExecutor** | Handler pipeline coordinator executing: Movement → Collection → Trading → Metrics → Respawn |
| **Factory Construction** | Required `Simulation.from_config()` pattern; never direct instantiation |
| **Determinism Hash** | Reproducibility digest excluding trade/debug metrics; stable across feature toggles |
| **Distance Scaling (k)** | Configurable 0-10 parameter: ΔU_discounted = ΔU_base / (1 + k × distance²) |
| **Intent Enumeration** | Draft trade proposals with priority sorting: `(-ΔU, seller_id, buyer_id, give_type, take_type)` |
| **Agent Modes** | State machine: idle ↔ forage ↔ return_home ↔ move_to_partner (with observer events) |
| **Launcher Architecture** | Modern GUI (`make launcher`) with TestRegistry, TestExecutor, modular tabs |
| **Feature Flags** | Environment variables controlling behavior: `ECONSIM_TRADE_*`, `ECONSIM_DEBUG_*`, etc. |
| **Economic Coherence** | Trade execution produces persistent inventory changes affecting subsequent behavior |

---

**Last Updated**: October 2, 2025  
**Status**: Unified Refactor Complete - GUILogger elimination achieved, observer pattern operational, launcher architecture modernized

### Quick Navigation

| Resource | Purpose |
|----------|---------|
| [`API_GUIDE.md`](API_GUIDE.md) | Programmatic usage examples |
| [`.github/copilot-instructions.md`](.github/copilot-instructions.md) | **Development constraints & invariants** |
| [`docs/launcher_architecture.md`](docs/launcher_architecture.md) | Launcher system design |
| [`baselines/`](baselines/) | Performance & determinism references |
| [`llm_counter/`](llm_counter/) | LLM context optimization tools |