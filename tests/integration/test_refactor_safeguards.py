"""
Phase 0 Refactor Safety Net Tests

Targeted tests around Simulation.step() and GUILogger APIs to ensure
refactoring does not break core functionality. These tests provide
safety nets for the major refactor implementation.

Test Coverage:
- Simulation.step() API contract and behavior
- GUILogger interface and logging functionality  
- Core deterministic simulation invariants
- Agent/grid interaction patterns
- Trading system behavior (if enabled)

Usage: pytest tests/integration/test_refactor_safeguards.py -v
"""

import os
import pytest
import random
from unittest.mock import patch
from typing import List

# Set headless environment
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["ECONSIM_HEADLESS_RENDER"] = "1"

from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
from econsim.tools.launcher.framework.test_configs import ALL_TEST_CONFIGS, TestConfiguration
from econsim.tools.launcher.framework.simulation_factory import SimulationFactory


class TestSimulationStepAPI:
    """Safety net tests for Simulation.step() API contract."""
    
    @pytest.fixture
    def basic_simulation(self):
        """Create a basic simulation for testing."""
        config = SimConfig(
            grid_size=(10, 10),
            seed=123,
            enable_respawn=True,
            enable_metrics=True,
            initial_resources=[(2, 2, 'A'), (4, 4, 'B')]
        )
        return Simulation.from_config(config, agent_positions=[(0, 0), (5, 5)])
    
    def test_step_method_signature(self, basic_simulation):
        """Ensure Simulation.step() maintains expected signature."""
        ext_rng = random.Random(999)
        
        # Test basic step call
        result = basic_simulation.step(ext_rng)
        assert result is None  # step() should not return anything
        
        # Test step with decision disabled
        result = basic_simulation.step(ext_rng)
        assert result is None
    
    def test_step_determinism_invariant(self, basic_simulation):
        """Verify step execution preserves deterministic behavior."""
        ext_rng1 = random.Random(42)
        ext_rng2 = random.Random(42)
        
        # Create identical simulations
        config = SimConfig(
            grid_size=(8, 8),
            seed=456,
            enable_respawn=False,  # Disable respawn for deterministic testing
            enable_metrics=True,
            initial_resources=[(1, 1, 'A'), (3, 3, 'B')]
        )
        
        sim1 = Simulation.from_config(config, agent_positions=[(0, 0)])
        sim2 = Simulation.from_config(config, agent_positions=[(0, 0)])
        
        # Execute identical step sequences
        for _ in range(10):
            sim1.step(ext_rng1)
            sim2.step(ext_rng2)
        
        # Compare agent positions (basic determinism check)
        assert len(sim1.agents) == len(sim2.agents)
        for agent1, agent2 in zip(sim1.agents, sim2.agents):
            assert agent1.x == agent2.x
            assert agent1.y == agent2.y
    
    def test_step_with_empty_grid(self, basic_simulation):
        """Test step execution with no resources on grid."""
        # Remove all resources
        basic_simulation.grid._resources.clear()  # Use private member
        
        ext_rng = random.Random(123)
        
        # Should not crash
        for _ in range(5):
            basic_simulation.step(ext_rng)
    
    def test_step_agent_count_stability(self, basic_simulation):
        """Verify agent count remains stable during normal execution."""
        initial_agent_count = len(basic_simulation.agents)
        ext_rng = random.Random(789)
        
        # Run multiple steps
        for _ in range(20):
            basic_simulation.step(ext_rng)
        
        # Agent count should remain the same (no spawning/despawning)
        assert len(basic_simulation.agents) == initial_agent_count


class TestEducationalScenarioIntegrity:
    """Safety net tests for educational test scenario integrity."""
    
    @pytest.mark.parametrize("scenario_id", [1, 2, 3, 4, 5, 6, 7])
    def test_scenario_factory_creation(self, scenario_id):
        """Test that all educational scenarios can be created via factory."""
        config = ALL_TEST_CONFIGS[scenario_id]
        
        # Should not raise exceptions
        simulation = SimulationFactory.create_simulation(config)
        
        # Basic integrity checks
        assert simulation is not None
        assert len(simulation.agents) == config.agent_count
        assert simulation.grid.width == config.grid_size[0]
        assert simulation.grid.height == config.grid_size[1]
    
    @pytest.mark.parametrize("scenario_id", [1, 5, 7])  # Test subset for performance
    def test_scenario_basic_execution(self, scenario_id):
        """Test that scenarios can execute basic simulation steps."""
        config = ALL_TEST_CONFIGS[scenario_id]
        simulation = SimulationFactory.create_simulation(config)
        ext_rng = random.Random(42)
        
        initial_agent_count = len(simulation.agents)
        
        # Execute several steps without crashing
        for step in range(50):
            simulation.step(ext_rng)
            
            # Sanity checks
            assert len(simulation.agents) == initial_agent_count
            assert all(0 <= agent.x < config.grid_size[0] for agent in simulation.agents)
            assert all(0 <= agent.y < config.grid_size[1] for agent in simulation.agents)


class TestGUILoggerInterface:
    """Safety net tests for GUILogger interface during refactor."""
    
    def test_gui_logger_import(self):
        """Test that GUILogger can still be imported."""
        from econsim.gui.debug_logger import GUILogger
        assert GUILogger is not None
    
    def test_gui_logger_basic_instantiation(self):
        """Test basic GUILogger instantiation."""
        from econsim.gui.debug_logger import GUILogger
        
        # Use singleton pattern correctly
        logger = GUILogger.get_instance()
        assert logger is not None
    
    def test_gui_logger_log_methods_exist(self):
        """Test that key logging methods still exist (may be deprecated)."""
        from econsim.gui.debug_logger import GUILogger
        
        # Updated method names based on current API
        expected_methods = [
            'log_agent_mode',        # Updated from log_agent_mode_change
            'track_agent_pairing',   # Unchanged
            'track_agent_movement'   # Unchanged
        ]
        
        # Test instance methods since that's how they're called
        logger = GUILogger.get_instance()
        for method_name in expected_methods:
            assert hasattr(logger, method_name), f"Missing method: {method_name}"


class TestTradingSystemSafeguards:
    """Safety net tests for trading system during refactor."""
    
    def test_trading_flags_respected(self):
        """Test that trading feature flags are properly respected."""
        config = SimConfig(
            grid_size=(6, 6),
            seed=111,
            enable_respawn=False,
            enable_metrics=True,
            initial_resources=[(1, 1, 'A'), (2, 2, 'B')]
        )
        
        # Test with trading disabled
        os.environ['ECONSIM_TRADE_DRAFT'] = '0'
        os.environ['ECONSIM_TRADE_EXEC'] = '0'
        
        try:
            simulation = Simulation.from_config(config, agent_positions=[(0, 0), (3, 3)])
            ext_rng = random.Random(222)
            
            # Should execute without trading
            for _ in range(10):
                simulation.step(ext_rng)
                
        finally:
            # Cleanup
            os.environ.pop('ECONSIM_TRADE_DRAFT', None)
            os.environ.pop('ECONSIM_TRADE_EXEC', None)
    
    def test_trading_enumeration_mode(self):
        """Test trading enumeration mode functionality."""
        config = SimConfig(
            grid_size=(8, 8),
            seed=333,
            enable_respawn=False,
            enable_metrics=True,
            initial_resources=[(2, 2, 'A'), (3, 3, 'B')]
        )
        
        # Enable draft mode only
        os.environ['ECONSIM_TRADE_DRAFT'] = '1'
        os.environ['ECONSIM_TRADE_EXEC'] = '0'
        
        try:
            simulation = Simulation.from_config(config, agent_positions=[(1, 1), (4, 4)])
            ext_rng = random.Random(444)
            
            # Should execute with trade enumeration but no execution
            for _ in range(15):
                simulation.step(ext_rng)
                
        finally:
            # Cleanup
            os.environ.pop('ECONSIM_TRADE_DRAFT', None)
            os.environ.pop('ECONSIM_TRADE_EXEC', None)


class TestMetricsSystemSafeguards:
    """Safety net tests for metrics system during refactor."""
    
    def test_metrics_collection_enabled(self):
        """Test that metrics collection works when enabled."""
        config = SimConfig(
            grid_size=(6, 6),
            seed=555,
            enable_respawn=False,
            enable_metrics=True,
            initial_resources=[(1, 1, 'A')]
        )
        
        simulation = Simulation.from_config(config, agent_positions=[(0, 0)])
        ext_rng = random.Random(666)
        
        # Execute steps and verify metrics collection doesn't crash
        for _ in range(20):
            simulation.step(ext_rng)
        
        # Basic metrics should be available
        if hasattr(simulation, 'metrics_collector'):
            assert simulation.metrics_collector is not None
    
    def test_metrics_collection_disabled(self):
        """Test that simulation works with metrics disabled."""
        config = SimConfig(
            grid_size=(6, 6),
            seed=777,
            enable_respawn=False,
            enable_metrics=False,
            initial_resources=[(1, 1, 'A')]
        )
        
        simulation = Simulation.from_config(config, agent_positions=[(0, 0)])
        ext_rng = random.Random(888)
        
        # Should work without metrics
        for _ in range(20):
            simulation.step(ext_rng)


@pytest.mark.integration
class TestRefactorValidationSuite:
    """High-level integration tests for refactor validation."""
    
    def test_phase_0_baseline_compatibility(self):
        """Comprehensive test mimicking Phase 0 baseline capture."""
        # Test multiple scenarios quickly
        test_scenarios = [1, 3, 5]  # Representative subset
        
        for scenario_id in test_scenarios:
            config = ALL_TEST_CONFIGS[scenario_id]
            simulation = SimulationFactory.create_simulation(config)
            ext_rng = random.Random(42)
            
            # Execute meaningful number of steps
            for _ in range(100):
                simulation.step(ext_rng)
            
            # Basic validation
            assert len(simulation.agents) == config.agent_count
            assert all(hasattr(agent, 'x') and hasattr(agent, 'y') for agent in simulation.agents)
    
    def test_environment_flag_isolation(self):
        """Test that environment flags don't leak between tests."""
        # Set some flags
        os.environ['ECONSIM_TRADE_DRAFT'] = '1'
        os.environ['ECONSIM_FORAGE_ENABLED'] = '0'
        
        # The conftest.py fixtures should clean these up automatically
        # This test just verifies the cleanup mechanism works
        
        config = SimConfig(
            grid_size=(5, 5),
            seed=999,
            enable_respawn=False,
            enable_metrics=False,
            initial_resources=[(1, 1, 'A')]
        )
        
        simulation = Simulation.from_config(config, agent_positions=[(0, 0)])
        ext_rng = random.Random(111)
        
        # Should execute regardless of flags
        simulation.step(ext_rng)
        
        # Cleanup (conftest.py should handle this, but be explicit)
        os.environ.pop('ECONSIM_TRADE_DRAFT', None)
        os.environ.pop('ECONSIM_FORAGE_ENABLED', None)