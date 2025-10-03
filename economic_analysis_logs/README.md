# Economic Analysis Logs - Human Reader Guide

This directory contains **Phase 4E optimized** economic behavior logs from VMT simulations. The logs use advanced semantic compression, pattern recognition, and dictionary compression to achieve **90-95% size reduction** while preserving all information.

## 🎯 **GUI Translation Interface**

**Note**: These logs are optimized for machine processing. A GUI translation interface is available in `src/econsim/observability/serializers/gui_translator.py` to translate the compressed format back to full human readability with interactive visualization.

## 📁 Directory Structure

```
economic_analysis_logs/
├── TestName_YYYY-MM-DD_HH-MM-SS/     # Test run directories
│   ├── economic_events.jsonl         # Phase 4E semantic compressed events log
│   └── config.json                   # Configuration + compression dictionaries
├── README.md                         # This guide
└── [AVAILABLE] gui_translator.py     # GUI translation interface in src/
```

## 📊 Phase 4E Log Format Overview

Each line in `economic_events.jsonl` represents one simulation step with all economic events compressed using advanced semantic compression techniques.

### Basic Structure
```json
{
  "s": 1,                    // Step number
  "t0": 0.33,               // Base timestamp for this step (or "dt": 0.01 for delta)
  "c": "t0,1,9,10,14,16,21,25-27,29",  // Collection events (semantic compressed)
  "m": ["2,t0,0-5,7-10,14-16,18,21,22,24-29", [...]],  // Mode events (semantic compressed)
  "o": [...]                // Other events (semantic compressed)
}
```

## 🔍 Phase 4E Event Types

### Collection Events (`"c"`) - Semantic Compression
Records when agents collect resources with ultra-compact semantic compression.

**Phase 4E Formats:**
- `"t0,1,9,10,14,16,21,25-27,29"` - Ultra-compact string format
- `"t0"` - Time offset 0.0 (dictionary code)
- `"25-27"` - Range compression for agents 25,26,27
- Individual agents: `"1,9,10,14,16,21"`

**Example:**
```json
"c": "t0,1,9,10,14,16,21,25-27,29"
```
**Translation:** 
- Agents 1,9,10,14,16,21,25,26,27,29 collected resources at time 0.0
- Ultra-compact format eliminates JSON nesting overhead

### Mode Change Events (`"m"`) - Semantic Pattern Compression
Records mode changes with semantic compression and context-aware grouping.

**Phase 4E Formats:**
- `"2,t0,0-5,7-10,14-16,18,21,22,24-29"` - Pattern 2 with agent ranges
- `["t0",6,"fi","nta"]` - Individual mode change: Agent 6, forage→idle, no_target_available
- Mixed format: Pattern strings + individual event arrays

**Example:**
```json
"m": ["2,t0,0-5,7-10,14-16,18,21,22,24-29", [["t0",6,"fi","nta"], ["t0",12,"fi","nta"]]]
```
**Translation:**
- Pattern 2: Agents 0-5,7-10,14-16,18,21,22,24-29 executed Pattern 2 (forage→home, collected_resource)
- Individual: Agents 6,12 executed forage→idle transitions with no_target_available reason

## 🔤 Phase 4E Compression Dictionaries

### Dictionary Codes (Phase 4A+4E)
| Code | Value | Usage |
|------|-------|-------|
| `t0` | `0.0` | Common time offset (start of step) |
| `cr` | `collected_resource` | Most common reason (87% reduction) |
| `rs` | `resource_selection` | Resource selection reason (87% reduction) |
| `nta` | `no_target_available` | No targets found (82% reduction) |
| `rcf` | `resource_claimed_fallback` | Fallback resource claim (88% reduction) |
| `ccf` | `carrying_capacity_full` | Inventory full (86% reduction) |
| `fh` | `forage` → `home` | Found resource, going home |
| `hf` | `home` → `forage` | Left home, searching again |
| `fi` | `forage` → `idle` | No targets found, going idle |
| `if` | `idle` → `forage` | Leaving idle, searching again |
| `hi` | `home` → `idle` | Completed delivery, going idle |
| `ih` | `idle` → `home` | Leaving idle, returning home |

### Behavioral Pattern Codes (Phase 4C+4E)
| Code | Pattern | Description | Frequency |
|------|---------|-------------|-----------|
| `1` | `['hf', 'rs']` | Home→forage + resource_selection | 598 occurrences |
| `2` | `['fh', 'cr']` | Forage→home + collected_resource | 600 occurrences |
| `P3` | `['fi', 'nta']` | Forage→idle + no_target_available | Rare |
| `P4` | `['if', 'rs']` | Idle→forage + resource_selection | Very rare |
| `P5` | `['hi', 'dg']` | Home→idle + deposited_goods | 25 occurrences |

### Semantic Compression Features
- **Ultra-compact strings**: `"t0,1-5,7,9-12"` instead of nested arrays
- **Context inference**: Event type implied by position in step structure
- **Range compression**: `"1-5"` for sequential agent IDs
- **Pattern frequency optimization**: Most common patterns get shortest codes

## 📖 Phase 4E Reading Examples

### Example 1: Semantic Compression
```json
{"s":1,"t0":0.33,"c":"t0,1,9,10,14,16,21,25-27,29","m":["2,t0,0-5,7-10,14-16,18,21,22,24-29",[["t0",6,"fi","nta"],["t0",12,"fi","nta"]]]}
```

**Human Translation:**
- **Step 1** at timestamp 0.33:
  - **Collections:** Agents 1,9,10,14,16,21,25,26,27,29 collected resources at time 0.0
  - **Mode Changes:** 
    - Pattern 2: Agents 0-5,7-10,14-16,18,21,22,24-29 executed forage→home + collected_resource
    - Individual: Agents 6,12 executed forage→idle transitions (no_target_available)

### Example 2: Delta Time Compression
```json
{"s":2,"dt":0.02,"c":"t0,0,2-5,7-10,15,16,18,21,22,24-28","m":["2,t0,0,2-5,7-11,15,16,18,19,21,22,24-29","1,t0,1,9,10,14,16,21,25-27,29"]}
```

**Human Translation:**
- **Step 2** with delta time +0.02s:
  - **Collections:** Agents 0,2-5,7-10,15,16,18,21,22,24-28 collected resources at time 0.0
  - **Mode Changes:**
    - Pattern 2: Agents 0,2-5,7-11,15,16,18,19,21,22,24-29 executed forage→home + collected_resource
    - Pattern 1: Agents 1,9,10,14,16,21,25-27,29 executed home→forage + resource_selection

### Example 3: Mixed Semantic Format
```json
{"s":23,"dt":0.01,"c":"t0,0-4,7,16,19,24,27","m":["1,t0,0,2-5,7,8,15,16,18,19,24,25,27,28","2,t0,0-5,7,9,15,16,19,24,27",[["t0",22,"fh","rcf"],["t0",26,"fh","rcf"]]]}
```

**Human Translation:**
- **Step 23** with delta time +0.01s:
  - **Collections:** Agents 0-4,7,16,19,24,27 collected resources at time 0.0
  - **Mode Changes:**
    - Pattern 1: Agents 0,2-5,7,8,15,16,18,19,24,25,27,28 executed home→forage + resource_selection
    - Pattern 2: Agents 0-5,7,9,15,16,19,24,27 executed forage→home + collected_resource
    - Individual: Agents 22,26 executed forage→home transitions (resource_claimed_fallback)

## 🛠️ Tools for Analysis

### GUI Translation Interface
**Available**: `src/econsim/observability/serializers/gui_translator.py`

```python
from econsim.observability.serializers.gui_translator import LogFormatTranslator

# Translate compressed log to human-readable format
translator = LogFormatTranslator()
stats = translator.translate_log_file(
    input_path="economic_events.jsonl",
    output_path="human_readable_log.txt"
)
print(f"Translated {stats['total_steps']} steps with {stats['compression_ratio']:.1f}% compression")
```

### Command Line Tools

**View specific step:**
```bash
# Get step 5
sed -n '5p' economic_events.jsonl | jq .

# Get first 10 steps
head -10 economic_events.jsonl
```

**Count events by type:**
```bash
# Count collection events (semantic format)
grep -o '"c":"[^"]*"' economic_events.jsonl | wc -l

# Count mode change events (semantic format)
grep -o '"m":\[[^]]*\]' economic_events.jsonl | wc -l
```

**Find specific agent activity:**
```bash
# Find all events for agent 5 (semantic format)
grep '"c":"[^"]*5[^"]*"' economic_events.jsonl
grep '"m":\[[^]]*5[^]]*\]' economic_events.jsonl
```

### Python Analysis
```python
import json

# Load and analyze a step
with open('economic_events.jsonl', 'r') as f:
    for line in f:
        step = json.loads(line)
        
        # Handle semantic compression format
        collections = step.get('c', '')
        mode_changes = step.get('m', [])
        
        # Count agents in semantic format
        if isinstance(collections, str):
            agent_count = len(collections.split(',')) - 1  # Subtract timestamp
        else:
            agent_count = len(collections)
            
        print(f"Step {step['s']}: {agent_count} collections, {len(mode_changes)} mode change groups")
```

## 🎯 Common Patterns

### High Activity Steps
Steps with long `"c"` strings (many agents) indicate high resource collection activity.

### Mode Transition Patterns (Phase 4E)
- **Pattern 1** (`hf` + `rs`): Agent leaving home to search (most common)
- **Pattern 2** (`fh` + `cr`): Successful foraging cycle (most common)
- **Individual `fi` + `nta`**: Failed foraging (no targets available)
- **Individual `fh` + `rcf`**: Resource claimed fallback scenario

### Agent Behavior Analysis
- **Active Agents:** Frequent Pattern 1/2 cycles
- **Idle Agents:** Many individual `fi`/`nta` transitions  
- **Efficient Agents:** High collection count in `"c"` strings
- **Range patterns**: Sequential agent IDs indicate coordinated behavior

## 🔧 Troubleshooting

### Missing Events
If you don't see expected events:
1. Check the `config.json` for logging configuration
2. Verify the simulation had economic activity during that step
3. Some events might be in the `"o"` (other) category
4. Use GUI translator to convert semantic format to human-readable

### Timestamp Interpretation (Phase 4E)
- `t0`: Absolute timestamp when the step started
- `dt`: Delta time from previous step (more efficient for sequential steps)
- Time offsets in events: Relative to step timestamp (usually `t0` = 0.0)

### Performance Notes (Phase 4E)
- Long `"c"` strings indicate many agents collecting simultaneously
- Complex `"m"` arrays suggest diverse agent behaviors in the step
- Steps with only `"m"` events (no `"c"`) indicate planning/decision phases
- Range compression (`"1-5"`) indicates coordinated agent behavior

## 📈 Phase 4E Optimization Benefits

This advanced semantic compressed format provides:
- **90-95% size reduction** compared to verbose JSON (up from 85-90% in Level 2B)
- **Semantic compression** with context-aware inference
- **Ultra-compact string formats** eliminating JSON nesting overhead
- **Pattern frequency optimization** for most common behavioral sequences
- **Advanced dictionary compression** for frequent strings and values
- **Range compression** for sequential agent IDs
- **Delta time compression** for efficient timestamp handling
- **Faster I/O** for large simulation runs
- **Better machine parsing** with optimized semantic formats
- **Preserved information** - no data loss

## 🎯 GUI Translation Interface (Available)

A GUI translation interface is available in `src/econsim/observability/serializers/gui_translator.py`:
- **Translate compressed logs** back to human-readable format
- **Interactive visualization** of agent behaviors and patterns
- **Pattern analysis** showing behavioral sequences
- **Real-time decompression** of dictionary codes and patterns
- **Export capabilities** for analysis in other tools
- **Format migration** between different compression versions

The semantic compressed format prioritizes machine processing efficiency while the GUI translator provides full human readability and analysis capabilities.

## 🚀 Phase 4E Implementation Status

**✅ COMPLETE**: All Phase 4E semantic compression features are implemented and operational:
- Context-aware compression logic
- Semantic inference for event types and patterns
- Format migration tools for V5_SEMANTIC
- GUI translation interface for semantic format
- Comprehensive testing and validation

The system is now ready for production use with excellent compression results!