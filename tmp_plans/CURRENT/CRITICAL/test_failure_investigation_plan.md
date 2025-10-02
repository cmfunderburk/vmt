# Test Failure Investigation & Resolution Plan

**Date**: October 2, 2025  
**Status**: Post-Agent Refactor Test Cleanup  
**Objective**: Fix remaining 7 test failures after successful agent refactor

---

## Executive Summary

After successfully completing the agent refactor and removing 15 obsolete tests (Leontief prospecting + GUILogger), 7 legitimate test failures remain. This document outlines a systematic approach to investigate and resolve these failures while maintaining the integrity of the refactored architecture.

**Current Status**:
- ✅ Agent refactor complete (6 components extracted)
- ✅ Obsolete tests removed (15 tests for removed functionality)
- ⚠️ 7 legitimate test failures remain
- ✅ Core functionality: 394 tests passing

---

## Failure Analysis Summary

| Category | Count | Priority | Root Cause |
|----------|-------|----------|------------|
| **Mode Change Events** | 4 | 🔴 Critical | Observer pattern integration issues |
| **Agent State Transitions** | 1 | 🟡 High | Mode transition logic changes |
| **Performance Overhead** | 1 | 🟡 Medium | Component architecture overhead |
| **System Stability** | 1 | 🟢 Low | Behavior change (may be acceptable) |

---

## Phase 1: Mode Change Event Investigation (Priority 1)

### **Issue**: Observer Pattern Integration Failure
**Symptoms**: No mode change events being emitted during agent operations
**Impact**: Critical - affects event-driven architecture

### **Step 1.1: Verify Event Emitter Integration**
**Time Estimate**: 30 minutes

**Actions**:
1. Check if `AgentEventEmitter` is properly initialized in Agent
2. Verify `_set_mode()` calls the event emitter correctly
3. Test event emission in isolation

**Commands**:
```bash
# Test event emitter directly
python -c "
from econsim.simulation.components.event_emitter import AgentEventEmitter
from econsim.simulation.agent import Agent
from econsim.preferences.cobb_douglas import CobbDouglasPreference

# Test standalone event emitter
emitter = AgentEventEmitter(1)
print('Event emitter created successfully')

# Test agent integration
agent = Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
print(f'Agent event emitter: {hasattr(agent, \"_event_emitter\")}')
print(f'Event emitter type: {type(agent._event_emitter)}')
"
```

**Expected Result**: Event emitter properly initialized and accessible

### **Step 1.2: Test Mode Change Event Emission**
**Time Estimate**: 45 minutes

**Actions**:
1. Create minimal test to verify `_set_mode()` emits events
2. Check observer registry integration
3. Verify event buffer integration

**Test Script**:
```python
# Create test_manual_event_emission.py
from econsim.simulation.agent import Agent, AgentMode
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.observability.registry import ObserverRegistry

# Test manual mode change
agent = Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
registry = ObserverRegistry()

# Capture events
events = []
class TestObserver:
    def notify(self, event):
        events.append(event)

registry.register(TestObserver())

# Trigger mode change
agent._set_mode(AgentMode.RETURN_HOME, "test_reason", registry, 1)
print(f"Events captured: {len(events)}")
```

**Expected Result**: Events are captured and logged

### **Step 1.3: Investigate Observer Integration**
**Time Estimate**: 60 minutes

**Actions**:
1. Check if simulation properly sets up observer registry
2. Verify event buffer integration in step execution
3. Test end-to-end event flow

**Investigation Points**:
- Does `Simulation._observer_registry` get passed to agents?
- Are events being buffered correctly?
- Is the observer pattern working in the step execution pipeline?

### **Step 1.4: Fix Event Emission Issues**
**Time Estimate**: 90 minutes

**Potential Fixes**:
1. **Fix Observer Registry Integration**: Ensure agents receive observer registry
2. **Fix Event Buffer Integration**: Ensure events are properly buffered
3. **Fix Component Integration**: Ensure event emitter is called correctly

---

## Phase 2: Agent State Transition Investigation (Priority 2)

### **Issue**: Mode Transition Logic Changes
**Symptoms**: `maybe_deposit()` not triggering mode transitions correctly
**Impact**: High - affects core agent behavior

### **Step 2.1: Analyze `maybe_deposit()` Method**
**Time Estimate**: 30 minutes

**Actions**:
1. Examine current `maybe_deposit()` implementation
2. Check if it calls `_set_mode()` correctly
3. Verify state machine integration

**Investigation**:
```python
# Test maybe_deposit behavior
agent = Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
agent.mode = AgentMode.RETURN_HOME
agent.carrying["good1"] = 3
print(f"Before deposit: mode={agent.mode}, carrying={agent.carrying}")

agent.maybe_deposit()
print(f"After deposit: mode={agent.mode}, carrying={agent.carrying}")
```

### **Step 2.2: Check State Machine Integration**
**Time Estimate**: 45 minutes

**Actions**:
1. Verify state machine validates transitions correctly
2. Check if invalid transitions are being rejected
3. Test transition validation logic

### **Step 2.3: Fix Mode Transition Issues**
**Time Estimate**: 60 minutes

**Potential Fixes**:
1. **Fix `maybe_deposit()` Logic**: Ensure proper mode transitions
2. **Fix State Machine Validation**: Ensure valid transitions are allowed
3. **Fix Component Integration**: Ensure state machine is called correctly

---

## Phase 3: Performance Overhead Investigation (Priority 3)

### **Issue**: Component Architecture Overhead
**Symptoms**: 4.46ms overhead exceeds 1.5ms limit
**Impact**: Medium - performance regression

### **Step 3.1: Profile Component Overhead**
**Time Estimate**: 45 minutes

**Actions**:
1. Profile individual component initialization
2. Measure component method call overhead
3. Identify performance bottlenecks

**Commands**:
```bash
# Profile component performance
python -c "
import time
from econsim.simulation.agent import Agent
from econsim.preferences.cobb_douglas import CobbDouglasPreference

# Time agent creation
start = time.time()
for _ in range(1000):
    agent = Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5))
end = time.time()
print(f'Agent creation: {(end-start)*1000/1000:.2f}ms per agent')
"
```

### **Step 3.2: Optimize Component Performance**
**Time Estimate**: 90 minutes

**Potential Optimizations**:
1. **Lazy Component Initialization**: Initialize components only when needed
2. **Optimize Component Methods**: Reduce method call overhead
3. **Cache Frequently Used Values**: Avoid repeated calculations

### **Step 3.3: Update Performance Expectations**
**Time Estimate**: 30 minutes

**Actions**:
1. Evaluate if 4.46ms overhead is acceptable for architectural benefits
2. Update performance baseline if needed
3. Document performance trade-offs

---

## Phase 4: System Stability Investigation (Priority 4)

### **Issue**: Empty Grid Behavior Change
**Symptoms**: Agents stay in FORAGE mode instead of going IDLE
**Impact**: Low - may be acceptable new behavior

### **Step 4.1: Analyze Empty Grid Behavior**
**Time Estimate**: 30 minutes

**Actions**:
1. Understand why agents don't go IDLE on empty grid
2. Check if this is intentional behavior change
3. Evaluate if new behavior is acceptable

### **Step 4.2: Decide on Approach**
**Time Estimate**: 15 minutes

**Options**:
1. **Fix Behavior**: Make agents go IDLE on empty grid
2. **Update Test**: Accept new behavior as correct
3. **Document Change**: Explain why behavior changed

---

## Implementation Timeline

### **Day 1: Critical Issues (4-6 hours)**
- **Morning**: Phase 1.1-1.2 (Event Emitter Investigation)
- **Afternoon**: Phase 1.3-1.4 (Observer Integration Fix)

### **Day 2: High Priority Issues (3-4 hours)**
- **Morning**: Phase 2.1-2.2 (State Transition Analysis)
- **Afternoon**: Phase 2.3 (Mode Transition Fix)

### **Day 3: Medium/Low Priority (2-3 hours)**
- **Morning**: Phase 3.1-3.2 (Performance Investigation)
- **Afternoon**: Phase 4.1-4.2 (System Stability Analysis)

---

## Risk Assessment

### **High Risk**
- **Observer Pattern Integration**: May require significant changes to event flow
- **State Machine Integration**: May affect core agent behavior

### **Medium Risk**
- **Performance Overhead**: May require architectural changes
- **Test Updates**: May reveal additional integration issues

### **Low Risk**
- **System Stability**: Likely just behavior change documentation

---

## Success Criteria

### **Phase 1 Success**
- ✅ Mode change events are emitted correctly
- ✅ Observer pattern integration works
- ✅ All 4 mode change event tests pass

### **Phase 2 Success**
- ✅ Agent state transitions work correctly
- ✅ `maybe_deposit()` triggers proper mode changes
- ✅ State machine validation works as expected

### **Phase 3 Success**
- ✅ Performance overhead is acceptable or optimized
- ✅ Component architecture maintains good performance
- ✅ Performance test passes or expectations updated

### **Phase 4 Success**
- ✅ Empty grid behavior is understood and documented
- ✅ System stability test passes or is updated
- ✅ Behavior change is justified and documented

---

## Rollback Plan

### **If Critical Issues Cannot Be Resolved**
1. **Document Issues**: Create detailed issue report
2. **Preserve Working State**: Ensure current functionality works
3. **Plan Alternative Approach**: Consider different integration strategy

### **If Performance Issues Are Unacceptable**
1. **Profile Deeply**: Identify specific performance bottlenecks
2. **Optimize Components**: Reduce component overhead
3. **Consider Hybrid Approach**: Keep some functionality in Agent class

---

## Next Steps

1. **Review and Approve Plan**: Discuss approach and priorities
2. **Begin Phase 1**: Start with mode change event investigation
3. **Daily Check-ins**: Review progress and adjust approach as needed
4. **Document Findings**: Create detailed issue reports for each failure

---

**Status**: Ready for implementation discussion and approval
