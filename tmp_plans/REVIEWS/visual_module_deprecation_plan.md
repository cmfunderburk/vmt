# Visual Module Deprecation Plan
**Date:** 2025-10-04  
**Status:** Ready for execution  
**Related:** legacy_code_cleanup_review.md

## Overview

The `src/econsim/visual/` module contains legacy delta recording and playback systems that have been superseded by `ComprehensiveDeltaRecorder` and `ComprehensivePlaybackController` in the `delta/` module.

## Files to Deprecate

### 1. `visual/delta_controller.py` (271 lines)
- **Class:** `DeltaPlaybackController`
- **Status:** DEPRECATED - Superseded by `ComprehensivePlaybackController`
- **Usage:** None (only exported, never imported elsewhere)
- **Action:** Add deprecation warnings, then delete

### 2. `visual/delta_recorder.py` (184 lines)
- **Class:** `VisualDeltaRecorder`
- **Status:** DEPRECATED - Superseded by `ComprehensiveDeltaRecorder`
- **Usage:** Used by `delta_controller.py:269` for loading old files
- **Action:** Keep for backward compatibility loading, add deprecation warnings

### 3. `visual/visual_delta.py` (data structures)
- **Classes:** `VisualDelta`, `VisualState`
- **Status:** KEEP - Shared by both systems
- **Usage:** Used by `ComprehensiveDeltaRecorder` for visual changes
- **Action:** None - this is the shared data format

## Current Production Usage

### ComprehensivePlaybackController (NEW - Active)
✅ `tools/launcher/framework/base_test.py:28, 401`
✅ `gui/embedded_pygame_delta.py:16, 30`
✅ `gui/economic_analysis_widget.py:19, 145`

### DeltaPlaybackController (OLD - Unused)
❌ No production usage
❌ Only exported from `visual/__init__.py`

### VisualDeltaRecorder (OLD - Legacy file support only)
❌ Only used by `delta_controller.py` for loading old `.pickle` files
✅ ComprehensiveDeltaRecorder is production standard

## Execution Steps

### Phase 1: Add Deprecation Warnings (Immediate)

**1.1 Update visual/__init__.py**
```python
"""
Visual module - DEPRECATED

This module is deprecated. Use `econsim.delta` instead:
- ComprehensiveDeltaRecorder (replaces VisualDeltaRecorder)
- ComprehensivePlaybackController (replaces DeltaPlaybackController)

The VisualDelta and VisualState data structures have been moved to
delta.data_structures and are the canonical implementation.
"""

# Data structures (kept for backward compatibility)
from .visual_delta import VisualDelta, VisualState

# DEPRECATED: Use ComprehensiveDeltaRecorder instead
from .delta_recorder import VisualDeltaRecorder

# DEPRECATED: Use ComprehensivePlaybackController instead  
from .delta_controller import DeltaPlaybackController

__all__ = [
    'VisualDelta',       # Shared data structure
    'VisualState',       # Shared data structure
    'VisualDeltaRecorder',  # DEPRECATED
    'DeltaPlaybackController',  # DEPRECATED
]
```

**1.2 Add warning to delta_controller.py**
```python
import warnings

class DeltaPlaybackController:
    """Controls delta-based playback for pygame visualization.
    
    .. deprecated:: 2025-10-04
        Use :class:`econsim.delta.ComprehensivePlaybackController` instead.
        This class is maintained only for backward compatibility with old
        .pickle delta files.
    """
    
    def __init__(self, initial_state: VisualState, visual_deltas: List[VisualDelta]):
        warnings.warn(
            "DeltaPlaybackController is deprecated. "
            "Use ComprehensivePlaybackController from econsim.delta instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # ... rest of __init__
```

**1.3 Add warning to delta_recorder.py**
```python
import warnings

class VisualDeltaRecorder:
    """Records visual deltas during simulation execution.
    
    .. deprecated:: 2025-10-04
        Use :class:`econsim.delta.ComprehensiveDeltaRecorder` instead.
        This class records only visual changes. ComprehensiveDeltaRecorder
        captures complete simulation state including economics and performance.
    """
    
    def __init__(self, output_path: str):
        warnings.warn(
            "VisualDeltaRecorder is deprecated. "
            "Use ComprehensiveDeltaRecorder from econsim.delta instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # ... rest of __init__
```

### Phase 2: Migration Period (1-2 weeks)

- Monitor for any usage of deprecated classes in logs
- Check if any tests or external scripts use the old system
- Update any remaining references

### Phase 3: Complete Removal (After verification)

**3.1 Delete deprecated files**
```bash
rm src/econsim/visual/delta_controller.py
rm src/econsim/visual/delta_recorder.py
```

**3.2 Update visual/__init__.py**
```python
"""
Visual data structures for delta recording and playback.

These data structures are used by the delta recording system in econsim.delta.
"""

from .visual_delta import VisualDelta, VisualState

__all__ = [
    'VisualDelta',
    'VisualState',
]
```

**3.3 Update visual/visual_delta.py docstring**
```python
"""
Visual Delta Data Structures

Defines visual state and delta structures used by ComprehensiveDeltaRecorder
for pygame rendering and playback.

These are lightweight representations of visual changes that can be efficiently
serialized and applied during playback.
"""
```

## Benefits of Removal

1. **Eliminate confusion:** Single source of truth for delta recording/playback
2. **Reduce maintenance:** ~455 lines of deprecated code removed
3. **Better features:** Comprehensive system includes economics, performance, and debugging
4. **Cleaner architecture:** Clear separation between data structures and controllers

## Risk Assessment

**Risk Level:** VERY LOW

**Why:**
- No production code uses deprecated classes
- ComprehensivePlaybackController is already production standard
- Visual data structures remain unchanged
- Only internal refactoring, no external API changes

**Mitigation:**
- Deprecation warnings alert any hidden usage
- Migration period allows time to catch issues
- Git history preserves old code if needed

## Testing Strategy

**Before removal:**
1. Run full test suite: `make test-unit`
2. Launch GUI: `make launcher`
3. Verify playback works with comprehensive system
4. Check no deprecation warnings in test output

**After removal:**
1. Verify imports work: `python -c "from econsim.visual import VisualDelta, VisualState"`
2. Verify delta module: `python -c "from econsim.delta import ComprehensiveDeltaRecorder, ComprehensivePlaybackController"`
3. Run playback test through launcher
4. Full regression test suite

## Timeline

- **Phase 1:** Immediate (30 minutes)
- **Phase 2:** 1-2 weeks (passive monitoring)
- **Phase 3:** After verification (15 minutes)

**Total removal:** ~455 lines of deprecated code

