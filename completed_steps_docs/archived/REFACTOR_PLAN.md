# Manual Tests Refactor Plan

## 🔍 **Current Pain Points Identified**

1. **Massive Code Duplication**: All 7 tests share nearly identical structure (~400 lines each)
2. **Phase Transition Logic**: Same phase schedule and implementation repeated 7 times  
3. **Debug Panel Setup**: Identical debug log display code in every test
4. **UI Layout**: Same PyQt6 layout patterns duplicated across all tests
5. **Configuration Management**: Test configs scattered with manual parameter setup
6. **Environment Variable Management**: Repetitive environment setup for debug flags

## 🏗️ **Proposed Refactor Architecture**

### **1. Base Test Framework Classes**
```python
# framework/base_test.py
class BaseManualTest(QWidget):
    """Abstract base class for all manual tests with common functionality."""
    
    def __init__(self, config: TestConfiguration):
        super().__init__()
        self.config = config
        self.simulation = None
        self.current_turn = 0
        self.phase = 1
        
        # Setup common components
        self.setup_ui()
        self.setup_debug_orchestrator()
        self.setup_timers()
        
    def setup_ui(self):
        """Create standardized three-panel layout."""
        pass  # Implementation details
        
    def setup_debug_orchestrator(self):
        """Configure debug logging for this test."""
        pass  # Implementation details

class StandardPhaseTest(BaseManualTest):
    """Standard 6-phase test with common phase transitions."""
    
    def __init__(self, config: TestConfiguration):
        super().__init__(config)
        self.phase_manager = PhaseManager.create_standard_phases()
        
class CustomPhaseTest(BaseManualTest): 
    """For tests with custom phase schedules."""
    
    def __init__(self, config: TestConfiguration, phases: List[PhaseDefinition]):
        super().__init__(config)
        self.phase_manager = PhaseManager(phases)
```

### **2. Configuration-Driven Test Definitions**
```python
# framework/test_configs.py
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class TestConfiguration:
    """Complete test specification - replaces scattered manual setup."""
    id: int
    name: str
    description: str
    grid_size: tuple[int, int]
    agent_count: int
    resource_density: float
    perception_radius: int
    preference_mix: str  # "mixed", "cobb_douglas", "leontief", "perfect_substitutes"
    seed: int
    viewport_size: int = 600
    custom_phases: Optional[List['PhaseDefinition']] = None
    debug_categories: Optional[List[str]] = None

# All current tests defined as configurations
TEST_1_BASELINE = TestConfiguration(
    id=1,
    name="Baseline Unified Target Selection",
    description="Validates unified target selection behavior with mixed preferences",
    grid_size=(30, 30),
    agent_count=20,
    resource_density=0.25,
    perception_radius=8,
    preference_mix="mixed",
    seed=12345
)

TEST_2_SPARSE = TestConfiguration(
    id=2,
    name="Sparse Long-Range",
    description="Tests distance-based decisions with sparse resources and long perception",
    grid_size=(50, 50),
    agent_count=10,
    resource_density=0.1,
    perception_radius=15,
    preference_mix="mixed",
    seed=67890
)

TEST_3_HIGH_DENSITY = TestConfiguration(
    id=3,
    name="High Density Local",
    description="Tests crowding behavior with many agents and short perception",
    grid_size=(15, 15),
    agent_count=30,
    resource_density=0.8,
    perception_radius=3,
    preference_mix="mixed",
    seed=11111
)

TEST_4_LARGE_WORLD = TestConfiguration(
    id=4,
    name="Large World Global",
    description="Tests global perception in sparse large world",
    grid_size=(60, 60),
    agent_count=15,
    resource_density=0.05,
    perception_radius=20,
    preference_mix="mixed",
    seed=22222
)

TEST_5_COBB_DOUGLAS = TestConfiguration(
    id=5,
    name="Pure Cobb-Douglas",
    description="Tests balanced utility optimization with single preference type",
    grid_size=(25, 25),
    agent_count=25,
    resource_density=0.4,
    perception_radius=6,
    preference_mix="cobb_douglas",
    seed=44444
)

TEST_6_LEONTIEF = TestConfiguration(
    id=6,
    name="Pure Leontief",
    description="Tests complementary resource behavior with Leontief preferences",
    grid_size=(25, 25),
    agent_count=25,
    resource_density=0.4,
    perception_radius=6,
    preference_mix="leontief",
    seed=66666
)

TEST_7_PERFECT_SUBSTITUTES = TestConfiguration(
    id=7,
    name="Pure Perfect Substitutes",
    description="Tests interchangeable resource behavior",
    grid_size=(25, 25),
    agent_count=25,
    resource_density=0.4,
    perception_radius=6,
    preference_mix="perfect_substitutes",
    seed=88888
)

# Registry for easy access
ALL_TEST_CONFIGS = {
    1: TEST_1_BASELINE,
    2: TEST_2_SPARSE,
    3: TEST_3_HIGH_DENSITY,
    4: TEST_4_LARGE_WORLD,
    5: TEST_5_COBB_DOUGLAS,
    6: TEST_6_LEONTIEF,
    7: TEST_7_PERFECT_SUBSTITUTES
}
```

### **3. Composable UI Components**
```python
# framework/ui_components.py
class DebugPanel(QWidget):
    """Reusable debug log display with live updating."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_update_timer()
        
    def setup_ui(self):
        """Create debug text display with proper formatting."""
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Debug Log"))
        
        self.debug_display = QTextEdit()
        self.debug_display.setReadOnly(True)
        self.debug_display.setMinimumWidth(300)
        self.debug_display.setMinimumHeight(600)
        self.debug_display.setStyleSheet(
            "QTextEdit { background:#f2f2f2; border:1px solid #ccc; padding:2px; }"
        )
        self.debug_display.setFont(QFont("Courier", 8))
        layout.addWidget(self.debug_display)
        
        self.setLayout(layout)
        self.setFixedWidth(320)
        
    def setup_update_timer(self):
        """Setup 250ms update timer for log file monitoring."""
        self.debug_timer = QTimer()
        self.debug_timer.timeout.connect(self.update_debug_log)
        self.debug_timer.start(250)
        
    def update_debug_log(self):
        """Update debug log display with latest content."""
        # Implementation from existing tests - centralized here
        pass

class ControlPanel(QWidget):
    """Standardized control panel with speed control and status display."""
    
    def __init__(self, test_config: TestConfiguration, parent=None):
        super().__init__(parent)
        self.config = test_config
        self.setup_ui()
        
    def setup_ui(self):
        """Create control panel layout."""
        layout = QVBoxLayout()
        
        # Test info
        layout.addWidget(QLabel(f"Manual Test {self.config.id}: {self.config.name}"))
        
        # Status labels
        self.turn_label = QLabel("Turn: 0")
        self.phase_label = QLabel("Phase: 1 (Both enabled)")
        self.agents_label = QLabel(f"Agents: {self.config.agent_count}")
        self.resources_label = QLabel("Resources: 0")
        
        layout.addWidget(self.turn_label)
        layout.addWidget(self.phase_label)
        layout.addWidget(self.agents_label)
        layout.addWidget(self.resources_label)
        
        # Speed control from test_utils
        from test_utils import create_speed_control
        speed_layout, self.speed_combo = create_speed_control(self, self.on_speed_changed)
        layout.addLayout(speed_layout)
        
        # Start button
        self.start_button = QPushButton("Start Test")
        layout.addWidget(self.start_button)
        
        # Status text
        self.status_text = QLabel("Ready to start")
        self.status_text.setWordWrap(True)
        layout.addWidget(self.status_text)
        
        self.setLayout(layout)
        
    def on_speed_changed(self, index):
        """Handle speed change - delegate to parent test."""
        if hasattr(self.parent(), 'on_speed_changed'):
            self.parent().on_speed_changed(index)

class TestLayout(QHBoxLayout):
    """Standard three-panel layout: debug + viewport + controls."""
    
    def __init__(self, test_config: TestConfiguration):
        super().__init__()
        self.config = test_config
        
        # Debug panel (left)
        self.debug_panel = DebugPanel()
        self.addWidget(self.debug_panel)
        
        # Pygame viewport (center) - placeholder initially
        self.pygame_placeholder = QLabel("Pygame viewport will appear here when test starts")
        self.pygame_placeholder.setFixedSize(600, 600)
        self.addWidget(self.pygame_placeholder)
        
        # Control panel (right)
        self.control_panel = ControlPanel(test_config)
        self.addWidget(self.control_panel)
        
    def replace_viewport(self, pygame_widget):
        """Replace placeholder with actual pygame widget."""
        self.replaceWidget(self.pygame_placeholder, pygame_widget)
```

### **4. Centralized Phase Management** 
```python  
# framework/phase_manager.py
from dataclasses import dataclass
from typing import Optional, List
import os

@dataclass
class PhaseDefinition:
    """Definition of a single test phase."""
    number: int
    turn_start: int
    turn_end: int
    description: str
    forage_enabled: bool
    trade_enabled: bool

@dataclass  
class PhaseTransition:
    """Result of a phase transition check."""
    new_phase: int
    description: str
    forage_enabled: bool
    trade_enabled: bool

class PhaseManager:
    """Handles phase transitions and environment configuration."""
    
    def __init__(self, phases: List[PhaseDefinition]):
        self.phases = {p.number: p for p in phases}
        
    @classmethod
    def create_standard_phases(cls) -> 'PhaseManager':
        """Create the standard 6-phase schedule used by most tests."""
        phases = [
            PhaseDefinition(1, 1, 200, "Both foraging and exchange enabled", True, True),
            PhaseDefinition(2, 201, 400, "Only foraging enabled", True, False),
            PhaseDefinition(3, 401, 600, "Only exchange enabled", False, True),
            PhaseDefinition(4, 601, 650, "Both disabled - agents should idle", False, False),
            PhaseDefinition(5, 651, 850, "Both enabled again", True, True),
            PhaseDefinition(6, 851, 900, "Final disabled phase", False, False)
        ]
        return cls(phases)
        
    def check_transition(self, current_turn: int, current_phase: int) -> Optional[PhaseTransition]:
        """Check if we need to transition to a new phase."""
        for phase_num, phase_def in self.phases.items():
            if (current_turn == phase_def.turn_start and 
                current_phase == phase_num - 1):
                
                # Configure environment variables
                os.environ['ECONSIM_FORAGE_ENABLED'] = '1' if phase_def.forage_enabled else '0'
                os.environ['ECONSIM_TRADE_DRAFT'] = '1' if phase_def.trade_enabled else '0'
                os.environ['ECONSIM_TRADE_EXEC'] = '1' if phase_def.trade_enabled else '0'
                
                # Log transition
                from econsim.gui.debug_logger import log_phase_transition, log_comprehensive
                log_phase_transition(phase_num, current_turn, phase_def.description)
                log_comprehensive(f"PHASE TRANSITION: {current_phase} -> {phase_num} at turn {current_turn}", current_turn)
                
                return PhaseTransition(
                    new_phase=phase_num,
                    description=phase_def.description,
                    forage_enabled=phase_def.forage_enabled,
                    trade_enabled=phase_def.trade_enabled
                )
        
        return None
        
    def get_phase_description(self, phase_number: int) -> str:
        """Get description for a phase number."""
        phase = self.phases.get(phase_number)
        return phase.description if phase else f"Phase {phase_number}"
        
    def is_test_complete(self, current_turn: int) -> bool:
        """Check if all phases are complete."""
        max_turn = max(p.turn_end for p in self.phases.values())
        return current_turn >= max_turn
```

### **5. Debug Output Orchestrator**
```python
# framework/debug_orchestrator.py  
import os
from typing import List, Optional

class DebugOrchestrator:
    """Centralized debug output management."""
    
    # Standard debug categories available
    STANDARD_CATEGORIES = [
        'AGENT_MODES', 'TRADES', 'SIMULATION', 
        'PHASES', 'DECISIONS', 'RESOURCES'
    ]
    
    def __init__(self, test_config: 'TestConfiguration'):
        self.test_config = test_config
        self.configure_base_logging()
        self.configure_test_specific_logging()
        
    def configure_base_logging(self):
        """Set up base debug environment variables for all tests."""
        # Enable comprehensive debug logging
        for category in self.STANDARD_CATEGORIES:
            os.environ[f'ECONSIM_DEBUG_{category}'] = '1'
            
        # Additional debug flags
        os.environ['ECONSIM_TRADE_GUI_INFO'] = '1'
        os.environ['ECONSIM_TRADE_DEBUG_OVERLAY'] = '1'
        
    def configure_test_specific_logging(self):
        """Configure debug categories specific to this test."""
        if self.test_config.debug_categories:
            for category in self.test_config.debug_categories:
                os.environ[f'ECONSIM_DEBUG_{category}'] = '1'
                
        # Test-type specific configurations
        if self.test_config.preference_mix == 'leontief':
            # Enable complementary resource tracking for Leontief tests
            os.environ['ECONSIM_DEBUG_COMPLEMENTARY'] = '1'
            
        elif self.test_config.preference_mix == 'perfect_substitutes':
            # Enable substitution pattern tracking
            os.environ['ECONSIM_DEBUG_SUBSTITUTION'] = '1'
            
    def get_available_categories(self) -> List[str]:
        """Return all available debug categories."""
        return self.STANDARD_CATEGORIES.copy()
        
    def customize_logging(self, categories: List[str]):
        """Allow runtime customization of debug categories."""
        # Disable all first
        for category in self.STANDARD_CATEGORIES:
            os.environ[f'ECONSIM_DEBUG_{category}'] = '0'
            
        # Enable selected
        for category in categories:
            if category in self.STANDARD_CATEGORIES:
                os.environ[f'ECONSIM_DEBUG_{category}'] = '1'
```

### **6. Simulation Factory**
```python
# framework/simulation_factory.py
import random
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation

class SimulationFactory:
    """Standardized simulation creation from test configurations."""
    
    @staticmethod
    def create_simulation(test_config: 'TestConfiguration') -> Simulation:
        """Create simulation from test configuration."""
        
        # Generate resources using test-specific seed
        resources = SimulationFactory._generate_resources(test_config)
        
        # Generate agent positions
        agent_positions = SimulationFactory._generate_agent_positions(test_config)
        
        # Create preference factory
        preference_factory = SimulationFactory._create_preference_factory(test_config)
        
        # Build simulation config
        sim_config = SimConfig(
            grid_size=test_config.grid_size,
            initial_resources=resources,
            seed=test_config.seed,
            enable_respawn=True,
            enable_metrics=True,
            perception_radius=test_config.perception_radius,
            respawn_target_density=test_config.resource_density,
            respawn_rate=0.25,
            distance_scaling_factor=0.0,
            viewport_size=test_config.viewport_size
        )
        
        # Create and return simulation
        return Simulation.from_config(sim_config, preference_factory, agent_positions=agent_positions)
        
    @staticmethod
    def _generate_resources(test_config: 'TestConfiguration') -> list:
        """Generate resources based on test configuration."""
        grid_w, grid_h = test_config.grid_size
        resource_count = int(grid_w * grid_h * test_config.resource_density)
        
        resource_rng = random.Random(test_config.seed)
        resources = []
        for _ in range(resource_count):
            x = resource_rng.randint(0, grid_w - 1)
            y = resource_rng.randint(0, grid_h - 1)
            resource_type = resource_rng.choice(['A', 'B'])
            resources.append((x, y, resource_type))
            
        return resources
        
    @staticmethod
    def _generate_agent_positions(test_config: 'TestConfiguration') -> list:
        """Generate non-overlapping agent positions."""
        grid_w, grid_h = test_config.grid_size
        pos_rng = random.Random(test_config.seed + 9999)  # Offset seed for positions
        
        positions = set()
        while len(positions) < test_config.agent_count:
            x = pos_rng.randint(0, grid_w - 1)
            y = pos_rng.randint(0, grid_h - 1)
            positions.add((x, y))
            
        return list(positions)
        
    @staticmethod  
    def _create_preference_factory(test_config: 'TestConfiguration'):
        """Create preference factory based on test configuration."""
        if test_config.preference_mix == "mixed":
            preferences = ['cobb_douglas', 'leontief', 'perfect_substitutes']
            pref_rng = random.Random(test_config.seed + 7777)
            
            def preference_factory(idx: int):
                pref_type = pref_rng.choice(preferences)
                if pref_type == 'cobb_douglas':
                    from econsim.preferences.cobb_douglas import CobbDouglasPreference
                    return CobbDouglasPreference(alpha=0.5)
                elif pref_type == 'leontief':
                    from econsim.preferences.leontief import LeontiefPreference
                    return LeontiefPreference(a=1.0, b=1.0)
                else:
                    from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference
                    return PerfectSubstitutesPreference(a=1.0, b=1.0)
                    
        elif test_config.preference_mix == "cobb_douglas":
            from econsim.preferences.cobb_douglas import CobbDouglasPreference
            preference_factory = lambda idx: CobbDouglasPreference(alpha=0.5)
            
        elif test_config.preference_mix == "leontief":
            from econsim.preferences.leontief import LeontiefPreference
            preference_factory = lambda idx: LeontiefPreference(a=1.0, b=1.0)
            
        elif test_config.preference_mix == "perfect_substitutes":
            from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference
            preference_factory = lambda idx: PerfectSubstitutesPreference(a=1.0, b=1.0)
            
        else:
            raise ValueError(f"Unknown preference mix: {test_config.preference_mix}")
            
        return preference_factory
```

## 📁 **Proposed File Structure**
```
MANUAL_TESTS/
├── framework/
│   ├── __init__.py
│   ├── base_test.py          # BaseManualTest, StandardPhaseTest  
│   ├── test_configs.py       # TestConfiguration, all test definitions
│   ├── phase_manager.py      # PhaseManager, PhaseDefinition
│   ├── ui_components.py      # DebugPanel, ControlPanel, TestLayout
│   ├── debug_orchestrator.py # Centralized debug management
│   └── simulation_factory.py # Standardized simulation creation
├── tests/
│   ├── test_1_baseline.py           # ~50 lines vs current 400+
│   ├── test_2_sparse.py             # ~50 lines  
│   ├── test_3_highdensity.py        # ~50 lines
│   ├── test_4_largeworld.py         # ~50 lines
│   ├── test_5_pure_cobbdouglas.py   # ~50 lines
│   ├── test_6_pure_leontief.py      # ~50 lines
│   └── test_7_pure_perfectsubs.py   # ~50 lines
├── launch_tests.py           # Updated to use framework
├── test_start_menu.py        # Updated to use configurations
└── README.md                 # Updated documentation
```

## 🎯 **Implementation Strategy**

### **Phase 1: Framework Foundation (High Impact)**
1. Create `BaseManualTest` class with common UI patterns
2. Build `TestConfiguration` dataclass with all current test specs  
3. Implement `DebugPanel` component with centralized log integration
4. Create `PhaseManager` with standardized 6-phase logic

### **Phase 2: Test Migration (Incremental)**
1. Migrate Test 1 to new framework (prove concept)
2. Migrate Tests 2-4 (validate framework flexibility)
3. Migrate Tests 5-7 (preference-specific tests)
4. Update test start menu to use configurations

### **Phase 3: Enhancement Features (Easy Additions)**
1. Add debug category filtering per test
2. Implement custom phase schedule support  
3. Add test result export/comparison tools
4. Create test template generator for new tests

## 💡 **Key Benefits After Refactor**

### **For Adding New Tests:**
```python
# NEW TEST - Just configuration + minimal class!
TEST_8_CONFIG = TestConfiguration(
    id=8,
    name="Ultra High Density",
    description="Extreme crowding with 200 agents in 20x20 grid",
    grid_size=(20, 20), 
    agent_count=200,
    resource_density=0.9,
    perception_radius=2,
    preference_mix="mixed",
    seed=98765
)

class Test8Window(StandardPhaseTest):
    """Ultra high density test - that's all the code needed!"""
    def __init__(self):
        super().__init__(TEST_8_CONFIG)
        
    # Optional: Override only if custom behavior needed
    # def get_custom_debug_categories(self):
    #     return super().get_custom_debug_categories() + ['CROWDING_ANALYSIS']

# Main function
def main():
    app = QApplication(sys.argv)
    test_window = Test8Window()
    test_window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
```

### **For Changing Debug Outputs:**
```python
# CENTRALIZED - Change once, affects all tests
class DebugOrchestrator:
    STANDARD_CATEGORIES = [
        'AGENT_MODES', 'TRADES', 'SIMULATION', 'PHASES', 
        'DECISIONS', 'RESOURCES', 'NEW_CATEGORY'  # Add here
    ]
    
    def configure_base_logging(self):
        # New category automatically available to all tests
        for category in self.STANDARD_CATEGORIES:
            os.environ[f'ECONSIM_DEBUG_{category}'] = '1'
```

### **For Custom Behavior:**
```python
# EXTENSIBLE - Override specific methods when needed
class Test6Window(StandardPhaseTest):
    """Leontief test with complementary resource tracking."""
    
    def __init__(self):
        super().__init__(TEST_6_LEONTIEF)
        
    def get_custom_debug_categories(self):
        """Add Leontief-specific debug categories."""
        return super().get_custom_debug_categories() + ['COMPLEMENTARY_TRACKING']
        
    def get_phase_specific_behavior(self, phase_num: int):
        """Custom behavior for Leontief agents during specific phases."""
        if phase_num == 3:  # Exchange-only phase
            return "Watch for complementary resource balancing trades"
        return super().get_phase_specific_behavior(phase_num)
```

## 🔧 **Migration Complexity Assessment**

- **Low Risk**: UI components, debug panels (pure extraction)
- **Medium Risk**: Phase management (logic centralization)  
- **High Impact**: Test configurations (eliminates most duplication)
- **Validation**: All existing tests must produce identical behavior

## 📊 **Expected Impact**

### **Code Reduction**
- **Before**: ~3000 lines across 7 test files
- **After**: ~800 lines (framework + streamlined tests)
- **Maintenance**: Single location for common changes

### **Developer Experience**  
- **New Test**: 30 lines vs 400 lines
- **Debug Changes**: 1 location vs 7 locations
- **UI Updates**: Component-based vs copy/paste

### **Testing & Validation**
- **Behavior**: Identical simulation behavior guaranteed
- **Performance**: No performance impact (same underlying code)
- **Compatibility**: Fully backward compatible with existing workflows

This refactor would transform the manual test suite from a maintenance burden into a flexible, extensible framework that makes educational enhancements and new test creation trivial.