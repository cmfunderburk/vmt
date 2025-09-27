# Monolithic Launcher Breakdown Plan

**Date:** 2025-09-27  
**Focus:** Decomposing the 1153-line `enhanced_test_launcher_v2.py` into modular, testable components

## Problem Statement

The current `MANUAL_TESTS/enhanced_test_launcher_v2.py` is a **41KB monolith** that violates single responsibility principle by mixing:
- Widget composition and UI layout
- Platform-specific styling logic  
- File parsing and custom test discovery
- Process launching and subprocess management
- Comparison mode state management
- Test card rendering and interaction
- Tab management for different tools
- Error handling and user messaging

This makes the code:
- **Hard to test** - GUI components tightly coupled with business logic
- **Hard to evolve** - changes ripple across unrelated concerns  
- **Hard to debug** - responsibilities scattered throughout single file
- **Hard to reuse** - styling and utilities embedded in main class

## Current Architecture Analysis

### File Structure (1153 lines total)
```python
# Lines 1-50: Imports and path hacks
# Lines 51-200: CustomTestsWidget class (~150 lines)
# Lines 201-350: CustomTestCardWidget class (~150 lines) 
# Lines 351-550: TestCardWidget class (~200 lines)
# Lines 551-900: EnhancedTestLauncher main class (~350 lines)
# Lines 901-1078: Platform styling function (~178 lines)
# Lines 1079-1153: Main entry point (~75 lines)
```

### Responsibility Overlaps
1. **UI Composition** - Mixed with business logic in single methods
2. **Event Handling** - Scattered across multiple classes without clear delegation
3. **State Management** - Comparison selections and UI state intermingled  
4. **Data Access** - Direct file system operations mixed with widget code
5. **Process Management** - Subprocess launching embedded in UI event handlers

## Proposed Decomposition Strategy

### Phase 1: Extract Pure Components (Low Risk)
**Goal:** Move self-contained utilities with no GUI dependencies

#### 1.1 Platform Styling Module
```python
# src/econsim/tools/launcher/style.py
class PlatformStyler:
    @staticmethod
    def configure_application(app: QApplication) -> None
    @staticmethod
    def get_platform_stylesheet() -> str
    @staticmethod  
    def apply_dark_mode_fixes() -> None
```
**Benefits:** Immediate reusability, easy to test, no GUI dependencies

#### 1.2 Custom Test Discovery Module  
```python
# src/econsim/tools/launcher/discovery.py
class CustomTestDiscovery:
    def __init__(self, tests_dir: Path)
    def discover_tests(self) -> List[CustomTestInfo]
    def parse_test_metadata(self, file_path: Path) -> CustomTestInfo
    def validate_test_file(self, file_path: Path) -> bool
```
**Benefits:** Pure business logic, easily unit testable

#### 1.3 Data Location Resolver
```python
# src/econsim/tools/launcher/data.py  
class DataLocationResolver:
    def get_config_dir(self) -> Path
    def get_data_dir(self) -> Path
    def get_state_dir(self) -> Path
    def migrate_legacy_data(self) -> None
```
**Benefits:** Centralizes XDG/appdata logic, testable without filesystem

### Phase 2: Extract Business Logic (Medium Risk)
**Goal:** Separate domain logic from presentation

#### 2.1 Test Registry and Metadata
```python
# src/econsim/tools/launcher/registry.py
class TestRegistry:
    def __init__(self, config_source: TestConfigSource)
    def get_all_configs(self) -> Dict[str, TestConfiguration]  
    def get_config_by_id(self, test_id: int) -> TestConfiguration
    def validate_registry(self) -> RegistryValidationResult
    def get_available_tests(self) -> List[TestInfo]
```

#### 2.2 Comparison Mode Controller  
```python
# src/econsim/tools/launcher/comparison.py
class ComparisonController:
    def __init__(self, max_selections: int = 4)
    def add_test(self, test_name: str) -> bool
    def remove_test(self, test_name: str) -> bool  
    def clear_selection(self) -> None
    def get_selected_tests(self) -> List[str]
    def can_launch(self) -> bool
```

#### 2.3 Test Execution Coordinator
```python
# src/econsim/tools/launcher/executor.py
class TestExecutor:
    def __init__(self, registry: TestRegistry)
    def launch_original(self, test_name: str) -> ExecutionResult
    def launch_framework(self, test_name: str) -> ExecutionResult  
    def launch_comparison(self, test_names: List[str]) -> ExecutionResult
    def get_execution_history(self) -> List[ExecutionRecord]
```

### Phase 3: Modularize UI Components (Higher Risk)
**Goal:** Create reusable, focused UI components

#### 3.1 Card Components
```python
# src/econsim/tools/launcher/cards.py
class BaseTestCard(QFrame):
    # Common card styling and behavior
    
class StandardTestCard(BaseTestCard):
    # Standard test configuration cards
    
class CustomTestCard(BaseTestCard):  
    # Custom generated test cards
    
class CardFactory:
    @staticmethod
    def create_card(test_info: TestInfo) -> BaseTestCard
```

#### 3.2 Gallery Management
```python
# src/econsim/tools/launcher/gallery.py
class TestGallery(QWidget):
    def __init__(self, registry: TestRegistry, executor: TestExecutor)
    def populate_tests(self) -> None
    def refresh_gallery(self) -> None
    def set_comparison_mode(self, enabled: bool) -> None
    
class GalleryLayout:
    def __init__(self, max_columns: int = 3)
    def add_card(self, card: BaseTestCard) -> None
    def clear_cards(self) -> None
    def get_card_count(self) -> int
```

#### 3.3 Tab Management  
```python
# src/econsim/tools/launcher/tabs/
# - base_tab.py: AbstractTab base class
# - gallery_tab.py: TestGalleryTab 
# - config_editor_tab.py: ConfigEditorTab
# - batch_runner_tab.py: BatchRunnerTab
# - bookmarks_tab.py: BookmarksTab
# - custom_tests_tab.py: CustomTestsTab

class TabManager:
    def __init__(self, parent: QWidget)
    def register_tab(self, tab: AbstractTab) -> None
    def switch_to_tab(self, tab_id: str) -> None
    def get_active_tab(self) -> AbstractTab
```

### Phase 4: Main Application Coordination (Highest Risk)
**Goal:** Slim main class that coordinates components

#### 4.1 Streamlined Main Window
```python
# src/econsim/tools/launcher/app.py
class VMTLauncher(QMainWindow):
    def __init__(self):
        # Inject dependencies
        self.registry = TestRegistry(...)
        self.executor = TestExecutor(self.registry)
        self.comparison = ComparisonController()
        self.discovery = CustomTestDiscovery(...)
        
        # Compose UI from modules
        self.gallery = TestGallery(self.registry, self.executor)
        self.tab_manager = TabManager(self)
        
        # Wire events between components
        self._connect_signals()
        
    def _connect_signals(self):
        # Pure delegation - no business logic here
```

## Incremental Migration Strategy

### Option A: File-by-File Extraction (Safest)
1. **Week 1:** Extract `PlatformStyler` and `CustomTestDiscovery`
2. **Week 2:** Extract `TestRegistry` and `ComparisonController`  
3. **Week 3:** Create `BaseTestCard` and card components
4. **Week 4:** Build `TestGallery` and `TabManager`
5. **Week 5:** Refactor main `VMTLauncher` class

**Pros:** Each step can be tested independently  
**Cons:** Slower progress, temporary duplication

### Option B: Big Bang Rewrite (Riskiest, Fastest)
1. **Day 1-2:** Create all module structure simultaneously
2. **Day 3-4:** Move code and fix imports
3. **Day 5:** Integration testing and bug fixes

**Pros:** Clean slate, no temporary duplication  
**Cons:** High integration risk, harder to isolate issues

### Option C: Hybrid Approach (Recommended)
1. **Phase 1:** Extract pure utilities (styling, discovery, data) - **LOW RISK**
2. **Phase 2:** Extract business logic (registry, comparison, executor) - **MEDIUM RISK** 
3. **Phase 3:** Refactor UI components using extracted utilities - **HIGHER RISK**
4. **Phase 4:** Slim down main application class - **HIGHEST RISK**

**Pros:** Gradual risk increase, early wins build confidence  
**Cons:** Some temporary complexity during transition

## Testing Strategy

### Unit Testing Targets
- **Pure Components:** `PlatformStyler`, `CustomTestDiscovery`, `DataLocationResolver`
- **Business Logic:** `TestRegistry`, `ComparisonController`, `TestExecutor` 
- **UI Components:** Mock dependencies for widget testing

### Integration Testing
- **Module Boundaries:** Ensure clean interfaces between components
- **Event Flow:** Verify signal/slot connections work correctly
- **Data Flow:** Test registry → executor → UI update cycles

### Regression Testing  
- **Screenshot Comparison:** Ensure UI appearance unchanged
- **Functional Testing:** All existing workflows must continue working
- **Performance Testing:** Ensure no degradation in startup/response time

## Discussion Points

1. **Dependency Injection:** Should we use a formal DI container or constructor injection?

2. **Signal/Slot Architecture:** PyQt6 signals vs custom event system vs observer pattern?

3. **Testing Framework:** Should we test UI components or focus on business logic?

4. **Migration Timeline:** Aggressive (2 weeks) vs conservative (6 weeks) schedule?

5. **Backwards Compatibility:** How long should we maintain the monolithic version?

6. **Error Handling:** Centralized error handling vs distributed responsibility?

## Success Metrics

### Code Quality
- **Cyclomatic Complexity:** Each module < 10 complexity
- **Line Count:** No single class > 150 lines  
- **Test Coverage:** > 80% coverage for business logic modules

### Maintainability  
- **Adding New Test:** Should require touching only `test_configs.py`
- **UI Styling Changes:** Should only affect `style.py` module
- **Platform Fixes:** Isolated to platform-specific modules

### Performance
- **Startup Time:** < 2 second regression from current
- **Memory Usage:** No significant increase in baseline memory
- **Responsiveness:** UI interactions remain < 100ms

---

**Next Steps:** Discuss preferred approach and begin with Phase 1 utilities extraction.