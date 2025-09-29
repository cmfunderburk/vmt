# VMT Widgets Migration Plan: MANUAL_TESTS to src/econsim/tools/widgets/

**Date**: September 29, 2025  
**Status**: CRITICAL - Required for launcher tab functionality  
**Objective**: Migrate GUI components from MANUAL_TESTS/ to proper src/econsim/tools/widgets/ location

## Problem Summary

The VMT Enhanced Test Launcher tabs (Configuration Editor, Batch Runner, Bookmarks) are failing because they try to import GUI components from `MANUAL_TESTS/` using complex path manipulation. This violates architectural principles and creates fragile dependencies.

### Current Issues:
1. **Architecture Violation**: GUI components in test directory instead of tools
2. **Import Failures**: Complex path calculations failing in launcher context  
3. **Path Manipulation**: Tabs doing `sys.path` manipulation with 5-level parent navigation
4. **Separation Violation**: Reusable components mixed with test files

## Target Architecture

```
src/econsim/tools/
├── launcher/              # Existing launcher system
└── widgets/               # NEW: Reusable GUI widgets
    ├── __init__.py       # Package initialization
    ├── config_editor.py  # From live_config_editor.py
    ├── batch_runner.py   # From batch_test_runner.py
    └── bookmark_manager.py # From test_bookmarks.py
```

## Detailed Migration Steps

### Phase 1: Infrastructure Setup

#### Step 1.1: Create widgets directory structure
```bash
mkdir -p src/econsim/tools/widgets
```

#### Step 1.2: Create package __init__.py
```python
# src/econsim/tools/widgets/__init__.py
"""Reusable GUI widgets for VMT tools.

This package contains GUI components that can be used across different
VMT tools and applications, extracted from MANUAL_TESTS for proper
architectural separation.
"""

from .config_editor import ConfigEditor
from .batch_runner import BatchRunner  
from .bookmark_manager import BookmarkManager

__all__ = ['ConfigEditor', 'BatchRunner', 'BookmarkManager']
```

### Phase 2: Component Migration

#### Step 2.1: Extract ConfigEditor from live_config_editor.py

**Source Analysis:**
- File: `MANUAL_TESTS/live_config_editor.py` (1,328 lines)
- Main class: `LiveConfigEditor` (should become `ConfigEditor`)
- Dependencies: PyQt6, econsim framework imports, test configurations

**Migration Actions:**
1. **Create** `src/econsim/tools/widgets/config_editor.py`
2. **Extract** the `LiveConfigEditor` class → rename to `ConfigEditor`
3. **Clean imports**: Remove project root path manipulation, use proper relative imports
4. **Update docstrings**: Reflect new location and purpose
5. **Preserve functionality**: All methods and signals intact

**Key Changes:**
```python
# OLD (live_config_editor.py):
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# NEW (config_editor.py):
# No path manipulation needed - proper package imports
from ...framework.test_configs import TestConfiguration, ALL_TEST_CONFIGS
```

#### Step 2.2: Extract BatchRunner from batch_test_runner.py

**Source Analysis:**
- File: `MANUAL_TESTS/batch_test_runner.py` (732 lines)
- Main class: `BatchTestRunner` (should become `BatchRunner`)
- Dependencies: PyQt6, threading, test execution logic

**Migration Actions:**
1. **Create** `src/econsim/tools/widgets/batch_runner.py`
2. **Extract** the `BatchTestRunner` class → rename to `BatchRunner`  
3. **Clean imports**: Remove path manipulation
4. **Preserve threading**: Maintain all execution logic
5. **Update progress tracking**: Ensure compatibility with launcher

#### Step 2.3: Extract BookmarkManager from test_bookmarks.py

**Source Analysis:**
- File: `MANUAL_TESTS/test_bookmarks.py` (890 lines)
- Main class: `TestBookmarkManager` (should become `BookmarkManager`)
- Dependencies: PyQt6, JSON persistence, search functionality

**Migration Actions:**
1. **Create** `src/econsim/tools/widgets/bookmark_manager.py`
2. **Extract** the `TestBookmarkManager` class → rename to `BookmarkManager`
3. **Clean imports**: Use proper package structure
4. **Preserve persistence**: Maintain bookmark storage functionality
5. **Update file paths**: Ensure bookmark storage location is correct

### Phase 3: Launcher Integration

#### Step 3.1: Update ConfigEditorTab
```python
# OLD:
from pathlib import Path
import sys
manual_tests_path = Path(__file__).parent.parent.parent.parent.parent / "MANUAL_TESTS"
sys.path.insert(0, str(manual_tests_path))
from live_config_editor import LiveConfigEditor

# NEW:
from econsim.tools.widgets import ConfigEditor

class ConfigEditorTab(AbstractTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tab_title = "⚙️ Configuration Editor"
        self._tab_id = "config_editor"
        
        # Clean, simple import - no path manipulation
        self.config_editor = ConfigEditor()
```

#### Step 3.2: Update BatchRunnerTab
```python
# OLD: Complex path manipulation
# NEW: from econsim.tools.widgets import BatchRunner
```

#### Step 3.3: Update BookmarksTab  
```python
# OLD: Complex path manipulation
# NEW: from econsim.tools.widgets import BookmarkManager
```

#### Step 3.4: Remove path manipulation code
- Delete all `manual_tests_path` calculations
- Delete all `sys.path.insert()` calls
- Remove debug print statements
- Clean up error handling for missing imports

### Phase 4: Backwards Compatibility

#### Step 4.1: Update MANUAL_TESTS files
Create thin wrapper files that import from new location:

```python
# MANUAL_TESTS/live_config_editor.py (new version)
#!/usr/bin/env python3
"""
Live Configuration Editor - Compatibility Wrapper
=================================================

This file now imports from the proper location in src/econsim/tools/widgets/
to maintain backwards compatibility for standalone usage.
"""

import sys
from pathlib import Path

# Add src to path to import from proper location
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import from proper location
from econsim.tools.widgets.config_editor import ConfigEditor as LiveConfigEditor

# Maintain original interface for compatibility
__all__ = ['LiveConfigEditor']

if __name__ == "__main__":
    # Standalone execution support
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    editor = LiveConfigEditor()
    editor.show()
    sys.exit(app.exec())
```

#### Step 4.2: Update test files that import these components
- Scan for other files importing live_config_editor, batch_test_runner, test_bookmarks
- Update imports to use new locations or compatibility wrappers
- Ensure all test scenarios still work

### Phase 5: Testing & Validation

#### Step 5.1: Launcher Testing
```bash
# Test launcher with new imports
cd /home/chris/PROJECTS/vmt
source vmt-dev/bin/activate
make launcher
# Verify all tabs load without "not available" messages
```

#### Step 5.2: Standalone Testing  
```bash
# Test standalone compatibility
python MANUAL_TESTS/live_config_editor.py
python MANUAL_TESTS/batch_test_runner.py
python MANUAL_TESTS/test_bookmarks.py
```

#### Step 5.3: Import Testing
```python
# Test direct imports work
from econsim.tools.widgets import ConfigEditor, BatchRunner, BookmarkManager
```

### Phase 6: Cleanup & Documentation

#### Step 6.1: Update documentation
- Update launcher architecture docs
- Update widget usage examples  
- Document import paths in API_GUIDE.md

#### Step 6.2: Code cleanup
- Remove old debug code
- Standardize docstrings
- Update type hints
- Ensure consistent naming

## Risk Assessment

### Low Risk:
- ✅ Pure code movement with no logic changes
- ✅ Backwards compatibility maintained via wrappers
- ✅ Incremental migration possible (one component at a time)

### Medium Risk:
- ⚠️ Import dependency updates across multiple files
- ⚠️ Path calculations for bookmark/config storage may need adjustment

### High Risk:
- 🚨 None identified - this is a straightforward refactoring

## Rollback Plan

If issues arise:
1. **Revert launcher tabs** to old path manipulation code
2. **Keep new widgets** but don't use them yet
3. **Restore original MANUAL_TESTS** files from git
4. **Investigate issues** before re-attempting

## Success Criteria

- [ ] ✅ Launcher tabs show actual content instead of "not available"
- [ ] ✅ Configuration Editor tab loads and functions
- [ ] ✅ Batch Runner tab loads and functions  
- [ ] ✅ Bookmarks tab loads and functions
- [ ] ✅ Custom Tests tab finds and displays custom tests
- [ ] ✅ All MANUAL_TESTS files still run standalone
- [ ] ✅ No import errors in launcher or tests
- [ ] ✅ No path manipulation code remains in tabs

## Implementation Priority

1. **HIGH**: ConfigEditor migration (fixes Configuration Editor tab)
2. **HIGH**: BatchRunner migration (fixes Batch Runner tab)
3. **HIGH**: BookmarkManager migration (fixes Bookmarks tab)
4. **MEDIUM**: MANUAL_TESTS compatibility wrappers
5. **LOW**: Documentation updates

## Next Steps

1. **Discuss approach** with user - confirm this plan
2. **Start with ConfigEditor** - single component migration to validate approach
3. **Test launcher integration** - ensure tab works properly
4. **Continue with remaining components** if successful
5. **Complete backwards compatibility** once core migration works

---

**Estimated Time**: 2-3 hours for full migration  
**Complexity**: Medium (architectural refactoring)  
**Impact**: High (fixes critical launcher functionality)