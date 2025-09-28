# VMT Launcher Troubleshooting Guide

**Updated**: September 28, 2025  
**Phase**: 6 Programmatic Runner Implementation

## Quick Diagnostics

### Health Check Command
```bash
cd /home/chris/PROJECTS/vmt
source vmt-dev/bin/activate
python -c "
from src.econsim.tools.launcher.test_runner import create_test_runner
runner = create_test_runner()
health = runner.get_health_check()
print('Overall Health:', '✅ HEALTHY' if health['overall_healthy'] else '❌ ISSUES')
for component, status in health['components'].items():
    print(f'  {component}: {\"✅\" if status else \"❌\"}')
if health['issues']:
    print('Issues:')
    for issue in health['issues']:
        print(f'  - {issue}')
"
```

### Status Overview
```bash
python -c "
from src.econsim.tools.launcher.test_runner import create_test_runner
runner = create_test_runner()
status = runner.get_status()
print(f'Available Tests: {status[\"available_tests\"]}')
print(f'Framework Available: {status[\"framework_available\"]}')
print(f'Qt Available: {status[\"qt_available\"]}')
print(f'Last Error: {status[\"last_error\"] or \"None\"}')"
```

## Common Issues & Solutions

### 1. TestRunner Initialization Failures

#### Issue: "No test configurations available"
**Symptoms**: TestRunner fails to initialize, empty registry  
**Root Cause**: Framework registry not loading properly

**Diagnosis**:
```bash
python -c "
from src.econsim.tools.launcher.framework.test_configs import ALL_TEST_CONFIGS
print(f'Registry loaded: {len(ALL_TEST_CONFIGS)} configs')
if ALL_TEST_CONFIGS:
    for config in ALL_TEST_CONFIGS:
        print(f'  {config.id}: {config.name}')
else:
    print('❌ Registry is empty - check framework imports')
"
```

**Solutions**:
1. **Check framework module paths**:
   ```bash
   python -c "import src.econsim.tools.launcher.framework.test_configs as tc; print('Import successful')"
   ```

2. **Verify virtual environment**:
   ```bash
   which python  # Should show vmt-dev/bin/python
   pip list | grep -E "(PyQt6|pygame)"  # Check required dependencies
   ```

3. **Review import errors**:
   ```python
   try:
       from src.econsim.tools.launcher.framework.test_configs import ALL_TEST_CONFIGS
       print(f"Success: {len(ALL_TEST_CONFIGS)} configs")
   except ImportError as e:
       print(f"Import failed: {e}")
   ```

#### Issue: "PyQt6 not available"  
**Symptoms**: GUI components fail, health check reports Qt issues  
**Root Cause**: Missing PyQt6 installation or import failure

**Diagnosis**:
```bash
python -c "
try:
    from PyQt6.QtWidgets import QApplication
    print('✅ PyQt6 available')
except ImportError as e:
    print(f'❌ PyQt6 import failed: {e}')
"
```

**Solutions**:
1. **Install PyQt6**:
   ```bash
   pip install PyQt6
   ```

2. **Check Qt platform plugins** (Linux):
   ```bash
   export QT_QPA_PLATFORM_PLUGIN_PATH=$VIRTUAL_ENV/lib/python*/site-packages/PyQt6/Qt6/plugins
   ```

3. **Verify display environment**:
   ```bash
   echo $DISPLAY  # Should show display (e.g., :0)
   ```

### 2. Test Launch Failures

#### Issue: Test launches but window doesn't appear
**Symptoms**: No errors but GUI window not visible  
**Root Cause**: Display/windowing system issues

**Diagnosis**:
```python
from src.econsim.tools.launcher.test_runner import create_test_runner
runner = create_test_runner()

# Check if test window is created
runner.run_by_id(1, "framework")
status = runner.get_status()
print(f"Current test active: {status['current_test']}")
```

**Solutions**:
1. **Check display server**:
   ```bash
   xdpyinfo | head  # X11 info
   echo $WAYLAND_DISPLAY  # Wayland check
   ```

2. **Force window visibility**:
   ```python
   # In framework code, ensure window.show() and window.raise_() are called
   ```

#### Issue: "Framework components not importable"
**Symptoms**: Programmatic launch fails, fallback to subprocess  
**Root Cause**: Framework module import issues

**Diagnosis**:
```python
# Test individual framework imports
try:
    from src.econsim.tools.launcher.framework.base_test import StandardPhaseTest
    print("✅ StandardPhaseTest import OK")
except ImportError as e:
    print(f"❌ StandardPhaseTest import failed: {e}")

try:
    from src.econsim.tools.launcher.framework.simulation_factory import SimulationFactory
    print("✅ SimulationFactory import OK") 
except ImportError as e:
    print(f"❌ SimulationFactory import failed: {e}")
```

**Solutions**:
1. **Check PYTHONPATH**:
   ```bash
   echo $PYTHONPATH
   python -c "import sys; print('\\n'.join(sys.path))"
   ```

2. **Verify framework structure**:
   ```bash
   find src/econsim/tools/launcher/framework -name "*.py" | head -5
   ```

3. **Check for circular imports**:
   ```bash
   python -c "import src.econsim.tools.launcher.framework"
   ```

### 3. Performance Issues

#### Issue: Slow test launching despite programmatic execution
**Symptoms**: Launch times >1 second, performance worse than expected  
**Root Cause**: Heavy framework imports or resource conflicts

**Performance Diagnosis**:
```python
import time
from src.econsim.tools.launcher.test_runner import create_test_runner

# Time individual components
start = time.time()
runner = create_test_runner()
init_time = time.time() - start

start = time.time()
status = runner.get_status()
status_time = time.time() - start

print(f"Initialization: {init_time:.4f}s")
print(f"Status query: {status_time:.4f}s")

# Expected: init <0.1s, status <0.001s
```

**Solutions**:
1. **Check import timing**:
   ```python
   import time
   start = time.time()
   from src.econsim.tools.launcher.framework.test_configs import ALL_TEST_CONFIGS
   import_time = time.time() - start
   print(f"Framework import time: {import_time:.4f}s")
   ```

2. **Profile heavy imports**:
   ```bash
   python -X importtime -c "from src.econsim.tools.launcher.test_runner import create_test_runner"
   ```

### 4. Logging & Monitoring Issues

#### Issue: Launcher logs not being created
**Symptoms**: Empty `launcher_logs/` directory, no event tracking  
**Root Cause**: Launcher logger initialization failure

**Diagnosis**:
```bash
ls -la launcher_logs/ 2>/dev/null || echo "❌ launcher_logs directory missing"

python -c "
from src.econsim.tools.launcher.launcher_logger import LauncherLogger
logger = LauncherLogger()
logger.info('Test log entry')
print('✅ Logger test successful')
"
```

**Solutions**:
1. **Create logs directory**:
   ```bash
   mkdir -p launcher_logs
   chmod 755 launcher_logs
   ```

2. **Check write permissions**:
   ```bash
   touch launcher_logs/test.log && rm launcher_logs/test.log
   echo "Write permissions: OK"
   ```

#### Issue: Health check reports false positives
**Symptoms**: Health check fails but components work manually  
**Root Cause**: Health check logic or component validation issues

**Manual Component Validation**:
```python
# Test each component individually
from src.econsim.tools.launcher.test_runner import TestRunner

runner = TestRunner()

# 1. Qt availability
try:
    from PyQt6.QtWidgets import QApplication
    qt_ok = True
except:
    qt_ok = False

# 2. Test configs
from src.econsim.tools.launcher.framework.test_configs import ALL_TEST_CONFIGS
configs_ok = len(ALL_TEST_CONFIGS) > 0

# 3. Framework components  
try:
    from src.econsim.tools.launcher.framework.base_test import StandardPhaseTest
    framework_ok = True
except:
    framework_ok = False

print(f"Manual validation:")
print(f"  Qt: {'✅' if qt_ok else '❌'}")
print(f"  Configs: {'✅' if configs_ok else '❌'} ({len(ALL_TEST_CONFIGS)})")
print(f"  Framework: {'✅' if framework_ok else '❌'}")

# Compare with health check
health = runner.get_health_check()
print(f"Health check result: {'✅' if health['overall_healthy'] else '❌'}")
```

### 5. GUI Integration Issues

#### Issue: Launcher window appears but test buttons don't work
**Symptoms**: GUI loads but test launching fails silently  
**Root Cause**: TestRunner integration or event handler issues

**Diagnosis**:
```python
# Check if TestRunner is properly integrated in launcher
# This would be done within the launcher application context
```

**Solution - Check launcher integration**:
```bash
# Review launcher logs for TestRunner initialization
tail -20 "$(ls -t launcher_logs/*.log | head -1)"

# Check for TestRunner initialization messages:
# - "✅ Test runner initialized successfully"  
# - "🔧 TestRunner initialized using programmatic TestRunner framework"
```

### 6. Fallback & Recovery Issues

#### Issue: Subprocess fallback not working
**Symptoms**: Both programmatic and fallback execution fail  
**Root Cause**: Subprocess environment or file path issues

**Fallback Diagnosis**:
```bash
# Test subprocess execution manually
cd MANUAL_TESTS
python test_1.py  # Should launch test successfully

# Check file permissions
ls -la test_*.py | head -3

# Verify Python executable in subprocess context
which python
python --version
```

**Solutions**:
1. **Fix test file paths**:
   ```bash
   find MANUAL_TESTS -name "test_*.py" -type f | wc -l  # Should be 7
   ```

2. **Environment variable check**:
   ```bash
   env | grep -E "(PYTHON|PATH|DISPLAY)"
   ```

## Advanced Debugging

### Enable Debug Logging
```bash
export ECONSIM_DEBUG_LAUNCHER=1
export ECONSIM_LOG_LEVEL=DEBUG
make launcher
```

### Comprehensive System Check
```python
#!/usr/bin/env python3
"""Comprehensive VMT TestRunner diagnostic script."""

import sys
import os
from pathlib import Path

def run_diagnostics():
    print("🔧 VMT TestRunner Comprehensive Diagnostics")
    print("=" * 50)
    
    # 1. Environment check
    print("\n1. Environment:")
    print(f"  Python: {sys.version}")
    print(f"  Virtual env: {sys.prefix}")
    print(f"  Working dir: {os.getcwd()}")
    
    # 2. Dependencies check
    print("\n2. Dependencies:")
    try:
        import PyQt6
        print(f"  ✅ PyQt6: {PyQt6.QtCore.qVersion()}")
    except ImportError as e:
        print(f"  ❌ PyQt6: {e}")
    
    try:
        import pygame
        print(f"  ✅ Pygame: {pygame.version.ver}")
    except ImportError as e:
        print(f"  ❌ Pygame: {e}")
    
    # 3. Framework imports
    print("\n3. Framework Imports:")
    try:
        from src.econsim.tools.launcher.framework.test_configs import ALL_TEST_CONFIGS
        print(f"  ✅ Test configs: {len(ALL_TEST_CONFIGS)} loaded")
    except ImportError as e:
        print(f"  ❌ Test configs: {e}")
    
    try:
        from src.econsim.tools.launcher.test_runner import create_test_runner
        print(f"  ✅ TestRunner: Import successful")
    except ImportError as e:
        print(f"  ❌ TestRunner: {e}")
    
    # 4. TestRunner functionality
    print("\n4. TestRunner Functionality:")
    try:
        runner = create_test_runner()
        status = runner.get_status()
        health = runner.get_health_check()
        
        print(f"  ✅ Initialization: Success")
        print(f"  ✅ Available tests: {status['available_tests']}")
        print(f"  ✅ Health status: {'HEALTHY' if health['overall_healthy'] else 'ISSUES'}")
        
        if health['issues']:
            for issue in health['issues']:
                print(f"    - {issue}")
                
    except Exception as e:
        print(f"  ❌ TestRunner: {e}")
    
    # 5. File system check
    print("\n5. File System:")
    paths_to_check = [
        "src/econsim/tools/launcher/",
        "MANUAL_TESTS/",
        "launcher_logs/",
        "gui_logs/"
    ]
    
    for path in paths_to_check:
        if Path(path).exists():
            print(f"  ✅ {path}: Exists")
        else:
            print(f"  ❌ {path}: Missing")
    
    print("\n" + "=" * 50)
    print("Diagnostic complete. Review any ❌ items above for issues.")

if __name__ == "__main__":
    run_diagnostics()
```

### Performance Profiling
```python
import cProfile
import pstats
from src.econsim.tools.launcher.test_runner import create_test_runner

def profile_runner():
    """Profile TestRunner performance."""
    pr = cProfile.Profile()
    pr.enable()
    
    # Profile critical operations
    runner = create_test_runner()
    status = runner.get_status()
    health = runner.get_health_check()
    available = runner.get_available_tests()
    
    pr.disable()
    
    # Generate report
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions

if __name__ == "__main__":
    profile_runner()
```

## Support Resources

### Log Locations
- **Launcher Events**: `launcher_logs/YYYY-MM-DD HH-MM-SS Launcher.log`
- **GUI Events**: `gui_logs/YYYY-MM-DD HH-MM-SS GUI.log` 
- **System Output**: Terminal output from `make launcher`

### Configuration Files
- **TestRunner**: `src/econsim/tools/launcher/test_runner.py`
- **Test Registry**: `src/econsim/tools/launcher/framework/test_configs.py`
- **Launcher GUI**: `src/econsim/tools/launcher/app_window.py`

### Key Directories
```
vmt/
├── src/econsim/tools/launcher/          # Launcher implementation
├── launcher_logs/                       # Launcher event logs
├── gui_logs/                           # GUI session logs
├── MANUAL_TESTS/                       # Original test files (fallback)
└── docs/                               # Documentation
```

---

**For additional support, review the Launcher Architecture Documentation and Programmatic API Usage Guide.**