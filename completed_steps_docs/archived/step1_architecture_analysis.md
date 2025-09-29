# Step 1: Architecture Analysis - Current vs Target State

**Analysis Date**: September 28, 2025  
**Purpose**: Document current subprocess launching system before implementing programmatic runner  
**Context**: Phase 6 implementation - replacing brittle subprocess approach with direct API calls

## Current Architecture Analysis

### 1. Current Test Launching (app_window.py)

#### Subprocess Implementation
Located in `src/econsim/tools/launcher/app_window.py`, lines 264-320:

```python
def launch_test(self, test_name: str, version: str = "framework") -> None:
    """Launch a test (always uses framework version now)."""
    # Version parameter kept for compatibility but ignored
    self._launch_test(test_name)
        
def _launch_test(self, test_name: str) -> None:
    """Launch test (framework version)."""
    # Find config by label to get ID  
    config = None
    for cfg in self._registry.all().values():
        if cfg.label == test_name:
            config = cfg
            break
    
    # HARDCODED MAPPING - This is what we need to eliminate
    id_to_file = {
        1: "test_1.py",
        2: "test_2.py", 
        3: "test_3.py",
        4: "test_4.py",
        5: "test_5.py",
        6: "test_6.py",
        7: "test_7.py"
    }
    
    # Construct path and launch subprocess
    test_path = Path(__file__).parent.parent.parent.parent.parent / "MANUAL_TESTS" / test_file
    subprocess.Popen([sys.executable, str(test_path)], cwd=str(test_path.parent))
```

#### Current Issues Identified
1. **Hardcoded filename mappings**: Brittle `id_to_file` dictionary
2. **Path construction complexity**: Deep relative path navigation 
3. **No mode distinction**: "framework" vs "original" parameter ignored
4. **Limited error handling**: Basic exception catching only
5. **Subprocess dependency**: Python interpreter startup overhead
6. **No process management**: Fire-and-forget subprocess launching

#### Error Handling Analysis
- Basic try/catch around entire launch process
- Uses `log_status()` for user feedback 
- Checks for test file existence before launch
- No subprocess exit code monitoring

### 2. Framework Infrastructure

#### Test Configuration Registry (`test_configs.py`)
- **TestConfiguration class**: Complete test specifications (id, name, grid_size, etc.)
- **ALL_TEST_CONFIGS**: Dictionary mapping IDs 1-7 to TestConfiguration objects
- **Rich metadata**: Each config has description, preference_mix, viewport_size, etc.

#### Simulation Factory (`simulation_factory.py`)
- **SimulationFactory class**: Creates Simulation objects from TestConfiguration
- **create_simulation() method**: Handles resource generation, agent positioning, preference factories
- **Integration ready**: Uses SimConfig and Simulation classes directly

#### GUI Integration Components
- **EmbeddedPygameWidget**: PyQt6↔Pygame integration for rendering
- **StandardPhaseTest**: Base class used by all framework test files
- **TestLayout**: Standardized UI components for test windows

### 3. Test File Analysis

#### Framework Test Structure (test_1.py through test_7.py)
All test files follow identical pattern:

```python
from econsim.tools.launcher.framework.base_test import StandardPhaseTest  
from econsim.tools.launcher.framework.test_configs import TEST_N_*

class TestNWindowNew(StandardPhaseTest):
    """Test N using framework."""
    
    def __init__(self):
        super().__init__(TEST_N_CONFIG)

def main():
    app = QApplication(sys.argv)
    test_window = TestNWindowNew()
    test_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

#### Test File Mapping
| Test ID | File | Config Object | Class Name | Status |
|---------|------|---------------|------------|--------|
| 1 | test_1.py | TEST_1_BASELINE | Test1WindowNew | Framework |
| 2 | test_2.py | TEST_2_SPARSE | Test2WindowNew | Framework |
| 3 | test_3.py | TEST_3_HIGH_DENSITY | Test3WindowNew | Framework |
| 4 | test_4.py | TEST_4_LARGE_WORLD | Test4WindowNew | Framework |
| 5 | test_5.py | TEST_5_COBB_DOUGLAS | Test5WindowNew | Framework |
| 6 | test_6.py | TEST_6_LEONTIEF | Test6WindowNew | Framework |
| 7 | test_7.py | TEST_7_PERFECT_SUBSTITUTES | Test7WindowNew | Framework |

#### Key Observations
1. **All tests use framework**: No "original" mode tests found - parameter is legacy
2. **Consistent structure**: Every test file follows same ~30 line pattern
3. **StandardPhaseTest inheritance**: All tests extend common base class
4. **Direct config usage**: Tests directly use TEST_N_* objects from registry
5. **Self-contained**: Each test file can run independently with `python test_N.py`

## Target Architecture Design

### Programmatic Test Execution Flow
```python
# CURRENT (subprocess):
test_name -> config lookup -> id_to_file mapping -> subprocess.Popen()

# TARGET (programmatic):
test_name -> config lookup -> TestRunner.run_config() -> direct GUI creation
```

### TestRunner API Design
Based on analysis, the TestRunner should:

```python
class TestRunner:
    def run_by_id(self, test_id: int, mode: str) -> None:
        """Run test by ID using registry lookup."""
        config = ALL_TEST_CONFIGS[test_id]
        self.run_config(config, mode)
    
    def run_config(self, config: TestConfiguration, mode: str) -> None:
        """Run test configuration programmatically."""
        if mode == "framework":
            self._run_framework_test(config)
        else:  # "original" - fallback to subprocess
            self._run_original_test(config)
```

### Framework Mode Implementation 
Direct instantiation without subprocess:

```python
def _run_framework_test(self, config: TestConfiguration) -> None:
    # Create simulation from config
    simulation = SimulationFactory.create_simulation(config)
    
    # Create GUI window directly
    window = QMainWindow()
    pygame_widget = EmbeddedPygameWidget(simulation=simulation, config=config)
    
    # Show and start
    window.show()
    pygame_widget.start_simulation()
```

## Current vs Target Comparison

### Subprocess Launch (Current)
**Advantages:**
- Process isolation (crashes don't affect launcher)
- Familiar debugging (separate Python process)
- Independent memory space

**Disadvantages:** 
- Python interpreter startup overhead (~100-200ms)
- Brittle hardcoded filename mappings
- Complex path construction 
- No process lifecycle management
- Limited error feedback

### Programmatic Launch (Target)  
**Advantages:**
- Eliminate hardcoded filename mappings
- Use existing TestConfiguration registry  
- Direct access to framework components
- Better error handling and user feedback
- Faster launch times (no Python startup)
- Proper integration with launcher lifecycle

**Disadvantages:**
- Shared memory space (potential crashes affect launcher)  
- Need careful cleanup between test runs
- More complex state management

## Implementation Readiness Assessment

### ✅ Ready Components
1. **TestConfiguration registry**: Complete with all test specs
2. **SimulationFactory**: Working simulation creation from configs
3. **EmbeddedPygameWidget**: GUI integration tested and working
4. **StandardPhaseTest**: Framework base class established

### ⚠️ Gaps to Address  
1. **Window lifecycle management**: Need proper cleanup between tests
2. **Error boundaries**: Prevent test crashes from affecting launcher
3. **Memory management**: Ensure no accumulation across multiple launches
4. **Original mode fallback**: Maintain subprocess option for compatibility

### 🔧 Integration Points
1. **Replace `_launch_test()` method**: Swap subprocess call with programmatic creation
2. **Remove `id_to_file` mapping**: Use TestConfiguration registry instead
3. **Enhanced error handling**: Better user feedback for test launch failures
4. **Status monitoring**: Track running tests and enable cleanup

## Recommended Implementation Approach

### Phase 1: Core TestRunner
Create `src/econsim/tools/launcher/test_runner.py` with:
- TestRunner class with run_by_id() and run_config() methods
- Framework mode using direct GUI creation  
- Original mode using improved subprocess (fallback)

### Phase 2: GUI Integration
Update `app_window.py`:
- Replace `_launch_test()` with TestRunner calls
- Remove hardcoded `id_to_file` mapping
- Add TestRunner initialization and error handling

### Phase 3: Testing & Validation
- Verify all 7 tests launch correctly
- Validate memory usage and cleanup
- Test error handling and fallback scenarios

## Architecture Decision Record

**Decision**: Implement dual-mode TestRunner with framework primary, subprocess fallback  
**Rationale**: Provides reliability through fallback while eliminating brittle filename mappings  
**Trade-offs**: Slightly more complexity for significantly better maintainability  
**Alternatives considered**: Framework-only (too risky), subprocess-only (doesn't solve core problem)

---

**Next Step**: Proceed to Step 2 - Create Test Runner Core implementation