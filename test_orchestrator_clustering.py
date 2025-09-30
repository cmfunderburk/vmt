#!/usr/bin/env python3
"""Test that DebugOrchestrator properly enables PAIRING_BATCH clustering."""

import os
import random
import sys
from pathlib import Path

# Configure headless environment
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["SDL_VIDEODRIVER"] = "dummy"

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import and setup DebugOrchestrator
from econsim.tools.launcher.framework.debug_orchestrator import DebugOrchestrator
from econsim.tools.launcher.framework.test_configs import TestConfiguration

# Create a test configuration
config = TestConfiguration(
    id=999,
    name="Clustering Test",
    description="Test clustering with orchestrator",
    grid_size=(10, 10),
    agent_count=10,
    resource_density=0.3,
    perception_radius=6,
    distance_scaling_factor=1.5,
    preference_mix="mixed",
    seed=12345
)

# Initialize DebugOrchestrator (this should set up comprehensive logging)
print("🔧 Initializing DebugOrchestrator...")
orchestrator = DebugOrchestrator(config)

# Now run a small simulation to test clustering
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation

def run_orchestrator_test():
    """Run a test using DebugOrchestrator setup."""
    print("\n=== Orchestrator Clustering Test ===")
    
    # Create simulation using same config pattern as launcher
    sim_config = SimConfig(
        grid_size=config.grid_size,
        seed=config.seed,
        enable_respawn=True,
        enable_metrics=True,
        distance_scaling_factor=config.distance_scaling_factor,
        initial_resources=[]
    )
    
    # Create simulation with agents
    agent_positions = [(i, 0) for i in range(config.agent_count)]
    sim = Simulation.from_config(sim_config, agent_positions=agent_positions)
    
    # Add some resources to encourage trading
    for i in range(6):
        x, y = random.randint(1, 8), random.randint(1, 8)
        resource_type = 'A' if i % 2 == 0 else 'B'
        sim.grid.add_resource(x, y, resource_type)
    
    ext_rng = random.Random(789)
    
    print(f"Running 50 steps with {config.agent_count} agents...")
    for step in range(50):
        sim.step(ext_rng, use_decision=True)
        if step % 20 == 0:
            resources = list(sim.grid.iter_resources_sorted())
            print(f"Step {step}: {len(resources)} resources")
    
    resources = list(sim.grid.iter_resources_sorted())
    print(f"Final step: {len(resources)} resources")

if __name__ == "__main__":
    # Check environment variables set by orchestrator
    print("Environment variables set:")
    print(f"  ECONSIM_LOG_LEVEL: {os.environ.get('ECONSIM_LOG_LEVEL')}")
    print(f"  ECONSIM_LOG_FORMAT: {os.environ.get('ECONSIM_LOG_FORMAT')}")
    print(f"  ECONSIM_LOG_CATEGORIES: {os.environ.get('ECONSIM_LOG_CATEGORIES')}")
    print()
    
    run_orchestrator_test()
    
    # Analyze the log file
    print("\n=== Log Analysis ===")
    log_files = list(Path("gui_logs/structured").glob("*.jsonl"))
    if log_files:
        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
        print(f"Latest log: {latest_log}")
        
        # Count events
        with open(latest_log) as f:
            lines = f.readlines()
        
        pairing_events = sum(1 for line in lines if '"category":"PAIRING"' in line)
        batch_events = sum(1 for line in lines if '"category":"PAIRING_BATCH"' in line)
        
        print(f"PAIRING events: {pairing_events}")
        print(f"PAIRING_BATCH events: {batch_events}")
        
        if batch_events > 0:
            print("✅ Clustering working with DebugOrchestrator!")
        else:
            print("❌ Clustering not working - debugging needed")
            
            # Show failed pairings by step
            failed_by_step = {}
            for line in lines:
                if '"category":"PAIRING"' in line and '"cho":-1' in line:
                    import json
                    try:
                        event = json.loads(line)
                        step = event.get("step", 0)
                        failed_by_step[step] = failed_by_step.get(step, 0) + 1
                    except:
                        pass
            
            multi_failed_steps = {k: v for k, v in failed_by_step.items() if v > 1}
            print(f"Steps with multiple failures (should be clustered): {multi_failed_steps}")
    else:
        print("No log files found!")