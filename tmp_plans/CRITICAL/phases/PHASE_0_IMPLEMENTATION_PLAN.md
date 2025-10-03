# Phase 0: Observer System Cleanup - Implementation Plan

**Date:** October 3, 2025  
**Status:** Ready for Execution  
**Duration:** 1-2 weeks (10 working days)  
**Priority:** P0 (must complete before Phase 2)  
**Prerequisites:** None (this is the first phase)

---

## Executive Summary

Phase 0 cleans and formalizes the observer system BEFORE building the output architecture on top of it. This is critical because Phase 2 (Simulation Output Architecture) depends on a production-ready FileObserver and clean event schema.

**Key Principle:** Clean foundation first, then build on top. No rework allowed.

**Success Criteria:** Observer system must be production-ready for Phase 2 to begin.

---

## Pre-Phase Setup

### Git Checkpoint Creation

```bash
# Create the starting checkpoint
git tag refactor-pre-phase0 -m "Refactoring begins - before observer cleanup"
git push origin refactor-pre-phase0

# Verify tag created
git tag -l "refactor-pre-phase0"
```

### Status Tracking Setup

Update `REFACTOR_STATUS.md`:
```markdown
## Current Phase: Phase 0 - Observer System Cleanup
- **Status:** 🟡 In Progress
- **Started:** 2025-10-03
- **Expected Completion:** 2025-10-17
- **Current Step:** 0.1 - Observer System Audit
```

---

## Step 0.1: Observer System Audit

**Duration:** 1-2 days  
**Goal:** Systematically review all observer-related code

### 0.1.1: Discover All Observer Files

```bash
# Navigate to project root
cd /home/chris/PROJECTS/vmt

# Find all observer-related Python files
find src/econsim/observability/ -name "*.py" > /tmp/observer_files.txt

# Also check for observer imports in other directories
grep -r "from.*observability" src/ --include="*.py" > /tmp/observer_imports.txt
grep -r "import.*observability" src/ --include="*.py" >> /tmp/observer_imports.txt
```

### 0.1.2: Create Audit Document

Create `tmp_plans/CURRENT/CRITICAL/OBSERVER_SYSTEM_AUDIT.md`:

```markdown
# Observer System Audit

**Date:** 2025-10-03  
**Auditor:** Chris  
**Purpose:** Document all observer components before cleanup

## File Inventory

### Core Observer Files
[To be populated during audit]

### Observer Usage
[To be populated during audit]

## Component Analysis

### FileObserver
- **Location:** 
- **Purpose:** 
- **Status:** Active/Deprecated/Legacy
- **Dependencies:** 
- **Issues:** 

### GUIObserver  
- **Location:** 
- **Purpose:** 
- **Status:** Active/Deprecated/Legacy
- **Dependencies:** 
- **Issues:** 

### GUILogger
- **Location:** 
- **Purpose:** 
- **Status:** Active/Deprecated/Legacy
- **Dependencies:** 
- **Issues:** 

## Issues Found
- [ ] List all "deprecated" comments
- [ ] List all "TODO" comments
- [ ] List all "FIXME" comments
- [ ] List all "legacy" comments

## Removal Candidates
- [ ] Components marked as deprecated
- [ ] Components with no current usage
- [ ] Duplicate functionality

## Next Steps
- [ ] Remove deprecated components
- [ ] Clarify ambiguous status
- [ ] Document remaining components
```

### 0.1.3: Analyze Each Observer File

For each file in `/tmp/observer_files.txt`:

1. **Read the file completely**
2. **Document in audit:**
   - Purpose and responsibility
   - Current status (active, deprecated, legacy)
   - Dependencies (what uses it?)
   - Issues (TODOs, FIXMEs, "deprecated" comments)
   - Import statements
   - Class/function definitions

3. **Look for specific patterns:**
   ```bash
   # Search for deprecated markers
   grep -n "deprecated\|legacy\|old\|unused" [filename]
   
   # Search for TODO/FIXME
   grep -n "TODO\|FIXME\|XXX" [filename]
   
   # Search for observer registration
   grep -n "register\|attach\|subscribe" [filename]
   ```

### 0.1.4: Check Usage Patterns

```bash
# Find all files that import observer components
grep -r "GUILogger\|GUIObserver\|FileObserver" src/ --include="*.py"

# Check for observer instantiation
grep -r "GUILogger()\|GUIObserver()\|FileObserver()" src/ --include="*.py"

# Check for observer method calls
grep -r "\.record_\|\.notify\|\.update" src/ --include="*.py"
```

### 0.1.5: Success Criteria Check

- [ ] All observer files documented in audit
- [ ] Status clarity for each component (Active/Deprecated/Legacy)
- [ ] All issues identified and categorized
- [ ] Removal candidates flagged
- [ ] Usage patterns documented

**Deliverable:** Complete `OBSERVER_SYSTEM_AUDIT.md`

---

## Step 0.2: Remove Deprecated Components

**Duration:** 2-3 days  
**Goal:** Clean up observer system of dead code

### 0.2.1: Confirm GUILogger Removal

```bash
# Search for any remaining GUILogger references
grep -r "GUILogger" src/
grep -r "gui_logger" src/

# If found, remove all references
# Document what was removed in audit
```

### 0.2.2: Resolve GUIObserver Status

Based on audit findings:

**If truly deprecated:**
```bash
# Remove the file
git rm src/econsim/observability/gui_observer.py

# Remove all imports
grep -r "from.*GUIObserver\|import.*GUIObserver" src/ --include="*.py"
# Edit each file to remove the import

# Remove all instantiations
grep -r "GUIObserver()" src/ --include="*.py"
# Edit each file to remove the instantiation
```

**If still needed:**
- Remove "deprecated" comments
- Document why it's still needed
- Update docstrings to clarify current purpose

**If partially needed:**
- Extract useful parts
- Remove deprecated parts
- Update documentation

### 0.2.3: Clean Up Legacy Event Classes

```bash
# Find event class definitions
grep -r "class.*Event" src/econsim/observability/ --include="*.py"

# For each event class:
# 1. Check if it's used anywhere
# 2. If unused, remove it
# 3. If used, document what remains and why
```

### 0.2.4: Remove Obsolete Observer Types

```bash
# Look for duplicate functionality
grep -r "class.*Observer" src/econsim/observability/ --include="*.py"

# Consolidate if duplicates found
# Remove if truly obsolete
```

### 0.2.5: Update Import Statements

After removing components:

```bash
# Run tests to find broken imports
pytest tests/ -v

# Fix any import errors
# Update __init__.py files if needed
```

### 0.2.6: Success Criteria Check

- [ ] No "deprecated" comments in observer code
- [ ] All imports updated and working
- [ ] Tests still pass
- [ ] No dead code remaining
- [ ] All changes documented in audit

**Deliverable:** Clean observer codebase with no deprecated components

---

## Step 0.3: Formalize Event Schema

**Duration:** 2-3 days  
**Goal:** Create official event schema documentation

### 0.3.1: Audit FileObserver Events

```bash
# Find all record_ methods in FileObserver
grep -r "def record_" src/econsim/observability/ --include="*.py"

# For each record_ method, document:
# - Method name
# - Parameters
# - When it's called
# - What data it records
```

### 0.3.2: Create Schema File

Create `src/econsim/observability/event_schema.py`:

```python
"""Official event schema for VMT EconSim observability.

Schema Version: 1.0.0-dev
Note: Schema unstable during refactor. Versioning comes post-refactor.
"""

SCHEMA_VERSION = "1.0.0-dev"

# Document all event types
EVENT_TYPES = {
    "agent_move": {
        "description": "Agent moves from one position to another",
        "fields": {
            "step": {"type": int, "required": True, "description": "Simulation step"},
            "agent_id": {"type": int, "required": True, "description": "Agent identifier"},
            "from_pos": {"type": tuple, "required": True, "description": "Starting position (x, y)"},
            "to_pos": {"type": tuple, "required": True, "description": "Ending position (x, y)"},
            "mode": {"type": str, "required": True, "description": "Movement mode (foraging, trading, etc.)"}
        },
        "example": {
            "step": 42,
            "agent_id": 0,
            "from_pos": [10, 10],
            "to_pos": [11, 10],
            "mode": "foraging"
        }
    },
    # Add all other event types found in audit
}

# Event categories
EVENT_CATEGORIES = {
    "agent_events": ["agent_move", "agent_spawn", "agent_despawn"],
    "resource_events": ["resource_spawn", "resource_consumed"],
    "trade_events": ["trade_initiated", "trade_completed", "trade_failed"],
    "simulation_events": ["simulation_start", "simulation_end", "step_complete"]
}

def validate_event(event_data: dict) -> bool:
    """Validate event data against schema."""
    # Implementation to be added
    pass

def get_event_schema(event_type: str) -> dict:
    """Get schema for specific event type."""
    return EVENT_TYPES.get(event_type, {})
```

### 0.3.3: Document Complete Schema

For each event type found in the audit:

1. **Document fields:**
   - Field name
   - Data type
   - Required vs optional
   - Description

2. **Add examples:**
   - Real example from simulation
   - Edge cases if any

3. **Document when emitted:**
   - Which simulation component emits it
   - Under what conditions

### 0.3.4: Create Schema Documentation

Update `docs/SIMULATION_OUTPUT_SCHEMA.md`:

```markdown
# Simulation Output Schema

**Version:** 1.0.0-dev  
**Status:** Unstable during refactor  
**Last Updated:** 2025-10-03

## Overview

This document describes the event schema used by the observer system to record simulation state changes.

**Important:** Schema is unstable during refactor. All saved outputs will be invalidated by changes.

## Event Types

### Agent Events

#### agent_move
Records when an agent moves from one position to another.

**Fields:**
- `step` (int, required): Simulation step number
- `agent_id` (int, required): Unique agent identifier  
- `from_pos` (tuple, required): Starting position [x, y]
- `to_pos` (tuple, required): Ending position [x, y]
- `mode` (str, required): Movement mode

**Example:**
```json
{
  "step": 42,
  "agent_id": 0,
  "from_pos": [10, 10],
  "to_pos": [11, 10],
  "mode": "foraging"
}
```

[Continue for all event types...]

## Schema Evolution

During refactor:
- Schema can change freely
- No migration needed
- All old outputs invalidated
- Version locked at release candidate
```

### 0.3.5: Success Criteria Check

- [ ] All event types documented in schema file
- [ ] Schema file created and functional
- [ ] Examples provided for each event type
- [ ] Documentation updated
- [ ] Ready for use in Phase 2

**Deliverable:** 
- `src/econsim/observability/event_schema.py`
- `docs/SIMULATION_OUTPUT_SCHEMA.md`

---

## Step 0.4: Consolidate Observer Responsibilities

**Duration:** 2 days  
**Goal:** Ensure FileObserver is production-ready

### 0.4.1: Create Test Suite

Create `tests/observability/test_file_observer.py`:

```python
"""Tests for FileObserver functionality."""

import pytest
import tempfile
import json
from pathlib import Path
from econsim.observability.file_observer import FileObserver


class TestFileObserver:
    """Test FileObserver recording and output format."""
    
    def test_file_observer_records_events(self):
        """Test that FileObserver captures all events."""
        with tempfile.TemporaryDirectory() as temp_dir:
            observer = FileObserver(output_dir=Path(temp_dir))
            
            # Simulate some events
            observer.record_agent_move(step=1, agent_id=0, from_pos=(0, 0), to_pos=(1, 0), mode="foraging")
            observer.record_trade_initiated(step=2, agent_id=0, other_agent_id=1, resource_type="food")
            
            # Verify events were recorded
            output_files = list(Path(temp_dir).glob("*.jsonl"))
            assert len(output_files) == 1
            
            # Read and verify content
            with open(output_files[0]) as f:
                lines = f.readlines()
                assert len(lines) == 2
                
                # Verify first event
                event1 = json.loads(lines[0])
                assert event1["event_type"] == "agent_move"
                assert event1["step"] == 1
                assert event1["agent_id"] == 0
    
    def test_file_observer_output_format(self):
        """Test output format matches schema."""
        # Test that all recorded events match the schema
        pass
    
    def test_file_observer_handles_errors(self):
        """Test graceful error handling."""
        # Test behavior with invalid data
        # Test behavior with disk full
        # Test behavior with permission errors
        pass
    
    def test_file_observer_performance(self):
        """Test performance requirements."""
        # Test that recording is fast enough (<0.01ms/event)
        pass
```

### 0.4.2: Run FileObserver in Real Simulation

Create `scripts/test_file_observer_real.py`:

```python
"""Test FileObserver with real simulation."""

from pathlib import Path
from econsim.simulation import Simulation
from econsim.observability.file_observer import FileObserver
from econsim.tools.launcher.framework.test_configuration import get_test_by_name

def test_file_observer_real_simulation():
    """Run 1000 steps of simulation with FileObserver."""
    
    # Get test configuration
    config = get_test_by_name("basic_foraging")
    
    # Create output directory
    output_dir = Path("tmp_observer_test")
    output_dir.mkdir(exist_ok=True)
    
    # Create simulation
    simulation = Simulation.from_config(config)
    
    # Attach FileObserver
    observer = FileObserver(output_dir=output_dir)
    simulation.attach_observer(observer)
    
    # Run simulation
    print("Running 1000 steps with FileObserver...")
    for step in range(1000):
        simulation.step()
        if step % 100 == 0:
            print(f"Completed step {step}")
    
    # Verify output
    output_files = list(output_dir.glob("*.jsonl"))
    assert len(output_files) == 1
    
    # Count events
    with open(output_files[0]) as f:
        event_count = sum(1 for line in f)
    
    print(f"Recorded {event_count} events")
    print(f"Output file size: {output_files[0].stat().st_size} bytes")
    
    # Cleanup
    import shutil
    shutil.rmtree(output_dir)
    
    print("✓ FileObserver real simulation test passed")

if __name__ == "__main__":
    test_file_observer_real_simulation()
```

### 0.4.3: Performance Testing

```bash
# Run the real simulation test
python scripts/test_file_observer_real.py

# Measure performance
time python scripts/test_file_observer_real.py

# Check file size and event count
# Verify performance is acceptable (<0.01ms/event)
```

### 0.4.4: Document Issues

Create `tmp_plans/CURRENT/CRITICAL/FILE_OBSERVER_ISSUES.md`:

```markdown
# FileObserver Issues and Status

**Date:** 2025-10-03  
**Status:** Testing in progress

## Performance Results
- **Event count:** [to be filled]
- **File size:** [to be filled]  
- **Time per event:** [to be filled]
- **Acceptable:** Yes/No

## Issues Found
- [ ] List any file format problems
- [ ] List any missing events
- [ ] List any performance concerns

## Fixes Applied
- [ ] List any fixes made during testing

## Status
- [ ] FileObserver test suite passes
- [ ] Real simulation test successful
- [ ] Output format validated
- [ ] Performance acceptable
```

### 0.4.5: Success Criteria Check

- [ ] FileObserver test suite passes
- [ ] Real simulation test successful
- [ ] Output format validated
- [ ] Performance acceptable (<0.01ms/event)
- [ ] Any issues documented and resolved

**Deliverable:** Production-ready FileObserver with comprehensive tests

---

## Step 0.5: Observer Documentation

**Duration:** 1-2 days  
**Goal:** Document observer system for Phase 2 developers

### 0.5.1: Create Observer Guide

Create `docs/OBSERVABILITY_GUIDE.md`:

```markdown
# Observability Guide

**Version:** 1.0  
**Last Updated:** 2025-10-03

## Overview

The observer system provides a clean way to record simulation events for analysis, playback, and visualization.

## How It Works

### Observer Pattern
The simulation emits events as it runs. Observers can be attached to receive these events.

### Event Flow
1. Simulation performs action (agent moves, trade occurs, etc.)
2. Simulation emits event with relevant data
3. All attached observers receive the event
4. Observers process event (record to file, update GUI, etc.)

## Available Observers

### FileObserver
Records all events to JSONL files for later analysis.

**Usage:**
```python
from econsim.observability.file_observer import FileObserver
from pathlib import Path

observer = FileObserver(output_dir=Path("sim_output"))
simulation.attach_observer(observer)
```

**Output Format:**
- One JSONL file per simulation run
- Each line is a JSON event
- Events ordered by simulation step

### Custom Observers
You can create custom observers by implementing the Observer interface.

## Event Schema

See [Simulation Output Schema](SIMULATION_OUTPUT_SCHEMA.md) for complete event documentation.

## Best Practices

1. **Attach observers before starting simulation**
2. **Use FileObserver for recording, custom observers for real-time processing**
3. **Check event schema before processing events**
4. **Handle errors gracefully in custom observers**

## Examples

### Basic Recording
```python
# Record simulation to file
observer = FileObserver(output_dir=Path("my_simulation"))
simulation.attach_observer(observer)
simulation.run(max_steps=1000)
```

### Custom Observer
```python
class MyObserver:
    def notify(self, event):
        if event["event_type"] == "agent_move":
            print(f"Agent {event['agent_id']} moved to {event['to_pos']}")

simulation.attach_observer(MyObserver())
```

## Troubleshooting

### Common Issues
- **No events recorded:** Check observer is attached before simulation starts
- **Large file sizes:** Consider filtering events or using compression
- **Performance issues:** Profile observer code, consider async processing

### Getting Help
- Check event schema documentation
- Review test examples in `tests/observability/`
- See implementation in `src/econsim/observability/`
```

### 0.5.2: Update Code Comments

For each observer file:

1. **Remove confusing legacy comments**
2. **Add clear docstrings**
3. **Document observer lifecycle**
4. **Add usage examples**

Example docstring update:

```python
class FileObserver:
    """Records simulation events to JSONL files.
    
    This observer captures all simulation events and writes them to
    JSONL (JSON Lines) format files for later analysis and playback.
    
    Usage:
        observer = FileObserver(output_dir=Path("output"))
        simulation.attach_observer(observer)
        simulation.run(max_steps=1000)
    
    Output:
        Creates timestamped JSONL files in the specified directory.
        Each line contains a JSON event object.
    """
```

### 0.5.3: Create Examples

Create `examples/observability/` directory with:

- `basic_recording.py` - Simple recording example
- `custom_observer.py` - Custom observer example  
- `event_analysis.py` - Analyzing recorded events
- `playback_example.py` - Loading and processing events

### 0.5.4: Success Criteria Check

- [ ] Observer guide complete and clear
- [ ] Code comments updated and helpful
- [ ] Examples provided and working
- [ ] Ready for Phase 2 use
- [ ] Documentation covers all observer types

**Deliverable:** 
- `docs/OBSERVABILITY_GUIDE.md`
- Updated code comments
- Working examples

---

## Phase 0 Exit Criteria

Before proceeding to Phase 1, verify ALL criteria are met:

### Technical Requirements
- [ ] All deprecated components removed or documented
- [ ] Event schema formalized and documented
- [ ] FileObserver tested and production-ready
- [ ] No confusing "deprecated" comments remain
- [ ] All observer tests pass

### Documentation Requirements  
- [ ] Observer system audit complete
- [ ] Event schema documented
- [ ] Observer guide written
- [ ] Code comments clear
- [ ] Examples provided

### Process Requirements
- [ ] All deliverables created
- [ ] Git checkpoint ready to create
- [ ] REFACTOR_STATUS.md updated
- [ ] Ready for Phase 2 use

### Git Checkpoint Creation

```bash
# Verify all tests pass
pytest tests/observability/ -v

# Verify no deprecated code remains
grep -r "deprecated" src/econsim/observability/ --include="*.py"
# Should return nothing or only documentation

# Create completion checkpoint
git add .
git commit -m "Phase 0 complete: Observer system cleaned and documented"
git tag refactor-post-phase0 -m "Observer system cleanup complete"
git push origin refactor-post-phase0
```

### Final Status Update

Update `REFACTOR_STATUS.md`:

```markdown
## Phase 0: Observer System Cleanup
- **Status:** ✅ Complete
- **Completed:** 2025-10-17
- **Duration:** 2 weeks
- **Git Checkpoint:** refactor-post-phase0

### What's Working
- ✅ Clean observer system with no deprecated code
- ✅ Formalized event schema documented
- ✅ FileObserver production-ready and tested
- ✅ Complete documentation and examples
- ✅ All observer tests passing

### Ready for Phase 1
- ✅ Observer system is clean foundation
- ✅ Event schema ready for output architecture
- ✅ FileObserver ready for SimulationRecorder integration
```

---

## Risk Mitigation

### If Tests Fail
1. **Don't create post-phase checkpoint**
2. **Fix issues before proceeding**
3. **Document any changes needed**
4. **Re-run all tests**

### If Performance Issues Found
1. **Profile FileObserver performance**
2. **Optimize if needed**
3. **Document performance characteristics**
4. **Ensure <0.01ms/event requirement met**

### If Schema Issues Found
1. **Document all issues**
2. **Fix schema before proceeding**
3. **Update documentation**
4. **Re-test with real simulation**

---

## Success Metrics

### Quantitative
- **Observer files:** All documented and clean
- **Test coverage:** 100% of observer functionality
- **Performance:** <0.01ms per event recorded
- **Documentation:** Complete guide and examples

### Qualitative
- **Code clarity:** No confusing comments or deprecated code
- **Schema clarity:** All events documented with examples
- **Usability:** Clear guide for Phase 2 developers
- **Maintainability:** Clean, well-documented codebase

---

## Next Phase Preparation

After Phase 0 completion:

1. **Review Phase 1 plan** in ACTIONABLE_REFACTORING_PLAN_V2.md
2. **Understand GUI will break** in Phase 1 (expected)
3. **Prepare for coupling analysis** (Step 1.1)
4. **Set up Phase 1 workspace** and documentation

**Remember:** Phase 0 success enables Phase 2. Observer system must be production-ready.

---

**Document Status:** Ready for execution  
**Next Action:** Create `refactor-pre-phase0` tag and begin Step 0.1  
**Reference:** See ACTIONABLE_REFACTORING_PLAN_V2.md for complete context
