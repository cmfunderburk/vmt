"""
Unit tests for the recording system.

Tests the direct recording approach without observer system overhead.
Focuses on performance, correctness, and file format validation.
"""

import pytest
import tempfile
import time
from pathlib import Path

from econsim.recording import (
    SimulationOutputFile,
    HeadlessSimulationRunner,
    SimulationCallbacks,
    create_simulation_output,
    load_simulation_output
)
from econsim.simulation.world import Simulation
from econsim.simulation.config import SimConfig
from econsim.tools.launcher.framework.test_configs import TEST_3_HIGH_DENSITY


class TestSimulationOutputFile:
    """Test SimulationOutputFile functionality."""
    
    def test_create_output_file(self):
        """Test creating a new simulation output file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_simulation.vmt"
            
            # Create output file
            output_file = create_simulation_output(
                output_path,
                snapshot_interval=50,
                config_hash="test_config"
            )
            
            assert output_file is not None
            assert output_file.filepath == output_path
            assert output_file.header.snapshot_interval == 50
            assert output_file.header.config_hash == "test_config"
            assert output_file.header.total_steps == 0
    
    def test_load_output_file(self):
        """Test loading an existing simulation output file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_simulation.vmt"
            
            # Create and write a simple output file
            output_file = create_simulation_output(output_path, snapshot_interval=10)
            output_file.finalize_recording()
            
            # Load the file
            loaded_file = load_simulation_output(output_path)
            
            assert loaded_file is not None
            assert loaded_file.filepath == output_path
            assert loaded_file.header.snapshot_interval == 10
    
    def test_file_format_validation(self):
        """Test file format validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_simulation.vmt"
            
            # Create valid file
            output_file = create_simulation_output(output_path)
            output_file.finalize_recording()
            
            # Should load successfully
            loaded_file = load_simulation_output(output_path)
            assert loaded_file is not None
            
            # Test invalid file
            invalid_path = Path(temp_dir) / "invalid.vmt"
            with open(invalid_path, 'wb') as f:
                f.write(b"INVALID_MAGIC_BYTES")
            
            with pytest.raises(ValueError, match="Invalid file format"):
                load_simulation_output(invalid_path)


class TestSimulationCallbacks:
    """Test SimulationCallbacks functionality."""
    
    def test_callbacks_creation(self):
        """Test creating simulation callbacks."""
        callbacks = SimulationCallbacks()
        
        assert callbacks is not None
        assert callbacks.is_enabled() is True
        assert len(callbacks.step_callbacks) == 0
        assert len(callbacks.error_callbacks) == 0
        assert len(callbacks.progress_callbacks) == 0
    
    def test_monitoring_stats(self):
        """Test monitoring statistics."""
        callbacks = SimulationCallbacks()
        
        # Start monitoring
        callbacks.start_monitoring(1000)
        
        # Simulate some steps
        for step in range(1, 101):
            callbacks.notify_step(step)
        
        stats = callbacks.finish_monitoring()
        
        assert stats['total_steps'] == 100
        assert stats['duration_seconds'] > 0
        assert stats['steps_per_second'] > 0
        assert stats['enabled'] is True
    
    def test_performance_monitoring(self):
        """Test performance monitoring capabilities."""
        callbacks = SimulationCallbacks()
        
        callbacks.start_monitoring(100)
        
        # Simulate steps with varying performance
        for step in range(1, 11):
            callbacks.notify_step(step)
            time.sleep(0.001)  # Simulate some processing time
        
        stats = callbacks.finish_monitoring()
        
        assert stats['duration_seconds'] > 0
        assert stats['steps_per_second'] > 0


class TestHeadlessRunner:
    """Test HeadlessSimulationRunner functionality."""
    
    def test_runner_creation(self):
        """Test creating headless runner."""
        config = SimConfig(
            grid_size=(10, 10),
            initial_resources=[(5, 5), (3, 3), (7, 7)]
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_run.vmt"
            
            runner = HeadlessSimulationRunner(
                config=config,
                output_path=output_path,
                snapshot_interval=10,
                enable_recording=True
            )
            
            assert runner is not None
            assert runner.config == config
            assert runner.output_path == output_path
            assert runner.snapshot_interval == 10
            assert runner.enable_recording is True
    
    def test_runner_without_recording(self):
        """Test headless runner without recording."""
        config = SimConfig(
            grid_size=(5, 5),
            initial_resources=[(2, 2), (3, 3)]
        )
        
        runner = HeadlessSimulationRunner(
            config=config,
            output_path="",  # No output path
            enable_recording=False
        )
        
        # Run simulation without recording
        metrics = runner.run(steps=10)
        
        assert metrics['total_steps_run'] == 10
        assert metrics['recording_enabled'] is False
        assert metrics['output_file_path'] is None
        assert metrics['simulation_created'] is True
    
    @pytest.mark.slow
    def test_runner_with_recording(self):
        """Test headless runner with recording using High Density Local baseline."""
        # Use TEST_3_HIGH_DENSITY as baseline configuration
        test_config = TEST_3_HIGH_DENSITY
        
        # Generate resources using the same logic as SimulationFactory
        import random
        random.seed(test_config.seed)
        resources = []
        for _ in range(int(test_config.grid_size[0] * test_config.grid_size[1] * test_config.resource_density)):
            x = random.randint(0, test_config.grid_size[0] - 1)
            y = random.randint(0, test_config.grid_size[1] - 1)
            resources.append((x, y))
        
        # Generate agent positions
        agent_positions = []
        for i in range(test_config.agent_count):
            x = random.randint(0, test_config.grid_size[0] - 1)
            y = random.randint(0, test_config.grid_size[1] - 1)
            agent_positions.append((x, y))
        
        config = SimConfig(
            grid_size=test_config.grid_size,
            initial_resources=resources,
            perception_radius=test_config.perception_radius,
            seed=test_config.seed,
            enable_respawn=True,
            enable_metrics=True,
            respawn_target_density=test_config.resource_density,
            respawn_rate=0.25
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_recording.vmt"
            
            runner = HeadlessSimulationRunner(
                config=config,
                output_path=output_path,
                snapshot_interval=10,
                enable_recording=True
            )
            
            # Run simulation with recording
            metrics = runner.run(steps=50, agent_positions=agent_positions)
            
            assert metrics['total_steps_run'] == 50
            assert metrics['recording_enabled'] is True
            assert metrics['output_file_path'] == str(output_path)
            assert metrics['file_size_bytes'] > 0
            assert metrics['snapshot_count'] > 0
            assert metrics['event_count'] > 0
            
            # Verify output file exists and is valid
            assert output_path.exists()
            
            # Load and verify the recorded file
            loaded_file = load_simulation_output(output_path)
            assert loaded_file.header.total_steps == 50
            assert loaded_file.header.agent_count == test_config.agent_count
            assert loaded_file.header.grid_width == test_config.grid_size[0]
            assert loaded_file.header.grid_height == test_config.grid_size[1]
    
    def test_runner_performance(self):
        """Test runner performance meets targets using High Density Local baseline."""
        # Use TEST_3_HIGH_DENSITY as baseline configuration
        test_config = TEST_3_HIGH_DENSITY
        
        # Generate resources using the same logic as SimulationFactory
        import random
        random.seed(test_config.seed)
        resources = []
        for _ in range(int(test_config.grid_size[0] * test_config.grid_size[1] * test_config.resource_density)):
            x = random.randint(0, test_config.grid_size[0] - 1)
            y = random.randint(0, test_config.grid_size[1] - 1)
            resources.append((x, y))
        
        config = SimConfig(
            grid_size=test_config.grid_size,
            initial_resources=resources,
            perception_radius=test_config.perception_radius,
            seed=test_config.seed,
            enable_respawn=True,
            enable_metrics=True,
            respawn_target_density=test_config.resource_density,
            respawn_rate=0.25
        )
        
        runner = HeadlessSimulationRunner(
            config=config,
            output_path="",  # No recording for performance test
            enable_recording=False
        )
        
        # Run simulation and measure performance
        start_time = time.time()
        metrics = runner.run(steps=100)
        end_time = time.time()
        
        total_time = end_time - start_time
        steps_per_second = metrics['total_steps_run'] / total_time
        
        # Performance targets:
        # - Should complete 100 steps in reasonable time
        # - Should achieve > 100 steps/second
        assert total_time < 10.0  # Should complete in under 10 seconds
        assert steps_per_second > 100  # Should achieve > 100 steps/second
        
        assert metrics['steps_per_second'] > 100


class TestRecordingPerformance:
    """Test recording system performance."""
    
    @pytest.mark.slow
    def test_recording_overhead(self):
        """Test that recording overhead is minimal."""
        config = SimConfig(
            world_width=15,
            world_height=15,
            num_agents=8,
            steps=200
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "overhead_test.vmt"
            
            # Run without recording
            runner_no_recording = HeadlessSimulationRunner(
                config=config,
                output_path="",
                enable_recording=False
            )
            
            start_time = time.time()
            metrics_no_recording = runner_no_recording.run(steps=200)
            time_no_recording = time.time() - start_time
            
            # Run with recording
            runner_with_recording = HeadlessSimulationRunner(
                config=config,
                output_path=output_path,
                snapshot_interval=50,
                enable_recording=True
            )
            
            start_time = time.time()
            metrics_with_recording = runner_with_recording.run(steps=200)
            time_with_recording = time.time() - start_time
            
            # Calculate overhead
            overhead = (time_with_recording - time_no_recording) / time_no_recording
            
            # Recording overhead should be < 20% (target is < 10%)
            assert overhead < 0.20, f"Recording overhead {overhead:.1%} exceeds 20%"
            
            # Verify recording worked
            assert metrics_with_recording['file_size_bytes'] > 0
            assert metrics_with_recording['snapshot_count'] > 0
    
    def test_file_size_targets(self):
        """Test that file sizes meet performance targets."""
        config = SimConfig(
            grid_size=(10, 10),
            initial_resources=[(5, 5), (3, 3), (7, 7), (2, 8), (8, 2)]
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "size_test.vmt"
            
            runner = HeadlessSimulationRunner(
                config=config,
                output_path=output_path,
                snapshot_interval=20,
                enable_recording=True
            )
            
            metrics = runner.run(steps=100)
            file_size_mb = metrics['file_size_bytes'] / (1024 * 1024)
            
            # File size should be reasonable (target is < 50MB for 10,000 steps with 100 agents)
            # For 100 steps with 5 agents, should be much smaller
            assert file_size_mb < 1.0, f"File size {file_size_mb:.2f}MB exceeds 1MB"


if __name__ == "__main__":
    pytest.main([__file__])
