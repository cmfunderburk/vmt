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
    MinimalObserver,
    create_simulation_output,
    load_simulation_output
)
from econsim.simulation.factory import SimulationFactory
from econsim.simulation.config import SimConfig


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


class TestMinimalObserver:
    """Test MinimalObserver functionality."""
    
    def test_observer_creation(self):
        """Test creating minimal observer."""
        observer = MinimalObserver(
            progress_interval=100,
            enable_debugging=True,
            enable_performance_monitoring=True
        )
        
        assert observer is not None
        assert observer.progress_interval == 100
        assert observer.enable_debugging is True
        assert observer.enable_performance_monitoring is True
        assert observer.enabled is True
    
    def test_monitoring_stats(self):
        """Test monitoring statistics."""
        observer = MinimalObserver()
        
        # Start monitoring
        observer.start_monitoring(1000)
        
        # Simulate some steps
        for step in range(1, 101):
            observer.flush_step(step)
        
        stats = observer.get_monitoring_stats()
        
        assert stats['current_step'] == 100
        assert stats['total_steps'] == 1000
        assert stats['progress_percentage'] == 10.0
        assert stats['elapsed_time'] > 0
    
    def test_performance_monitoring(self):
        """Test performance monitoring capabilities."""
        observer = MinimalObserver(
            enable_performance_monitoring=True,
            enable_debugging=False
        )
        
        observer.start_monitoring(100)
        
        # Simulate steps with varying performance
        for step in range(1, 11):
            observer.flush_step(step)
            time.sleep(0.001)  # Simulate some processing time
        
        stats = observer.get_monitoring_stats()
        
        assert stats['average_step_time'] > 0
        assert stats['performance_monitoring_enabled'] is True


class TestHeadlessRunner:
    """Test HeadlessSimulationRunner functionality."""
    
    def test_runner_creation(self):
        """Test creating headless runner."""
        config = SimConfig(
            world_width=10,
            world_height=10,
            num_agents=5,
            steps=100
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
            world_width=5,
            world_height=5,
            num_agents=3,
            steps=10
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
        """Test headless runner with recording."""
        config = SimConfig(
            world_width=10,
            world_height=10,
            num_agents=5,
            steps=50
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
            metrics = runner.run(steps=50)
            
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
            assert loaded_file.header.agent_count == 5
            assert loaded_file.header.grid_width == 10
            assert loaded_file.header.grid_height == 10
    
    def test_runner_performance(self):
        """Test runner performance meets targets."""
        config = SimConfig(
            world_width=20,
            world_height=20,
            num_agents=10,
            steps=100
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
            world_width=10,
            world_height=10,
            num_agents=5,
            steps=100
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
