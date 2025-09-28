# Framework Migration Plan - Phase 1

**Date:** 2025-09-27  
**Context:** Post Part 2 UI extraction, proceeding with Critical Review Phase 1  
**Scope:** Move `MANUAL_TESTS/framework/` to `src/econsim/tools/launcher/framework/`  
**Priority:** Critical architectural cleanup - eliminates `sys.path` hacks and import gymnastics

---

## 0. Objectives
1. **Eliminate `sys.path` manipulation** in launcher components
2. **Centralize framework code** under proper package structure
3. **Enable clean imports** from `econsim.tools.launcher.framework`
4. **Maintain backward compatibility** for existing manual tests during transition
5. **Validate no circular dependencies** between framework and core simulation

---

## 1. Current State Analysis

### 1.1 Framework Files to Migrate
```
MANUAL_TESTS/framework/
├── __init__.py
├── base_test.py                    # BaseTest class + common test patterns
├── debug_orchestrator.py           # Debug logging coordination
├── phase_manager.py                # Phase configuration management  
├── simulation_factory.py          # Simulation construction helpers
├── test_configs.py                 # TestConfiguration registry (ALL_TEST_CONFIGS)
└── ui_components.py                # Shared UI components
```

### 1.2 Current Import Patterns (Problems)
```python
# MANUAL_TESTS/enhanced_test_launcher_v2.py:34
sys.path.insert(0, str(project_root))

# MANUAL_TESTS/enhanced_test_launcher_v2.py:48  
from framework.test_configs import TestConfiguration, ALL_TEST_CONFIGS

# Multiple manual tests have similar patterns
```

### 1.3 Dependencies to Analyze
- **Framework → Core**: Check if framework imports from `src/econsim/simulation/`
- **Core → Framework**: Ensure core simulation doesn't depend on framework
- **Cross-Framework**: Dependencies between framework modules

---

## 2. Migration Strategy (Low-Risk Incremental)

### 2.1 Phase 1.1: Dependency Analysis & Validation
**Goal:** Understand current coupling before moving files

#### Actions:
1. **Map Current Imports**:
   ```bash
   # Find all framework imports in codebase
   grep -r "from framework" MANUAL_TESTS/
   grep -r "import framework" MANUAL_TESTS/
   ```

2. **Check Framework Dependencies**:
   ```bash
   # What does framework import from core?
   grep -r "from src.econsim" MANUAL_TESTS/framework/
   grep -r "from econsim" MANUAL_TESTS/framework/
   ```

3. **Identify Circular Risk**:
   ```bash
   # Does core reference framework? (should be NO)
   grep -r "framework" src/econsim/
   ```

#### Exit Criteria:
- ✅ Complete import map documented
- ✅ No circular dependencies found
- ✅ Framework only uses public APIs from `src/econsim/`

### 2.2 Phase 1.2: Target Structure Creation
**Goal:** Create clean target structure with proper package hierarchy

#### Actions:
1. **Create Target Directory**:
   ```bash
   mkdir -p src/econsim/tools/launcher/framework/
   ```

2. **Create Package Structure**:
   ```
   src/econsim/tools/launcher/framework/
   ├── __init__.py                 # Package exports
   ├── base_test.py               # BaseTest class
   ├── debug_orchestrator.py      # Debug coordination  
   ├── phase_manager.py           # Phase management
   ├── simulation_factory.py     # Simulation helpers
   ├── test_configs.py            # Test registry
   └── ui_components.py           # Shared UI components
   ```

3. **Design Clean Exports**:
   ```python
   # src/econsim/tools/launcher/framework/__init__.py
   from .test_configs import TestConfiguration, ALL_TEST_CONFIGS
   from .base_test import BaseTest
   from .phase_manager import PhaseManager
   from .simulation_factory import SimulationFactory
   # ... etc
   ```

#### Exit Criteria:
- ✅ Target structure created
- ✅ Package `__init__.py` designed
- ✅ Import paths planned

### 2.3 Phase 1.3: File Migration & Import Fixes
**Goal:** Move files and fix internal framework imports

#### Actions:
1. **Copy Files** (not move yet - keep backups):
   ```bash
   cp MANUAL_TESTS/framework/*.py src/econsim/tools/launcher/framework/
   ```

2. **Fix Internal Framework Imports**:
   ```python
   # Change relative imports within framework
   # FROM: from .test_configs import ALL_TEST_CONFIGS  
   # TO:   from .test_configs import ALL_TEST_CONFIGS  (same)
   
   # Change absolute imports to new package
   # FROM: from framework.phase_manager import PhaseManager
   # TO:   from econsim.tools.launcher.framework.phase_manager import PhaseManager
   ```

3. **Update External API Imports**:
   ```python
   # Ensure framework only imports public APIs
   # FROM: from src.econsim.simulation.world import Simulation
   # TO:   from econsim.simulation.world import Simulation
   ```

#### Exit Criteria:
- ✅ All framework files copied to target location
- ✅ Internal imports working in new structure
- ✅ Framework can import successfully

### 2.4 Phase 1.4: Consumer Update (Launcher Integration)
**Goal:** Update Part 2 launcher components to use new framework location

#### Actions:
1. **Update Existing Part 2 Components**:
   ```python
   # src/econsim/tools/launcher/adapters.py
   # FROM: from framework.test_configs import ALL_TEST_CONFIGS
   # TO:   from .framework.test_configs import ALL_TEST_CONFIGS
   ```

2. **Test Framework Import in Launcher**:
   ```python
   # Verify new imports work
   from econsim.tools.launcher.framework import TestConfiguration, ALL_TEST_CONFIGS
   ```

3. **Update Runner if Needed**:
   ```python
   # src/econsim/tools/launcher/runner.py
   # Any framework references should use new path
   ```

#### Exit Criteria:
- ✅ Part 2 launcher components updated
- ✅ All launcher tests still pass
- ✅ No `sys.path` hacks in launcher package

### 2.5 Phase 1.5: Manual Tests Transition
**Goal:** Update manual tests to use new framework location while maintaining compatibility

#### Actions:
1. **Add Compatibility Layer** (temporary):
   ```python
   # MANUAL_TESTS/framework_compat.py (temporary bridge)
   # Allows existing manual tests to work during transition
   from econsim.tools.launcher.framework import *
   ```

2. **Update Manual Tests Incrementally**:
   ```python
   # MANUAL_TESTS/enhanced_test_launcher_v2.py
   # FROM: sys.path.insert(0, str(project_root))
   #       from framework.test_configs import ALL_TEST_CONFIGS
   # TO:   from econsim.tools.launcher.framework import ALL_TEST_CONFIGS
   ```

3. **Test Each Manual Test File**:
   ```bash
   # Verify each manual test still launches
   cd MANUAL_TESTS
   python enhanced_test_launcher_v2.py  # Should work
   python test_1_baseline_simple.py     # Should work
   # ... etc
   ```

#### Exit Criteria:
- ✅ All manual tests launch successfully
- ✅ Framework imports resolved
- ✅ No broken functionality

### 2.6 Phase 1.6: Cleanup & Finalization
**Goal:** Remove old framework location and finalize migration

#### Actions:
1. **Remove `sys.path` Hacks**:
   ```python
   # Remove from all files:
   # sys.path.insert(0, str(project_root))
   ```

2. **Remove Old Framework Directory**:
   ```bash
   # Only after all tests pass
   rm -rf MANUAL_TESTS/framework/
   ```

3. **Update Documentation**:
   ```markdown
   # Update any docs that reference MANUAL_TESTS/framework/
   # Point to src/econsim/tools/launcher/framework/
   ```

#### Exit Criteria:
- ✅ Old framework directory removed
- ✅ No `sys.path` manipulation anywhere
- ✅ All tests passing
- ✅ Documentation updated

---

## 3. Validation Strategy

### 3.1 Automated Tests
```bash
# After each phase, run:
pytest tests/unit/launcher/ -v                    # Part 2 components
QT_QPA_PLATFORM=offscreen python -m econsim.tools.launcher.runner --headless --list-tests
```

### 3.2 Manual Test Validation
```bash
# Test each manual test interface:
cd MANUAL_TESTS
python enhanced_test_launcher_v2.py              # Enhanced launcher
python test_1_baseline_simple.py                 # Individual tests  
python batch_test_runner.py                      # Batch runner
python test_bookmarks.py                         # Bookmarks
```

### 3.3 Import Validation
```python
# Should work cleanly after migration:
from econsim.tools.launcher.framework import TestConfiguration
from econsim.tools.launcher.framework import ALL_TEST_CONFIGS  
from econsim.tools.launcher.framework import BaseTest
from econsim.tools.launcher.framework import PhaseManager
```

---

## 4. Risk Assessment & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|---------|------------|
| Circular dependency introduced | Low | High | Thorough dependency analysis first |
| Manual tests break during transition | Medium | Medium | Compatibility layer + incremental testing |
| Framework imports core internals | Medium | High | Audit framework imports; fix to use public APIs |
| Path-dependent code failures | Low | Medium | Search for hardcoded paths; use relative imports |

---

## 5. Success Metrics

### 5.1 Code Quality
- **Zero `sys.path` manipulations** in any launcher code
- **Clean package imports** using standard Python import syntax
- **No circular dependencies** between framework and core

### 5.2 Functionality
- **All launcher tests pass** (42 tests currently)  
- **All manual tests launch** without errors
- **Framework components importable** from proper package paths

### 5.3 Architecture
- **Framework centralized** under single package hierarchy
- **Public API boundaries respected** (framework → core only via public APIs)
- **Import paths consistent** across all consumers

---

## 6. Implementation Sequence

### Quick Start (2-3 hours):
1. **30 min**: Phase 1.1 - Dependency analysis
2. **30 min**: Phase 1.2 - Create target structure  
3. **60 min**: Phase 1.3 - File migration + import fixes
4. **30 min**: Phase 1.4 - Update launcher integration
5. **30 min**: Phase 1.5 - Manual tests transition
6. **15 min**: Phase 1.6 - Cleanup

### Conservative (1 day):
- Add validation steps between each phase
- Test each manual test individually  
- Create rollback checkpoints

---

## 7. Rollback Plan

If issues arise:
1. **Revert launcher changes**: `git checkout src/econsim/tools/launcher/`
2. **Restore old framework**: `git checkout MANUAL_TESTS/framework/`
3. **Fix issues** in isolation
4. **Re-attempt migration** with fixes applied

---

## 8. Next Steps After Framework Migration

Once Phase 1 complete, enables:
1. **Data Location Migration** (Critical Review Phase 5)
2. **Console Script Packaging** (Critical Review Phase 6)  
3. **Full Makefile Integration** (`make enhanced-tests` uses package)

The framework migration is the **critical enabler** for full launcher packaging since it eliminates the last `sys.path` dependency that prevents clean package installation.

---

**Ready to proceed?** The incremental approach minimizes risk while achieving clean architectural separation. Each phase has clear validation criteria and rollback options.