# Economic Behavior Analysis Report

**Analysis Date**: 2025-10-02 17:58:42
**Simulation Steps**: 100 (estimated)

## Simulation Configuration

- **Grid Size**: 12x12
- **Agents**: 5
- **Resources**: 83
- **Resource Density**: 57.6%

## Agent Preferences

- **Agent 0**: CobbDouglasPreference
  - Alpha: 0.80
  - Position: (1, 5)
  - Final Inventory: {'good1': 56, 'good2': 18}
  - Current Mode: AgentMode.RETURN_HOME

- **Agent 1**: CobbDouglasPreference
  - Alpha: 0.20
  - Position: (1, 8)
  - Final Inventory: {'good1': 18, 'good2': 49}
  - Current Mode: AgentMode.RETURN_HOME

- **Agent 2**: LeontiefPreference
  - Position: (2, 9)
  - Final Inventory: {}
  - Current Mode: AgentMode.IDLE

- **Agent 3**: PerfectSubstitutesPreference
  - Position: (2, 1)
  - Final Inventory: {'good1': 40, 'good2': 45}
  - Current Mode: AgentMode.RETURN_HOME

- **Agent 4**: CobbDouglasPreference
  - Alpha: 0.50
  - Position: (1, 5)
  - Final Inventory: {'good1': 37, 'good2': 38}
  - Current Mode: AgentMode.FORAGE

## Event Analysis

- **Total Events**: 862
- **Event Types**:
  - agent_mode_change: 596
  - resource_collection: 265
  - trade_execution: 1

## Economic Patterns

- **Total Trades**: 1
- **Most Common Mode Transition**: forage -> return_home (301 times)
- **Resource Distribution**: {'unknown': 265}
- **Agent Activity**: {2: 1, 3: 168, 4: 147, 0: 147, 1: 133}

## Trading Analysis

Found 1 trades:
1. Step 96: Agent -1 -> Agent -1 ( for )
   Utility changes: Seller +0.000, Buyer +0.000

## Economic Insights

✅ **Resource Collection**: Agents are actively collecting resources (301 collections)

✅ **Resource Seeking**: Agents are actively seeking new resources (294 searches)

## Final Resource Distribution

- **Total Good1**: 151
- **Total Good2**: 150
- **Resource Utilization**: 301 total goods collected

## Recommendations

1. **Trading is Active**: Economic system appears to be functioning
2. **Monitor Utility**: Check if trades are providing positive utility gains
3. **Analyze Patterns**: Look for optimal trading strategies
