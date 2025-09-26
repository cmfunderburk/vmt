#!/usr/bin/env python3
"""
Simple Test Validation
======================

This script creates a simple test simulation to validate the approach works before
running the full manual tests.
"""

import sys
import os
import random

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

def test_basic_simulation():
    """Test that we can create a basic simulation."""
    print("Testing basic simulation creation...")
    
    try:
        from econsim.simulation.config import SimConfig
        from econsim.simulation.world import Simulation
        from econsim.preferences.cobb_douglas import CobbDouglasPreference
        
        # Create simple config
        config = SimConfig(
            grid_size=(10, 10),
            initial_resources=[(1, 1, 'A'), (2, 2, 'B'), (3, 3, 'A')],
            seed=12345,
            enable_respawn=False,
            enable_metrics=False
        )
        
        # Create simple preference factory
        def preference_factory(idx: int):
            return CobbDouglasPreference(alpha=0.5)
        
        agent_positions = [(0, 0), (1, 0), (2, 0)]
        
        # Create simulation
        sim = Simulation.from_config(config, preference_factory, agent_positions=agent_positions)
        
        print(f"✅ Created simulation with {len(sim.agents)} agents")
        
        # Test a few simulation steps
        ext_rng = random.Random(789)
        for step in range(5):
            sim.step(ext_rng, use_decision=True)
            print(f"  Step {step + 1}: {len(sim.agents)} agents, {len(list(sim.grid.iter_resources()))} resources")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic simulation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 50)
    print("SIMPLE TEST VALIDATION")
    print("=" * 50)
    
    if test_basic_simulation():
        print("\n🎉 Basic simulation test PASSED!")
        print("The core simulation can be created and run.")
        print("Manual tests should work correctly.")
    else:
        print("\n❌ Basic simulation test FAILED!")
        print("There may be issues with the core simulation setup.")
    
    print("=" * 50)

if __name__ == '__main__':
    main()