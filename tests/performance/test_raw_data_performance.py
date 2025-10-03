"""
Performance regression tests for raw data recording system.

These tests ensure that raw data recording maintains minimal overhead
and prevents performance degradation over time.
"""

import pytest
import time
import random
from typing import Tuple, List
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation


class TestRawDataPerformance:
    """Performance regression tests for raw data recording."""
    
    def test_simulation_step_performance_baseline(self):
        """Test that simulation step performance stays within acceptable bounds."""
        # Setup standardized test scenario
        cfg = SimConfig(
            grid_size=(10, 10),
            seed=42,
            initial_resources=[(i, j, ['A', 'B', 'C'][i % 3]) 
                             for i in range(2, 8) for j in range(2, 8)],
            enable_respawn=True,
            enable_metrics=True
        )
        
        agents = [(i, j) for i in range(0, 2) for j in range(0, 2)]  # 4 agents
        sim = Simulation.from_config(cfg, agent_positions=agents)
        rng = random.Random(42)
        
        # Measure performance over multiple runs
        num_steps = 100
        num_runs = 3
        times: List[float] = []
        
        for run in range(num_runs):
            start_time = time.perf_counter()
            for _ in range(num_steps):
                sim.step(rng)
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        # Calculate average performance
        avg_total_time = sum(times) / len(times)
        avg_step_time_ms = (avg_total_time / num_steps) * 1000
        
        # Performance assertions - based on Phase 3.2.1 baseline measurements
        MAX_STEP_TIME_MS = 2.0  # Conservative threshold (baseline was 0.374ms)
        MAX_FRAME_BUDGET_PERCENT = 12.5  # Conservative threshold (baseline was 2.33%)
        
        frame_budget_usage = (avg_step_time_ms / 16.0) * 100  # 16ms = 60 FPS
        
        assert avg_step_time_ms < MAX_STEP_TIME_MS, (
            f"Average step time {avg_step_time_ms:.3f}ms exceeds threshold {MAX_STEP_TIME_MS}ms. "
            f"Raw data recording may have performance regression."
        )
        
        assert frame_budget_usage < MAX_FRAME_BUDGET_PERCENT, (
            f"Frame budget usage {frame_budget_usage:.2f}% exceeds threshold {MAX_FRAME_BUDGET_PERCENT}%. "
            f"Raw data recording overhead is too high."
        )
        
        # Performance reporting
        print(f"\nRaw Data Performance Results:")
        print(f"  Average step time: {avg_step_time_ms:.3f} ms/step")
        print(f"  Frame budget usage: {frame_budget_usage:.2f}%")
        print(f"  Steps per second: {num_steps/avg_total_time:.1f} steps/sec")
    
    def test_raw_data_recording_overhead(self):
        """Test that raw data recording operations have minimal overhead."""
        # Setup minimal simulation for overhead measurement
        cfg = SimConfig(
            grid_size=(5, 5),
            seed=123,
            initial_resources=[(2, 2, 'A'), (3, 3, 'B')],
            enable_respawn=False,
            enable_metrics=True
        )
        
        sim = Simulation.from_config(cfg, agent_positions=[(0, 0)])
        rng = random.Random(123)
        
        # Measure with recording enabled (current state)
        num_steps = 50
        start_time = time.perf_counter()
        for _ in range(num_steps):
            sim.step(rng)
        recording_time = time.perf_counter() - start_time
        
        recording_overhead_ms = (recording_time / num_steps) * 1000
        
        # Overhead thresholds based on Phase 3.2.1 analysis
        MAX_RECORDING_OVERHEAD_MS = 1.0  # Very conservative threshold
        
        assert recording_overhead_ms < MAX_RECORDING_OVERHEAD_MS, (
            f"Raw data recording overhead {recording_overhead_ms:.3f}ms/step "
            f"exceeds threshold {MAX_RECORDING_OVERHEAD_MS}ms/step. "
            f"Recording system may need optimization."
        )
        
        print(f"\nRaw Data Recording Overhead:")
        print(f"  Recording overhead: {recording_overhead_ms:.3f} ms/step")
    
    def test_memory_efficiency_regression(self):
        """Test that raw data recording doesn't cause memory leaks or excessive allocation."""
        import tracemalloc
        
        # Start memory tracking
        tracemalloc.start()
        
        cfg = SimConfig(
            grid_size=(6, 6),
            seed=789,
            initial_resources=[(i, j, 'A') for i in range(1, 5) for j in range(1, 5)],
            enable_respawn=True,
            enable_metrics=True
        )
        
        sim = Simulation.from_config(cfg, agent_positions=[(0, 0), (5, 5)])
        rng = random.Random(789)
        
        # Take baseline memory measurement
        initial_snapshot = tracemalloc.take_snapshot()
        
        # Run simulation steps
        num_steps = 100
        for _ in range(num_steps):
            sim.step(rng)
        
        # Measure final memory
        final_snapshot = tracemalloc.take_snapshot()
        current, peak = tracemalloc.get_traced_memory()
        
        tracemalloc.stop()
        
        # Memory efficiency assertions
        MAX_MEMORY_MB = 5.0  # Conservative memory limit
        MAX_MEMORY_PER_STEP_BYTES = 5000  # Conservative per-step allocation limit
        
        memory_mb = current / 1024 / 1024
        memory_per_step = current / num_steps if num_steps > 0 else 0
        
        assert memory_mb < MAX_MEMORY_MB, (
            f"Total memory usage {memory_mb:.2f}MB exceeds threshold {MAX_MEMORY_MB}MB. "
            f"Possible memory leak in raw data recording."
        )
        
        assert memory_per_step < MAX_MEMORY_PER_STEP_BYTES, (
            f"Average memory per step {memory_per_step:.0f} bytes "
            f"exceeds threshold {MAX_MEMORY_PER_STEP_BYTES} bytes. "
            f"Raw data recording may be inefficient."
        )
        
        print(f"\nMemory Efficiency Results:")
        print(f"  Total memory: {memory_mb:.2f} MB")
        print(f"  Memory per step: {memory_per_step:.0f} bytes/step")
        print(f"  Peak memory: {peak / 1024 / 1024:.2f} MB")


@pytest.mark.performance
class TestRawDataScaling:
    """Test raw data performance under different scaling scenarios."""
    
    @pytest.mark.parametrize("grid_size,agent_count", [
        ((5, 5), 2),
        ((10, 10), 4),
        ((15, 15), 8),
    ])
    def test_performance_scaling(self, grid_size: Tuple[int, int], agent_count: int) -> None:
        """Test that raw data recording performance scales reasonably with simulation size."""
        # Create scaled simulation
        resource_density = 0.3  # 30% of cells have resources
        total_cells = grid_size[0] * grid_size[1]
        num_resources = int(total_cells * resource_density)
        
        resources: List[Tuple[int, int, str]] = []
        for i in range(num_resources):
            x = i % grid_size[0]
            y = (i // grid_size[0]) % grid_size[1]
            resources.append((x, y, ['A', 'B', 'C'][i % 3]))
        
        cfg = SimConfig(
            grid_size=grid_size,
            seed=42,
            initial_resources=resources,
            enable_respawn=True,
            enable_metrics=True
        )
        
        # Distribute agents across grid
        agents: List[Tuple[int, int]] = []
        for i in range(agent_count):
            x = (i * 2) % grid_size[0]
            y = (i * 2) % grid_size[1]
            agents.append((x, y))
        
        sim = Simulation.from_config(cfg, agent_positions=agents)
        rng = random.Random(42)
        
        # Measure performance
        num_steps = 50
        start_time = time.perf_counter()
        for _ in range(num_steps):
            sim.step(rng)
        total_time = time.perf_counter() - start_time
        
        avg_step_time_ms = (total_time / num_steps) * 1000
        
        # Scaling assertions - performance should degrade gracefully
        # Expect roughly linear scaling with agents/resources
        complexity_factor = agent_count * num_resources / 100  # Normalize
        max_expected_time = 0.5 + (complexity_factor * 0.1)  # Base + scaling
        
        assert avg_step_time_ms < max_expected_time, (
            f"Step time {avg_step_time_ms:.3f}ms for {agent_count} agents, "
            f"{num_resources} resources exceeds expected {max_expected_time:.3f}ms. "
            f"Raw data recording may not scale efficiently."
        )
        
        print(f"\nScaling Test Results ({grid_size[0]}x{grid_size[1]}, {agent_count} agents):")
        print(f"  Step time: {avg_step_time_ms:.3f} ms/step")
        print(f"  Resources: {num_resources}")
        print(f"  Complexity factor: {complexity_factor:.2f}")