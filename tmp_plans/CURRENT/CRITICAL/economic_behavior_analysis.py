#!/usr/bin/env python3
"""Economic Behavior Analysis - Comprehensive Economic Logic Review

This script runs a comprehensive economic analysis of the simulation to identify
economic behavior patterns, utility optimization, and potential issues in the
economic model.

Usage:
    python economic_behavior_analysis.py
"""

import os
import sys
import time
import json
from pathlib import Path
from collections import defaultdict, Counter

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from econsim.observability import (
    ObserverRegistry, ObservabilityConfig, 
    initialize_global_observer_logger
)
from econsim.observability.observers.file_observer import FileObserver
from econsim.simulation.world import Simulation
from econsim.simulation.grid import Grid
from econsim.simulation.agent import Agent
from econsim.simulation.respawn import RespawnScheduler
from econsim.simulation.metrics import MetricsCollector
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.preferences.leontief import LeontiefPreference
from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference
import random


def create_economic_test_scenario() -> Simulation:
    """Create a comprehensive economic test scenario."""
    # Create output directory
    output_dir = Path("economic_analysis_logs")
    output_dir.mkdir(exist_ok=True)
    
    # Create medium-sized grid
    grid = Grid(12, 12)
    
    # Add resources (60% density)
    for i in range(86):  # 60% of 144 cells
        x = (i * 7) % grid.width
        y = (i * 11) % grid.height
        grid.add_resource(x, y, "A" if i % 2 == 0 else "B")
    
    # Create agents with diverse preferences
    agents = [
        Agent(id=0, x=2, y=2, preference=CobbDouglasPreference(alpha=0.8)),   # Strong good1 preference
        Agent(id=1, x=9, y=2, preference=CobbDouglasPreference(alpha=0.2)),   # Strong good2 preference
        Agent(id=2, x=2, y=9, preference=LeontiefPreference()),               # Perfect complements
        Agent(id=3, x=9, y=9, preference=PerfectSubstitutesPreference()),     # Perfect substitutes
        Agent(id=4, x=6, y=6, preference=CobbDouglasPreference(alpha=0.5)),   # Balanced
    ]
    
    sim = Simulation(grid=grid, agents=agents, config=None)
    
    # Set up comprehensive logging
    config = ObservabilityConfig()
    log_path = output_dir / "economic_behavior_analysis.jsonl"
    file_observer = FileObserver(
        config=config,
        output_path=log_path,
        buffer_size=500,
        format='jsonl'
    )
    sim._observer_registry.register(file_observer)
    
    # Add dynamic systems
    sim._rng = random.Random(42)
    sim.respawn_scheduler = RespawnScheduler(
        target_density=0.6, max_spawn_per_tick=8, respawn_rate=0.4
    )
    sim.metrics_collector = MetricsCollector()
    
    print(f"✅ Economic test scenario created")
    print(f"   📄 Log file: {log_path}")
    print(f"   👥 Agents: {len(agents)} with diverse preferences")
    print(f"   🗺️  Grid: {grid.width}x{grid.height}")
    print(f"   📦 Resources: {grid.resource_count()}")
    
    return sim


def run_economic_analysis(sim: Simulation, steps: int = 100) -> None:
    """Run comprehensive economic analysis."""
    # Set up environment variables for comprehensive logging
    os.environ["ECONSIM_DEBUG_AGENT_MODES"] = "1"
    os.environ["ECONSIM_DEBUG_TRADES"] = "1"
    os.environ["ECONSIM_DEBUG_DECISIONS"] = "1"
    os.environ["ECONSIM_DEBUG_RESOURCES"] = "1"
    os.environ["ECONSIM_DEBUG_SIMULATION"] = "1"
    os.environ["ECONSIM_LOG_LEVEL"] = "DEBUG"
    os.environ["ECONSIM_LOG_FORMAT"] = "STRUCTURED"
    os.environ["ECONSIM_LOG_CATEGORIES"] = "ALL"
    
    # Enable trading for economic analysis
    os.environ["ECONSIM_FORAGE_ENABLED"] = "1"
    os.environ["ECONSIM_TRADE_DRAFT"] = "1"
    os.environ["ECONSIM_TRADE_EXEC"] = "1"
    
    print(f"🚀 Running economic analysis for {steps} steps...")
    
    start_time = time.time()
    
    # Run simulation
    rng = random.Random(12345)
    for step in range(steps):
        sim.step(rng)
        
        # Print progress every 20 steps
        if step % 20 == 0:
            elapsed = time.time() - start_time
            print(f"   Step {step:3d}/{steps} ({elapsed:.1f}s elapsed)")
    
    total_time = time.time() - start_time
    
    print(f"✅ Economic analysis complete")
    print(f"   ⏱️  Total time: {total_time:.2f}s")
    print(f"   📈 Steps/sec: {steps/total_time:.1f}")


def analyze_economic_behavior(log_file: Path) -> dict:
    """Analyze economic behavior from log data."""
    if not log_file.exists():
        return {"error": "Log file not found"}
    
    # Parse log events
    events = []
    with open(log_file, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    event = json.loads(line)
                    events.append(event)
                except json.JSONDecodeError:
                    continue
    
    # Analyze events
    analysis = {
        "total_events": len(events),
        "event_types": Counter(event.get("event_type", "unknown") for event in events),
        "agent_behavior": defaultdict(list),
        "resource_activity": defaultdict(int),
        "trading_activity": [],
        "mode_transitions": defaultdict(int),
        "economic_patterns": {}
    }
    
    # Analyze agent behavior
    for event in events:
        event_type = event.get("event_type", "")
        agent_id = event.get("agent_id", -1)
        
        if event_type == "agent_mode_change":
            old_mode = event.get("old_mode", "")
            new_mode = event.get("new_mode", "")
            reason = event.get("reason", "")
            
            analysis["agent_behavior"][agent_id].append({
                "step": event.get("step", 0),
                "transition": f"{old_mode} -> {new_mode}",
                "reason": reason
            })
            
            analysis["mode_transitions"][f"{old_mode} -> {new_mode}"] += 1
        
        elif event_type == "resource_collection":
            resource_type = event.get("resource_type", "unknown")
            analysis["resource_activity"][resource_type] += 1
        
        elif event_type == "trade_execution":
            analysis["trading_activity"].append({
                "step": event.get("step", 0),
                "seller": event.get("seller_id", -1),
                "buyer": event.get("buyer_id", -1),
                "give": event.get("give_type", ""),
                "take": event.get("take_type", ""),
                "seller_delta": event.get("delta_u_seller", 0.0),
                "buyer_delta": event.get("delta_u_buyer", 0.0)
            })
    
    # Analyze economic patterns
    analysis["economic_patterns"] = {
        "total_trades": len(analysis["trading_activity"]),
        "most_common_transition": max(analysis["mode_transitions"].items(), key=lambda x: x[1]) if analysis["mode_transitions"] else ("none", 0),
        "resource_distribution": dict(analysis["resource_activity"]),
        "agent_activity": {agent_id: len(behaviors) for agent_id, behaviors in analysis["agent_behavior"].items()}
    }
    
    return analysis


def generate_economic_report(sim: Simulation, analysis: dict, output_dir: Path) -> None:
    """Generate comprehensive economic analysis report."""
    report_path = output_dir / "economic_analysis_report.md"
    
    with open(report_path, 'w') as f:
        f.write("# Economic Behavior Analysis Report\n\n")
        f.write(f"**Analysis Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Simulation Steps**: {len(sim.agents) * 20} (estimated)\n\n")
        
        f.write("## Simulation Configuration\n\n")
        f.write(f"- **Grid Size**: {sim.grid.width}x{sim.grid.height}\n")
        f.write(f"- **Agents**: {len(sim.agents)}\n")
        f.write(f"- **Resources**: {sim.grid.resource_count()}\n")
        f.write(f"- **Resource Density**: {sim.grid.resource_count() / (sim.grid.width * sim.grid.height):.1%}\n\n")
        
        f.write("## Agent Preferences\n\n")
        for agent in sim.agents:
            pref_type = type(agent.preference).__name__
            f.write(f"- **Agent {agent.id}**: {pref_type}\n")
            if hasattr(agent.preference, 'alpha'):
                f.write(f"  - Alpha: {agent.preference.alpha:.2f}\n")
            f.write(f"  - Position: ({agent.x}, {agent.y})\n")
            f.write(f"  - Final Inventory: {agent.total_inventory()}\n")
            f.write(f"  - Current Mode: {agent.mode}\n\n")
        
        f.write("## Event Analysis\n\n")
        f.write(f"- **Total Events**: {analysis.get('total_events', 0)}\n")
        f.write(f"- **Event Types**:\n")
        for event_type, count in analysis.get('event_types', {}).items():
            f.write(f"  - {event_type}: {count}\n")
        f.write("\n")
        
        f.write("## Economic Patterns\n\n")
        patterns = analysis.get('economic_patterns', {})
        f.write(f"- **Total Trades**: {patterns.get('total_trades', 0)}\n")
        f.write(f"- **Most Common Mode Transition**: {patterns.get('most_common_transition', ('none', 0))[0]} ({patterns.get('most_common_transition', ('none', 0))[1]} times)\n")
        f.write(f"- **Resource Distribution**: {patterns.get('resource_distribution', {})}\n")
        f.write(f"- **Agent Activity**: {patterns.get('agent_activity', {})}\n\n")
        
        f.write("## Trading Analysis\n\n")
        trades = analysis.get('trading_activity', [])
        if trades:
            f.write(f"Found {len(trades)} trades:\n")
            for i, trade in enumerate(trades[:10]):  # Show first 10 trades
                f.write(f"{i+1}. Step {trade['step']}: Agent {trade['seller']} -> Agent {trade['buyer']} ({trade['give']} for {trade['take']})\n")
                f.write(f"   Utility changes: Seller +{trade['seller_delta']:.3f}, Buyer +{trade['buyer_delta']:.3f}\n")
            if len(trades) > 10:
                f.write(f"... and {len(trades) - 10} more trades\n")
        else:
            f.write("No trades occurred during the simulation.\n")
        f.write("\n")
        
        f.write("## Economic Insights\n\n")
        
        # Analyze economic behavior
        if patterns.get('total_trades', 0) == 0:
            f.write("⚠️ **No Trading Activity**: The simulation shows no trading between agents.\n")
            f.write("   - This could indicate agents are not finding beneficial trade opportunities\n")
            f.write("   - Check if agents have complementary preferences and resources\n")
            f.write("   - Verify trading system is properly enabled\n\n")
        
        mode_transitions = analysis.get('mode_transitions', {})
        if 'forage -> return_home' in mode_transitions:
            f.write(f"✅ **Resource Collection**: Agents are actively collecting resources ({mode_transitions['forage -> return_home']} collections)\n\n")
        
        if 'return_home -> forage' in mode_transitions:
            f.write(f"✅ **Resource Seeking**: Agents are actively seeking new resources ({mode_transitions['return_home -> forage']} searches)\n\n")
        
        # Check for economic efficiency
        agent_inventories = [agent.total_inventory() for agent in sim.agents]
        total_goods = {good: sum(inv.get(good, 0) for inv in agent_inventories) for good in ['good1', 'good2']}
        f.write(f"## Final Resource Distribution\n\n")
        f.write(f"- **Total Good1**: {total_goods.get('good1', 0)}\n")
        f.write(f"- **Total Good2**: {total_goods.get('good2', 0)}\n")
        f.write(f"- **Resource Utilization**: {sum(total_goods.values())} total goods collected\n\n")
        
        f.write("## Recommendations\n\n")
        if patterns.get('total_trades', 0) == 0:
            f.write("1. **Enable Trading**: Investigate why no trades are occurring\n")
            f.write("2. **Check Preferences**: Ensure agents have complementary preferences\n")
            f.write("3. **Verify Resources**: Confirm agents have different resource types to trade\n")
        else:
            f.write("1. **Trading is Active**: Economic system appears to be functioning\n")
            f.write("2. **Monitor Utility**: Check if trades are providing positive utility gains\n")
            f.write("3. **Analyze Patterns**: Look for optimal trading strategies\n")
    
    print(f"   📋 Analysis report: {report_path}")


def main():
    """Main economic analysis function."""
    try:
        # Create economic test scenario
        sim = create_economic_test_scenario()
        
        # Run economic analysis
        run_economic_analysis(sim, steps=100)
        
        # Analyze economic behavior
        log_file = Path("economic_analysis_logs/economic_behavior_analysis.jsonl")
        analysis = analyze_economic_behavior(log_file)
        
        # Generate report
        output_dir = Path("economic_analysis_logs")
        generate_economic_report(sim, analysis, output_dir)
        
        print(f"\n🎉 Economic behavior analysis complete!")
        print(f"   📁 Results in: economic_analysis_logs/")
        print(f"   📊 Check the analysis report for detailed findings")
        
    except Exception as e:
        print(f"❌ Error during economic analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
