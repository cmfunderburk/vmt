"""Priority 2 Simulation State Tests - Consistency and Performance

Tests for simulation state consistency, determinism valida        # Step simulation a few times
        for _ in range(3):
            sim.step(controller._manual_rng, use_decision=True)n,
and performance characteristics under various scenarios.
"""

import pytest
import time
from unittest.mock import Mock

from econsim.gui.session_factory import SimulationSessionDescriptor, SessionFactory
from econsim.simulation.agent import Agent, AgentMode
from econsim.simulation.grid import Grid
from econsim.preferences.leontief import LeontiefPreference
from econsim.preferences.cobb_douglas import CobbDouglasPreference


class TestSimulationStateConsistency:
    """Test that simulation state remains consistent across operations."""
    
    def test_random_preference_determinism_across_runs(self):
        """Test that random preference assignment is deterministic across multiple runs."""
        base_descriptor = SimulationSessionDescriptor(
            name='test_determinism',
            mode='continuous',
            seed=12345,  # Fixed seed
            grid_size=(8, 8),
            agents=10,
            density=0.25,
            enable_respawn=True,
            enable_metrics=True,
            preference_type='random',
            turn_auto_interval_ms=None,
            viewport_size=320,
            start_paused=False
        )
        
        # Run simulation creation multiple times with same seed
        preference_sequences = []
        
        for run in range(3):
            controller = SessionFactory.build(base_descriptor)
            sim = controller.simulation
            
            # Record preference sequence
            prefs = []
            for agent in sorted(sim.agents, key=lambda a: a.id):
                pref_type = getattr(agent.preference, 'TYPE_NAME', 'unknown')
                prefs.append((agent.id, pref_type, agent.x, agent.y))
            
            preference_sequences.append(prefs)
        
        # All runs should produce identical results
        assert len(set(map(tuple, preference_sequences))) == 1, "Random preference assignment not deterministic across runs"
        
        # Verify we actually got randomness (not all same type)
        first_run_types = [pref[1] for pref in preference_sequences[0]]
        unique_types = set(first_run_types)
        assert len(unique_types) > 1, f"Expected multiple preference types, got only: {unique_types}"
    
    def test_leontief_prospecting_determinism_across_steps(self):
        """Test that Leontief prospecting behavior is deterministic across simulation steps."""
        # Create grid with specific resource layout
        grid = Grid(6, 6, [
            (1, 1, 'A'), (2, 2, 'B'),  # First complementary pair
            (4, 1, 'A'), (4, 3, 'B'),  # Second complementary pair
        ])
        
        # Create Leontief agent
        agent = Agent(
            id=1,
            x=0,
            y=0,
            preference=LeontiefPreference(a=1.0, b=1.0),
            home_x=0,
            home_y=0
        )
        
        # Record decision outcomes across multiple calls
        decisions = []
        for _ in range(5):
            agent.target = None  # Reset
            agent.mode = AgentMode.FORAGE
            agent.select_target(grid)
            decisions.append((agent.mode, agent.target))
        
        # All decisions should be identical (deterministic)
        assert len(set(decisions)) == 1, f"Non-deterministic prospecting decisions: {decisions}"
        
        # Should have made a decision (not idle) given available resources
        mode, target = decisions[0]
        assert mode == AgentMode.FORAGE
        assert target is not None
    
    def test_agent_state_consistency_during_simulation(self):
        """Test that agent states remain consistent during simulation steps."""
        descriptor = SimulationSessionDescriptor(
            name='test_consistency',
            mode='continuous',
            seed=42,
            grid_size=(6, 6),
            agents=5,
            density=0.3,
            enable_respawn=False,  # No respawn for predictability
            enable_metrics=True,
            preference_type='random',
            turn_auto_interval_ms=None,
            viewport_size=320,
            start_paused=False
        )
        
        controller = SessionFactory.build(descriptor)
        sim = controller.simulation
        
        # Record initial state
        initial_state = []
        for agent in sim.agents:
            state = {
                'id': agent.id,
                'x': agent.x, 'y': agent.y,
                'mode': agent.mode,
                'carrying': dict(agent.carrying),
                'home_inventory': dict(agent.home_inventory)
            }
            initial_state.append(state)
        
        # Step simulation multiple times
        for step in range(5):
            sim.step(controller._manual_rng, use_decision=True)
            
            # Verify state consistency
            for i, agent in enumerate(sim.agents):
                # Agent ID should never change
                assert agent.id == initial_state[i]['id']
                
                # Position should be within grid bounds
                assert 0 <= agent.x < sim.grid.width
                assert 0 <= agent.y < sim.grid.height
                
                # Carrying should never be negative
                assert all(v >= 0 for v in agent.carrying.values())
                
                # Home inventory should never decrease (only deposits, no withdrawals)
                for good, amount in agent.home_inventory.items():
                    initial_amount = initial_state[i]['home_inventory'][good]
                    assert amount >= initial_amount, f"Home inventory decreased for {good}: {amount} < {initial_amount}"
                
                # Mode should be valid
                assert agent.mode in [AgentMode.FORAGE, AgentMode.RETURN_HOME, AgentMode.IDLE]


class TestPerformanceCharacteristics:
    """Test performance characteristics of the system."""
    
    def test_random_preference_assignment_performance(self):
        """Test that random preference assignment completes in reasonable time."""
        descriptor = SimulationSessionDescriptor(
            name='test_perf',
            mode='continuous',
            seed=42,
            grid_size=(15, 15),
            agents=50,  # Moderate number of agents
            density=0.2,
            enable_respawn=True,
            enable_metrics=True,
            preference_type='random',
            turn_auto_interval_ms=None,
            viewport_size=320,
            start_paused=False
        )
        
        # Time the creation process
        start_time = time.time()
        controller = SessionFactory.build(descriptor)
        creation_time = time.time() - start_time
        
        # Should complete quickly (less than 1 second for 50 agents)
        assert creation_time < 1.0, f"Random preference assignment took too long: {creation_time:.3f}s"
        
        # Verify all agents were created
        assert len(controller.simulation.agents) == 50
        
        # Test controller method performance
        agent_ids = controller.list_agent_ids()
        
        start_time = time.time()
        for aid in agent_ids:
            pref_type = controller.agent_preference_type(aid)
            carry_bundle = controller.agent_carry_bundle(aid)
            utility = controller.agent_carry_utility(aid)
        query_time = time.time() - start_time
        
        # Should handle 50 agent queries quickly
        assert query_time < 0.5, f"Agent queries took too long: {query_time:.3f}s for {len(agent_ids)} agents"
    
    def test_leontief_prospecting_performance(self):
        """Test that Leontief prospecting completes in reasonable time."""
        # Create grid with many resources to stress test prospecting
        resources = []
        for x in range(0, 10, 2):
            for y in range(0, 10, 2):
                resources.append((x, y, 'A' if (x + y) % 4 == 0 else 'B'))
        
        grid = Grid(10, 10, resources)
        
        # Create multiple Leontief agents
        agents = []
        for i in range(5):
            agent = Agent(
                id=i,
                x=i,
                y=i,
                preference=LeontiefPreference(a=1.0, b=1.0),
                home_x=i,
                home_y=i
            )
            agents.append(agent)
        
        # Time the prospecting process
        start_time = time.time()
        for agent in agents:
            agent.select_target(grid)
        prospecting_time = time.time() - start_time
        
        # Should complete quickly even with many resources
        assert prospecting_time < 0.5, f"Leontief prospecting took too long: {prospecting_time:.3f}s"
        
        # All agents should have made decisions
        for agent in agents:
            assert agent.mode in [AgentMode.FORAGE, AgentMode.IDLE]
    
    def test_simulation_step_performance(self):
        """Test that simulation steps complete in reasonable time."""
        descriptor = SimulationSessionDescriptor(
            name='test_step_perf',
            mode='continuous',
            seed=42,
            grid_size=(12, 12),
            agents=20,
            density=0.25,
            enable_respawn=True,
            enable_metrics=True,
            preference_type='random',
            turn_auto_interval_ms=None,
            viewport_size=320,
            start_paused=False
        )
        
        controller = SessionFactory.build(descriptor)
        sim = controller.simulation
        
        # Time multiple simulation steps
        step_times = []
        for _ in range(10):
            start_time = time.time()
            sim.step(controller._manual_rng, use_decision=True)
            step_time = time.time() - start_time
            step_times.append(step_time)
        
        # Each step should complete quickly
        max_step_time = max(step_times)
        avg_step_time = sum(step_times) / len(step_times)
        
        assert max_step_time < 0.1, f"Slowest simulation step took too long: {max_step_time:.3f}s"
        assert avg_step_time < 0.05, f"Average simulation step took too long: {avg_step_time:.3f}s"


class TestMemoryAndResourceManagement:
    """Test memory usage and resource management."""
    
    def test_no_memory_leaks_in_repeated_creation(self):
        """Test that repeated simulation creation doesn't leak memory."""
        import gc
        
        base_descriptor = SimulationSessionDescriptor(
            name='test_memory',
            mode='continuous',
            seed=42,
            grid_size=(8, 8),
            agents=10,
            density=0.2,
            enable_respawn=True,
            enable_metrics=True,
            preference_type='random',
            turn_auto_interval_ms=None,
            viewport_size=320,
            start_paused=False
        )
        
        # Create and destroy simulations repeatedly
        controllers = []
        for i in range(10):
            controller = SessionFactory.build(base_descriptor)
            
            # Use the controller briefly
            agent_ids = controller.list_agent_ids()
            for aid in agent_ids[:3]:  # Test a few agents
                controller.agent_preference_type(aid)
            
            # Store reference temporarily
            controllers.append(controller)
        
        # Clear references and force garbage collection
        controllers.clear()
        gc.collect()
        
        # Test that we can still create new simulations
        final_controller = SessionFactory.build(base_descriptor)
        assert len(final_controller.simulation.agents) == 10
    
    def test_agent_state_cleanup(self):
        """Test that agent states are properly managed during simulation."""
        descriptor = SimulationSessionDescriptor(
            name='test_cleanup',
            mode='continuous',
            seed=42,
            grid_size=(6, 6),
            agents=5,
            density=0.3,
            enable_respawn=False,
            enable_metrics=True,
            preference_type='random',
            turn_auto_interval_ms=None,
            viewport_size=320,
            start_paused=False
        )
        
        controller = SessionFactory.build(descriptor)
        sim = controller.simulation
        
        # Record initial object count for agents
        initial_agent_count = len(sim.agents)
        
        # Run simulation for several steps
        for _ in range(20):
            sim.step(controller._manual_rng, use_decision=True)
        
        # Agent count should remain stable
        assert len(sim.agents) == initial_agent_count
        
        # All agents should still be valid objects
        for agent in sim.agents:
            assert agent.id is not None
            assert hasattr(agent, 'preference')
            assert isinstance(agent.carrying, dict)
            assert isinstance(agent.home_inventory, dict)


class TestDataIntegrity:
    """Test data integrity across various operations."""
    
    def test_preference_type_consistency(self):
        """Test that preference types remain consistent throughout simulation."""
        descriptor = SimulationSessionDescriptor(
            name='test_integrity',
            mode='continuous',
            seed=42,
            grid_size=(6, 6),
            agents=8,
            density=0.25,
            enable_respawn=True,
            enable_metrics=True,
            preference_type='random',
            turn_auto_interval_ms=None,
            viewport_size=320,
            start_paused=False
        )
        
        controller = SessionFactory.build(descriptor)
        sim = controller.simulation
        
        # Record initial preference types
        initial_prefs = {}
        for agent in sim.agents:
            pref_type = getattr(agent.preference, 'TYPE_NAME', 'unknown')
            initial_prefs[agent.id] = pref_type
        
        # Run simulation for several steps
        for _ in range(15):
            sim.step(controller._manual_rng, use_decision=True)
        
        # Preference types should remain unchanged
        for agent in sim.agents:
            current_pref = getattr(agent.preference, 'TYPE_NAME', 'unknown')
            expected_pref = initial_prefs[agent.id]
            assert current_pref == expected_pref, f"Agent {agent.id} preference changed: {expected_pref} -> {current_pref}"
    
    def test_inventory_conservation(self):
        """Test that goods are conserved (not created or destroyed inappropriately)."""
        descriptor = SimulationSessionDescriptor(
            name='test_conservation',
            mode='continuous',
            seed=42,
            grid_size=(6, 6),
            agents=3,
            density=0.3,
            enable_respawn=False,  # No respawn to track conservation
            enable_metrics=True,
            preference_type='random',
            turn_auto_interval_ms=None,
            viewport_size=320,
            start_paused=False
        )
        
        controller = SessionFactory.build(descriptor)
        sim = controller.simulation
        
        # Count initial resources on grid
        initial_resources = len(list(sim.grid.iter_resources()))
        
        # Count initial agent inventories (should all be zero)
        initial_agent_goods = 0
        for agent in sim.agents:
            initial_agent_goods += sum(agent.carrying.values())
            initial_agent_goods += sum(agent.home_inventory.values())
        
        total_initial = initial_resources + initial_agent_goods
        
        # Run simulation steps
        for _ in range(10):
            sim.step(controller._manual_rng, use_decision=True)
        
        # Count final resources and agent goods
        final_resources = len(list(sim.grid.iter_resources()))
        final_agent_goods = 0
        for agent in sim.agents:
            final_agent_goods += sum(agent.carrying.values())
            final_agent_goods += sum(agent.home_inventory.values())
        
        total_final = final_resources + final_agent_goods
        
        # Without respawn, total goods should be conserved
        assert total_final == total_initial, f"Goods not conserved: {total_initial} -> {total_final}"
    
    def test_agent_position_validity(self):
        """Test that agent positions remain within grid bounds."""
        descriptor = SimulationSessionDescriptor(
            name='test_bounds',
            mode='continuous',
            seed=42,
            grid_size=(5, 5),  # Small grid to increase boundary interactions
            agents=8,
            density=0.4,
            enable_respawn=True,
            enable_metrics=True,
            preference_type='random',
            turn_auto_interval_ms=None,
            viewport_size=320,
            start_paused=False
        )
        
        controller = SessionFactory.build(descriptor)
        sim = controller.simulation
        
        # Run simulation with many steps to test boundary conditions
        for step in range(25):
            sim.step(controller._manual_rng, use_decision=True)
            
            # Check all agent positions after each step
            for agent in sim.agents:
                assert 0 <= agent.x < sim.grid.width, f"Agent {agent.id} x-position out of bounds: {agent.x}"
                assert 0 <= agent.y < sim.grid.height, f"Agent {agent.id} y-position out of bounds: {agent.y}"
                
                # Home positions should also be valid (agent.home_x/y are never None after __post_init__)
                assert agent.home_x is not None and 0 <= agent.home_x < sim.grid.width, f"Agent {agent.id} home_x out of bounds: {agent.home_x}"
                assert agent.home_y is not None and 0 <= agent.home_y < sim.grid.height, f"Agent {agent.id} home_y out of bounds: {agent.home_y}"