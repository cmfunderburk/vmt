# VMT Launcher Architecture Documentation

**Updated**: September 28, 2025  
**Phase**: 6 - Programmatic Runner Implementation Complete

## Overview

The VMT Enhanced Test Launcher provides programmatic test execution for educational microeconomic simulations, replacing subprocess-based launching with direct framework instantiation for improved performance, reliability, and maintainability.

## Architecture Components

### Core Components

#### 1. TestRunner (`src/econsim/tools/launcher/test_runner.py`)
**Primary programmatic execution engine**

```python
from econsim.tools.launcher.test_runner import create_test_runner

# Instant test execution
runner = create_test_runner()  # ~0.004s initialization
runner.run_by_id(1, "framework")  # Launch test directly
```

**Key Features:**
- **Registry-based configuration**: Uses `ALL_TEST_CONFIGS` instead of hardcoded mappings
- **Direct framework instantiation**: No subprocess overhead
- **Comprehensive status monitoring**: Real-time health checks and error tracking
- **Factory pattern**: Simple `create_test_runner()` instantiation

**API Methods:**
- `run_by_id(test_id, mode)`: Execute test by configuration ID
- `get_status()`: Current runner state and test availability  
- `get_health_check()`: Comprehensive component health validation
- `get_available_tests()`: Available test configurations mapping

#### 2. Launcher Logger (`src/econsim/tools/launcher/launcher_logger.py`)
**Independent logging system for launcher events**

**Features:**
- **Separate from simulation logs**: Independent `launcher_logs/` directory
- **Immediate file creation**: No deferred logging, instant persistence
- **Comprehensive event tracking**: TestRunner init, test execution, GUI events
- **Dual output**: Console + file logging for immediate feedback

**Directory Structure:**
```
launcher_logs/
├── 2025-09-28 16-17-18 Launcher.log
├── 2025-09-28 15-57-38 Launcher.log
└── ...
```

#### 3. GUI Integration (`src/econsim/tools/launcher/app_window.py`)
**Enhanced launcher window with programmatic execution**

**Key Enhancements:**
- **TestRunner integration**: Seamless programmatic test launching
- **Real-time status display**: Dynamic test count and framework health indicators
- **Color-coded health states**: Green (healthy), Yellow (warning), Red (error)
- **Enhanced error handling**: Comprehensive fallback with PID tracking
- **Launcher logging**: All GUI events tracked independently

## Execution Flow

### Primary Execution Path (Programmatic)

```mermaid
graph TD
    A[User Clicks Test] --> B[_launch_test()]
    B --> C[TestRunner.run_by_id()]
    C --> D[Registry Lookup]
    D --> E[StandardPhaseTest Framework]
    E --> F[Direct GUI Window Creation]
    F --> G[Simulation Started]
    
    B --> H[Launcher Logging]
    H --> I[Status Updates]
    I --> J[Health Monitoring]
```

### Fallback Execution Path (Subprocess)

```mermaid
graph TD
    A[Programmatic Failure] --> B[_launch_test_subprocess_fallback()]
    B --> C[Hardcoded File Mapping]
    C --> D[subprocess.Popen()]
    D --> E[PID Tracking]
    E --> F[Enhanced Error Logging]
```

## Configuration Registry System

### TestConfiguration Registry
**Location**: `src/econsim/tools/launcher/framework/test_configs.py`

```python
# Registry-based approach (NEW)
from econsim.tools.launcher.framework.test_configs import ALL_TEST_CONFIGS

# Automatic configuration discovery
config = next((c for c in ALL_TEST_CONFIGS if c.id == test_id), None)

# vs. Old hardcoded approach (ELIMINATED)
id_to_file = {1: "test_1.py", 2: "test_2.py", ...}  # ❌ Removed
```

**Benefits:**
- **Dynamic configuration**: Test configs loaded from framework registry
- **Extensible**: New tests automatically available via registry
- **Type-safe**: TestConfiguration objects with proper validation
- **Maintainable**: Single source of truth for test metadata

### Available Test Configurations

| ID | Name | Description |
|----|------|-------------|
| 1 | Baseline Unified Target Selection | Standard decision-making behavior |
| 2 | Sparse Long-Range | Low density, long-distance interactions |
| 3 | High Density Local | Dense grid, local interactions |
| 4 | Large World Global | Expansive simulation space |
| 5 | Pure Cobb-Douglas | Single preference type testing |
| 6 | Pure Leontief | Complementary goods preferences |
| 7 | Pure Perfect Substitutes | Interchangeable goods preferences |

## Status Monitoring System

### Health Check Components

The `get_health_check()` API monitors 5 critical components:

1. **PyQt6 Availability**: GUI framework status
2. **Test Configurations**: Registry loading and count validation
3. **Framework Components**: Import capability and integration
4. **Active Test State**: Current test window tracking
5. **Error State**: Recent error capture and reporting

### Status API Structure

```python
# get_status() returns:
{
    "available_tests": 7,           # Total configurations loaded
    "current_test": False,          # Active test window status
    "framework_available": True,    # Framework import success
    "last_error": None,            # Recent error message
    "qt_available": True,          # PyQt6 availability
    "test_configs_loaded": True    # Registry loading success
}

# get_health_check() returns:
{
    "overall_healthy": True,        # Aggregate health status
    "components": {...},           # Individual component states
    "issues": []                   # List of actionable problems
}
```

## Performance Characteristics

### Launch Time Performance
- **Programmatic initialization**: ~0.004s average
- **Subprocess overhead eliminated**: Direct framework instantiation
- **Memory stable**: Stateless runner design prevents accumulation

### Resource Usage
- **Low memory footprint**: No subprocess creation overhead
- **Fast test switching**: Instant configuration lookup
- **Scalable architecture**: Supports batch execution and automation

## Error Handling & Recovery

### Error Recovery Strategy
1. **Programmatic execution** (primary path)
2. **Comprehensive error logging** with launcher logger
3. **Automatic subprocess fallback** with enhanced error handling
4. **PID tracking** for subprocess monitoring
5. **Health status updates** with actionable issue reporting

### Common Error Scenarios

| Error Type | Programmatic Response | Fallback Action |
|------------|----------------------|-----------------|
| Config not found | `ValueError` with clear message | N/A (registry issue) |
| Framework import failure | Health check reports issue | Subprocess fallback |
| GUI creation failure | Exception logged + fallback | Enhanced subprocess launch |
| Unknown test ID | User feedback + logging | Fallback with error tracking |

## Integration Points

### Framework Dependencies
- **TestConfiguration Registry**: `framework/test_configs.py`
- **Simulation Factory**: `framework/simulation_factory.py` 
- **StandardPhaseTest**: `framework/base_test.py`
- **GUI Integration**: `gui/embedded_pygame.py`

### Backward Compatibility
- **Subprocess fallback preserved** for reliability
- **Original test files maintained** in `MANUAL_TESTS/`
- **GUI interface unchanged** for users
- **Enhanced error handling** improves user experience

## Development Guidelines

### Adding New Tests
1. **Create TestConfiguration** in framework registry
2. **Test appears automatically** in launcher (no hardcoded mapping)
3. **Programmatic execution** handles GUI creation
4. **Fallback support** via MANUAL_TESTS file (optional)

### Debugging Test Issues
1. **Check launcher logs** (`launcher_logs/` directory)
2. **Monitor health status** via GUI indicators  
3. **Use status API** for programmatic debugging
4. **Review error messages** in comprehensive logging

### Performance Optimization
- **Registry caching**: Configurations loaded once at startup
- **Stateless runner**: No memory accumulation across launches
- **Direct instantiation**: Eliminates subprocess overhead
- **Health monitoring**: Proactive issue detection

## Future Architecture Enhancements

### Enabled Capabilities
- **Automated test sequences**: Batch execution via programmatic API
- **Parameter sweeping**: Dynamic configuration modification
- **External framework integration**: CI/CD pipeline support
- **Advanced logging**: Structured data for analytics

### Potential Extensions
- **Remote test execution**: Network-based launcher capabilities
- **Configuration hot-reloading**: Dynamic test registry updates
- **Performance profiling**: Built-in execution metrics
- **Test result aggregation**: Automated reporting systems

---

**For implementation details and troubleshooting, see the companion API Usage Guide and Troubleshooting Documentation.**