# Launcher Packaging Roadmap - Future Contributor Guide

**Date**: 2025-09-28  
**Status**: POST PHASE 4 COMPLETION - Remaining Reorganization Work  
**Context**: Phase 4 achieved 87% code reduction and monolith elimination. This document outlines remaining packaging/UX improvements.

## Executive Summary

Phase 4 successfully eliminated the monolithic launcher (1153 → 145 lines, 87% reduction) and created a clean modular architecture under `src/econsim/tools/launcher/`. However, several user experience and packaging improvements from the original reorganization plan remain unimplemented.

**What's Complete**: ✅ Monolith decomposition, ✅ Framework extraction, ✅ Modular architecture, ✅ Performance testing enhancement, ✅ Documentation modernization

**What's Remaining**: ~~XDG/appdata data locations~~ ✅, programmatic runner API, sys.path hack elimination, brittle filename mapping cleanup

## Phase 5: Data Location Simplification ✅ **COMPLETED**

**Goal**: Maintain project-local logs and user data with proper .gitignore handling

### Step 5.1: Implement AppData Resolver (45 minutes)

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

### Step 5.2: Simplify Debug Logger ✅

1. **Updated `src/econsim/gui/debug_logger.py`**:
```python
class GUILogger:
    def __init__(self):
        # Always use project-local logs directory
        # Logs stay in the project for development convenience and are excluded via .gitignore
        self.logs_dir = Path(__file__).parent.parent.parent.parent / "gui_logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
```

**Acceptance**: 
- ✅ All logs stay in project `gui_logs/` directory
- ✅ Logs excluded from git via `.gitignore` (already configured)
- ✅ No complex migration or appdata handling needed

### Step 5.3: Simplify Launcher Data ✅

1. **Updated custom tests tab** to use project location:
```python
def get_custom_tests_dir(self) -> Path:
    """Get custom tests directory (always in project)."""
    # Always use project-local custom tests directory  
    project_root = Path(__file__).parent.parent.parent.parent.parent.parent
    return project_root / "MANUAL_TESTS" / "custom_tests"
```

2. **Updated config presets** to stay local:
```python
def _get_presets_file(self) -> Path:
    """Get presets file (always in project)."""
    # Always use project-local presets file
    return Path(__file__).parent / "config_presets.json"
```

**Acceptance**: 
- ✅ Custom tests stay in `MANUAL_TESTS/custom_tests/` 
- ✅ Config presets stay in `MANUAL_TESTS/config_presets.json`
- ✅ User can choose to commit custom tests or add to .gitignore as needed

## Phase 6: Programmatic Runner Implementation

**Goal**: Replace subprocess launching with programmatic API

### Step 6.1: Create Test Runner API (60 minutes)

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

### Step 6.2: Remove Filename Mappings (30 minutes)

1. **Remove hardcoded `id_to_file` mapping** from app_window.py
2. **Use registry-based dispatch** through TestRunner
3. **Clean up subprocess launching code**

**Acceptance**: No more brittle filename mappings, all launches through registry

## Phase 7: Path Hack Elimination

**Goal**: Remove all `sys.path` manipulation from MANUAL_TESTS files

### Step 7.1: Update Test Files (45 minutes)

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

### Step 7.2: Clean Up Entry Points (15 minutes)

1. **Remove `sys.path` from enhanced_test_launcher_v2.py**
2. **Use proper package imports** throughout
3. **Clean up old framework cache directories**

```bash
rm -rf MANUAL_TESTS/framework/__pycache__/
rm -rf MANUAL_TESTS/__pycache__/
```

**Acceptance**: No sys.path hacks anywhere in codebase

## Phase 8: Documentation and Testing

### Step 8.1: Update Documentation (30 minutes)

1. **Create `docs/LAUNCHER_PACKAGING.md`**:
   - Installation instructions  
   - Development vs production data locations
   - Migration notes
   - Launcher architecture guide

2. **Update README.md** with launcher usage patterns
3. **Update copilot instructions** with packaging info

### Step 8.2: Add Packaging Tests (30 minutes)

1. **Add smoke tests** for programmatic runner  
2. **Test appdata location creation**
3. **Validate data migration functionality**

## Implementation Priority

**Recommended Order**:
1. **Phase 6** (Programmatic Runner) - Eliminates subprocess brittleness, highest technical value  
2. **Phase 5** (Data Locations) - Better user experience, stops repo pollution
3. **Phase 7** (Path Cleanup) - Code quality improvement, enables proper packaging
4. **Phase 8** (Documentation) - Support and maintenance

**Rationale**: Since the GUI launcher is core to VMT's educational mission, focus on improving the existing launcher architecture rather than adding unnecessary console script complexity.

## Risk Assessment

**Low Risk**:
- AppData resolver (isolated utility)
- Documentation updates
- Path cleanup (dev environment improvement)

**Medium Risk**:
- Data location migration (user impact if broken)
- Programmatic runner (changes execution model)

**Mitigation Strategy**:
- Implement dev mode overrides for all data locations  
- Preserve backward compatibility during migration
- Test thoroughly in development environment first
- Maintain `make launcher` as primary entry point

## Success Criteria

**Phase 5 Complete**: ✅ Project-local logs with .gitignore, simplified data locations
**Phase 6 Complete**: No subprocess launching, programmatic test execution  
**Phase 7 Complete**: No sys.path hacks anywhere
**Phase 8 Complete**: Comprehensive documentation, automated tests

**Overall Success**: VMT launcher architecture is modernized while preserving its core educational GUI mission

## Recommended Next Steps

**Immediate Priority**: Address any current GUI regressions or launcher issues before implementing packaging improvements.

**Phase Selection**: 
- **Phase 6 (Programmatic Runner)** offers the highest technical value by eliminating subprocess brittleness
- **Phase 5 (Data Locations)** provides immediate user experience improvements  
- Both phases are independent and can be implemented in parallel

**Development Approach**: 
- Maintain `make launcher` as the primary entry point for VMT
- Keep PyQt6 as a core dependency since GUI is essential to educational mission
- Focus on improving launcher architecture rather than adding packaging complexity

This roadmap provides a clear path for future contributors to complete the packaging modernization while preserving VMT's core educational GUI focus.