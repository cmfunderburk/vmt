"""Test random preference assignment functionality.

Tests the random preference assignment feature added in commit 554b5d3,
ensuring deterministic behavior, proper distribution, and robust error handling.
"""

import pytest

from econsim.gui.session_factory import SimulationSessionDescriptor, SessionFactory
from econsim.gui.simulation_controller import SimulationController
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference
from econsim.preferences.leontief import LeontiefPreference


def test_random_preference_deterministic():
    """Test that same seed produces same preference distribution."""
    descriptor = SimulationSessionDescriptor(
        name='determinism_test',
        mode='continuous',
        seed=42,
        grid_size=(8, 8),
        agents=6,
        density=0.2,
        enable_respawn=False,
        enable_metrics=False,
        preference_type='random',
        turn_auto_interval_ms=None,
        viewport_size=320,
        start_paused=False
    )
    
    # Create two simulations with same seed
    controller1 = SessionFactory.build(descriptor)
    controller2 = SessionFactory.build(descriptor)
    
    # Get preference types from both simulations
    agents1 = controller1.simulation.agents
    agents2 = controller2.simulation.agents
    
    prefs1 = [getattr(agent.preference, 'TYPE_NAME', 'unknown') for agent in agents1]
    prefs2 = [getattr(agent.preference, 'TYPE_NAME', 'unknown') for agent in agents2]
    
    # Should be identical
    assert prefs1 == prefs2, f"Same seed produced different distributions: {prefs1} vs {prefs2}"
    
    # Should have some variety (not all the same preference)
    unique_prefs = set(prefs1)
    assert len(unique_prefs) > 1, f"No variety in preferences: {prefs1}"


def test_random_preference_distribution():
    """Test that random assignment uses all preference types over multiple runs."""
    all_seen_types = set()
    
    # Test with different seeds to see variety
    for seed in [10, 20, 30, 40, 50]:
        descriptor = SimulationSessionDescriptor(
            name=f'distribution_test_{seed}',
            mode='continuous',
            seed=seed,
            grid_size=(6, 6),
            agents=9,  # More agents = better chance to see all types
            density=0.2,
            enable_respawn=False,
            enable_metrics=False,
            preference_type='random',
            turn_auto_interval_ms=None,
            viewport_size=320,
            start_paused=False
        )
        
        controller = SessionFactory.build(descriptor)
        agents = controller.simulation.agents
        
        for agent in agents:
            pref_type = getattr(agent.preference, 'TYPE_NAME', 'unknown')
            all_seen_types.add(pref_type)
    
    # Should see all three preference types across runs
    expected_types = {'cobb_douglas', 'perfect_substitutes', 'leontief'}
    assert all_seen_types >= expected_types, f"Missing preference types. Saw: {all_seen_types}, Expected: {expected_types}"


def test_random_preference_seed_variation():
    """Test that different seeds produce different distributions."""
    descriptor_base = SimulationSessionDescriptor(
        name='seed_variation_test',
        mode='continuous',
        seed=100,  # Will be changed
        grid_size=(6, 6),
        agents=5,
        density=0.2,
        enable_respawn=False,
        enable_metrics=False,
        preference_type='random',
        turn_auto_interval_ms=None,
        viewport_size=320,
        start_paused=False
    )
    
    distributions = []
    
    # Test multiple seeds
    for seed in [100, 200, 300]:
        descriptor_base.seed = seed
        controller = SessionFactory.build(descriptor_base)
        agents = controller.simulation.agents
        
        prefs = [getattr(agent.preference, 'TYPE_NAME', 'unknown') for agent in agents]
        distributions.append(prefs)
    
    # At least some distributions should be different
    unique_distributions = [tuple(d) for d in distributions]
    assert len(set(unique_distributions)) > 1, f"All seeds produced identical distributions: {distributions}"


def test_agent_preference_type_retrieval():
    """Test SimulationController.agent_preference_type() method."""
    descriptor = SimulationSessionDescriptor(
        name='retrieval_test',
        mode='continuous',
        seed=123,
        grid_size=(5, 5),
        agents=3,
        density=0.2,
        enable_respawn=False,
        enable_metrics=False,
        preference_type='random',
        turn_auto_interval_ms=None,
        viewport_size=320,
        start_paused=False
    )
    
    controller = SessionFactory.build(descriptor)
    agent_ids = controller.list_agent_ids()
    
    assert len(agent_ids) == 3, f"Expected 3 agents, got {len(agent_ids)}"
    
    # Test each agent
    for agent_id in agent_ids:
        pref_type = controller.agent_preference_type(agent_id)
        
        # Should return a valid preference type
        assert pref_type in {'cobb_douglas', 'perfect_substitutes', 'leontief'}, f"Invalid preference type: {pref_type}"
        
        # Should be consistent with direct agent access
        agent = next(a for a in controller.simulation.agents if a.id == agent_id)
        direct_pref_type = getattr(agent.preference, 'TYPE_NAME', 'unknown')
        assert pref_type == direct_pref_type, f"Inconsistent preference type retrieval: {pref_type} vs {direct_pref_type}"


def test_agent_preference_type_edge_cases():
    """Test edge cases for agent preference type retrieval."""
    descriptor = SimulationSessionDescriptor(
        name='edge_case_test',
        mode='continuous',
        seed=456,
        grid_size=(4, 4),
        agents=2,
        density=0.2,
        enable_respawn=False,
        enable_metrics=False,
        preference_type='random',
        turn_auto_interval_ms=None,
        viewport_size=320,
        start_paused=False
    )
    
    controller = SimulationController(SessionFactory.build(descriptor).simulation)
    
    # Test invalid agent ID
    invalid_pref = controller.agent_preference_type(999)
    assert invalid_pref is None, f"Expected None for invalid agent ID, got {invalid_pref}"
    
    # Test negative agent ID
    negative_pref = controller.agent_preference_type(-1)
    assert negative_pref is None, f"Expected None for negative agent ID, got {negative_pref}"


def test_random_preference_specific_types():
    """Test that random assignment creates correct preference instances."""
    descriptor = SimulationSessionDescriptor(
        name='type_instance_test',
        mode='continuous',
        seed=789,
        grid_size=(6, 6),
        agents=6,
        density=0.2,
        enable_respawn=False,
        enable_metrics=False,
        preference_type='random',
        turn_auto_interval_ms=None,
        viewport_size=320,
        start_paused=False
    )
    
    controller = SessionFactory.build(descriptor)
    agents = controller.simulation.agents
    
    type_counts = {'cobb_douglas': 0, 'perfect_substitutes': 0, 'leontief': 0}
    
    for agent in agents:
        pref = agent.preference
        pref_type = getattr(pref, 'TYPE_NAME', 'unknown')
        
        # Count types
        if pref_type in type_counts:
            type_counts[pref_type] += 1
        
        # Test that instances are correct types
        if pref_type == 'cobb_douglas':
            assert isinstance(pref, CobbDouglasPreference), f"Wrong instance type for cobb_douglas: {type(pref)}"
        elif pref_type == 'perfect_substitutes':
            assert isinstance(pref, PerfectSubstitutesPreference), f"Wrong instance type for perfect_substitutes: {type(pref)}"
        elif pref_type == 'leontief':
            assert isinstance(pref, LeontiefPreference), f"Wrong instance type for leontief: {type(pref)}"
        else:
            pytest.fail(f"Unknown preference type: {pref_type}")
        
        # Test that preferences can compute utility
        test_bundle = (1.0, 1.0)
        utility = pref.utility(test_bundle)
        assert isinstance(utility, (int, float)), f"Utility should be numeric, got {type(utility)}"
        assert utility >= 0, f"Utility should be non-negative, got {utility}"
    
    # Should have created at least one of each type across multiple runs (tested elsewhere)
    # Here just ensure all created instances are valid
    total_agents = sum(type_counts.values())
    assert total_agents == len(agents), f"Type count mismatch: {type_counts} vs {len(agents)} agents"


def test_random_preference_reproducible_with_session_factory():
    """Test that SessionFactory produces reproducible random preferences."""
    descriptor1 = SimulationSessionDescriptor(
        name='reproducible_test_1',
        mode='continuous',
        seed=555,
        grid_size=(5, 5),
        agents=4,
        density=0.2,
        enable_respawn=False,
        enable_metrics=False,
        preference_type='random',
        turn_auto_interval_ms=None,
        viewport_size=320,
        start_paused=False
    )
    
    descriptor2 = SimulationSessionDescriptor(
        name='reproducible_test_2',  # Different name
        mode='continuous',
        seed=555,  # Same seed
        grid_size=(5, 5),
        agents=4,
        density=0.2,
        enable_respawn=False,
        enable_metrics=False,
        preference_type='random',
        turn_auto_interval_ms=None,
        viewport_size=320,
        start_paused=False
    )
    
    # Build twice with same seed but different descriptors
    controller1 = SessionFactory.build(descriptor1)
    controller2 = SessionFactory.build(descriptor2)
    
    # Get preference assignments
    prefs1 = []
    prefs2 = []
    
    for agent in controller1.simulation.agents:
        prefs1.append((agent.id, getattr(agent.preference, 'TYPE_NAME')))
    
    for agent in controller2.simulation.agents:
        prefs2.append((agent.id, getattr(agent.preference, 'TYPE_NAME')))
    
    # Sort by agent ID for comparison
    prefs1.sort()
    prefs2.sort()
    
    assert prefs1 == prefs2, f"Same seed should produce same preference assignments: {prefs1} vs {prefs2}"