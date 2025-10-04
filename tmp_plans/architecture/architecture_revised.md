# VMT Codebase Migration Plan: Restructuring for Maintainability

## Overview

This document outlines a comprehensive migration plan to restructure the VMT codebase from its current organic growth pattern to a clean, maintainable architecture. The migration will be performed by creating a new `source/` folder structure rather than modifying the existing codebase, ensuring zero downtime and safe rollback capabilities.

## Current State Analysis

### Current Structure Issues
- **Mixed concerns**: GUI and simulation logic intertwined
- **Deep nesting**: Components buried in multiple subdirectories
- **Unclear boundaries**: Tools, launcher, and core simulation mixed together
- **Inconsistent naming**: `step_executor.py` vs `world.py` naming conventions
- **Scattered agent logic**: Agent behavior spread across multiple files and components

### Key Current Components
- **Simulation Core**: `src/econsim/simulation/` (agent.py, world.py, grid.py, config.py, etc.)
- **GUI Components**: `src/econsim/gui/` + `src/econsim/tools/launcher/`
- **Agent Components**: `src/econsim/simulation/components/` (inventory, movement, target_selection, trading_partner)
- **Delta System**: `src/econsim/delta/` (recording and playback)
- **Preferences**: `src/econsim/preferences/` (agent utility functions)
- **Trade System**: `src/econsim/simulation/trade.py` (bilateral trading logic)
- **Snapshot System**: `src/econsim/simulation/snapshot.py` (simulation state snapshots)

## Target Architecture

```
source/econsim/
├── gui/                    # All GUI components
│   ├── __init__.py
│   ├── launcher/           # Test launcher GUI (migrated from tools/launcher)
│   ├── widgets/            # Reusable GUI widgets (migrated from tools/widgets)
│   ├── analysis/           # Economic analysis displays
│   └── embedded/           # Embedded pygame components
└── simulation/             # Core simulation domain
    ├── __init__.py
    ├── agent/              # Agent behavior and decision-making
    │   ├── __init__.py
    │   ├── core.py         # Main Agent class (migrated from agent.py)
    │   ├── decision.py     # Unified selection pass logic
    │   ├── preferences/    # Agent preference systems (migrated from econsim/preferences/)
    │   ├── components/     # Agent sub-components
    │   │   ├── inventory/
    │   │   ├── trading_partner/
    │   │   ├── target_selection/   # Agent decision modes
    │   │   │   ├── bilateral.py    # Renamed from trade.py
    │   │   │   ├── forage.py
    │   │   │   └── idle.py
    │   │   └── movement/
    │   └── modes.py        # Agent mode management (migrated from agent_mode_utils.py)
    ├── world/              # Grid and spatial systems
    │   ├── __init__.py
    │   ├── grid.py         # Grid data structure
    │   ├── spatial.py      # Spatial indexing and queries
    │   ├── respawn.py      # Resource respawn logic
    │   └── coordinates.py  # Position utilities (extracted from grid.py)
    ├── logging/            # Recording and delta systems
    │   ├── __init__.py
    │   ├── delta/          # Current delta system (migrated from econsim/delta/)
    │   ├── recorder.py     # Recording interfaces
    │   ├── playback.py     # Playback engines
    │   └── snapshot.py     # Simulation snapshot system (migrated from simulation/snapshot.py)
    ├── executor.py         # StepExecutor (renamed from step_executor.py)
    ├── coordinator.py      # Simulation coordinator (renamed from world.py)
    ├── config.py           # Simulation configuration
    ├── features.py         # Feature flags
    └── constants.py        # Simulation constants
```

## Migration Strategy

### Phase 1: Infrastructure Setup
**Goal**: Create new source structure and establish parallel development capability

#### 1.1 Create New Source Directory
```bash
mkdir -p source/econsim/{gui/{launcher,widgets,analysis,embedded},simulation/{agent/{preferences,components/{inventory,trading_partner,target_selection,movement}},world,logging/{delta}}}
```

#### 1.2 Initialize Package Structure
- Create all `__init__.py` files with proper imports
- Set up basic package hierarchy
- Configure `pyproject.toml` to support dual source paths during transition

#### 1.3 Establish Import Compatibility Layer
- Create compatibility imports in new structure that reference old locations
- This allows gradual migration without breaking existing code

### Phase 2: Core Simulation Migration
**Goal**: Migrate core simulation components with minimal interface changes

#### 2.1 World/Coordinator Migration
- **Source**: `src/econsim/simulation/world.py` → `source/econsim/simulation/coordinator.py`
- **Changes**: 
  - Rename `Simulation` class to `SimulationCoordinator` for clarity
  - Extract coordinate utilities to `world/coordinates.py`
  - Maintain exact same public API for backward compatibility

#### 2.2 Agent System Restructuring
- **Source**: `src/econsim/simulation/agent.py` → `source/econsim/simulation/agent/core.py`
- **Changes**:
  - Extract decision logic to `agent/decision.py`
  - Migrate mode management from `agent_mode_utils.py` to `agent/modes.py`
  - Reorganize components under `agent/components/`
  - Maintain existing agent behavior interfaces

#### 2.3 Preferences System Migration
- **Source**: `src/econsim/preferences/` → `source/econsim/simulation/agent/preferences/`
- **Changes**: 
  - Move preference system under agent hierarchy
  - Maintain exact same preference interfaces and factory patterns
  - Update import paths to reflect new location

#### 2.4 Trade System Migration
- **Source**: `src/econsim/simulation/trade.py` → `source/econsim/simulation/agent/components/target_selection/bilateral.py`
- **Changes**:
  - Rename file from `trade.py` to `bilateral.py`
  - Move to target_selection components as bilateral trading is a decision mode
  - Maintain exact same trading logic and interfaces

#### 2.5 Grid and Spatial Systems
- **Source**: `src/econsim/simulation/grid.py` → `source/econsim/simulation/world/grid.py`
- **Source**: `src/econsim/simulation/spatial.py` → `source/econsim/simulation/world/spatial.py`
- **Source**: `src/econsim/simulation/respawn.py` → `source/econsim/simulation/world/respawn.py`
- **Changes**: Extract coordinate utilities to separate module

#### 2.6 Execution System
- **Source**: `src/econsim/simulation/step_executor.py` → `source/econsim/simulation/executor.py`
- **Changes**: Rename `OptimizedStepExecutor` to `StepExecutor` for consistency

### Phase 3: Logging and Delta System Migration
**Goal**: Migrate recording and playback systems

#### 3.1 Delta System Migration
- **Source**: `src/econsim/delta/` → `source/econsim/simulation/logging/delta/`
- **Changes**: 
  - Maintain exact same recording format and interfaces
  - Update import paths in recording components

#### 3.2 Snapshot System Migration
- **Source**: `src/econsim/simulation/snapshot.py` → `source/econsim/simulation/logging/snapshot.py`
- **Changes**: 
  - Move snapshot system under logging hierarchy
  - Maintain exact same snapshot interfaces and functionality

#### 3.3 Recording Interface Consolidation
- Create unified `recorder.py` interface
- Migrate playback logic to `playback.py`
- Maintain backward compatibility with existing recordings

### Phase 4: GUI System Migration
**Goal**: Consolidate all GUI components under single hierarchy

#### 4.1 Launcher Migration
- **Source**: `src/econsim/tools/launcher/` → `source/econsim/gui/launcher/`
- **Changes**: Update import paths, maintain exact same functionality

#### 4.2 Widget Consolidation
- **Source**: `src/econsim/tools/widgets/` → `source/econsim/gui/widgets/`
- **Source**: `src/econsim/gui/` → `source/econsim/gui/{analysis,embedded}/`
- **Changes**: Organize by functional area, maintain interfaces

### Phase 5: Configuration and Integration
**Goal**: Update configuration and establish new entry points

#### 5.1 Configuration Migration
- **Source**: `src/econsim/simulation/config.py` → `source/econsim/simulation/config.py`
- **Source**: `src/econsim/simulation/features.py` → `source/econsim/simulation/features.py`
- **Source**: `src/econsim/simulation/constants.py` → `source/econsim/simulation/constants.py`
- **Changes**: Update import paths, maintain exact same configuration interfaces

#### 5.2 Entry Point Updates
- Update `pyproject.toml` entry points to reference new structure
- Create compatibility layer for existing entry points
- Update documentation and examples

### Phase 6: Automated Migration Testing Implementation
**Goal**: Implement comprehensive automated testing to validate migration

#### 6.1 Migration Test Framework
- Create automated tests that validate each component migration
- Implement comparison tests between old and new structures
- Create performance regression detection
- Implement determinism validation tests

#### 6.2 Component Validation Tests
- Test suite migration to new structure
- Automated import path validation
- Interface compatibility testing
- Performance benchmark validation

#### 6.3 Integration Testing
- Test launcher functionality
- Verify delta recording/playback
- Validate GUI components
- Check deterministic behavior

### Phase 7: Documentation and Cleanup
**Goal**: Update documentation and remove old structure

#### 7.1 Documentation Updates
- Update all README files
- Update API documentation
- Update development guides
- Update examples

#### 7.2 Legacy Cleanup
- Remove old `src/` directory (after thorough validation)
- Update CI/CD pipelines
- Update development scripts

## Risk Mitigation Strategies

### 1. Determinism Preservation
**Risk**: Migration could introduce non-deterministic behavior
**Mitigation**: 
- Maintain exact same execution order in all components
- Preserve all RNG seeding and usage patterns
- Run determinism tests after each migration phase
- Keep old and new systems running in parallel during validation

### 2. Performance Regression
**Risk**: New structure could introduce performance overhead
**Mitigation**:
- Maintain exact same execution paths
- Preserve all optimizations (spatial indexing, step executor)
- Run performance benchmarks after each phase
- Profile critical paths to ensure no degradation

### 3. Import Path Breakage
**Risk**: External code depending on VMT could break
**Mitigation**:
- No external dependencies to consider (per requirements)
- Focus on internal consistency and clean structure
- Automated testing will catch any import issues
- Branch-based development allows safe iteration

### 4. GUI Component Integration
**Risk**: GUI components might not integrate properly in new structure
**Mitigation**:
- Test GUI integration after each migration phase
- Maintain exact same widget interfaces
- Preserve all event handling and observer patterns
- Test launcher functionality thoroughly

### 5. Delta System Compatibility
**Risk**: Recording format or playback could break
**Mitigation**:
- Maintain exact same recording format
- Preserve all delta interfaces
- Test with existing recordings
- Version the delta format if changes are needed

## Validation Criteria

### Functional Validation
- [ ] All existing tests pass
- [ ] Launcher works identically
- [ ] Simulation produces identical results
- [ ] GUI displays correctly
- [ ] Delta recording/playback works
- [ ] Performance within 5% of baseline

### Architectural Validation
- [ ] Clean separation of GUI and simulation concerns
- [ ] Logical component grouping
- [ ] Consistent naming conventions
- [ ] Clear module boundaries
- [ ] Maintainable import structure

### Integration Validation
- [ ] Documentation is accurate
- [ ] Examples work correctly
- [ ] CI/CD pipelines function
- [ ] Development workflow is improved
- [ ] All automated migration tests pass

## Rollback Plan

Since this migration is being done on a separate branch with no PR until completion:

1. **Branch-Based Safety**: Issues can be resolved on the migration branch without affecting main
2. **Component Isolation**: Keep working components, fix problematic ones in place
3. **Automated Testing**: Continuous validation catches issues early
4. **Incremental Progress**: Each phase can be validated before proceeding to the next

## Success Metrics

- **Maintainability**: Reduced coupling, clearer boundaries
- **Developer Experience**: Easier navigation, consistent patterns
- **Performance**: No regression in simulation speed
- **Reliability**: All existing functionality preserved
- **Extensibility**: Easier to add new features

## Development Approach

- **Quality-First**: No time pressure - focus on thorough, correct migration
- **Automated Validation**: Comprehensive testing ensures correctness at each step
- **Branch-Based**: Safe development on separate branch until complete replacement is ready
- **Incremental Progress**: Each phase validated before proceeding to next
- **Zero Downtime**: Old structure remains untouched until new structure is fully validated

This migration plan ensures a safe, systematic restructuring of the VMT codebase while preserving all existing functionality and performance characteristics.
