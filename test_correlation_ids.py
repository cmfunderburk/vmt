#!/usr/bin/env python3
"""
Headless test for correlation ID and causal chain system
Based on the big_test.py configuration to ensure consistent testing
"""

import os
import sys
from pathlib import Path

# Set headless environment
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["SDL_VIDEODRIVER"] = "dummy"

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

import random
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation

def main():
    print("=== CORRELATION ID & CAUSAL CHAIN TEST ===")
    print("Testing Phase 3.1 enhancements with big_test.py configuration")
    
    # Enable trading flags like in the successful big_test logs we analyzed
    os.environ["ECONSIM_TRADE_DRAFT"] = "1"
    os.environ["ECONSIM_TRADE_EXEC"] = "1" 
    os.environ["ECONSIM_DEBUG_TRADES"] = "1"
    
    print("✅ Trading flags enabled: DRAFT=1, EXEC=1, DEBUG=1")
    print()
    
    # Use the exact same configuration as big_test.py
    cfg = SimConfig(
        grid_size=(30, 30),
        seed=12345,  # Same seed as big_test.py
        enable_respawn=True,
        enable_metrics=True,
        distance_scaling_factor=2.0,  # Same as big_test.py
        initial_resources=[]  # Will be populated by respawn system
    )
    
    # Generate agent positions (50 agents like big_test.py)
    agent_positions = []
    grid_w, grid_h = cfg.grid_size
    pos_rng = random.Random(cfg.seed)
    
    for i in range(50):  # Same agent count as big_test.py
        x = pos_rng.randint(0, grid_w - 1)
        y = pos_rng.randint(0, grid_h - 1)
        agent_positions.append((x, y))
    
    print(f"Configuration: {cfg.grid_size[0]}x{cfg.grid_size[1]} grid, {len(agent_positions)} agents")
    print(f"Seed: {cfg.seed}, Distance scaling: {cfg.distance_scaling_factor}")
    
    # Create simulation
    sim = Simulation.from_config(cfg, agent_positions=agent_positions)
    ext_rng = random.Random(999)  # External RNG for step execution
    
    # Run the full big_test simulation (10,100 steps like the original)
    print("\n--- Running Full Big Test Simulation (10,100 steps) ---")
    print("This will take about 60 seconds and should generate correlation chains")
    print("Progress updates every 1,000 steps...")
    
    import time
    start_time = time.time()
    
    for step in range(10100):
        sim.step(ext_rng, use_decision=True)
        
        # Progress updates every 1000 steps
        if step % 1000 == 999:
            elapsed = time.time() - start_time
            print(f"  Step {step+1:,}/10,100 completed ({elapsed:.1f}s elapsed)")
    
    total_time = time.time() - start_time
    print(f"\n✅ Simulation completed in {total_time:.1f} seconds")
    
    print("\n🎉 Test completed successfully!")
    print("\n--- Analyzing Log Results ---")
    
    # Check the latest log file
    logs_dir = project_root / "gui_logs" / "structured"
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.jsonl"))
        if log_files:
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            print(f"📄 Latest log: {latest_log.name}")
            
            # Analyze correlation ID events
            with open(latest_log, 'r') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            causal_chains = [line for line in lines if '"CAUSAL_CHAIN"' in line]
            successful_pairings = [line for line in lines if '"PAIRING"' in line and '"cho":[0-9]' in line]
            
            print(f"📊 Total log lines: {total_lines}")
            print(f"🔗 CAUSAL_CHAIN events: {len(causal_chains)}")
            print(f"✅ Successful pairings: {len(successful_pairings)}")
            
            if causal_chains:
                print("\n🎯 Sample CAUSAL_CHAIN event:")
                import json
                try:
                    sample = json.loads(causal_chains[0])
                    print(f"  - Correlation ID: {sample.get('correlation_id', 'N/A')}")
                    print(f"  - Outcome: {sample.get('outcome', 'N/A')}")
                    print(f"  - Sequence length: {len(sample.get('sequence', []))}")
                    print(f"  - Educational note: {sample.get('educational_note', 'N/A')[:80]}...")
                except json.JSONDecodeError:
                    print("  (Unable to parse sample event)")
            else:
                print("⚠️  No CAUSAL_CHAIN events found - correlation system may need debugging")
                
                if successful_pairings:
                    print("💡 However, successful pairings were detected:")
                    print(f"   This suggests correlation ID generation might have an issue")
                else:
                    print("💭 No successful pairings found either - agents may not be trading")
        else:
            print("❌ No log files found")
    else:
        print("❌ Logs directory not found")

if __name__ == "__main__":
    main()