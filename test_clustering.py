#!/usr/bin/env python3
"""Test Phase 3.4 Intra-Step Event Clustering.

Validates that failed PAIRING events on the same step are clustered into PAIRING_BATCH events
while preserving successful pairings and anomalies individually for correlation tracking.
"""

import os
import random
from pathlib import Path

# Configure headless environment before imports
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["SDL_VIDEODRIVER"] = "dummy"

# Enable trading and clustering
os.environ["ECONSIM_TRADE_DRAFT"] = "1"
os.environ["ECONSIM_TRADE_EXEC"] = "1"
os.environ["ECONSIM_FORAGE_ENABLED"] = "1"

# Set up logging to show clustering events
os.environ["ECONSIM_LOG_LEVEL"] = "DEBUG"
os.environ["ECONSIM_LOG_FORMAT"] = "structured"
os.environ["ECONSIM_LOG_CATEGORIES"] = "PAIRING,PAIRING_BATCH,PAIRING_SUMMARY,CAUSAL_CHAIN"

from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation


def run_clustering_test():
    """Test intra-step event clustering with smaller simulation for focused analysis."""
    # Smaller test configuration for clear clustering patterns
    cfg = SimConfig(
        grid_size=(15, 15), 
        seed=42,
        distance_scaling_factor=1.5,
        enable_respawn=True,
        enable_metrics=True,
        initial_resources=[
            (5, 5, 'A'), (10, 10, 'A'), (3, 12, 'A'),
            (8, 3, 'B'), (12, 8, 'B'), (6, 14, 'B'),
        ]
    )
    
    # Fewer agents for clearer clustering analysis
    agent_positions = [
        (2, 2), (13, 13), (2, 13), (13, 2), (7, 7),   # 5 agents
        (4, 4), (11, 11), (4, 11), (11, 4), (8, 8),   # 10 agents  
        (6, 6), (9, 9), (5, 10), (10, 5), (7, 8)      # 15 agents
    ]
    
    # Create simulation
    sim = Simulation.from_config(cfg, agent_positions=agent_positions)
    ext_rng = random.Random(999)
    
    print(f"Starting clustering test:")
    print(f"- Grid: {cfg.grid_size[0]}x{cfg.grid_size[1]}")
    print(f"- Agents: {len(agent_positions)}")
    print(f"- Resources: {len(cfg.initial_resources)}")
    print(f"- Steps: 150 (focused test)")
    print()
    
    # Run for 150 steps to get clustering patterns
    step_count = 150
    for step in range(step_count):
        sim.step(ext_rng, use_decision=True)
        
        if step % 50 == 0:
            print(f"Step {step}: {sim.grid.resource_count()} resources remaining")
    
    print(f"\nCompleted {step_count} steps")
    print(f"Final resources: {sim.grid.resource_count()}")
    
    # Analyze clustering results
    log_dir = Path("gui_logs/structured")
    if log_dir.exists():
        log_files = sorted(log_dir.glob("*.jsonl"))
        if log_files:
            latest_log = log_files[-1]
            print(f"\nAnalyzing clustering in: {latest_log}")
            
            analyze_clustering_effectiveness(latest_log)
        else:
            print("❌ No log files found")
    else:
        print("❌ Log directory not found")


def analyze_clustering_effectiveness(log_file: Path):
    """Analyze the effectiveness of the clustering implementation."""
    import json
    
    pairing_events = 0
    pairing_batch_events = 0
    successful_pairings = 0
    failed_pairings_clustered = 0
    causal_chains = 0
    
    # Collect per-step statistics
    step_analysis = {}
    
    with open(log_file, 'r') as f:
        for line in f:
            try:
                event = json.loads(line)
                category = event.get('category', '')
                step = event.get('step', 0)
                
                if category == "PAIRING":
                    pairing_events += 1
                    chosen_id = event.get("cho", -1)
                    if chosen_id >= 0:
                        successful_pairings += 1
                    
                    # Track per-step PAIRING events
                    if step not in step_analysis:
                        step_analysis[step] = {"pairing": 0, "pairing_batch": 0}
                    step_analysis[step]["pairing"] += 1
                
                elif category == "PAIRING_BATCH":
                    pairing_batch_events += 1
                    failed_count = event.get("failed_count", 0)
                    failed_pairings_clustered += failed_count
                    
                    print(f"PAIRING_BATCH at step {step}: {failed_count} failed pairings clustered")
                    print(f"  Agent IDs: {event.get('agent_ids', [])}")
                    print(f"  Total rejections: {event.get('total_rejections', 0)}")
                    print(f"  Rejection breakdown: {event.get('rejection_breakdown', {})}")
                    
                    # Track per-step PAIRING_BATCH events
                    if step not in step_analysis:
                        step_analysis[step] = {"pairing": 0, "pairing_batch": 0}
                    step_analysis[step]["pairing_batch"] += 1
                
                elif category == "CAUSAL_CHAIN":
                    causal_chains += 1
                    
            except json.JSONDecodeError:
                continue
    
    print(f"\n📊 Clustering Analysis Results:")
    print(f"- Individual PAIRING events: {pairing_events}")
    print(f"  └─ Successful pairings: {successful_pairings} (preserved for correlation tracking)")
    print(f"- PAIRING_BATCH events: {pairing_batch_events}")
    print(f"  └─ Failed pairings clustered: {failed_pairings_clustered}")
    print(f"- CAUSAL_CHAIN events: {causal_chains} (from successful pairings)")
    
    # Calculate compression effectiveness
    original_events = pairing_events + failed_pairings_clustered
    compressed_events = pairing_events + pairing_batch_events
    
    if original_events > 0:
        compression_ratio = (original_events - compressed_events) / original_events * 100
        print(f"\n🎯 Compression Results:")
        print(f"- Original events (without clustering): {original_events}")
        print(f"- Compressed events (with clustering): {compressed_events}")
        print(f"- Compression ratio: {compression_ratio:.1f}%")
        
        if compression_ratio > 0:
            print("✅ Clustering working - achieved compression!")
        else:
            print("⚠️  No compression achieved")
    
    # Show steps with clustering activity
    clustering_steps = [(step, data) for step, data in step_analysis.items() 
                       if data.get("pairing_batch", 0) > 0]
    
    if clustering_steps:
        print(f"\n📈 Steps with clustering activity:")
        for step, data in clustering_steps[:5]:  # Show first 5
            print(f"  Step {step}: {data['pairing']} individual + {data['pairing_batch']} batch")
    else:
        print("\n❌ No clustering activity detected")


if __name__ == "__main__":
    run_clustering_test()
