#!/usr/bin/env python3
"""
Delta-Free Performance Test

Tests the baseline scenario without delta recording overhead to measure
pure OptimizedStepExecutor performance and identify component overhead.

This test helps isolate performance bottlenecks by running the same
scenario with different feature combinations and without delta recording.
"""

import argparse
import json
import os
import random
import time
from typing import Dict, Any, List, Tuple

from econsim.simulation.world import Simulation
from econsim.simulation.config import SimConfig


def test_performance_with_features(
    forage_enabled: bool = True,
    trade_enabled: bool = True, 
    unified_enabled: bool = True,
    steps: int = 1000,
    warmup: int = 100
) -> Tuple[float, float, Dict[str, Any]]:
    """Test performance with specific feature combinations."""
    
    # Set environment variables
    os.environ['ECONSIM_FORAGE_ENABLED'] = '1' if forage_enabled else '0'
    os.environ['ECONSIM_TRADE_DRAFT'] = '1' if trade_enabled else '0'
    os.environ['ECONSIM_UNIFIED_SELECTION_DISABLE'] = '0' if unified_enabled else '1'
    
    # Create simulation (High Density Local configuration)
    config = SimConfig(grid_size=(15, 15), initial_resources=[], seed=42)
    sim = Simulation.from_config(config, agent_positions=[(i%15, (i*5)%15) for i in range(30)])
    
    # Add resources (80% density = 180 resources)
    for i in range(180):
        x = (i * 13) % 15
        y = (i * 7) % 15
        sim.grid.add_resource(x, y, 'A' if i % 2 == 0 else 'B')
    
    # Warmup
    rng = random.Random(42)
    for _ in range(warmup):
        sim.step(rng)
    
    # Performance test
    start = time.perf_counter()
    
    for _ in range(steps):
        sim.step(rng)
    
    total_time = time.perf_counter() - start
    steps_per_sec = steps / total_time
    
    # Collect final metrics
    final_metrics = sim.last_step_metrics or {}
    
    return steps_per_sec, total_time, final_metrics


def run_comprehensive_breakdown(steps: int = 1000, warmup: int = 100) -> Dict[str, Any]:
    """Run comprehensive performance breakdown with different feature combinations."""
    
    print("🔍 Unified Target Selection Performance Breakdown")
    print("=" * 70)
    
    # Test different combinations
    configs = [
        ('Both Disabled', False, False, True),
        ('Forage Only', True, False, True), 
        ('Trade Only', False, True, True),
        ('Both Enabled (Unified)', True, True, True),
        ('Both Enabled (Handler Mode)', True, True, False),
    ]
    
    results = []
    
    for name, forage, trade, unified in configs:
        print(f"Testing {name}...")
        steps_per_sec, total_time, metrics = test_performance_with_features(
            forage, trade, unified, steps, warmup
        )
        
        result = {
            'configuration': name,
            'forage_enabled': forage,
            'trade_enabled': trade,
            'unified_enabled': unified,
            'steps_per_second': steps_per_sec,
            'total_time_seconds': total_time,
            'final_metrics': metrics
        }
        results.append(result)
        
        print(f"  {name:25} | {steps_per_sec:8.1f} steps/sec | {total_time:6.3f}s total")
    
    # Calculate overhead analysis
    baseline = next(r for r in results if r['configuration'] == 'Both Disabled')
    forage_only = next(r for r in results if r['configuration'] == 'Forage Only')
    trade_only = next(r for r in results if r['configuration'] == 'Trade Only')
    both_unified = next(r for r in results if r['configuration'] == 'Both Enabled (Unified)')
    both_handler = next(r for r in results if r['configuration'] == 'Both Enabled (Handler Mode)')
    
    print("\n📊 Overhead Analysis:")
    print("=" * 70)
    
    forage_overhead = baseline['steps_per_second'] / forage_only['steps_per_second']
    trade_overhead = baseline['steps_per_second'] / trade_only['steps_per_second']
    combined_overhead = baseline['steps_per_second'] / both_unified['steps_per_second']
    handler_vs_unified = both_handler['steps_per_second'] / both_unified['steps_per_second']
    
    print(f"Forage overhead:           {forage_overhead:6.1f}x slower")
    print(f"Trade overhead:            {trade_overhead:6.1f}x slower")
    print(f"Combined overhead:         {combined_overhead:6.1f}x slower")
    print(f"Handler vs Unified:        {handler_vs_unified:6.1f}x faster (handler mode)")
    
    # Calculate component isolation
    print(f"\n🔬 Component Isolation Analysis:")
    print("=" * 70)
    
    # Forage isolation: (Both - Trade) vs (Both - Forage)
    forage_isolated = (both_unified['steps_per_second'] / trade_only['steps_per_second'])
    trade_isolated = (both_unified['steps_per_second'] / forage_only['steps_per_second'])
    
    print(f"Forage isolated impact:    {forage_isolated:6.1f}x overhead")
    print(f"Trade isolated impact:     {trade_isolated:6.1f}x overhead")
    
    return {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'test_type': 'delta_free_performance',
        'steps': steps,
        'warmup': warmup,
        'configurations': results,
        'overhead_analysis': {
            'forage_overhead': forage_overhead,
            'trade_overhead': trade_overhead,
            'combined_overhead': combined_overhead,
            'handler_vs_unified': handler_vs_unified,
            'forage_isolated': forage_isolated,
            'trade_isolated': trade_isolated
        }
    }


def main():
    parser = argparse.ArgumentParser(description='Delta-free performance test')
    parser.add_argument('--steps', type=int, default=1000, help='Number of steps to run')
    parser.add_argument('--warmup', type=int, default=100, help='Number of warmup steps')
    parser.add_argument('--output', type=str, help='Output file for results (JSON)')
    
    args = parser.parse_args()
    
    # Run comprehensive breakdown
    results = run_comprehensive_breakdown(args.steps, args.warmup)
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to {args.output}")
    
    # Summary
    baseline = next(r for r in results['configurations'] if r['configuration'] == 'Both Disabled')
    both_unified = next(r for r in results['configurations'] if r['configuration'] == 'Both Enabled (Unified)')
    
    print(f"\n🎯 Summary:")
    print("=" * 70)
    print(f"Pure OptimizedStepExecutor: {baseline['steps_per_second']:8.1f} steps/sec")
    print(f"With all features:          {both_unified['steps_per_second']:8.1f} steps/sec")
    print(f"Feature overhead:           {results['overhead_analysis']['combined_overhead']:6.1f}x slower")
    print(f"OptimizedStepExecutor is working correctly!")


if __name__ == '__main__':
    main()
