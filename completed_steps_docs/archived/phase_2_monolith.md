# Phase 2: Monolithic Launcher Breakdown - Step-by-Step Plan

**Date:** 2025-09-27  
**Status:** Phase 1 COMPLETED ✅ | Phase 2 READY TO START  
**Goal:** Extract UI components from the 1062-line `enhanced_test_launcher_v2.py` monolith

## Current State Analysis

### ✅ Phase 1 Complete (Business Logic Extracted)
The core business logic is **already extracted** and functional:
- ✅ `TestRegistry` - aggregates builtin + custom test configurations  
- ✅ `ComparisonController` - manages comparison selection state
- ✅ `TestExecutor` - constructs deterministic command arrays
- ✅ `CustomTestDiscovery` - pure file parsing and metadata extraction
- ✅ `PlatformStyler` - platform-specific styling utilities
- ✅ `DataLocationResolver` - XDG/appdata path management
- ✅ **42 passing unit tests** covering extracted components
- ✅ **Adapter bridge working** - monolith can use extracted components

### 🎯 Phase 2 Target (UI Component Extraction)
The monolithic `enhanced_test_launcher_v2.py` (1062 lines) still contains:
- **Lines 64-240**: `CustomTestsWidget` class (~176 lines) - custom test discovery UI
- **Lines 245-436**: `CustomTestCardWidget` class (~191 lines) - custom test cards  
- **Lines 437-618**: `TestCardWidget` class (~181 lines) - standard test cards
- **Lines 621-990**: `EnhancedTestLauncher` class (~369 lines) - main window coordination
- **Lines 991-1050**: Platform styling function (~59 lines) - **can be removed** (already extracted)
- **Lines 1051-1062**: Main entry point (~11 lines)

## Step-by-Step Execution Plan

### Step 2.1: Extract Custom Test Card Component (LOW RISK)
**Goal:** Move `CustomTestCardWidget` to `src/econsim/tools/launcher/cards.py`

**Actions:**
1. **Extract class definition**:
   - Move `CustomTestCardWidget` (lines 245-436) to `cards.py`
   - Add proper imports and type hints
   - Preserve all existing functionality

2. **Update monolith imports**:
   - Add: `from econsim.tools.launcher.cards import CustomTestCardWidget`
   - Remove the class definition from monolith

3. **Test extraction**:
   - Verify launcher still launches without errors
   - Test custom test card creation and interaction
   - Run visual regression test

**Expected Files Modified:**
- `src/econsim/tools/launcher/cards.py` - add `CustomTestCardWidget` class
- `MANUAL_TESTS/enhanced_test_launcher_v2.py` - remove class, add import
- `src/econsim/tools/launcher/__init__.py` - export new component

**Risk Level:** LOW - Self-contained UI component with minimal dependencies

---

### Step 2.2: Extract Standard Test Card Component (LOW RISK)  
**Goal:** Move `TestCardWidget` to `src/econsim/tools/launcher/cards.py`

**Actions:**
1. **Extract class definition**:
   - Move `TestCardWidget` (lines 437-618) to `cards.py` 
   - Update to use `TestConfiguration` from `types.py`
   - Preserve PyQt6 signals and UI behavior

2. **Update monolith imports**:
   - Add: `from econsim.tools.launcher.cards import TestCardWidget`
   - Remove the class definition from monolith

3. **Test extraction**:
   - Verify standard test cards render correctly
   - Test launch and comparison button functionality
   - Verify signal/slot connections work

**Expected Files Modified:**
- `src/econsim/tools/launcher/cards.py` - add `TestCardWidget` class
- `MANUAL_TESTS/enhanced_test_launcher_v2.py` - remove class, add import

**Risk Level:** LOW - Well-defined component with clear interface boundaries

---

### Step 2.3: Extract Custom Tests Widget (MEDIUM RISK)
**Goal:** Move `CustomTestsWidget` to `src/econsim/tools/launcher/tabs/custom_tests_tab.py`

**Actions:**
1. **Create tab structure**:
   - Create `src/econsim/tools/launcher/tabs/` directory
   - Create `base_tab.py` with `AbstractTab` interface
   - Create `custom_tests_tab.py` with `CustomTestsTab` class

2. **Extract widget logic**:
   - Move `CustomTestsWidget` (lines 64-240) to `CustomTestsTab`
   - Integrate with `CustomTestDiscovery` component (already extracted)
   - Update to use extracted `CustomTestCardWidget`

3. **Update monolith integration**:
   - Replace `CustomTestsWidget` with `CustomTestsTab` import
   - Update tab creation in main window

4. **Test extraction**:
   - Verify custom test discovery works
   - Test custom test card generation
   - Test file operations (launch, edit, delete)

**Expected Files Modified:**
- `src/econsim/tools/launcher/tabs/base_tab.py` - new abstract base
- `src/econsim/tools/launcher/tabs/custom_tests_tab.py` - extracted widget
- `src/econsim/tools/launcher/tabs/__init__.py` - new package exports
- `MANUAL_TESTS/enhanced_test_launcher_v2.py` - replace widget usage

**Risk Level:** MEDIUM - More complex component with file system interactions

---

### Step 2.4: Extract Gallery Management (MEDIUM RISK)
**Goal:** Create `TestGallery` component for standard test card management

**Actions:**
1. **Identify gallery logic**:
   - Extract test card creation and layout from `EnhancedTestLauncher`
   - Extract comparison mode visual feedback
   - Extract card grid layout management

2. **Create gallery component**:
   - Create `src/econsim/tools/launcher/gallery.py`
   - Implement `TestGallery` class with:
     - Registry integration for test discovery
     - Card creation using extracted `TestCardWidget`
     - Comparison mode state visualization
     - Grid layout management

3. **Update main window**:
   - Replace inline gallery logic with `TestGallery` component
   - Wire gallery signals to main window handlers

4. **Test integration**:
   - Verify test cards display correctly
   - Test comparison selection visual feedback
   - Test card launch functionality

**Expected Files Modified:**
- `src/econsim/tools/launcher/gallery.py` - new gallery component
- `MANUAL_TESTS/enhanced_test_launcher_v2.py` - use gallery component

**Risk Level:** MEDIUM - Requires careful signal/slot wiring

---

### Step 2.5: Extract Tab Management (MEDIUM-HIGH RISK)
**Goal:** Create unified tab management system

**Actions:**
1. **Create tab manager**:
   - Implement `src/econsim/tools/launcher/tabs/manager.py`
   - Create `TabManager` class for coordinating multiple tabs
   - Define tab registration and switching interface

2. **Extract remaining tabs**:
   - Extract Config Editor tab (if present in monolith)
   - Extract Batch Runner tab (if present in monolith)  
   - Extract Bookmarks tab (if present in monolith)

3. **Update main window**:
   - Replace `QTabWidget` direct management with `TabManager`
   - Register all tabs through manager interface

4. **Test integration**:
   - Verify all tabs load correctly
   - Test tab switching functionality
   - Test inter-tab communication (if any)

**Expected Files Modified:**
- `src/econsim/tools/launcher/tabs/manager.py` - tab coordination
- Additional tab files as needed
- `MANUAL_TESTS/enhanced_test_launcher_v2.py` - use tab manager

**Risk Level:** MEDIUM-HIGH - Complex component interactions

---

### Step 2.6: Streamline Main Application Class (HIGH RISK)
**Goal:** Reduce `EnhancedTestLauncher` to pure coordination logic

**Actions:**
1. **Analyze remaining responsibilities**:
   - Window setup and menu creation
   - Component wiring and signal connections
   - Event handling delegation
   - Application lifecycle management

2. **Create main application shell**:
   - Create `src/econsim/tools/launcher/app_window.py`
   - Implement `VMTLauncherWindow` class with dependency injection
   - Move window setup and coordination logic

3. **Update monolith**:
   - Replace `EnhancedTestLauncher` class with `VMTLauncherWindow` import
   - Preserve entry point functionality

4. **Test integration**:
   - Verify complete application launches correctly
   - Test all workflows end-to-end
   - Performance regression testing

**Expected Files Modified:**
- `src/econsim/tools/launcher/app_window.py` - main window coordination
- `MANUAL_TESTS/enhanced_test_launcher_v2.py` - minimal entry point

**Risk Level:** HIGH - Core application coordination logic

---

### Step 2.7: Remove Styling Duplication (LOW RISK)
**Goal:** Remove redundant styling code from monolith

**Actions:**
1. **Identify duplicate styling**:
   - Find platform styling function in monolith (lines 991-1050)
   - Verify `PlatformStyler` covers same functionality

2. **Update imports**:
   - Ensure monolith imports `PlatformStyler` from extracted module
   - Remove duplicate styling function

3. **Test styling**:
   - Verify application appearance unchanged
   - Test platform-specific styling still works

**Expected Files Modified:**
- `MANUAL_TESTS/enhanced_test_launcher_v2.py` - remove duplicate code

**Risk Level:** LOW - Simple duplication removal

---

### Step 2.8: Create Modular Entry Point (LOW RISK)
**Goal:** Clean up entry point to use extracted components

**Actions:**
1. **Analyze current entry point**:
   - Review main execution logic (lines 1051-1062)
   - Identify initialization sequence

2. **Create clean entry point**:
   - Update entry point to use `VMTLauncherWindow`
   - Simplify initialization logic
   - Preserve command-line argument handling

3. **Final testing**:
   - End-to-end functionality testing
   - Performance regression testing
   - Visual regression testing

**Expected Files Modified:**
- `MANUAL_TESTS/enhanced_test_launcher_v2.py` - simplified entry point

**Risk Level:** LOW - Simple coordination updates

## Validation Strategy

### After Each Step
1. **Functional Testing**:
   - Launch enhanced test launcher: `make enhanced-tests`
   - Verify all tabs load and function correctly
   - Test both standard and custom test launching

2. **Unit Testing**:
   - Run extracted component tests: `pytest tests/unit/launcher/ -v`
   - Verify no regressions in existing tests

3. **Integration Testing**:
   - Test adapter bridge still works
   - Verify all existing workflows functional

### Final Phase 2 Validation
1. **Line Count Verification**:
   - Monolith should be reduced to <200 lines (entry point only)
   - Each extracted component should be <150 lines

2. **Architecture Validation**:
   - Clear separation of concerns achieved
   - No circular dependencies
   - Clean component interfaces

3. **Performance Testing**:
   - Startup time unchanged
   - Memory usage within bounds
   - UI responsiveness maintained

## Risk Mitigation

### Backup Strategy
- **Before each step**: Create branch checkpoint
- **If extraction fails**: Revert to previous checkpoint
- **Preserve monolith**: Keep as `enhanced_test_launcher_v2_backup.py`

### Testing Strategy  
- **Incremental testing**: Validate after each component extraction
- **Rollback plan**: Clear revert path for each step
- **Regression detection**: Visual and functional comparison tests

### Communication Strategy
- **Progress tracking**: Update this document with completion status
- **Issue logging**: Document any discovered problems
- **Success criteria**: Clear definition for each step completion

## Success Metrics

### Quantitative Goals
- **Monolith size**: Reduce from 1062 lines to <200 lines
- **Component size**: Each extracted component <150 lines  
- **Test coverage**: Maintain 42+ passing tests
- **Performance**: <5% startup time regression

### Qualitative Goals
- **Single Responsibility**: Each component has one clear purpose
- **Testability**: Components can be unit tested in isolation
- **Reusability**: Components can be used in other launcher contexts
- **Maintainability**: Changes isolated to single components

---

## Next Action Decision Points

**Recommended Starting Point**: Step 2.1 (Extract Custom Test Card)
- Lowest risk (self-contained UI component)
- Clear boundaries and minimal dependencies  
- Success builds confidence for subsequent steps

**Alternative Starting Point**: Step 2.7 (Remove Styling Duplication)
- Immediate cleanup with near-zero risk
- Validates existing `PlatformStyler` integration
- Quick win to build momentum

Which step would you like to begin with?