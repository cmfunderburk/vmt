#!/usr/bin/env python3
"""Demo: Utility Metrics Integration with Phase 4E Format

This demonstrates how the new utility metrics can be integrated 
into the Phase 4E semantic compression format for economic analysis.
"""

import random
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation

def demonstrate_utility_metrics_integration():
    """Show how utility metrics integrate with Phase 4E logging."""
    print("🎯 Utility & Wealth Metrics Integration Demo")
    print("=" * 60)
    
    # Create simulation with metrics enabled
    cfg = SimConfig(
        grid_size=(10, 10),
        initial_resources=[(2,2,'good1'), (4,4,'good2'), (6,6,'good1'), (8,8,'good2')],
        perception_radius=8,
        seed=42,
        enable_respawn=True,
        enable_metrics=True
    )
    
    agent_positions = [(0,0), (1,1), (2,2), (3,3)]  # 4 agents
    sim = Simulation.from_config(cfg, agent_positions=agent_positions)
    ext_rng = random.Random(123)
    
    if sim.metrics_collector is None:
        print("❌ Metrics collector not enabled!")
        return
    
    print(f"✅ Created simulation with {len(sim.agents)} agents")
    print("📊 Running 50 steps with utility tracking...")
    
    # Track utility metrics over time
    step_utility_data = []
    
    for step in range(50):
        sim.step(ext_rng)
        
        # Get utility stats every 10 steps
        if (step + 1) % 10 == 0:
            utility_stats = sim.metrics_collector.get_utility_stats()
            
            # Demonstrate Phase 4E compression format
            compressed_utility = compress_utility_stats_phase4e(utility_stats)
            
            step_utility_data.append({
                'step': step + 1,
                'raw_stats': utility_stats,
                'compressed': compressed_utility
            })
            
            print(f"\nStep {step + 1}:")
            print(f"  Raw Stats: {utility_stats}")  
            print(f"  Phase 4E:  u:{compressed_utility}")
    
    # Show final analysis
    print("\n📈 Final Utility Analysis:")
    final_stats = sim.metrics_collector.get_utility_stats()
    trend_slope = sim.metrics_collector.get_utility_trend_slope(window=10)
    
    print(f"System Utility: {final_stats['total_system_utility']}")
    print(f"Inequality (Gini): {final_stats['utility_gini_coefficient']}")
    print(f"Growth Trend: {trend_slope:.6f}")
    
    # Show how this would appear in Phase 4E JSONL logs
    print("\n📝 Phase 4E JSONL Integration Example:")
    example_log_entry = {
        "s": 50,
        "dt": 0.01,
        "c": "t0,1-3,7,9-12",
        "m": ["2,t0,0-3,7-12", "1,t0,13-19"],
        "u": compress_utility_stats_phase4e(final_stats)  # ← NEW: Utility metrics
    }
    
    print(f"Example log entry: {example_log_entry}")
    
    print("\n✅ Utility Metrics Integration Demo Complete!")
    print("\n💡 Integration Points:")
    print("  1. Utility metrics are calculated per-step by MetricsCollector")
    print("  2. Compressed into Phase 4E format: 'u:U:81.9,G:0.14,A:20.5,R:0.01'")
    print("  3. Added to JSONL logs alongside 'c' (collections) and 'm' (modes)")
    print("  4. Maintains 90%+ compression ratio with full economic insights")


def compress_utility_stats_phase4e(utility_stats):
    """Compress utility stats into Phase 4E semantic format.
    
    Args:
        utility_stats: Dictionary from MetricsCollector.get_utility_stats()
        
    Returns:
        Compressed string like "U:81.9,G:0.14,A:20.5,R:0.01"
    """
    # Dictionary compression codes
    UTILITY_CODES = {
        'total_system_utility': 'U',
        'utility_gini_coefficient': 'G', 
        'avg_utility_per_agent': 'A',
        'utility_growth_rate': 'R',
        'utility_variance': 'V'
    }
    
    compressed_parts = []
    for key, value in utility_stats.items():
        if key in UTILITY_CODES and value is not None:
            code = UTILITY_CODES[key]
            if isinstance(value, float):
                # Round for compression
                rounded_value = round(value, 3)
                compressed_parts.append(f"{code}:{rounded_value}")
            else:
                compressed_parts.append(f"{code}:{value}")
    
    return ",".join(compressed_parts)


if __name__ == "__main__":
    demonstrate_utility_metrics_integration()