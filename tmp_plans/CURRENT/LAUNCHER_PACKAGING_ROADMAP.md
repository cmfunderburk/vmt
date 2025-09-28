# Launcher Packaging Roadmap - Future Contributor Guide

**Date**: 2025-09-28  
**Status**: POST PHASE 4 COMPLETION - Remaining Reorganization Work  
**Context**: Phase 4 achieved 87% code reduction and monolith elimination. This document outlines remaining packaging/UX improvements.

## Executive Summary

Phase 4 successfully eliminated the monolithic launcher (1153 → 145 lines, 87% reduction) and created a clean modular architecture under `src/econsim/tools/launcher/`. However, several user experience and packaging improvements from the original reorganization plan remain unimplemented.

**What's Complete**: ✅ Monolith decomposition, ✅ Framework extraction, ✅ Modular architecture, ✅ Performance testing enhancement, ✅ Documentation modernization

**What's Remaining**: Console script entry points, XDG/appdata data locations, programmatic runner API, sys.path hack elimination, brittle filename mapping cleanup

## Phase 5: Console Script Implementation

**Goal**: Enable `pip install econsim-vmt[launcher]` and `econsim-launcher` command

### Step 5.1: Add Console Script Entry Point (30 minutes)

1. **Create `src/econsim/tools/launcher/__main__.py`**:
```python
"""Console entry point for VMT Enhanced Test Launcher."""
from .app_window import main

if __name__ == "__main__":
    main()
```

2. **Update `pyproject.toml`** to add:
```toml
[project.scripts]
econsim-launcher = "econsim.tools.launcher:main"

[project.optional-dependencies]
launcher = ["PyQt6>=6.5.0"]
dev = [
  "pytest>=7.4.0",
  "black>=24.0.0", 
  "ruff>=0.5.0",
  "mypy>=1.8.0",
]
```

3. **Move PyQt6 dependency** from main dependencies to launcher extra:
```toml
dependencies = [
  "pygame>=2.5.0",
  "numpy>=1.24.0"
]
```

4. **Update app_window.py** to export main function:
```python
def main():
    """Console script entry point."""
    # Existing main() logic
```

**Acceptance**: 
- `pip install -e .[launcher]` then `econsim-launcher` launches GUI
- `pip install -e .` provides core simulation without GUI dependencies
- `python -m econsim.tools.launcher` works

### Step 5.2: Update Makefile and Documentation (15 minutes)

1. **Update Makefile** `launcher` target to use module entry:
```makefile
launcher:
	@echo "🚀 Starting VMT Enhanced Test Launcher..."
	ECONSIM_LOG_LEVEL=EVENTS ECONSIM_LOG_FORMAT=COMPACT \
	ECONSIM_DEBUG_AGENT_MODES=1 ECONSIM_DEBUG_TRADES=1 \
	ECONSIM_DEBUG_ECONOMICS=1 ECONSIM_LOG_BUNDLE_TRADES=1 \
	python -m econsim.tools.launcher
```

2. **Update README.md** quick start section:
```markdown
# Install with launcher GUI
pip install econsim-vmt[launcher]
econsim-launcher

# Or for development
make launcher
```

**Acceptance**: Documentation reflects new installation method, Makefile uses module entry

## Phase 6: Data Location Modernization

**Goal**: Stop polluting repo with logs and user data; use XDG/appdata conventions

### Step 6.1: Implement AppData Resolver (45 minutes)

1. **Create `src/econsim/tools/launcher/appdata.py`**:
```python
"""Cross-platform application data directory resolver."""
from pathlib import Path
import os
from typing import Optional

class AppDataResolver:
    """Resolves application data directories following platform conventions."""
    
    @staticmethod
    def get_config_dir() -> Path:
        """Get configuration directory (~/.config/econsim on Linux)."""
        if os.name == 'nt':  # Windows
            return Path(os.environ.get('APPDATA', '~')) / 'econsim'
        elif os.environ.get('XDG_CONFIG_HOME'):
            return Path(os.environ['XDG_CONFIG_HOME']) / 'econsim'
        else:  # Linux/macOS default
            return Path.home() / '.config' / 'econsim'
    
    @staticmethod
    def get_data_dir() -> Path:
        """Get data directory (~/.local/share/econsim on Linux)."""
        if os.name == 'nt':  # Windows
            return Path(os.environ.get('LOCALAPPDATA', '~')) / 'econsim'
        elif os.environ.get('XDG_DATA_HOME'):
            return Path(os.environ['XDG_DATA_HOME']) / 'econsim'
        else:  # Linux/macOS default
            return Path.home() / '.local' / 'share' / 'econsim'
    
    @staticmethod
    def get_state_dir() -> Path:
        """Get state directory (~/.local/state/econsim on Linux)."""
        if os.name == 'nt':  # Windows
            return AppDataResolver.get_data_dir() / 'state'
        elif os.environ.get('XDG_STATE_HOME'):
            return Path(os.environ['XDG_STATE_HOME']) / 'econsim'
        else:  # Linux/macOS default
            return Path.home() / '.local' / 'state' / 'econsim'
    
    @staticmethod
    def get_launcher_config_file() -> Path:
        """Get launcher configuration file path."""
        return AppDataResolver.get_config_dir() / 'launcher' / 'config.json'
    
    @staticmethod
    def get_custom_tests_dir() -> Path:
        """Get custom tests directory."""
        return AppDataResolver.get_data_dir() / 'launcher' / 'custom_tests'
    
    @staticmethod
    def get_logs_dir() -> Path:
        """Get logs directory."""
        return AppDataResolver.get_state_dir() / 'gui_logs'
```

2. **Add development override** environment variable support:
```python
def get_config_dir(dev_override: Optional[str] = None) -> Path:
    """Get config dir with optional development override."""
    if dev_override or os.environ.get('ECONSIM_DEV_APPDATA'):
        return Path(dev_override or os.environ['ECONSIM_DEV_APPDATA']) / 'config'
    # ... normal logic
```

**Acceptance**: AppData resolver returns proper paths for all platforms

### Step 6.2: Migrate Debug Logger (30 minutes)

1. **Update `src/econsim/gui/debug_logger.py`**:
```python
from ..tools.launcher.appdata import AppDataResolver

class GuiDebugLogger:
    def __init__(self):
        # Use appdata location with dev override
        if os.environ.get('ECONSIM_DEV_MODE'):
            # Keep repo location for development
            self.logs_dir = Path(__file__).parent.parent.parent.parent / "gui_logs"
        else:
            self.logs_dir = AppDataResolver.get_logs_dir()
        
        self.logs_dir.mkdir(parents=True, exist_ok=True)
```

2. **Add migration logic**:
```python
def migrate_old_logs(self):
    """One-time migration from repo gui_logs/ to appdata."""
    old_logs = Path(__file__).parent.parent.parent.parent / "gui_logs"
    if old_logs.exists() and not os.environ.get('ECONSIM_DEV_MODE'):
        # Copy logs to new location, then remove old ones
        # Implementation details...
```

**Acceptance**: 
- Production: logs go to `~/.local/state/econsim/gui_logs/`
- Development: `ECONSIM_DEV_MODE=1` keeps repo logs
- One-time migration preserves existing logs

### Step 6.3: Migrate Launcher Data (30 minutes)

1. **Update custom tests tab** to use appdata:
```python
# In custom_tests_tab.py
from ..appdata import AppDataResolver

def get_custom_tests_dir(self):
    if os.environ.get('ECONSIM_DEV_MODE'):
        return Path(__file__).parent.parent.parent.parent.parent.parent / "MANUAL_TESTS" / "custom_tests"
    return AppDataResolver.get_custom_tests_dir()
```

2. **Migrate config presets**:
```python
# Similar pattern for config_presets.json
def get_presets_file(self):
    if os.environ.get('ECONSIM_DEV_MODE'):
        return Path("MANUAL_TESTS/config_presets.json")
    return AppDataResolver.get_config_dir() / 'launcher' / 'presets.json'
```

**Acceptance**: 
- Production: data in appdata locations
- Development: `ECONSIM_DEV_MODE=1` uses repo locations
- First-run migration preserves existing presets/custom tests

## Phase 7: Programmatic Runner Implementation

**Goal**: Replace subprocess launching with programmatic API

### Step 7.1: Create Test Runner API (60 minutes)

1. **Create `src/econsim/tools/launcher/test_runner.py`**:
```python
"""Programmatic test execution API."""
from typing import Optional, Dict, Any
from pathlib import Path

from .framework.test_configs import TestConfiguration, ALL_TEST_CONFIGS

class TestRunner:
    """Executes tests programmatically without subprocess."""
    
    def run_by_id(self, test_id: int, mode: str = "framework") -> None:
        """Run test by ID using registry lookup."""
        config = self._get_config_by_id(test_id)
        if not config:
            raise ValueError(f"Test ID {test_id} not found")
        
        self.run_config(config, mode)
    
    def run_config(self, config: TestConfiguration, mode: str = "framework") -> None:
        """Run test configuration programmatically."""
        if mode == "framework":
            self._run_framework_test(config)
        elif mode == "original":
            self._run_original_test(config)
        else:
            raise ValueError(f"Unknown mode: {mode}")
    
    def _run_framework_test(self, config: TestConfiguration) -> None:
        """Execute framework test directly."""
        # Import and execute test configuration directly
        from .framework.simulation_factory import create_simulation_from_config
        from econsim.gui.embedded_pygame import EmbeddedPygameWidget
        
        # Direct execution without subprocess
        simulation = create_simulation_from_config(config)
        # Launch GUI directly...
    
    def _get_config_by_id(self, test_id: int) -> Optional[TestConfiguration]:
        """Get configuration by ID from registry."""
        return next((c for c in ALL_TEST_CONFIGS if c.id == test_id), None)
```

2. **Update app_window.py** to use runner:
```python
from .test_runner import TestRunner

class VMTLauncherWindow:
    def __init__(self):
        self.test_runner = TestRunner()
    
    def launch_test(self, config_id: int, mode: str):
        """Launch test using programmatic runner."""
        try:
            self.test_runner.run_by_id(config_id, mode)
            self.log_status(f"🚀 Launched test {config_id} ({mode})")
        except Exception as e:
            self.log_status(f"✗ Failed to launch test: {e}")
```

**Acceptance**: Tests launch programmatically without subprocess or filename mapping

### Step 7.2: Remove Filename Mappings (30 minutes)

1. **Remove hardcoded `id_to_file` mapping** from app_window.py
2. **Use registry-based dispatch** through TestRunner
3. **Clean up subprocess launching code**

**Acceptance**: No more brittle filename mappings, all launches through registry

## Phase 8: Path Hack Elimination

**Goal**: Remove all `sys.path` manipulation from MANUAL_TESTS files

### Step 8.1: Update Test Files (45 minutes)

1. **Create proper package structure** for MANUAL_TESTS if needed
2. **Replace `sys.path.insert()` calls** with proper imports:

```python
# OLD (in test_*.py files):
sys.path.insert(0, os.path.join(repo_root, "src"))
from econsim.gui.embedded_pygame import EmbeddedPygameWidget

# NEW:
from econsim.gui.embedded_pygame import EmbeddedPygameWidget
```

3. **Update all MANUAL_TESTS/*.py files** systematically:
   - `test_1.py` through `test_7.py`
   - `test_bookmarks.py`
   - `phase_config_editor.py`
   - Custom test templates

**Acceptance**: No `sys.path` manipulation in any MANUAL_TESTS files

### Step 8.2: Clean Up Entry Points (15 minutes)

1. **Remove `sys.path` from enhanced_test_launcher_v2.py**
2. **Use proper package imports** throughout
3. **Clean up old framework cache directories**

```bash
rm -rf MANUAL_TESTS/framework/__pycache__/
rm -rf MANUAL_TESTS/__pycache__/
```

**Acceptance**: No sys.path hacks anywhere in codebase

## Phase 9: Documentation and Testing

### Step 9.1: Update Documentation (30 minutes)

1. **Create `docs/LAUNCHER_PACKAGING.md`**:
   - Installation instructions
   - Console script usage
   - Development vs production data locations
   - Migration notes

2. **Update README.md** with new installation methods
3. **Update copilot instructions** with packaging info

### Step 9.2: Add Packaging Tests (30 minutes)

1. **Add smoke tests** for console script
2. **Test appdata location creation**
3. **Validate optional dependencies structure**

## Implementation Priority

**Recommended Order**:
1. **Phase 5** (Console Scripts) - Highest user value, enables proper distribution
2. **Phase 7** (Programmatic Runner) - Eliminates subprocess brittleness  
3. **Phase 6** (Data Locations) - Better user experience, stops repo pollution
4. **Phase 8** (Path Cleanup) - Code quality improvement
5. **Phase 9** (Documentation) - Support and maintenance

## Risk Assessment

**Low Risk**:
- Console script implementation (additive)
- AppData resolver (isolated utility)
- Documentation updates

**Medium Risk**:
- Data location migration (user impact if broken)
- Programmatic runner (changes execution model)

**Mitigation Strategy**:
- Implement dev mode overrides for all data locations
- Preserve backward compatibility during migration
- Test thoroughly in development environment first

## Success Criteria

**Phase 5 Complete**: `pip install econsim-vmt[launcher]` && `econsim-launcher` works
**Phase 6 Complete**: No repo pollution, proper appdata usage, dev mode preserved
**Phase 7 Complete**: No subprocess launching, programmatic test execution
**Phase 8 Complete**: No sys.path hacks anywhere
**Phase 9 Complete**: Comprehensive documentation, automated tests

This roadmap provides a clear path for future contributors to complete the packaging modernization started in the original reorganization plan.