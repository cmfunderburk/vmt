# VMT EconSim GUI Debug Logs

This directory contains timestamped debug logs from VMT EconSim GUI sessions. The logging system has been optimized for **conciseness and high signal-to-noise ratio**, achieving 90%+ size reduction while preserving all educational and debugging value.

## 📋 Quick Reference

### Log Format Types
- **LEGACY**: Full verbose format (original)
- **COMPACT**: 60-85% shorter messages, high readability
- **STRUCTURED**: Machine-parseable `CATEGORY|STEP|MESSAGE` format

### Log Levels
- **CRITICAL**: Errors, warnings, phase transitions only
- **EVENTS**: + trades, utility changes, agent mode switches
- **PERIODIC**: + step summaries every 25 steps, performance windows  
- **VERBOSE**: Everything (classic behavior)

## 🔧 Configuration

Control logging via environment variables:

```bash
# Default: Everything in optimized compact format (92% size reduction)
make enhanced-tests

# Balanced: Lighter logging for faster analysis
ECONSIM_LOG_LEVEL=EVENTS make enhanced-tests

# Minimal: Critical events only (phase transitions, errors)
ECONSIM_LOG_LEVEL=CRITICAL make enhanced-tests

# Legacy: Original verbose format (for compatibility)
ECONSIM_LOG_FORMAT=LEGACY make enhanced-tests
```

## 📖 Reading Compact Format

### Header Information
The log header shows active configuration:
```
VMT EconSim GUI Debug Log
Session started: 2025-09-26 21:06:10
Log Level: VERBOSE | Format: COMPACT    ← Default since optimization
==================================================
```

### Message Types

#### **Agent Mode Switches**
```
Format: A{ID}: {old_mode}→{new_mode} c{carrying} @({x},{y})

Examples:
 A002: return_home→forage c1 @(9,14)     # Agent 002 starts foraging, carrying 1 unit
 A015: forage→return_home c0 @(5,17)     # Agent 015 returns home, no items
 A008: idle→forage c12 @(2,1)            # Agent 008 starts foraging with 12 units
```

#### **Phase Transitions**
```
Format: PHASE{N}@{turn}: {description}

Examples:
PHASE2@201: Forage only (turns 201-400)
PHASE3@401: Exchange only (turns 401-600)  
PHASE4@601: Both disabled (turns 601-650)
PHASE5@651: Both enabled (turns 651-850)
```

#### **Trade Execution**
```
Format: S{step} T: A{seller}↔A{buyer} {give_resource}→{receive_resource} +{utility_gain}

Examples:
S20 T: A001↔A009 good2→good1 +0.0        # Step 20: Agent 001 trades good2 for good1
S157 T: A001↔A016 good1→good2 +0.4       # Step 157: Positive utility gain of 0.4
S298 T: A005↔A012 resource→material -0.1  # Step 298: Slight utility loss
```

#### **Utility Changes**
```
Format: S{step} U: A{agent} {old}→{new} Δ{change} ({reason})

Examples:
S20 U: A001 4.42→4.34 Δ-0.08 (trade)     # Agent 001 loses utility from trade
S20 U: A009 5.10→5.21 Δ+0.12 (trade)     # Agent 009 gains utility from same trade
S150 U: A005 12.5→15.3 Δ+2.8 (forage)    # Agent 005 gains from foraging
```

#### **Performance Metrics** *(PERIODIC/VERBOSE levels only)*
```
Format: S{step} P: {rate}s/s {frame_time}ms R{resources}

Examples:
S25 P: 124.7s/s 5.1ms R122              # Step 25: 124.7 steps/sec, 122 resources
S50 P: 98.3s/s 8.2ms R145               # Step 50: Performance drop, more resources
```

## 📊 Size Comparison

| **Format** | **Typical Size** | **Use Case** |
|------------|------------------|--------------|
| LEGACY + VERBOSE | 800KB | Legacy compatibility, detailed debugging |
| COMPACT + EVENTS | 65KB | **Recommended**: Analysis and review |
| COMPACT + PERIODIC | 85KB | Educational use with performance data |
| COMPACT + CRITICAL | 15KB | Monitoring and error detection |

## 🔍 Analysis Tips

### Finding Specific Events
```bash
# Phase transitions
grep "PHASE" logfile.log

# All trades in step range 100-200  
grep "S[12][0-9][0-9] T:" logfile.log

# Agent mode changes for specific agent
grep "A007:" logfile.log

# Utility losses (negative deltas)
grep "Δ-" logfile.log

# High-value trades (utility > 1.0)
grep "T:.*+[1-9]" logfile.log
```

### Message Counts
```bash
# Count message types
echo "Mode switches: $(grep -c 'A[0-9][0-9][0-9]:' logfile.log)"
echo "Trades: $(grep -c ' T:' logfile.log)" 
echo "Phase transitions: $(grep -c 'PHASE' logfile.log)"
echo "Utility changes: $(grep -c ' U:' logfile.log)"
```

### Educational Analysis
```bash
# Trade activity by phase
grep -A5 -B5 "PHASE" logfile.log

# Agent behavior patterns  
grep "A001:" logfile.log | head -20

# Economic efficiency (positive utility trades)
grep "T:.*+[0-9]" logfile.log | wc -l
```

## 🎯 Educational Value

The compact format preserves all key information for educational analysis:

- **Agent Decision Patterns**: Mode switches show foraging vs trading behavior
- **Market Dynamics**: Trade frequency and utility outcomes across phases  
- **Economic Efficiency**: Positive vs negative utility changes reveal market health
- **Spatial Behavior**: Agent positions show clustering and resource distribution
- **Phase Transitions**: Clear demarcation of different behavioral regimes

## 🚀 Performance Impact

The optimized logging system provides:
- **92% size reduction** compared to legacy format
- **Faster log parsing** due to consistent message structure
- **Reduced I/O overhead** during simulation execution
- **Better readability** for human analysis
- **Machine parseable** for automated analysis tools

## 📝 Session Management

Each log session is automatically finalized to prevent post-completion noise:
```
[21:06:45.123] SESSION: === LOG SESSION ENDED ===
```
Messages after this marker indicate cleanup activity and can be ignored for analysis.

## ⚙️ Implementation Details

- **Thread-safe logging** with singleton pattern
- **Conditional message filtering** based on log level
- **Automatic trade aggregation** for multi-trade steps (COMPACT format)
- **Performance-aware logging** (every 25 steps or >10% rate change)
- **Educational markers** (phase transitions) always logged regardless of level

---

*Generated by VMT EconSim optimized logging system - achieving conciseness without sacrificing educational value.*