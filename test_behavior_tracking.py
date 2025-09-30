#!/usr/bin/env python3
"""Test Phase 3.2 Multi-Dimensional Agent Behavior Aggregation.

Validates that behavior tracking (pairing, movement, utility gains, retargeting, 
resource acquisitions) works correctly and generates meaningful AGENT_BEHAVIOR_SUMMARY events.
"""

import os
import random
from pathlib import Path

# Configure headless environment before imports
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["SDL_VIDEODRIVER"] = "dummy"

# Enable behavior tracking and trading
os.environ["ECONSIM_TRADE_DRAFT"] = "1"
os.environ["ECONSIM_TRADE_EXEC"] = "1"
os.environ["ECONSIM_FORAGE_ENABLED"] = "1"

# Set up logging
os.environ["ECONSIM_LOG_LEVEL"] = "DEBUG"
os.environ["ECONSIM_LOG_FORMAT"] = "structured"
os.environ["ECONSIM_LOG_CATEGORIES"] = "ALL"  # Show all events to see what's happening

# Configure test parameters based on big_test.py
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation


def run_behavior_tracking_test():
    """Run behavior tracking test with exact big_test.py configuration."""
    # Exact big_test.py configuration
    cfg = SimConfig(
        grid_size=(30, 30),
        seed=12345,
        distance_scaling_factor=2.0,
        enable_respawn=True,
        enable_metrics=True,
        initial_resources=[
            (5, 5, 'A'), (25, 25, 'A'), (10, 10, 'A'), (20, 20, 'A'), (15, 15, 'A'),
            (7, 7, 'B'), (23, 23, 'B'), (12, 12, 'B'), (18, 18, 'B'), (9, 21, 'B'),
            (3, 27, 'A'), (27, 3, 'B'), (1, 1, 'A'), (29, 29, 'B'), (14, 8, 'A'),
        ]
    )
    
    # Agent positions - spread across grid for diverse behavior
    agent_positions = [
        (2, 2), (28, 28), (2, 28), (28, 2), (15, 15),  # Corners and center
        (10, 5), (20, 25), (5, 20), (25, 10), (12, 18),  # Mid positions  
        (8, 8), (22, 22), (8, 22), (22, 8), (16, 10),  # Diagonal spread
        (6, 15), (24, 15), (15, 6), (15, 24), (19, 19),  # Cross pattern
        # Add more agents for richer behavioral patterns
        (4, 12), (26, 18), (11, 25), (17, 3), (13, 13),
        (9, 9), (21, 21), (7, 16), (23, 14), (14, 7),
        (18, 26), (12, 4), (25, 8), (5, 22), (29, 15),
        (1, 17), (27, 11), (8, 3), (22, 27), (16, 20),
        (3, 9), (29, 21), (11, 14), (19, 6), (14, 23),
        (26, 5), (4, 18), (20, 12), (6, 26), (24, 2)  # 50 total agents
    ]
    
    # Create simulation
    sim = Simulation.from_config(cfg, agent_positions=agent_positions)
    ext_rng = random.Random(999)  # External RNG for step calls
    
    print(f"Starting behavior tracking test:")
    print(f"- Grid: {cfg.grid_size[0]}x{cfg.grid_size[1]}")
    print(f"- Agents: {len(agent_positions)}")
    print(f"- Resources: {len(cfg.initial_resources)}")
    print(f"- Steps: 300 (3 behavior flush cycles)")
    print()
    
    # Run for 300 steps (3 behavior flush cycles at 100-step intervals)
    step_count = 300
    for step in range(step_count):
        sim.step(ext_rng, use_decision=True)
        
        # Progress indicator
        if step % 50 == 0:
            print(f"Step {step}: {sim.grid.resource_count()} resources remaining")
    
    print(f"\nCompleted {step_count} steps")
    print(f"Final resources remaining: {sim.grid.resource_count()}")
    
    # Check recent logs for AGENT_BEHAVIOR_SUMMARY events
    log_dir = Path("gui_logs/structured")
    if log_dir.exists():
        log_files = sorted(log_dir.glob("*.jsonl"))
        if log_files:
            latest_log = log_files[-1]
            print(f"\nChecking latest log: {latest_log}")
            
            behavior_summaries = 0
            causal_chains = 0
            pairing_summaries = 0
            
            # Parse JSON events properly
            import json
            with open(latest_log, 'r') as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        category = event.get('category', '')
                        
                        if category == "AGENT_BEHAVIOR_SUMMARY":
                            behavior_summaries += 1
                            step = event.get('step', 0)
                            print(f"Found AGENT_BEHAVIOR_SUMMARY event #{behavior_summaries} at step {step}")
                            
                            # Display key metrics
                            print(f"  - Step range: {event.get('step_range', '')}")
                            print(f"  - Total agents: {event.get('total_agents', 0)}")
                            print(f"  - Total pairings: {event.get('total_pairings', 0)}")
                            print(f"  - Success rate: {event.get('success_rate_percent', 0)}%")
                            print(f"  - High-activity agents: {len(event.get('high_activity_agents', []))}")
                            
                            # Show typical behavior metrics
                            typical = event.get('typical_behavior', {})
                            print(f"  - Avg pairings: {typical.get('avg_pairings', 0):.1f}")
                            print(f"  - Avg movement: {typical.get('avg_movement_distance', 0):.1f}")
                            print(f"  - Avg utility gain: {typical.get('avg_utility_gain', 0):.1f}")
                            print(f"  - Avg partner diversity: {typical.get('avg_partner_diversity', 0):.2f}")
                            
                            # Show top agent
                            high_activity = event.get('high_activity_agents', [])
                            if high_activity:
                                top_agent = high_activity[0]
                                print(f"  - Top agent: {top_agent.get('agent_id')} ({top_agent.get('pairing_count')} pairings, {top_agent.get('successful_trades')} successful)")
                        
                        elif category == "CAUSAL_CHAIN":
                            causal_chains += 1
                        elif category == "PAIRING_SUMMARY":
                            pairing_summaries += 1
                            
                    except json.JSONDecodeError:
                        continue
            
            print(f"\nLog analysis:")
            print(f"- AGENT_BEHAVIOR_SUMMARY events: {behavior_summaries}")
            print(f"- CAUSAL_CHAIN events: {causal_chains}")  
            print(f"- PAIRING_SUMMARY events: {pairing_summaries}")
            
            if behavior_summaries >= 2:  # Should have 2-3 behavior summaries at 100-step intervals
                print("✅ Behavior tracking working correctly!")
            else:
                print("❌ Expected at least 2 behavior summary events")
                
        else:
            print("❌ No log files found")
    else:
        print("❌ Log directory not found")


if __name__ == "__main__":
    run_behavior_tracking_test()