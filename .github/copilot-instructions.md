# VMT EconSim Architecture Migration Instructions

This codebase is undergoing a comprehensive architecture restructure from `src/` to `source/` directory structure. The migration follows a phased approach with strict validation requirements to maintain deterministic behavior and performance.

## Migration Overview

**Current State**: Organic growth pattern with mixed concerns (GUI/simulation intertwined)
**Target State**: Clean domain-driven architecture with clear boundaries
**Approach**: Create new `source/` structure in parallel, validate each phase, then replace

## Target Directory Structure

```
source/econsim/
├── gui/                    # All GUI components (from src/econsim/{gui,tools/launcher})
│   ├── launcher/           # Test launcher GUI
│   ├── widgets/            # Reusable GUI widgets  
│   ├── analysis/           # Economic analysis displays
│   └── embedded/           # Embedded pygame components
└── simulation/             # Core simulation domain
    ├── agent/              # Agent behavior and decision-making
    │   ├── core.py         # Main Agent class (from agent.py)
    │   ├── decision.py     # Unified selection pass logic
    │   ├── preferences/    # Agent utility functions (from src/econsim/preferences/)
    │   ├── components/     # Agent sub-components
    │   │   ├── inventory/
    │   │   ├── trading_partner/
    │   │   ├── target_selection/
    │   │   │   ├── bilateral.py    # Renamed from trade.py
    │   │   │   ├── forage.py
    │   │   │   └── idle.py
    │   │   └── movement/
    │   └── modes.py        # Agent mode management (from agent_mode_utils.py)
    ├── world/              # Grid and spatial systems
    │   ├── grid.py         # Grid data structure
    │   ├── spatial.py      # Spatial indexing
    │   ├── respawn.py      # Resource respawn logic
    │   └── coordinates.py  # Position utilities
    ├── logging/            # Recording and delta systems
    │   ├── delta/          # Delta system (from src/econsim/delta/)
    │   ├── recorder.py     # Recording interfaces
    │   ├── playback.py     # Playback engines
    │   └── snapshot.py     # Simulation snapshots
    ├── executor.py         # StepExecutor (renamed from step_executor.py)
    ├── coordinator.py      # Simulation coordinator (renamed from world.py)
    ├── config.py           # Simulation configuration
    ├── features.py         # Feature flags
    └── constants.py        # Simulation constants
```

## Migration Phases

### Phase 1: Infrastructure Setup
- Create `source/econsim/` directory structure
- Initialize all `__init__.py` files with proper imports
- Configure `pyproject.toml` for dual source paths
- Establish import compatibility layer

### Phase 2: Core Simulation Migration
**Critical**: Must maintain exact behavioral compatibility

#### Key Renames and Moves:
- `world.py` → `coordinator.py` (class: `Simulation` → `SimulationCoordinator`)
- `agent.py` → `agent/core.py`
- `preferences/` → `agent/preferences/`
- `trade.py` → `agent/components/target_selection/bilateral.py`
- `step_executor.py` → `executor.py`

### Phase 3: Logging System Migration
- `src/econsim/delta/` → `source/econsim/simulation/logging/delta/`
- `snapshot.py` → `logging/snapshot.py`
- Maintain exact same MessagePack recording format

### Phase 4: GUI System Migration
- `src/econsim/tools/launcher/` → `source/econsim/gui/launcher/`
- `src/econsim/gui/` → `source/econsim/gui/{analysis,embedded}/`

## Critical Migration Requirements

### Determinism Preservation
```python
# MUST maintain exact execution order
# MUST preserve RNG seeding patterns
# MUST keep tie-breaking consistent: (-utility_delta, distance, x, y)

# Example: When migrating agent decision logic
def select_target(self, candidates, rng):
    # Preserve exact sorting order
    return sorted(candidates, key=lambda c: (-c.utility_delta, c.distance, c.x, c.y))
```

### Performance Requirements
- **No O(n²) introductions**: Maintain O(n) per-step complexity
- **Preserve spatial indexing**: Keep `grid.spatial_index` optimizations
- **Benchmark validation**: Run `make perf` after each phase

### Interface Compatibility
```python
# OLD import (during transition)
from econsim.simulation.agent import Agent

# NEW import (post-migration)
from econsim.simulation.agent.core import Agent

# MIGRATION: Use compatibility imports initially
# source/econsim/simulation/agent/__init__.py
from .core import Agent  # Maintains import compatibility
```

## Validation Commands

### Pre-Migration Baseline Capture
```bash
make phase0-capture          # Capture performance/determinism baselines
make test-unit              # Ensure all 210+ tests pass
```

### Migration Validation (Per Phase)
```bash
make test-unit              # All tests must still pass
make perf                   # Performance within 5% of baseline
pytest tests/integration/test_refactor_safeguards.py -v
```

### Determinism Validation
```bash
# Compare simulation outcomes between old and new structure
python tests/performance/determinism_capture.py --compare
```

## File Migration Patterns

### Component Migration Template
```python
# 1. Copy file to new location
# 2. Update internal imports to use new structure
# 3. Maintain exact same public interface
# 4. Add compatibility import in old location
# 5. Validate with tests

# Example: Migrating agent.py → agent/core.py
# OLD: src/econsim/simulation/agent.py
# NEW: source/econsim/simulation/agent/core.py
# COMPAT: from .core import Agent  # In agent/__init__.py
```

### Import Path Updates
```python
# During migration, update imports systematically:
# OLD: from .agent import Agent
# NEW: from .agent.core import Agent

# For external imports:
# OLD: from econsim.simulation.world import Simulation  
# NEW: from econsim.simulation.coordinator import SimulationCoordinator
```

## Risk Mitigation

### Rollback Strategy
- Migration occurs on separate branch (`arch_rework`)
- Old structure remains untouched until complete validation
- Each phase validated before proceeding to next

### Testing Strategy
- Run full test suite after each file migration
- Compare delta recordings between old/new structure
- Performance regression detection with 5% tolerance
- Determinism hash validation

### Branch Safety
```bash
# Work exclusively in arch_rework branch
git checkout arch_rework

# Never merge until complete migration validated
# Use automated tests to catch regressions early
```

## Success Criteria

- [ ] All 210+ unit/integration tests pass
- [ ] Performance within 5% of baseline (`make perf`)
- [ ] GUI launcher works identically (`make launcher`)
- [ ] Delta recording/playback maintains compatibility
- [ ] Determinism hashes match baseline
- [ ] Import paths updated throughout codebase
- [ ] Documentation updated for new structure

This migration maintains zero downtime through parallel development and comprehensive validation at each phase.