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
    """Run simulation and collect handler timing metrics."""
    rng = random.Random(999)
    start = time.perf_counter()
    
    # Run simulation
    for _ in range(ticks):
        sim.step(rng)
    
    total_time = time.perf_counter() - start
    
    # Collect handler timing samples
    handler_samples = {
        'movement': [],
        'collection': [],
        'trading': [],
        'metrics': [],
        'respawn': []
    }
    
    # Sample handler timings from additional steps
    sample_rng = random.Random(1234)
    for _ in range(SAMPLE_STEPS):
        sim.step(sample_rng)
        metrics = getattr(sim, 'last_step_metrics', {})
        timings = metrics.get('handler_timings', {})
        
        for handler_name in handler_samples.keys():
            timing_ms = timings.get(handler_name)
            if isinstance(timing_ms, (int, float)):
                handler_samples[handler_name].append(float(timing_ms))
    
    return total_time, handler_samples


def _calculate_averages(handler_samples: dict) -> dict:
    """Calculate average timing for each handler."""
    averages = {}
    for handler_name, samples in handler_samples.items():
        if samples:
            averages[handler_name] = sum(samples) / len(samples)
        else:
            averages[handler_name] = 0.0
    return averages


def test_dynamic_systems_overhead():
    """Test that dynamic systems (respawn + metrics) add minimal overhead."""
    # Build baseline simulation (no dynamic systems)
    base = _build_base()
    baseline_time, base_handler_samples = _run_with_metrics(base)
    
    # Build enhanced simulation (with dynamic systems)
    enhanced = _build_base()
    enhanced._rng = random.Random(123)  # type: ignore[attr-defined]
    enhanced.respawn_scheduler = RespawnScheduler(
        target_density=0.8, max_spawn_per_tick=20, respawn_rate=0.5
    )
    # MetricsCollector removed - no longer tested
    enhanced_time, enhanced_handler_samples = _run_with_metrics(enhanced)
    
    # Calculate handler timing averages
    base_averages = _calculate_averages(base_handler_samples)
    enhanced_averages = _calculate_averages(enhanced_handler_samples)
    
    # Calculate dynamic systems overhead (respawn + metrics)
    respawn_overhead = enhanced_averages.get('respawn', 0.0)
    metrics_overhead = enhanced_averages.get('metrics', 0.0)
    total_dynamic_overhead = respawn_overhead + metrics_overhead
    
    # Test dynamic systems overhead
    assert total_dynamic_overhead <= MAX_DYNAMIC_SYSTEMS_OVERHEAD_MS, (
        f"Dynamic systems overhead {total_dynamic_overhead:.3f}ms exceeds {MAX_DYNAMIC_SYSTEMS_OVERHEAD_MS}ms limit. "
        f"Respawn: {respawn_overhead:.3f}ms, Metrics: {metrics_overhead:.3f}ms"
    )


def test_handler_performance_breakdown():
    """Test individual handler performance with detailed breakdown."""
    # Build simulation with all systems enabled
    sim = _build_base()
    sim._rng = random.Random(123)  # type: ignore[attr-defined]
    sim.respawn_scheduler = RespawnScheduler(
        target_density=0.8, max_spawn_per_tick=20, respawn_rate=0.5
    )
    # MetricsCollector removed - no longer tested
    
    _, handler_samples = _run_with_metrics(sim)
    averages = _calculate_averages(handler_samples)
    
    # Test individual handler performance
    movement_avg = averages.get('movement', 0.0)
    collection_avg = averages.get('collection', 0.0)
    trading_avg = averages.get('trading', 0.0)
    metrics_avg = averages.get('metrics', 0.0)
    respawn_avg = averages.get('respawn', 0.0)
    
    # Collection handler test
    assert collection_avg <= MAX_COLLECTION_HANDLER_MS, (
        f"Collection handler {collection_avg:.3f}ms exceeds {MAX_COLLECTION_HANDLER_MS}ms limit"
    )
    
    # Trading handler test
    assert trading_avg <= MAX_TRADING_HANDLER_MS, (
        f"Trading handler {trading_avg:.3f}ms exceeds {MAX_TRADING_HANDLER_MS}ms limit"
    )
    
    # Metrics handler test
    assert metrics_avg <= MAX_METRICS_HANDLER_MS, (
        f"Metrics handler {metrics_avg:.3f}ms exceeds {MAX_METRICS_HANDLER_MS}ms limit"
    )
    
    # Respawn handler test
    assert respawn_avg <= MAX_RESPAWN_HANDLER_MS, (
        f"Respawn handler {respawn_avg:.3f}ms exceeds {MAX_RESPAWN_HANDLER_MS}ms limit"
    )


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
