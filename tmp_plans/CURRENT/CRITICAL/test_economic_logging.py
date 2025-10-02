#!/usr/bin/env python3
"""Test Economic Logging - Quick Test of Observer System

This script provides a quick test of the economic logging system to ensure
the observer pattern is working correctly for economic event capture.

Usage:
    python test_economic_logging.py
"""

import os
import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from econsim.observability import (
    ObserverRegistry, ObservabilityConfig, 
    initialize_global_observer_logger,
    get_global_observer_logger
)
from econsim.observability.observers.file_observer import FileObserver
from econsim.simulation.world import Simulation
from econsim.simulation.grid import Grid
from econsim.simulation.agent import Agent
from econsim.simulation.respawn import RespawnScheduler
from econsim.simulation.metrics import MetricsCollector
from econsim.preferences.cobb_douglas import CobbDouglasPreference
import random


def create_test_simulation() -> Simulation:
    """Create a simple test simulation with logging setup."""
    # Create test output directory
    output_dir = Path("test_economic_logs")
    output_dir.mkdir(exist_ok=True)
    
    # Create small grid
    grid = Grid(5, 5)
    
    # Add some resources
    for i in range(8):
        x = i % grid.width
        y = i // grid.width
        grid.add_resource(x, y, "A" if i % 2 == 0 else "B")
    
    # Create 2 agents with different preferences
    agents = [
        Agent(id=0, x=1, y=1, preference=CobbDouglasPreference(alpha=0.7)),
        Agent(id=1, x=3, y=3, preference=CobbDouglasPreference(alpha=0.3)),
    ]
    
    sim = Simulation(grid=grid, agents=agents, config=None)
    
    # Set up file observer on the simulation's observer registry
    config = ObservabilityConfig()
    log_path = output_dir / "test_economic_events.jsonl"
    file_observer = FileObserver(
        config=config,
        output_path=log_path,
        buffer_size=100,
        format='jsonl'
    )
    sim._observer_registry.register(file_observer)
    
    # Add dynamic systems
    sim._rng = random.Random(42)
    sim.respawn_scheduler = RespawnScheduler(
        target_density=0.8, max_spawn_per_tick=5, respawn_rate=0.5
    )
    sim.metrics_collector = MetricsCollector()
    
    print(f"✅ Test logging setup complete")
    print(f"   📄 Log file: {log_path}")
    
    return sim


def run_test_simulation(sim: Simulation, steps: int = 20) -> None:
    """Run test simulation with logging enabled."""
    # Set up environment variables for logging
    os.environ["ECONSIM_DEBUG_AGENT_MODES"] = "1"
    os.environ["ECONSIM_DEBUG_TRADES"] = "1"
    os.environ["ECONSIM_DEBUG_DECISIONS"] = "1"
    os.environ["ECONSIM_DEBUG_RESOURCES"] = "1"
    os.environ["ECONSIM_DEBUG_SIMULATION"] = "1"
    os.environ["ECONSIM_LOG_LEVEL"] = "DEBUG"
    os.environ["ECONSIM_LOG_FORMAT"] = "STRUCTURED"
    os.environ["ECONSIM_LOG_CATEGORIES"] = "ALL"
    
    # Enable trading
    os.environ["ECONSIM_FORAGE_ENABLED"] = "1"
    os.environ["ECONSIM_TRADE_DRAFT"] = "1"
    os.environ["ECONSIM_TRADE_EXEC"] = "1"
    
    print(f"🚀 Running test simulation for {steps} steps...")
    
    # Get global logger
    logger = get_global_observer_logger()
    if logger:
        logger.log_economics("Starting economic test simulation", step=0)
    
    # Run simulation
    rng = random.Random(12345)
    for step in range(steps):
        sim.step(rng)
        
        # Log economic events manually for testing
        if logger:
            logger.log_economics(f"Step {step} completed - Agents: {len(sim.agents)}, Resources: {sim.grid.resource_count()}", step=step)
        
        if step % 5 == 0:
            print(f"   Step {step}/{steps}")
    
    if logger:
        logger.log_economics("Economic test simulation completed", step=steps)
    
    print(f"✅ Test simulation complete")


def main():
    """Main test function."""
    try:
        # Create test simulation (includes logging setup)
        sim = create_test_simulation()
        
        # Run test simulation
        run_test_simulation(sim, steps=20)
        
        print(f"\n🎉 Economic logging test complete!")
        print(f"   📁 Check test_economic_logs/ for output files")
        print(f"   📊 Verify that economic events are being captured")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
