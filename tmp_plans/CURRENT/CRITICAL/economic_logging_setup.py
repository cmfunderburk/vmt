#!/usr/bin/env python3
"""Economic Logging Setup for VMT EconSim

This script sets up comprehensive economic logging through the observer system
to enable detailed analysis of economic behavior in the simulation.

Usage:
    python economic_logging_setup.py [--steps N] [--output-dir DIR] [--scenario SCENARIO]

Features:
- Comprehensive economic event logging
- Structured JSON output for analysis
- Configurable simulation scenarios
- Real-time economic behavior monitoring
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from econsim.observability import (
    ObserverRegistry, ObservabilityConfig, 
    initialize_global_observer_logger,
    AgentModeChangeEvent, ResourceCollectionEvent, TradeExecutionEvent,
    AgentDecisionEvent, ResourceEvent, DebugLogEvent
)
from econsim.observability.observers.file_observer import FileObserver
from econsim.observability.observers.educational_observer import EducationalObserver
from econsim.simulation.world import Simulation
from econsim.simulation.grid import Grid
from econsim.simulation.agent import Agent
from econsim.simulation.respawn import RespawnScheduler
from econsim.simulation.metrics import MetricsCollector
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.preferences.leontief import LeontiefPreference
from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference
import random


def setup_economic_logging(output_dir: Path) -> ObserverRegistry:
    """Set up comprehensive economic logging through observer system.
    
    Args:
        output_dir: Directory to write log files
        
    Returns:
        Configured observer registry
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create observability configuration
    config = ObservabilityConfig()
    
    # Create observer registry
    registry = ObserverRegistry()
    
    # Set up file observer for structured logging
    economic_log_path = output_dir / "economic_events.jsonl"
    file_observer = FileObserver(
        config=config,
        output_path=economic_log_path,
        buffer_size=1000,
        format='jsonl'
    )
    registry.register(file_observer)
    
    # Set up educational observer for human-readable output
    educational_observer = EducationalObserver(config=config)
    registry.register(educational_observer)
    
    # Initialize global observer logger
    initialize_global_observer_logger(registry)
    
    print(f"✅ Economic logging setup complete")
    print(f"   📁 Output directory: {output_dir}")
    print(f"   📄 Structured logs: {economic_log_path}")
    print(f"   📝 Summary logs: {educational_log_path}")
    
    return registry


def create_economic_scenario(scenario_name: str) -> Simulation:
    """Create a simulation scenario optimized for economic analysis.
    
    Args:
        scenario_name: Name of scenario to create
        
    Returns:
        Configured simulation
    """
    if scenario_name == "basic_trading":
        # Basic trading scenario: 2 agents with different preferences
        grid = Grid(10, 10)
        
        # Add resources
        for i in range(20):
            x = i % grid.width
            y = i // grid.width
            grid.add_resource(x, y, "A" if i % 2 == 0 else "B")
        
        # Create agents with different preferences
        agents = [
            Agent(id=0, x=2, y=2, preference=CobbDouglasPreference(alpha=0.7)),  # Prefers good1
            Agent(id=1, x=7, y=7, preference=CobbDouglasPreference(alpha=0.3)),  # Prefers good2
        ]
        
        sim = Simulation(grid=grid, agents=agents, config=None)
        
    elif scenario_name == "diverse_preferences":
        # Diverse preferences scenario: Multiple agents with different utility functions
        grid = Grid(15, 15)
        
        # Add resources
        for i in range(50):
            x = (i * 7) % grid.width
            y = (i * 11) % grid.height
            grid.add_resource(x, y, "A" if i % 3 == 0 else "B")
        
        # Create agents with diverse preferences
        agents = [
            Agent(id=0, x=3, y=3, preference=CobbDouglasPreference(alpha=0.8)),  # Strong good1 preference
            Agent(id=1, x=11, y=3, preference=CobbDouglasPreference(alpha=0.2)),  # Strong good2 preference
            Agent(id=2, x=3, y=11, preference=LeontiefPreference()),  # Perfect complements
            Agent(id=3, x=11, y=11, preference=PerfectSubstitutesPreference()),  # Perfect substitutes
            Agent(id=4, x=7, y=7, preference=CobbDouglasPreference(alpha=0.5)),  # Balanced
        ]
        
        sim = Simulation(grid=grid, agents=agents, config=None)
        
    elif scenario_name == "high_density":
        # High density scenario: Many agents, many resources
        grid = Grid(20, 20)
        
        # Add many resources (80% density)
        for i in range(320):  # 80% of 400 cells
            x = (i * 13) % grid.width
            y = (i * 7) % grid.height
            grid.add_resource(x, y, "A" if i % 2 == 0 else "B")
        
        # Create many agents
        agents = []
        for i in range(15):
            x = (i * 3) % grid.width
            y = (i * 5) % grid.height
            alpha = 0.2 + (i % 8) * 0.1  # Vary preferences
            agents.append(Agent(id=i, x=x, y=y, preference=CobbDouglasPreference(alpha=alpha)))
        
        sim = Simulation(grid=grid, agents=agents, config=None)
        
    else:
        raise ValueError(f"Unknown scenario: {scenario_name}")
    
    # Add dynamic systems for comprehensive logging
    sim._rng = random.Random(42)
    sim.respawn_scheduler = RespawnScheduler(
        target_density=0.8, max_spawn_per_tick=10, respawn_rate=0.3
    )
    sim.metrics_collector = MetricsCollector()
    
    return sim


def run_economic_analysis(sim: Simulation, steps: int, output_dir: Path) -> None:
    """Run simulation with comprehensive economic logging.
    
    Args:
        sim: Simulation to run
        steps: Number of steps to simulate
        output_dir: Directory for output files
    """
    print(f"🚀 Starting economic analysis simulation")
    print(f"   📊 Steps: {steps}")
    print(f"   👥 Agents: {len(sim.agents)}")
    print(f"   🗺️  Grid: {sim.grid.width}x{sim.grid.height}")
    print(f"   📦 Resources: {sim.grid.resource_count()}")
    
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
    
    start_time = time.time()
    
    # Run simulation with logging
    rng = random.Random(12345)
    for step in range(steps):
        sim.step(rng)
        
        # Print progress every 10 steps
        if step % 10 == 0:
            elapsed = time.time() - start_time
            print(f"   Step {step:3d}/{steps} ({elapsed:.1f}s elapsed)")
    
    total_time = time.time() - start_time
    
    print(f"✅ Economic analysis complete")
    print(f"   ⏱️  Total time: {total_time:.2f}s")
    print(f"   📈 Steps/sec: {steps/total_time:.1f}")
    
    # Generate summary report
    generate_economic_summary(sim, steps, output_dir)


def generate_economic_summary(sim: Simulation, steps: int, output_dir: Path) -> None:
    """Generate a summary report of economic behavior.
    
    Args:
        sim: Completed simulation
        steps: Number of steps run
        output_dir: Directory for output files
    """
    summary_path = output_dir / "economic_summary.md"
    
    with open(summary_path, 'w') as f:
        f.write("# Economic Analysis Summary\n\n")
        f.write(f"**Simulation Steps**: {steps}\n")
        f.write(f"**Agents**: {len(sim.agents)}\n")
        f.write(f"**Grid Size**: {sim.grid.width}x{sim.grid.height}\n")
        f.write(f"**Resources**: {sim.grid.resource_count()}\n\n")
        
        f.write("## Agent Preferences\n\n")
        for agent in sim.agents:
            pref_type = type(agent.preference).__name__
            f.write(f"- **Agent {agent.id}**: {pref_type}\n")
            if hasattr(agent.preference, 'alpha'):
                f.write(f"  - Alpha: {agent.preference.alpha:.2f}\n")
        
        f.write("\n## Final Agent States\n\n")
        for agent in sim.agents:
            carrying = agent.carrying
            home = agent.home_inventory
            total = agent.total_inventory()
            f.write(f"- **Agent {agent.id}** (at {agent.x},{agent.y}):\n")
            f.write(f"  - Carrying: {carrying}\n")
            f.write(f"  - Home: {home}\n")
            f.write(f"  - Total: {total}\n")
            f.write(f"  - Mode: {agent.mode}\n")
        
        f.write("\n## Resource Distribution\n\n")
        resource_counts = {}
        for x, y, resource_type in sim.grid.iter_resources():
            resource_counts[resource_type] = resource_counts.get(resource_type, 0) + 1
        
        for resource_type, count in resource_counts.items():
            f.write(f"- **{resource_type}**: {count} resources\n")
    
    print(f"   📋 Summary report: {summary_path}")


def main():
    """Main function for economic logging setup."""
    parser = argparse.ArgumentParser(description="Economic Logging Setup for VMT EconSim")
    parser.add_argument("--steps", type=int, default=100, help="Number of simulation steps")
    parser.add_argument("--output-dir", type=str, default="economic_logs", help="Output directory")
    parser.add_argument("--scenario", type=str, default="diverse_preferences", 
                       choices=["basic_trading", "diverse_preferences", "high_density"],
                       help="Simulation scenario")
    
    args = parser.parse_args()
    
    # Set up output directory
    output_dir = Path(args.output_dir)
    timestamp = int(time.time())
    output_dir = output_dir / f"economic_analysis_{timestamp}"
    
    try:
        # Set up economic logging
        registry = setup_economic_logging(output_dir)
        
        # Create simulation scenario
        sim = create_economic_scenario(args.scenario)
        
        # Run economic analysis
        run_economic_analysis(sim, args.steps, output_dir)
        
        print(f"\n🎉 Economic analysis complete!")
        print(f"   📁 Results in: {output_dir}")
        print(f"   📊 Check the log files for detailed economic behavior analysis")
        
    except Exception as e:
        print(f"❌ Error during economic analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
