# VMT Programmatic API Usage Guide

**Updated**: September 28, 2025  
**Phase**: 6 Implementation Complete

## Quick Start

### Basic Usage

```python
from econsim.tools.launcher.test_runner import create_test_runner

# Create test runner instance
runner = create_test_runner()  # ~0.004s initialization

# Launch test by ID
runner.run_by_id(1, "framework")  # Test 1: Baseline Unified Target Selection

# Check available tests
tests = runner.get_available_tests()
print(f"Available tests: {list(tests.keys())}")
# Output: Available tests: [1, 2, 3, 4, 5, 6, 7]
```

### Status Monitoring

```python
# Get current status
status = runner.get_status()
print(f"Tests available: {status['available_tests']}")
print(f"Framework ready: {status['framework_available']}")

# Comprehensive health check
health = runner.get_health_check()
if health['overall_healthy']:
    print("✅ All systems operational")
else:
    print("⚠️ Issues detected:")
    for issue in health['issues']:
        print(f"  - {issue}")
```

## TestRunner API Reference

### Core Methods

#### `create_test_runner() -> TestRunner`
Factory function for TestRunner instantiation.

**Returns**: Initialized TestRunner instance  
**Raises**: `RuntimeError` if framework unavailable  
**Performance**: ~0.004s average initialization

#### `run_by_id(test_id: int, mode: str = "framework") -> None`
Execute test by configuration ID.

**Parameters**:
- `test_id`: Test configuration ID (1-7)
- `mode`: Execution mode ("framework" only currently supported)

**Raises**:
- `ValueError`: Invalid test ID or unsupported mode
- `RuntimeError`: Framework execution failure

**Example**:
```python
runner.run_by_id(3, "framework")  # High Density Local test
```

#### `get_status() -> Dict[str, Any]`
Get current runner status and capabilities.

**Returns**:
```python
{
    "available_tests": int,        # Number of loaded test configs
    "current_test": bool,          # Active test window exists
    "framework_available": bool,   # Framework components importable
    "last_error": str | None,     # Most recent error message
    "qt_available": bool,         # PyQt6 availability
    "test_configs_loaded": bool   # Registry successfully loaded
}
```

#### `get_health_check() -> Dict[str, Any]`
Comprehensive component health validation.

**Returns**:
```python
{
    "overall_healthy": bool,       # Aggregate health status
    "components": {               # Individual component states
        "qt": bool,
        "test_configs": bool,
        "framework": bool,
        "active_test": bool,
        "error_state": bool
    },
    "issues": List[str]           # Actionable problem descriptions
}
```

#### `get_available_tests() -> Dict[int, str]`
Get mapping of test IDs to configuration names.

**Returns**: `{1: "Baseline Unified Target Selection", 2: "Sparse Long-Range", ...}`

#### `close_current_test() -> bool`
Close currently active test window if exists.

**Returns**: `True` if window was closed, `False` if no active window

### Advanced Usage

#### Error Handling Pattern

```python
from econsim.tools.launcher.test_runner import create_test_runner

try:
    runner = create_test_runner()
    runner.run_by_id(test_id, "framework")
    
    # Success logging
    print(f"✅ Test {test_id} launched successfully")
    
except ValueError as e:
    print(f"❌ Configuration error: {e}")
    
except RuntimeError as e:
    print(f"❌ Execution failure: {e}")
    # Could implement subprocess fallback here
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
```

#### Health Monitoring Integration

```python
def monitor_runner_health(runner):
    """Continuous health monitoring for robust applications."""
    health = runner.get_health_check()
    
    if not health['overall_healthy']:
        print("⚠️ TestRunner health issues detected:")
        
        for issue in health['issues']:
            print(f"  🔸 {issue}")
            
            # Automated responses
            if "PyQt6 not available" in issue:
                print("    → Consider subprocess fallback")
            elif "No test configurations" in issue:
                print("    → Check framework registry loading")
            elif "Recent error" in issue:
                print("    → Review launcher logs for details")
    
    return health['overall_healthy']
```

#### Batch Test Execution

```python
def run_test_sequence(test_ids, runner=None):
    """Execute multiple tests in sequence."""
    if runner is None:
        runner = create_test_runner()
    
    results = []
    
    for test_id in test_ids:
        try:
            print(f"🚀 Launching test {test_id}...")
            runner.run_by_id(test_id, "framework")
            results.append((test_id, "SUCCESS"))
            
            # Optional: Wait for user interaction or automated validation
            input(f"Press Enter when test {test_id} complete...")
            runner.close_current_test()
            
        except Exception as e:
            results.append((test_id, f"FAILED: {e}"))
    
    return results

# Usage
test_sequence = [1, 3, 5, 7]  # Baseline, High Density, Cobb-Douglas, Perfect Substitutes
results = run_test_sequence(test_sequence)
```

## Integration Patterns

### GUI Application Integration

```python
from PyQt6.QtWidgets import QMainWindow, QPushButton
from econsim.tools.launcher.test_runner import create_test_runner

class VMTTestController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.runner = create_test_runner()
        self.setup_ui()
    
    def setup_ui(self):
        # Create test buttons dynamically from available tests
        available_tests = self.runner.get_available_tests()
        
        for test_id, test_name in available_tests.items():
            button = QPushButton(f"Test {test_id}: {test_name}")
            button.clicked.connect(lambda checked, tid=test_id: self.launch_test(tid))
            # Add button to layout...
    
    def launch_test(self, test_id):
        try:
            self.runner.run_by_id(test_id, "framework")
            self.update_status(f"✅ Test {test_id} launched")
        except Exception as e:
            self.update_status(f"❌ Launch failed: {e}")
```

### Automated Testing Integration

```python
import pytest
from econsim.tools.launcher.test_runner import create_test_runner

class TestVMTSuite:
    @pytest.fixture
    def runner(self):
        """Provide TestRunner instance for tests."""
        return create_test_runner()
    
    @pytest.mark.parametrize("test_id", [1, 2, 3, 4, 5, 6, 7])
    def test_all_configurations_launch(self, runner, test_id):
        """Validate all test configurations launch successfully."""
        # This would need adaptation for non-interactive testing
        assert runner._get_config_by_id(test_id) is not None
    
    def test_runner_health(self, runner):
        """Validate TestRunner health status."""
        health = runner.get_health_check()
        assert health['overall_healthy'] is True
        assert len(health['issues']) == 0
```

### Configuration Validation

```python
def validate_test_environment():
    """Validate TestRunner environment before critical operations."""
    try:
        runner = create_test_runner()
        
        # Check basic functionality
        status = runner.get_status()
        required_tests = 7
        
        if status['available_tests'] < required_tests:
            raise RuntimeError(f"Only {status['available_tests']}/{required_tests} tests available")
        
        if not status['framework_available']:
            raise RuntimeError("Framework components not available")
        
        # Health validation
        health = runner.get_health_check()
        if not health['overall_healthy']:
            issues = ", ".join(health['issues'])
            raise RuntimeError(f"Health check failed: {issues}")
        
        print("✅ Test environment validated successfully")
        return runner
        
    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        raise
```

## Best Practices

### Performance Optimization

1. **Reuse TestRunner instances** - Initialization cost is minimal but can be amortized
2. **Monitor memory usage** - Runner is stateless but test windows consume resources  
3. **Close test windows** - Use `close_current_test()` for cleanup
4. **Batch operations** - Group multiple test launches for efficiency

### Error Handling

1. **Check health status** before critical operations
2. **Implement fallback strategies** for robustness
3. **Use comprehensive logging** for debugging
4. **Validate configurations** before execution

### Integration Guidelines

1. **Factory pattern usage** - Always use `create_test_runner()` for instantiation
2. **Status monitoring** - Implement health checks for production applications
3. **Exception handling** - Handle both `ValueError` (config) and `RuntimeError` (execution)
4. **Resource cleanup** - Properly close test windows when done

## Common Patterns

### Robust Test Launcher

```python
def robust_test_launch(test_id, max_retries=2):
    """Robust test launching with retry logic."""
    for attempt in range(max_retries + 1):
        try:
            runner = create_test_runner()
            
            # Validate health before launch
            if not monitor_runner_health(runner):
                raise RuntimeError("Health check failed")
            
            # Attempt launch
            runner.run_by_id(test_id, "framework")
            return runner
            
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries:
                print(f"🔄 Retrying... ({max_retries - attempt} attempts remaining)")
            else:
                print("💥 All retry attempts exhausted")
                raise
```

### Dynamic Test Discovery

```python
def discover_and_launch_tests(filter_func=None):
    """Discover available tests and launch based on criteria."""
    runner = create_test_runner()
    available_tests = runner.get_available_tests()
    
    # Apply filter if provided
    if filter_func:
        filtered_tests = {k: v for k, v in available_tests.items() if filter_func(k, v)}
    else:
        filtered_tests = available_tests
    
    print(f"Discovered {len(filtered_tests)} tests:")
    for test_id, test_name in filtered_tests.items():
        print(f"  {test_id}: {test_name}")
    
    return filtered_tests

# Usage examples
preference_tests = discover_and_launch_tests(
    lambda id, name: "Cobb-Douglas" in name or "Leontief" in name
)

density_tests = discover_and_launch_tests(
    lambda id, name: "Density" in name or "Sparse" in name  
)
```

## Troubleshooting

### Common Issues

1. **"No test configurations available"**
   - Check framework registry loading
   - Verify `ALL_TEST_CONFIGS` import path
   - Review module import errors

2. **"PyQt6 not available"**
   - Install PyQt6: `pip install PyQt6`
   - Check virtual environment activation
   - Consider subprocess fallback

3. **"Framework components not importable"**
   - Verify framework module paths
   - Check for circular import issues
   - Review Python path configuration

### Debugging Tools

```python
# Debug runner state
runner = create_test_runner()
print("Status:", runner.get_status())
print("Health:", runner.get_health_check())
print("Available:", runner.get_available_tests())

# Check specific configuration
config = runner._get_config_by_id(1)
print(f"Config 1: {config.name if config else 'Not found'}")
```

### Logging Integration

The TestRunner integrates with the launcher logging system. Check `launcher_logs/` directory for detailed execution logs including:

- TestRunner initialization events
- Test execution start/success/failure
- Health check results and issues  
- Error messages with full tracebacks

---

**For architecture details and advanced integration patterns, see the Launcher Architecture Documentation.**