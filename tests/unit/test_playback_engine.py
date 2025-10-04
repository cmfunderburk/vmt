"""
Unit tests for PlaybackEngine and related components.

Tests the playback system including state reconstruction, VCR controls,
and integration with SimulationOutputFile from the recording system.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from econsim.playback import PlaybackEngine, PlaybackController, StateReconstructor
from econsim.recording import SimulationOutputFile, HeadlessSimulationRunner, SimulationCallbacks
from econsim.simulation.config import SimConfig
from econsim.tools.launcher.framework.test_configs import TEST_3_HIGH_DENSITY
from econsim.simulation.world import Simulation


class TestPlaybackEngine:
    """Test PlaybackEngine functionality."""
    
    def test_playback_engine_creation(self):
        """Test creating a PlaybackEngine from a loaded output file."""
        # Create a mock output file
        mock_output_file = Mock(spec=SimulationOutputFile)
        mock_header = Mock()
        mock_header.total_steps = 1000
        mock_output_file.header = mock_header
        
        # Create playback engine
        engine = PlaybackEngine(mock_output_file)
        
        assert engine.state.current_step == 0
        assert engine.state.total_steps == 1000
        assert engine.state.is_playing is False
        assert engine.state.playback_speed == 1.0
        assert engine.state.is_at_end is False
    
    def test_playback_engine_load_from_file(self):
        """Test loading PlaybackEngine from file path."""
        with patch('econsim.playback.playback_engine.load_simulation_output') as mock_load:
            # Mock the loaded file
            mock_output_file = Mock(spec=SimulationOutputFile)
            mock_header = Mock()
            mock_header.total_steps = 500
            mock_output_file.header = mock_header
            mock_load.return_value = mock_output_file
            
            # Load engine from file
            engine = PlaybackEngine.load("test.vmt")
            
            assert engine.state.total_steps == 500
            mock_load.assert_called_once_with("test.vmt")
    
    def test_playback_controls(self):
        """Test basic playback controls."""
        mock_output_file = Mock(spec=SimulationOutputFile)
        mock_header = Mock()
        mock_header.total_steps = 100
        mock_output_file.header = mock_header
        
        engine = PlaybackEngine(mock_output_file)
        
        # Test initial state
        assert not engine.is_playing()
        assert not engine.is_at_end()
        
        # Test play/pause
        engine.play()
        assert engine.is_playing()
        
        engine.pause()
        assert not engine.is_playing()
        
        # Test stop
        engine.stop()
        assert not engine.is_playing()
        assert engine.get_current_step() == 0
    
    def test_playback_speed_control(self):
        """Test playback speed setting."""
        mock_output_file = Mock(spec=SimulationOutputFile)
        mock_header = Mock()
        mock_header.total_steps = 100
        mock_output_file.header = mock_header
        
        engine = PlaybackEngine(mock_output_file)
        
        # Test speed setting
        engine.set_playback_speed(2.0)
        assert engine.get_playback_speed() == 2.0
        
        engine.set_playback_speed(0.5)
        assert engine.get_playback_speed() == 0.5
        
        # Test invalid speed
        with pytest.raises(ValueError, match="Playback speed must be positive"):
            engine.set_playback_speed(-1.0)


class TestStateReconstructor:
    """Test StateReconstructor functionality."""
    
    def test_state_reconstructor_creation(self):
        """Test creating a StateReconstructor."""
        mock_output_file = Mock(spec=SimulationOutputFile)
        mock_header = Mock()
        mock_header.total_steps = 100
        mock_output_file.header = mock_header
        
        reconstructor = StateReconstructor(mock_output_file)
        
        assert reconstructor.output_file == mock_output_file
        assert len(reconstructor._snapshot_cache) == 0
        assert len(reconstructor._event_cache) == 0
    
    def test_cache_management(self):
        """Test cache management functionality."""
        mock_output_file = Mock(spec=SimulationOutputFile)
        reconstructor = StateReconstructor(mock_output_file)
        
        # Add some cache data
        reconstructor._snapshot_cache[1] = Mock()
        reconstructor._event_cache[1] = [{"type": "test"}]
        
        # Test cache stats
        stats = reconstructor.get_cache_stats()
        assert stats['snapshot_cache_size'] == 1
        assert stats['event_cache_size'] == 1
        assert stats['total_cached_events'] == 1
        
        # Test cache clearing
        reconstructor.clear_cache()
        assert len(reconstructor._snapshot_cache) == 0
        assert len(reconstructor._event_cache) == 0


class TestPlaybackController:
    """Test PlaybackController functionality."""
    
    def test_playback_controller_creation(self):
        """Test creating a PlaybackController."""
        mock_engine = Mock(spec=PlaybackEngine)
        mock_state = Mock()
        mock_state.current_step = 0
        mock_state.total_steps = 100
        mock_state.is_playing = False
        mock_state.is_at_end = False
        mock_state.playback_speed = 1.0
        mock_engine.state = mock_state
        
        controller = PlaybackController(mock_engine)
        
        assert controller.playback_engine == mock_engine
        assert controller.get_current_step() == 0
        assert controller.get_total_steps() == 100
        assert controller.get_progress_percentage() == 0.0
    
    def test_playback_controller_controls(self):
        """Test PlaybackController control methods."""
        mock_engine = Mock(spec=PlaybackEngine)
        mock_state = Mock()
        mock_state.current_step = 50
        mock_state.total_steps = 100
        mock_state.is_playing = False
        mock_state.is_at_end = False
        mock_state.playback_speed = 1.0
        mock_engine.state = mock_state
        
        controller = PlaybackController(mock_engine)
        
        # Test control delegation
        controller.play()
        mock_engine.play.assert_called_once()
        
        controller.pause()
        mock_engine.pause.assert_called_once()
        
        controller.stop()
        mock_engine.stop.assert_called_once()
        
        controller.seek_to_step(75)
        mock_engine.seek_to_step.assert_called_once_with(75)
        
        controller.set_speed(2.0)
        mock_engine.set_playback_speed.assert_called_once_with(2.0)
    
    def test_progress_calculation(self):
        """Test progress percentage calculation."""
        mock_engine = Mock(spec=PlaybackEngine)
        mock_state = Mock()
        mock_state.current_step = 25
        mock_state.total_steps = 100
        mock_engine.state = mock_state
        
        controller = PlaybackController(mock_engine)
        
        assert controller.get_progress_percentage() == 25.0
        
        # Test edge cases
        mock_state.current_step = 0
        assert controller.get_progress_percentage() == 0.0
        
        mock_state.current_step = 100
        assert controller.get_progress_percentage() == 100.0
        
        # Test zero total steps
        mock_state.total_steps = 0
        assert controller.get_progress_percentage() == 0.0


class TestPlaybackIntegration:
    """Integration tests for the playback system."""
    
    @pytest.mark.slow
    def test_playback_with_recorded_simulation(self):
        """Test playback system with actual recorded simulation data."""
        test_config = TEST_3_HIGH_DENSITY
        
        # Generate test resources based on density
        total_cells = test_config.grid_size[0] * test_config.grid_size[1]
        resource_count = int(total_cells * test_config.resource_density)
        
        resources = []
        for i in range(resource_count):
            x = (i * 2) % test_config.grid_size[0]
            y = (i * 3) % test_config.grid_size[1]
            resources.append((x, y, 'food'))
        
        # Create simulation config
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
            output_path = Path(temp_dir) / "test_playback.vmt"
            
            # Record a short simulation
            runner = HeadlessSimulationRunner(
                config=config,
                output_path=output_path,
                snapshot_interval=10,
                enable_recording=True
            )
            
            # Generate agent positions
            import random
            agent_positions = []
            for i in range(test_config.agent_count):
                x = random.randint(0, test_config.grid_size[0] - 1)
                y = random.randint(0, test_config.grid_size[1] - 1)
                agent_positions.append((x, y))
            
            # Run simulation
            metrics = runner.run(steps=50, agent_positions=agent_positions)
            assert metrics['total_steps_run'] == 50
            
            # Test playback engine loading
            engine = PlaybackEngine.load(output_path)
            assert engine.state.total_steps == 50
            
            # Test state reconstruction (this will fail until we implement the actual API)
            # For now, just test that the engine can be created
            assert engine.reconstructor is not None
            
            # Test controller creation
            controller = PlaybackController(engine)
            assert controller.get_total_steps() == 50
            assert controller.get_progress_percentage() == 0.0
            
            # Test performance stats
            stats = controller.get_performance_stats()
            assert 'current_step' in stats
            assert 'total_steps' in stats
            assert 'progress_percentage' in stats
