# VMT Copilot Instructions

## Project Overview
VMT is an educational microeconomic simulation combining PyQt6 desktop GUI with a deterministic Pygame-rendered spatial agent model. Agents with economic preferences move on a grid, collect resources, and engage in bilateral trade while maintaining strict determinism for educational reproducibility.

## Architecture Essentials

### Core Pipeline (IMMUTABLE)
`QTimer(16ms)` → `Simulation.step(ext_rng, use_decision)` → `_update_scene()` → `paintEvent()`

Never add: extra timers, threads, blocking loops, surface reallocation, or per-pixel Python operations.

### Key Components
- **`simulation/world.py`**: Core orchestrator with `Simulation` class
- **`simulation/agent.py`**: Agent behavior, unified target selection with distance-discounted utility  
- **`simulation/grid.py`**: 2D spatial grid with deterministic resource iteration via `iter_resources_sorted()`
- **`gui/embedded_pygame.py`**: PyQt6↔Pygame integration with single off-screen surface
- **`preferences/factory.py`**: Economic preference types (Cobb-Douglas, Perfect Substitutes, Leontief)
- **`simulation/config.py`**: SimConfig factory pattern for deterministic setup

## Determinism Requirements (CRITICAL)
1. **Tie-breaking**: Always use `(-ΔU, distance, x, y)` for resources; `(-ΔU, seller_id, buyer_id, give_type, take_type)` for trade
2. **Iteration order**: Use `iter_resources_sorted()`, maintain agent list order for processing priority  
3. **RNG separation**: External `rng` parameter vs internal `Simulation._rng` for hooks
4. **Hash contract**: `simulation/metrics.py` excludes trade metrics and debug overlays
5. **Serialization**: All schemas are append-only (`world.py`, `agent.py`, `grid.py`, `snapshot.py`)

## Development Workflow

### Environment Setup
```bash
make venv && source vmt-dev/bin/activate
```

### Primary Commands
- **`make launcher`**: Main development interface (canonical test launcher)
- **`make dev`**: Legacy GUI (Start Menu → scenarios)  
- **`pytest -q`**: Full test suite (210+ tests)
- **`make perf`**: Performance validation (~62 FPS target, ≥30 floor)

### Factory Pattern (Preferred)
```python
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation

cfg = SimConfig(
    grid_size=(12,12), 
    seed=123, 
    distance_scaling_factor=0.0,  # k=0 no distance penalty, k=5 local behavior
    enable_respawn=True,
    enable_metrics=True
)
sim = Simulation.from_config(cfg, agent_positions=[(0,0)])
```

## Key Patterns & Conventions

### Decision Logic
- **Unified selection**: `Agent.select_unified_target()` evaluates resources vs trade partners
- **Distance scaling**: `ΔU_discounted = ΔU_base / (1 + k × distance²)`
- **Spatial indexing**: `AgentSpatialGrid` rebuilt each step, maintains O(n) complexity

### Feature Flags
- `ECONSIM_LEGACY_RANDOM=1`: Force legacy random walk instead of decision mode
- `ECONSIM_FORAGE_ENABLED=0`: Disable resource collection  
- `ECONSIM_TRADE_DRAFT=1`: Enable trade intent enumeration
- `ECONSIM_TRADE_EXEC=1`: Enable trade execution
- `ECONSIM_DEBUG_AGENT_MODES=1`: Log mode transitions

### Performance Constraints  
- Maintain O(n) per step where n=agents+resources
- Overlays must be <2% FPS overhead, read-only
- No quadratic scans in hot paths
- Cache fonts, reuse surfaces, avoid per-frame allocations

## Testing & Quality

### Before Any Change
1. Run `pytest -q` (determinism tests must pass)
2. Run `make perf` (no FPS regression)  
3. Update hash tests only for intentional additive fields
4. Ensure no unordered iteration where order matters

### Test Categories
- **Determinism**: `test_determinism_hash.py`, `test_decision_determinism.py`
- **Performance**: `test_perf_simulation.py`, `scripts/perf_stub.py`
- **Integration**: Factory construction, GUI controls, overlay regression

## Common Pitfalls
- **Breaking determinism**: Changing tie-break keys, adding unguarded RNG calls, reordering agent lists
- **Performance regressions**: Adding O(n²) scans, allocations in step loop, redundant surface operations  
- **Hash drift**: Silently adding fields to metrics without excluding from hash
- **Pipeline violations**: Extra timers, blocking operations, surface recreation

## Git Commit Guidelines
When committing changes, keep messages concise and neutral in tone. They serve as changelog entries for future developer reference, not sales pitches. Focus on:
- What was changed (technical implementation)
- Why it was changed (problem solved)
- Key impacts (performance, compatibility, functionality)

## Current Status & Roadmap
**Completed**: Gate 6 integration (factory patterns, GUI defaults, overlay toggle)
**Active**: Choose Gate 7 (trading primitives) OR console script packaging  
**Planning**: See `ROADMAP_REVISED.md` and `tmp_plans/CURRENT/`

Use `make launcher` for primary development. All changes must preserve educational clarity and deterministic reproducibility.