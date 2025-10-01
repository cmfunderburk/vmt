"""Priority 2 Integration Tests - Edge Cases and Error Handling

Tests for edge cases, error conditions, and integration scenarios
that could cause regressions in the VMT simulation system.
"""

import pytest
from unittest.mock import Mock, patch

from econsim.gui.session_factory import SimulationSessionDescriptor, SessionFactory
from econsim.simulation.agent import Agent, AgentMode
from econsim.simulation.grid import Grid
from econsim.preferences.leontief import LeontiefPreference
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference


class TestInvalidScenarioHandling:
    """Test handling of invalid configurations and error conditions."""
    
    def test_random_preference_with_zero_agents(self):
        """Test random preference assignment with zero agents."""
        descriptor = SimulationSessionDescriptor(
            name='test_zero',
            mode='continuous',
            seed=42,
            grid_size=(5, 5),
            agents=0,  # Zero agents
            density=0.25,
            enable_respawn=True,
            enable_metrics=True,
            preference_type='random',
            turn_auto_interval_ms=None,
            viewport_size=320,
            start_paused=False
        )
        
        # Should handle gracefully
        controller = SessionFactory.build(descriptor)
        assert len(controller.simulation.agents) == 0
        
        # Should not crash when getting agent IDs
        agent_ids = controller.list_agent_ids()
        assert agent_ids == []
    
    def test_random_preference_with_large_agent_count(self):
        """Test random preference assignment with large number of agents."""
        descriptor = SimulationSessionDescriptor(
            name='test_large',
            mode='continuous',
            seed=42,
            grid_size=(20, 20),
            agents=100,  # Large number of agents
            density=0.1,  # Low density to fit them
            enable_respawn=True,
            enable_metrics=True,
            preference_type='random',
            turn_auto_interval_ms=None,
            viewport_size=320,
            start_paused=False
        )
        
        controller = SessionFactory.build(descriptor)
        sim = controller.simulation
        
        # Should create all agents
        assert len(sim.agents) == 100
        
        # Should distribute preferences across types
        preference_counts = {}
        for agent in sim.agents:
            pref_type = getattr(agent.preference, 'TYPE_NAME', 'unknown')
            preference_counts[pref_type] = preference_counts.get(pref_type, 0) + 1
        
        # Should have multiple preference types represented
        assert len(preference_counts) > 1, f"Expected multiple preference types, got {preference_counts}"
        
        # No type should dominate completely (with 100 agents, each type should get some share)
        max_count = max(preference_counts.values())
        assert max_count < 90, f"One preference type dominates too much: {preference_counts}"
    
    def test_invalid_preference_type_fallback(self):
        """Test behavior when invalid preference type is specified."""
        # Test with a preference type that doesn't exist
        descriptor = SimulationSessionDescriptor(
            name='test_invalid',
            mode='continuous',
            seed=42,
            grid_size=(5, 5),
            agents=3,
            density=0.25,
            enable_respawn=True,
            enable_metrics=True,
            preference_type='nonexistent_preference_type',
            turn_auto_interval_ms=None,
            viewport_size=320,
            start_paused=False
        )
        
        # Should fall back to a valid preference type (likely Cobb-Douglas)
        controller = SessionFactory.build(descriptor)
        sim = controller.simulation
        
        # Should create agents with valid preferences
        assert len(sim.agents) == 3
        for agent in sim.agents:
            assert hasattr(agent, 'preference')
            assert hasattr(agent.preference, 'utility')
            # Should be a known preference type
            pref_type = getattr(agent.preference, 'TYPE_NAME', None)
            assert pref_type in ['cobb_douglas', 'leontief', 'perfect_substitutes'], f"Unknown preference type: {pref_type}"


class TestLeontiefAgentEdgeCases:
    """Test edge cases specific to Leontief agent prospecting behavior."""
    
    def test_leontief_agent_on_grid_boundaries(self):
        """Test Leontief prospecting when agent is at grid boundaries."""
        agent = Agent(
            id=1,
            x=0,  # At left boundary
            y=0,  # At top boundary
            preference=LeontiefPreference(a=1.0, b=1.0),
            home_x=0,
            home_y=0
        )
        
        # Resources near boundaries
        grid = Grid(5, 5, [
            (0, 1, 'A'),  # Below agent
            (1, 0, 'B'),  # Right of agent
            (4, 4, 'A'),  # Far corner
            (4, 3, 'B'),  # Far corner complement
        ])
        
        agent.select_target(grid)
        
        # Should select one of the nearby resources despite boundary position
        assert agent.target is not None
        assert agent.mode == AgentMode.FORAGE
        assert agent.target in [(0, 1), (1, 0)], f"Should select nearby resource, got {agent.target}"
    
    def test_leontief_agent_with_same_position_resources(self):
        """Test Leontief prospecting when multiple resources are at same distance."""
        agent = Agent(
            id=1,
            x=2,
            y=2,
            preference=LeontiefPreference(a=1.0, b=1.0),
            home_x=2,
            home_y=2
        )
        
        # Multiple resources at same distance (Manhattan = 1)
        grid = Grid(5, 5, [
            (1, 2, 'A'),  # West, distance 1
            (3, 2, 'A'),  # East, distance 1
            (2, 1, 'B'),  # North, distance 1
            (2, 3, 'B'),  # South, distance 1
        ])
        
        # Should be deterministic despite multiple options
        targets = []
        for _ in range(5):
            agent.target = None
            agent.select_target(grid)
            targets.append(agent.target)
        
        # All selections should be identical (deterministic)
        assert len(set(targets)) == 1, f"Non-deterministic selections: {targets}"
        assert targets[0] is not None
    
    def test_leontief_agent_with_unreachable_complements(self):
        """Test Leontief behavior when complements are outside perception radius."""
        agent = Agent(
            id=1,
            x=1,
            y=1,
            preference=LeontiefPreference(a=1.0, b=1.0),
            home_x=1,
            home_y=1
        )
        
        # Resources where complements are very far apart
        grid = Grid(20, 20, [
            (2, 1, 'A'),  # Close good1
            (18, 18, 'B'),  # Very far good2 (outside perception radius)
        ])
        
        agent.select_target(grid)
        
        # Should go idle since no viable prospect pairs within perception
        assert agent.mode == AgentMode.IDLE
        assert agent.target is None
    
    def test_leontief_agent_resource_disappears_during_approach(self):
        """Test behavior when target resource disappears while agent approaches."""
        agent = Agent(
            id=1,
            x=0,
            y=0,
            preference=LeontiefPreference(a=1.0, b=1.0),
            home_x=0,
            home_y=0
        )
        
        # Initial grid with resources
        grid = Grid(5, 5, [(2, 0, 'A'), (2, 2, 'B')])
        
        # Agent selects target
        agent.select_target(grid)
        initial_target = agent.target
        assert initial_target == (2, 0)
        
        # Simulate resource disappearing (someone else collected it)
        grid = Grid(5, 5, [(2, 2, 'B')])  # Only B resource remains
        
        # Agent should re-evaluate and go idle (no complements for remaining resource)
        agent.select_target(grid)
        assert agent.mode == AgentMode.IDLE
        assert agent.target is None


class TestCrossFeatureIntegration:
    """Test integration between multiple features."""
    
    def test_random_preference_with_highlighting_integration(self):
        """Test that random preference assignment works with agent highlighting."""
        descriptor = SimulationSessionDescriptor(
            name='test_integration',
            mode='continuous',
            seed=42,
            grid_size=(8, 8),
            agents=5,
            density=0.2,
            enable_respawn=True,
            enable_metrics=True,
            preference_type='random',
            turn_auto_interval_ms=None,
            viewport_size=320,
            start_paused=False
        )
        
        controller = SessionFactory.build(descriptor)
        
        # Test that we can get agent IDs (needed for highlighting)
        agent_ids = controller.list_agent_ids()
        assert len(agent_ids) == 5
        
        # Test that we can get preference types (displayed in inspector)
        for aid in agent_ids:
            pref_type = controller.agent_preference_type(aid)
            assert pref_type in ['Cobb-Douglas', 'Leontief', 'Perfect Substitutes', 'Random', 'cobb_douglas', 'leontief', 'perfect_substitutes']
            
            # Test other inspector methods work
            carry_bundle = controller.agent_carry_bundle(aid)
            assert isinstance(carry_bundle, tuple)
            assert len(carry_bundle) == 2
            
            home_bundle = controller.agent_home_bundle(aid)
            assert isinstance(home_bundle, tuple) 
            assert len(home_bundle) == 2
            
            utility = controller.agent_carry_utility(aid)
            assert isinstance(utility, (int, float))
    
    def test_leontief_prospecting_with_respawn_system(self):
        """Test Leontief prospecting behavior when resources respawn."""
        # Create simulation with Leontief agents and respawn enabled
        descriptor = SimulationSessionDescriptor(
            name='test_respawn',
            mode='continuous',
            seed=42,
            grid_size=(6, 6),
            agents=2,
            density=0.3,
            enable_respawn=True,
            enable_metrics=True,
            preference_type='leontief',  # All Leontief agents
            turn_auto_interval_ms=None,
            viewport_size=320,
            start_paused=False
        )
        
        controller = SessionFactory.build(descriptor)
        sim = controller.simulation
        
        # Verify agents have Leontief preferences
        for agent in sim.agents:
            assert getattr(agent.preference, 'TYPE_NAME', '') == 'leontief'
        
        # Let agents make some decisions
        initial_modes = [agent.mode for agent in sim.agents]
        
        # Step simulation a few times
        for _ in range(3):
            sim.step(controller._manual_rng)
        
        # At least some agents should be in FORAGE mode (not all idle)
        final_modes = [agent.mode for agent in sim.agents]
        forage_count = sum(1 for mode in final_modes if mode == AgentMode.FORAGE)
        
        # With resources and Leontief prospecting, at least one agent should be foraging
        assert forage_count > 0, f"Expected some agents foraging, got modes: {final_modes}"
    
    def test_mixed_preference_types_interaction(self):
        """Test that different preference types coexist properly."""
        # Manually create simulation with mixed preference types
        grid = Grid(8, 8, [(1, 1, 'A'), (2, 2, 'B'), (5, 5, 'A'), (6, 6, 'B')])
        
        agents = [
            Agent(id=1, x=0, y=0, preference=CobbDouglasPreference(alpha=0.5)),
            Agent(id=2, x=0, y=1, preference=LeontiefPreference(a=1.0, b=1.0)),
            Agent(id=3, x=1, y=0, preference=PerfectSubstitutesPreference(a=1.0, b=1.0)),
        ]
        
        # Each agent should select targets based on their preference
        for agent in agents:
            agent.select_target(grid)
        
        # All agents should have made decisions (not stuck)
        for i, agent in enumerate(agents):
            assert agent.mode in [AgentMode.FORAGE, AgentMode.IDLE], f"Agent {i} in unexpected mode: {agent.mode}"
        
        # Leontief agent should use prospecting if at (0,0) bundle
        leontief_agent = agents[1]
        if leontief_agent.carrying == {'good1': 0, 'good2': 0}:
            # Should either find a prospect or go idle
            assert leontief_agent.mode in [AgentMode.FORAGE, AgentMode.IDLE]


class TestSystemStabilityUnderStress:
    """Test system stability under edge conditions."""
    
    def test_rapid_preference_type_switching(self):
        """Test system stability when rapidly switching preference types."""
        base_descriptor = SimulationSessionDescriptor(
            name='test_rapid',
            mode='continuous',
            seed=42,
            grid_size=(5, 5),
            agents=3,
            density=0.3,
            enable_respawn=True,
            enable_metrics=True,
            preference_type='cobb_douglas',  # Will be changed
            turn_auto_interval_ms=None,
            viewport_size=320,
            start_paused=False
        )
        
        # Test rapid switching between preference types
        preference_types = ['cobb_douglas', 'leontief', 'perfect_substitutes', 'random']
        
        for pref_type in preference_types:
            base_descriptor.preference_type = pref_type
            
            # Should not crash
            controller = SessionFactory.build(base_descriptor)
            sim = controller.simulation
            
            # Should create valid agents
            assert len(sim.agents) == 3
            
            # All agents should have valid preferences
            for agent in sim.agents:
                assert hasattr(agent.preference, 'utility')
                
                # Test utility calculation doesn't crash
                test_bundle = (1.0, 1.0)
                utility = agent.preference.utility(test_bundle)
                assert isinstance(utility, (int, float))
                assert utility >= 0  # Utility should be non-negative for positive bundles
    
    def test_controller_method_resilience(self):
        """Test controller methods handle edge cases gracefully."""
        descriptor = SimulationSessionDescriptor(
            name='test_resilience',
            mode='continuous',
            seed=42,
            grid_size=(5, 5),
            agents=2,
            density=0.2,
            enable_respawn=True,
            enable_metrics=True,
            preference_type='random',
            turn_auto_interval_ms=None,
            viewport_size=320,
            start_paused=False
        )
        
        controller = SessionFactory.build(descriptor)
        
        # Test with invalid agent IDs
        invalid_ids = [-1, 999, None]
        
        for invalid_id in invalid_ids:
            try:
                # These should either return sensible defaults or raise expected exceptions
                carry_bundle = controller.agent_carry_bundle(invalid_id)
                # If it returns something, should be a valid tuple
                if carry_bundle is not None:
                    assert isinstance(carry_bundle, tuple)
                    assert len(carry_bundle) == 2
            except (KeyError, TypeError, AttributeError):
                # Expected exceptions for invalid IDs
                pass
            
            try:
                pref_type = controller.agent_preference_type(invalid_id)
                # If it returns something, should be a string
                if pref_type is not None:
                    assert isinstance(pref_type, str)
            except (KeyError, TypeError, AttributeError):
                # Expected exceptions for invalid IDs
                pass
    
    def test_empty_grid_stability(self):
        """Test system stability with empty resource grid."""
        descriptor = SimulationSessionDescriptor(
            name='test_empty',
            mode='continuous',
            seed=42,
            grid_size=(5, 5),
            agents=3,
            density=0.0,  # No resources
            enable_respawn=False,  # No respawn
            enable_metrics=True,
            preference_type='random',
            turn_auto_interval_ms=None,
            viewport_size=320,
            start_paused=False
        )
        
        controller = SessionFactory.build(descriptor)
        sim = controller.simulation
        
        # Should create agents even with no resources
        assert len(sim.agents) == 3
        
        # Step simulation several times - should not crash
        for _ in range(10):
            sim.step(controller._manual_rng)
        
        # All agents should be idle (no resources to forage)
        for agent in sim.agents:
            assert agent.mode == AgentMode.IDLE
            assert agent.target is None