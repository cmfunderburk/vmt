#!/usr/bin/env python3
"""
Quick test script to verify all debug instrumentation events are working.
Runs a short simulation with all periodic events set to emit every step.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Set all periodic emission intervals to 1 (every step)
os.environ["ECONSIM_SELECTION_SAMPLE_PERIOD"] = "1"
os.environ["ECONSIM_CHURN_EMIT_PERIOD"] = "1" 
os.environ["ECONSIM_PARTNER_SEARCH_SAMPLE_PERIOD"] = "1"
os.environ["ECONSIM_CHURN_WINDOW"] = "10"
os.environ["ECONSIM_PERF_SPIKE_FACTOR"] = "1.1"
os.environ["ECONSIM_LOG_LEVEL"] = "VERBOSE"
os.environ["ECONSIM_LOG_FORMAT"] = "STRUCTURED"
os.environ["ECONSIM_TRADE_DRAFT"] = "1"
os.environ["ECONSIM_TRADE_EXEC"] = "1"
os.environ["ECONSIM_FORAGE_ENABLED"] = "1"

def test_debug_events():
    """Run a short simulation and check for debug events."""
    try:
        from econsim.simulation.config import SimConfig
        from econsim.simulation.world import Simulation
        import random
        
        print("Creating test simulation...")
        
        # Initialize the GUI logger first
        from econsim.gui.debug_logger import get_gui_logger
        logger = get_gui_logger()
        print("GUI logger initialized")
        
        # Create a small simulation with multiple agents for interaction
        config = SimConfig(
            grid_size=(8, 8),
            initial_resources=[(1, 1, 'A'), (2, 2, 'B'), (3, 3, 'A'), (4, 4, 'B')],
            seed=123,
            distance_scaling_factor=1.0,
            enable_respawn=True,
            enable_metrics=True
        )
        
        # Create agents at different positions to encourage movement and interaction
        agent_positions = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]
        sim = Simulation.from_config(config, agent_positions=agent_positions)
        
        print(f"Created simulation with {len(sim.agents)} agents")
        print("Running 50 steps to generate debug events...")
        
        # Run simulation for 50 steps
        rng = random.Random(123)
        for step in range(50):
            sim.step(rng, use_decision=True)
            if step % 10 == 0:
                print(f"  Step {step}")
        
        print("Simulation completed!")
        print("\nChecking for debug events in log files...")
        
        # Check for log files
        log_dir = Path("gui_logs/structured")
        if log_dir.exists():
            log_files = list(log_dir.glob("*.jsonl"))
            if log_files:
                latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
                print(f"Latest log file: {latest_log}")
                
                # Count different event types
                import json
                event_counts = {}
                with open(latest_log, 'r') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            if 'event' in data:
                                event_type = data['event']
                                event_counts[event_type] = event_counts.get(event_type, 0) + 1
                        except json.JSONDecodeError:
                            continue
                
                print("\nEvent counts found:")
                for event, count in sorted(event_counts.items()):
                    print(f"  {event}: {count}")
                
                # Check for the specific events we're looking for
                target_events = [
                    'trade_intent_funnel',
                    'partner_search', 
                    'partner_reject',
                    'selection_sample',
                    'perf_spike',
                    'respawn_cycle',
                    'respawn_skipped',
                    'target_churn',
                    'stagnation_trigger'
                ]
                
                print("\nTarget instrumentation events:")
                for event in target_events:
                    count = event_counts.get(event, 0)
                    status = "✅" if count > 0 else "❌"
                    print(f"  {status} {event}: {count}")
                    
            else:
                print("No log files found!")
        else:
            print("Log directory not found!")
            
    except Exception as e:
        print(f"Error running test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_debug_events()
