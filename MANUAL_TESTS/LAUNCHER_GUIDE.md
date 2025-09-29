# VMT Launcher Guide

This directory contains the enhanced VMT test launcher and associated tools for educational simulation testing.

## Quick Start

### Primary Launcher Interface
```bash
# From project root
make launcher
```

This launches the comprehensive VMT Enhanced Test Launcher with:
- Visual test gallery with 7 educational scenarios
- Side-by-side original vs framework comparison
- Live configuration editor
- Batch test runner integration
- Custom test creation and management

### Standalone Widget Access

Individual widgets can be run standalone for focused workflows:

```bash
# Config editor (create and modify test configurations)
python MANUAL_TESTS/live_config_editor.py

# Batch runner (sequential test execution)
python MANUAL_TESTS/batch_test_runner.py
```

## Main Tools

### Enhanced Test Launcher (New Modular Architecture)
Located at `src/econsim/tools/launcher/app_window.py`, providing:
- **Test Gallery**: Visual cards for all 7 test scenarios
- **Comparison Mode**: Launch original or framework versions
- **Config Editor Tab**: Real-time configuration modification
- **Batch Runner Tab**: Sequential test execution
- **Custom Tests Tab**: User-generated test management

### Reusable Widgets (`src/econsim/tools/widgets/`)
GUI components available as both standalone apps and integrated tabs:

**Config Editor** (`widgets/config_editor.py`)
- Interactive parameter adjustment with live validation
- Configuration presets and templates
- Custom test generation and export
- Phase configuration support
- *Standalone wrapper*: `MANUAL_TESTS/live_config_editor.py`

**Batch Runner** (`widgets/batch_runner.py`)
- Professional sequential test execution
- Progress tracking and time estimates
- Pause/Resume capabilities
- Detailed execution logs and results
- *Standalone wrapper*: `MANUAL_TESTS/batch_test_runner.py`

### Phase Config Editor (`phase_config_editor.py`)
GUI dialog for creating custom phase schedules:
- Configure phase behavior (forage, exchange, both, or idle)
- Set phase durations
- Define phase sequences
- *Note*: Will be migrated to `src/econsim/tools/widgets/dialogs/` in future refactoring

## Test Scenarios

### Core Test Suite (`test_1.py` through `test_7.py`)
Educational scenarios validating unified target selection:

1. **Baseline Dense**: High-density resource distribution
2. **Sparse Long-Range**: Sparse resources, long perception
3. **High-Density Local**: Dense resources, short perception  
4. **Multi-Type Interaction**: Mixed A/B resource types
5. **Mixed Density**: Varied resource clustering
6. **Agent Interaction**: Focus on bilateral exchange
7. **Comprehensive**: Full feature integration

Each test runs 900 turns with phase transitions testing different behavioral modes.

## Configuration Management

### Presets (`config_presets.json`)
Saved configuration presets for quick access:
- Standard educational scenarios
- Research configurations
- Performance testing setups
- Custom user configurations

### Custom Tests (`custom_tests/`)
User-created test scenarios:
- Generated from live config editor
- Custom phase configurations
- Experimental setups
- Student projects

## Advanced Usage

### Environment Variables
Control logging and behavior:
```bash
ECONSIM_LOG_LEVEL=EVENTS       # QUIET, EVENTS, VERBOSE
ECONSIM_LOG_FORMAT=COMPACT     # COMPACT, STRUCTURED  
ECONSIM_DEBUG_AGENT_MODES=1    # Enable agent mode logging
ECONSIM_DEBUG_TRADES=1         # Enable trade logging
ECONSIM_DEBUG_ECONOMICS=1      # Enable economics logging
ECONSIM_LOG_BUNDLE_TRADES=1    # Bundle trade+utility logging
```

### Development Mode
For launcher development and debugging:
```bash
ECONSIM_DEV_MODE=1 make launcher
```

### Performance Testing
Integration with performance validation:
```bash
make perf  # Runs synthetic + widget performance tests
```

## File Organization

### Current Structure (Post-Refactoring)

```
MANUAL_TESTS/                         # Educational test files
├── README.md                         # Basic usage guide
├── LAUNCHER_GUIDE.md                 # This comprehensive guide
├── live_config_editor.py             # Wrapper → src/econsim/tools/widgets/config_editor.py
├── batch_test_runner.py              # Wrapper → src/econsim/tools/widgets/batch_runner.py
├── phase_config_editor.py            # Phase editor dialog (TODO: migrate to widgets/dialogs/)
├── test_1.py ... test_7.py           # Core educational scenarios
├── config_presets.json               # Configuration presets
├── custom_tests/                     # User-generated custom tests
└── examples/                         # Phase configuration examples
    ├── example_custom_phases.py
    ├── phase_examples_demo.py
    ├── test_custom_phases.py
    ├── test_framework_validation.py
    └── test_improved_phases.py

src/econsim/tools/                    # Production tool modules
├── launcher/                         # Main launcher application
│   ├── app_window.py                # Enhanced Test Launcher window
│   ├── tabs/                        # Tab components
│   ├── framework/                   # Test framework
│   └── ...
└── widgets/                          # Reusable GUI widgets
    ├── __init__.py
    ├── config_editor.py             # Configuration editor widget
    └── batch_runner.py              # Batch test runner widget
```

### Architecture Notes

The widgets have been properly migrated to `src/econsim/tools/widgets/` for:
- ✅ Proper architectural separation (tools vs tests)
- ✅ Clean imports without path manipulation
- ✅ Reusability across different applications
- ✅ Maintainability with single source of truth

Compatibility wrappers in `MANUAL_TESTS/` allow standalone execution and preserve existing workflows.

## Educational Context

The launcher is designed for educational use, demonstrating:
- **Spatial Resource Allocation**: Agent movement and resource collection
- **Economic Decision Making**: Utility maximization and trade behavior
- **System Dynamics**: Emergent behavior from simple rules
- **Parameter Sensitivity**: How configuration changes affect outcomes

Each test scenario highlights different aspects of the economic simulation, making complex concepts observable through visual interaction.

## Integration with Main Codebase

The launcher leverages the modular architecture in `src/econsim/tools/launcher/`:
- Clean separation of UI components and business logic
- Standardized configuration management  
- Consistent logging and debugging infrastructure
- Performance monitoring and validation

This provides a professional interface while maintaining educational accessibility and development flexibility.