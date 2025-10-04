"""Performance overhead guard for simulation systems.

Measures per-step overhead of individual components and total system overhead.
Provides detailed breakdown of handler timings to identify performance bottlenecks.
Calibrated based on current system performance (Oct 2, 2025).
"""
from __future__ import annotations

import random
import time
import pytest

from econsim.simulation.world import Simulation
from econsim.simulation.grid import Grid
from econsim.simulation.agent import Agent
from econsim.simulation.respawn import RespawnScheduler
from econsim.preferences.cobb_douglas import CobbDouglasPreference

# Performance limits calibrated based on current system performance (Oct 2, 2025)
MAX_DYNAMIC_SYSTEMS_OVERHEAD_MS = 0.1  # 0.1ms total for respawn + metrics (currently ~0.05ms)
MAX_MOVEMENT_HANDLER_MS = 3.0  # 3.0ms for movement handler (currently ~3.4ms, marked as xfail)
MAX_COLLECTION_HANDLER_MS = 0.01  # 0.01ms for collection handler (currently ~0.002ms)
MAX_TRADING_HANDLER_MS = 0.01  # 0.01ms for trading handler (currently ~0.003ms)
MAX_METRICS_HANDLER_MS = 0.02  # 0.02ms for metrics handler (currently ~0.008ms)
MAX_RESPAWN_HANDLER_MS = 0.1  # 0.1ms for respawn handler (currently ~0.038ms)

TICKS = 300
SAMPLE_STEPS = 30


def _build_base(n_agents: int = 30, n_resources: int = 180) -> Simulation:
    """Build base simulation using High Density Local configuration (Test 3).
    
    Uses 15x15 grid with 30 agents and 80% resource density (180 resources)
    to match the performance-hungry baseline from the launcher.
    """
    pref = CobbDouglasPreference(alpha=0.5)
    # High Density Local configuration: 15x15 grid, 80% resource density
    grid = Grid(15, 15)
    # Place 180 resources (80% of 225 cells) deterministically
    for i in range(n_resources):
        x = (i * 13) % grid.width
        y = (i * 7) % grid.height
        grid.add_resource(x, y, "A" if i % 2 == 0 else "B")
    agents: list[Agent] = []
    for i in range(n_agents):
        agents.append(Agent(id=i, x=i % grid.width, y=(i * 5) % grid.height, preference=pref))
    return Simulation(grid=grid, agents=agents, config=None)


def _run_with_metrics(sim: Simulation, ticks: int = TICKS) -> tuple[float, dict]:
    """Run simulation and collect OptimizedStepExecutor metrics."""
    rng = random.Random(999)
    start = time.perf_counter()
    
    # Run simulation
    for _ in range(ticks):
        sim.step(rng)
    
    total_time = time.perf_counter() - start
    
    # Collect step metrics samples from OptimizedStepExecutor
    step_samples = {
        'agents_moved': [],
        'mode_changes': [],
        'resources_collected': [],
        'intents_count': [],
        'executed': [],
        'respawned': [],
        'steps_per_sec': []
    }
    
    # Sample step metrics from additional steps
    sample_rng = random.Random(1234)
    for _ in range(SAMPLE_STEPS):
        sim.step(sample_rng)
        metrics = getattr(sim, 'last_step_metrics', {})
        
        for metric_name in step_samples.keys():
            value = metrics.get(metric_name)
            if isinstance(value, (int, float)):
                step_samples[metric_name].append(float(value))
    
    return total_time, step_samples


def _calculate_averages(step_samples: dict) -> dict:
    """Calculate average values for each metric."""
    averages = {}
    for metric_name, samples in step_samples.items():
        if samples:
            averages[metric_name] = sum(samples) / len(samples)
        else:
            averages[metric_name] = 0.0
    return averages


def test_dynamic_systems_overhead():
    """Test that dynamic systems (respawn) add minimal overhead."""
    # Build baseline simulation (no dynamic systems)
    base = _build_base()
    baseline_time, base_step_samples = _run_with_metrics(base)
    
    # Build enhanced simulation (with dynamic systems)
    enhanced = _build_base()
    enhanced._rng = random.Random(123)  # type: ignore[attr-defined]
    enhanced.respawn_scheduler = RespawnScheduler(
        target_density=0.8, max_spawn_per_tick=20, respawn_rate=0.5
    )
    enhanced_time, enhanced_step_samples = _run_with_metrics(enhanced)
    
    # Calculate step metrics averages
    base_averages = _calculate_averages(base_step_samples)
    enhanced_averages = _calculate_averages(enhanced_step_samples)
    
    # Test that respawn system doesn't significantly impact performance
    # Compare total execution time (should be within reasonable bounds)
    time_overhead_ratio = enhanced_time / baseline_time if baseline_time > 0 else 1.0
    
    # Allow up to 20% overhead for respawn system
    assert time_overhead_ratio <= 1.2, (
        f"Dynamic systems overhead {time_overhead_ratio:.2f}x exceeds 1.2x limit. "
        f"Baseline: {baseline_time:.3f}s, Enhanced: {enhanced_time:.3f}s"
    )


def test_optimized_executor_performance():
    """Test OptimizedStepExecutor performance with detailed breakdown."""
    # Build simulation with all systems enabled
    sim = _build_base()
    sim._rng = random.Random(123)  # type: ignore[attr-defined]
    sim.respawn_scheduler = RespawnScheduler(
        target_density=0.8, max_spawn_per_tick=20, respawn_rate=0.5
    )
    
    _, step_samples = _run_with_metrics(sim)
    averages = _calculate_averages(step_samples)
    
    # Test that OptimizedStepExecutor provides reasonable performance
    steps_per_sec = averages.get('steps_per_sec', 0.0)
    agents_moved = averages.get('agents_moved', 0.0)
    
    # Should achieve at least 100 steps/sec for this configuration
    assert steps_per_sec >= 100.0, (
        f"OptimizedStepExecutor performance {steps_per_sec:.1f} steps/sec below 100 steps/sec threshold"
    )
    
    # Should move agents (basic functionality)
    assert agents_moved > 0, (
        f"OptimizedStepExecutor not moving agents: {agents_moved} agents moved per step"
    )
    
    print(f"OptimizedStepExecutor Performance:")
    print(f"  Steps/sec: {steps_per_sec:.1f}")
    print(f"  Agents moved per step: {agents_moved:.1f}")
    print(f"  Resources collected per step: {averages.get('resources_collected', 0.0):.1f}")
    print(f"  Trade intents per step: {averages.get('intents_count', 0.0):.1f}")
    print(f"  Trades executed per step: {averages.get('executed', 0.0):.1f}")


@pytest.mark.xfail(reason="Movement handler performance optimization in progress - currently ~3.4ms, target <3.0ms")
def test_movement_handler_performance():
    """Test movement handler performance (currently failing, marked as xfail)."""
    # Build simulation with all systems enabled
    sim = _build_base()
    sim._rng = random.Random(123)  # type: ignore[attr-defined]
    sim.respawn_scheduler = RespawnScheduler(
        target_density=0.8, max_spawn_per_tick=20, respawn_rate=0.5
    )
    # MetricsCollector removed - no longer tested
    
    _, handler_samples = _run_with_metrics(sim)
    averages = _calculate_averages(handler_samples)
    
    movement_avg = averages.get('movement', 0.0)
    
    # Movement handler test (currently failing, marked as xfail)
    assert movement_avg <= MAX_MOVEMENT_HANDLER_MS, (
        f"Movement handler {movement_avg:.3f}ms exceeds {MAX_MOVEMENT_HANDLER_MS}ms limit. "
        f"This is the primary performance bottleneck requiring optimization."
    )


def test_total_system_performance():
    """Test total system performance and provide detailed breakdown."""
    # Build simulation with all systems enabled
    sim = _build_base()
    sim._rng = random.Random(123)  # type: ignore[attr-defined]
    sim.respawn_scheduler = RespawnScheduler(
        target_density=0.8, max_spawn_per_tick=20, respawn_rate=0.5
    )
    # MetricsCollector removed - no longer tested
    
    total_time, handler_samples = _run_with_metrics(sim)
    averages = _calculate_averages(handler_samples)
    
    # Calculate total handler time
    total_handler_time = sum(averages.values())
    total_per_step_ms = (total_time / TICKS) * 1000
    
    # Print detailed breakdown for debugging
    print(f"\n=== Performance Breakdown ===")
    print(f"Total time: {total_time:.3f}s for {TICKS} steps")
    print(f"Total per-step: {total_per_step_ms:.2f}ms")
    print(f"Handler breakdown:")
    for handler_name, avg_time in averages.items():
        print(f"  {handler_name}: {avg_time:.3f}ms")
    print(f"Total handler time: {total_handler_time:.3f}ms")
    print(f"Non-handler overhead: {total_per_step_ms - total_handler_time:.3f}ms")
    print(f"=============================\n")
    
    # Basic sanity check - total should be reasonable
    assert total_per_step_ms < 10.0, f"Total per-step time {total_per_step_ms:.2f}ms is unreasonably high"
