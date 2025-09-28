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
- Bookmark manager for favorite configurations
- Custom test creation and management

### Alternative Interfaces

```bash
# Batch test runner (sequential execution)
make batch-tests

# Bookmark manager (organize configurations) 
make bookmarks

# Basic GUI with start menu
make manual-tests
```

## Main Tools

### Enhanced Test Launcher (`enhanced_test_launcher_v2.py`)
The primary interface providing:
- **Test Gallery**: Visual cards for all 7 test scenarios
- **Comparison Mode**: Launch original or framework versions
- **Live Editor**: Real-time configuration modification
- **Integration**: Direct access to batch runner and bookmarks

### Batch Test Runner (`batch_test_runner.py`)
Professional sequential test execution with:
- Progress tracking and time estimates
- Configurable delays between tests
- Comprehensive logging and results summary

### Bookmark Manager (`test_bookmarks.py`)
Organize and quick-launch favorite configurations:
- Save test configurations with custom names
- Categorize bookmarks with tags
- Search and filter bookmark collections
- Direct launch from bookmark list

### Live Config Editor (`live_config_editor.py`)
Real-time configuration modification:
- Interactive parameter adjustment
- Live preview of changes
- Save custom configurations
- Export to standalone test files

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

```
MANUAL_TESTS/
├── README.md                    # Basic usage guide
├── LAUNCHER_GUIDE.md           # This comprehensive guide
├── enhanced_test_launcher_v2.py # Main launcher
├── batch_test_runner.py        # Batch execution
├── test_bookmarks.py           # Bookmark manager
├── live_config_editor.py       # Config editor  
├── phase_config_editor.py      # Phase editor
├── test_start_menu.py          # Basic GUI
├── test_utils.py               # Shared utilities
├── test_1.py ... test_7.py     # Core scenarios
├── config_presets.json         # User presets
├── custom_tests/               # User custom tests
└── examples/                   # Optional examples
    ├── example_custom_phases.py
    ├── phase_examples_demo.py
    ├── test_custom_phases.py
    ├── test_framework_validation.py
    └── test_improved_phases.py
```

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