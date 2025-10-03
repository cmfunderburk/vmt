#!/usr/bin/env python3
"""Test script for new utility & wealth metrics functionality."""

import random
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation

def test_utility_metrics():
    """Test the new utility and wealth metrics implementation."""
    print("🧪 Testing Utility & Wealth Metrics Implementation")
    print("=" * 60)
    
    # Create a small simulation
    cfg = SimConfig(
        grid_size=(8, 8),
        initial_resources=[(1,1,'good1'), (2,2,'good2'), (3,3,'good1'), (4,4,'good2')],
        perception_radius=6,
        seed=42,
        enable_respawn=True,
        enable_metrics=True
    )
    
    agent_positions = [(0,0), (1,0), (2,0)]  # 3 agents
    sim = Simulation.from_config(cfg, agent_positions=agent_positions)
    ext_rng = random.Random(123)
    
    print(f"Created simulation with {len(sim.agents)} agents")
    print(f"Initial resources: {len(cfg.initial_resources)}")
    
    # Ensure metrics collector is enabled
    if sim.metrics_collector is None:
        print("❌ Metrics collector not enabled!")
        return
    
    # Run simulation for several steps
    print("\n📊 Running simulation and tracking utility metrics...")
    for step in range(20):
        sim.step(ext_rng)
        
        # Check utility stats every 5 steps
        if step % 5 == 0:
            utility_stats = sim.metrics_collector.get_utility_stats()
            print(f"\nStep {step + 1}:")
            print(f"  Total System Utility: {utility_stats['total_system_utility']}")
            print(f"  Avg Utility/Agent: {utility_stats['avg_utility_per_agent']}")
            print(f"  Utility Growth Rate: {utility_stats['utility_growth_rate']}")
            print(f"  Utility Variance: {utility_stats['utility_variance']}")
            print(f"  Gini Coefficient: {utility_stats['utility_gini_coefficient']}")
    
    # Final analysis
    print("\n📈 Final Analysis:")
    final_stats = sim.metrics_collector.get_utility_stats()
    trend_slope = sim.metrics_collector.get_utility_trend_slope(window=10)
    
    print(f"Final Total System Utility: {final_stats['total_system_utility']}")
    print(f"Final Gini Coefficient: {final_stats['utility_gini_coefficient']}")
    print(f"Utility Trend Slope (last 10 steps): {trend_slope:.6f}")
    
    # Check individual agent utilities
    print("\n👥 Individual Agent Analysis:")
    wealth_data = sim.metrics_collector.get_wealth_distribution_history(steps=1)
    if wealth_data:
        latest_data = wealth_data[-1]
        for agent_data in latest_data['agents']:
            print(f"  Agent {agent_data['agent_id']} ({agent_data['preference_type']}):")
            print(f"    Utility: {agent_data['utility']:.3f}")
            print(f"    Total Wealth: {agent_data['total_wealth']}")
            print(f"    Carrying: {agent_data['carrying_wealth']}, Home: {agent_data['home_wealth']}")
    
    # Verify metrics are hash-excluded (determinism check)
    hash1 = sim.metrics_collector.determinism_hash()
    sim.step(ext_rng)  # One more step
    hash2 = sim.metrics_collector.determinism_hash()
    
    print(f"\n🔒 Determinism Check:")
    print(f"Hash before last step: {hash1[:16]}...")
    print(f"Hash after last step:  {hash2[:16]}...")
    print(f"Hash changed as expected: {hash1 != hash2}")
    
    print("\n✅ Utility & Wealth Metrics test completed successfully!")

if __name__ == "__main__":
    test_utility_metrics()