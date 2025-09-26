# Comprehensive Debug Logging System for VMT EconSim

## Overview
The VMT EconSim now includes a comprehensive debug logging system that provides detailed visibility into simulation behavior for educational purposes and debugging. The system generates rich, timestamped log files and displays them in real-time debug panels within all manual tests.

## Features

### 🎯 **Centralized Logging System**
- **Location**: `src/econsim/gui/debug_logger.py`
- **Log Directory**: `gui_logs/` (project root)
- **Format**: Timestamped files (`YYYY-MM-DD HH-MM-SS GUI.log`)
- **Thread-safe**: Singleton pattern with locking

### 📊 **Comprehensive Event Tracking**
The system logs multiple categories of events:

1. **Simulation Steps**
   - Step-by-step progression with START/END markers
   - Agent count, resource count, decision mode status
   - Resource dynamics (collection, respawn, depletion)

2. **Agent Behaviors**
   - Mode transitions: `idle` ↔ `forage` ↔ `return_home` ↔ `move_to_partner`
   - Decision-making details and reasoning
   - Carrying status and deposits

3. **Phase Transitions**
   - Manual test phase changes with descriptions
   - Environment flag updates (foraging/trading enabled/disabled)
   - Turn-based progression tracking

4. **Trading Activities**
   - Trade drafts and executions
   - Partner selection and negotiation
   - Trade outcomes and fairness metrics

5. **Resource Events**
   - Resource pickup and deposit events
   - Respawn activities and locations
   - Resource type distributions

### 🔧 **Environment Variables**
Enable specific logging categories:

```bash
# Agent mode transitions (idle, forage, return_home, move_to_partner)
ECONSIM_DEBUG_AGENT_MODES=1

# Trading system debugging
ECONSIM_DEBUG_TRADES=1

# General simulation events and step progression
ECONSIM_DEBUG_SIMULATION=1

# Phase transition logging in manual tests
ECONSIM_DEBUG_PHASES=1

# Agent decision-making details
ECONSIM_DEBUG_DECISIONS=1

# Resource-related events (pickup, deposit, spawn)
ECONSIM_DEBUG_RESOURCES=1
```

### 🎮 **Manual Test Integration**
All 7 manual tests now include:

1. **Debug Panel** (left side of UI)
   - Real-time log file display
   - Auto-scrolling to latest content
   - 300px width, monospace font
   - Updates every 250ms

2. **Comprehensive Debug Flags**
   - All debug categories enabled by default
   - Automatic activation when starting tests
   - Phase transition logging integrated

3. **Enhanced UI Layout**
   - Debug panel | Pygame viewport | Control panel
   - Consistent across all manual tests
   - Proper cleanup on close

## Usage

### 🚀 **Quick Start**
```bash
# Run any manual test with full debug logging
cd /path/to/vmt
source vmt-dev/bin/activate
python MANUAL_TESTS/test_1_baseline_simple.py
```

### 📝 **Log File Example**
```log
VMT EconSim GUI Debug Log
Session started: 2025-09-26 16:17:53
==================================================

[16:17:57.908] [Step 1] SIMULATION: === SIMULATION STEP 1 START ===
[16:17:57.908] [Step 1] SIMULATION: Agents: 20, Resources: 200, Decision Mode: True
[16:17:57.909] AGENT_MODE: Agent 2 mode: return_home -> forage (deposited, both forage+trade enabled)
[16:17:57.917] AGENT_MODE: Agent 15 mode: return_home -> forage (deposited, both forage+trade enabled)
[16:17:57.918] AGENT_MODE: Agent 18 mode: return_home -> forage (deposited, both forage+trade enabled)
[16:17:57.919] [Step 1] SIMULATION: === SIMULATION STEP 1 END ===
[16:17:57.922] [Step 2] SIMULATION: === SIMULATION STEP 2 START ===
[16:17:57.922] [Step 2] SIMULATION: Agents: 20, Resources: 201, Decision Mode: True
...
```

### 🔍 **Debugging Specific Issues**
```bash
# Agent behavior debugging
ECONSIM_DEBUG_AGENT_MODES=1 python MANUAL_TESTS/test_1_baseline_simple.py

# Trade system debugging
ECONSIM_DEBUG_TRADES=1 python MANUAL_TESTS/test_1_baseline_simple.py

# Full comprehensive logging (default in manual tests)
ECONSIM_DEBUG_AGENT_MODES=1 \
ECONSIM_DEBUG_TRADES=1 \
ECONSIM_DEBUG_SIMULATION=1 \
ECONSIM_DEBUG_PHASES=1 \
ECONSIM_DEBUG_DECISIONS=1 \
ECONSIM_DEBUG_RESOURCES=1 \
python MANUAL_TESTS/test_1_baseline_simple.py
```

## Educational Benefits

### 👨‍🏫 **For Instructors**
- **Real-time visibility** into agent behavior patterns
- **Phase-by-phase analysis** of different economic scenarios  
- **Detailed logs** for post-session analysis and discussion
- **Troubleshooting** simulation issues during class

### 👨‍🎓 **For Students**
- **Visual feedback** on economic agent decision-making
- **Step-by-step understanding** of simulation progression
- **Data collection** for assignments and research
- **Debugging skills** for economic modeling

## Technical Implementation

### 🏗️ **Architecture**
- **Singleton logger** ensures unified output destination
- **Environment-based control** allows selective logging
- **Thread-safe operations** for GUI integration
- **File-based persistence** with GUI display mirroring

### 📁 **Key Files**
- `src/econsim/gui/debug_logger.py` - Core logging system
- `src/econsim/simulation/world.py` - Step-level logging
- `src/econsim/simulation/agent.py` - Agent mode logging  
- `MANUAL_TESTS/test_*.py` - Debug panel integration
- `gui_logs/*.log` - Generated log files

### ⚡ **Performance**
- **Minimal overhead** when debug flags disabled
- **Efficient file I/O** with buffered writes
- **Real-time updates** without blocking simulation
- **Automatic cleanup** of UI timers on close

## Troubleshooting

### ❓ **Common Issues**
1. **Empty log files**: Ensure debug environment variables are set to "1"
2. **Missing debug panel**: Check that manual test UI layout includes debug_display
3. **Import errors**: Verify Python path includes src/ directory
4. **Performance impact**: Disable unused debug categories for faster execution

### 🛠️ **Debug the Debugger**
```python
# Test logging system directly
import sys, os
sys.path.insert(0, 'src')
from econsim.gui.debug_logger import get_gui_logger, log_simulation

os.environ['ECONSIM_DEBUG_SIMULATION'] = '1'
log_simulation('Test message')
print("Check gui_logs/ directory for output")
```

## Future Enhancements

- **Log filtering** by category in GUI panel
- **Export functionality** for classroom data collection
- **Statistical summaries** of agent behavior patterns
- **Visualization integration** with matplotlib/plotly
- **Remote logging** for distributed classroom setups

---

*This comprehensive debug logging system transforms the VMT EconSim into a fully observable educational environment, enabling deep insights into agent-based economic modeling and providing rich data for both teaching and research purposes.*