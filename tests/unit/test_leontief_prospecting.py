"""Test Leontief prospecting behavior functionality.

Tests the Leontief prospecting feature added in commit 1b5f3a9,
ensuring agents with Leontief preferences can find complementary resources
and make forward-looking decisions when starting with (0,0) bundles.
"""

import pytest

from econsim.simulation.agent import Agent, AgentMode
from econsim.simulation.grid import Grid
from econsim.preferences.leontief import LeontiefPreference
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference


def test_leontief_prospecting_basic():
    """Test that Leontief agents find complementary resource pairs."""
    # Create Leontief agent with (0,0) starting bundle at (2,2)
    agent = Agent(
        id=1, 
        x=2, 
        y=2, 
        preference=LeontiefPreference(a=1.0, b=1.0),
        home_x=2,
        home_y=2
    )
    
    # Create grid with complementary resources nearby
    grid = Grid(6, 6, [
        (1, 2, 'A'),  # good1 at distance 1
        (3, 2, 'B'),  # good2 at distance 1  
        (0, 0, 'A'),  # farther good1
        (5, 5, 'B'),  # farther good2
    ])
    
    # Agent should initially be in FORAGE mode with no target
    assert agent.mode == AgentMode.FORAGE
    assert agent.target is None
    assert agent.carrying == {'good1': 0, 'good2': 0}
    
    # Run target selection - should use prospecting
    agent.select_target(grid)
    
    # Should have selected a target (not go idle or return home)
    assert agent.mode == AgentMode.FORAGE
    assert agent.target is not None
    
    # Target should be one of the nearby resources
    assert agent.target in [(1, 2), (3, 2)], f"Expected nearby resource, got {agent.target}"


def test_leontief_prospecting_scoring():
    """Test prospect scoring calculation (utility gain / effort)."""
    agent = Agent(
        id=1,
        x=0,
        y=0, 
        preference=LeontiefPreference(a=1.0, b=1.0),
        home_x=0,
        home_y=0
    )
    
    # Create grid with resources at different distances
    grid = Grid(8, 8, [
        (1, 0, 'A'),  # Close good1
        (2, 0, 'B'),  # Close good2 (complement to first)
        (5, 0, 'A'),  # Far good1  
        (7, 0, 'B'),  # Far good2 (complement to far good1)
    ])
    
    agent.select_target(grid)
    
    # Should prefer the closer pair (1,0) over the farther pair (5,0)
    # since prospect score = utility_gain / total_effort
    assert agent.target == (1, 0), f"Should prefer closer resource, got {agent.target}"


def test_leontief_prospecting_deterministic():
    """Test deterministic tie-breaking in prospect selection."""
    agent = Agent(
        id=1,
        x=3,
        y=3,
        preference=LeontiefPreference(a=1.0, b=1.0),
        home_x=3,
        home_y=3
    )
    
    # Create symmetric scenario for tie-breaking test
    grid = Grid(7, 7, [
        (2, 3, 'A'),  # Distance 1 to left
        (4, 3, 'A'),  # Distance 1 to right  
        (3, 2, 'B'),  # Distance 1 up
        (3, 4, 'B'),  # Distance 1 down
    ])
    
    # Run selection multiple times - should be deterministic
    targets = []
    for _ in range(5):
        agent.target = None  # Reset
        agent.select_target(grid)
        targets.append(agent.target)
    
    # All selections should be identical
    assert len(set(targets)) == 1, f"Non-deterministic target selection: {targets}"
    
    # Should pick based on deterministic tie-breaking rules
    selected_target = targets[0]
    assert selected_target is not None, "Should have selected a target"


def test_leontief_no_complement_fallback():
    """Test behavior when no complementary resources available."""
    agent = Agent(
        id=1,
        x=2,
        y=2,
        preference=LeontiefPreference(a=1.0, b=1.0),
        home_x=2,
        home_y=2
    )
    
    # Grid with only one type of resource (no complements)
    grid = Grid(5, 5, [
        (1, 2, 'A'),  # Only good1 resources
        (3, 2, 'A'),
        (2, 1, 'A'),
    ])
    
    agent.select_target(grid)
    
    # Should go idle since no complementary pairs available
    # and single resources provide no utility for Leontief at (0,0)
    assert agent.mode == AgentMode.IDLE
    assert agent.target is None


def test_non_leontief_agents_unaffected():
    """Test that prospecting only affects Leontief agents."""
    # Test Cobb-Douglas agent
    cobb_agent = Agent(
        id=1, 
        x=2,
        y=2,
        preference=CobbDouglasPreference(alpha=0.5),
        home_x=2,
        home_y=2
    )
    
    # Test Perfect Substitutes agent  
    subs_agent = Agent(
        id=2,
        x=2, 
        y=2,
        preference=PerfectSubstitutesPreference(a=1.0, b=1.0),
        home_x=2,
        home_y=2
    )
    
    grid = Grid(5, 5, [(1, 2, 'A'), (3, 2, 'B')])
    
    # Both should select targets normally (no prospecting needed)
    cobb_agent.select_target(grid)
    subs_agent.select_target(grid)
    
    # Should have targets (not idle) because they get positive utility from single resources
    assert cobb_agent.mode == AgentMode.FORAGE
    assert cobb_agent.target is not None
    assert subs_agent.mode == AgentMode.FORAGE  
    assert subs_agent.target is not None


def test_leontief_prospecting_after_partial_collection():
    """Test that prospecting doesn't interfere after agent has some goods."""
    agent = Agent(
        id=1,
        x=2,
        y=2,
        preference=LeontiefPreference(a=1.0, b=1.0),
        home_x=2,
        home_y=2
    )
    
    # Give agent some goods (no longer at 0,0 bundle)
    agent.carrying['good1'] = 1
    
    grid = Grid(5, 5, [(1, 2, 'A'), (3, 2, 'B')])
    
    agent.select_target(grid)
    
    # Should target the complement (good2) since agent now has good1=1
    # and normal targeting should work (no prospecting needed)
    assert agent.mode == AgentMode.FORAGE
    assert agent.target == (3, 2), f"Should target complement resource B, got {agent.target}"


def test_leontief_prospecting_with_home_inventory():
    """Test prospecting considers home inventory in bundle calculation."""
    agent = Agent(
        id=1,
        x=2,
        y=2,
        preference=LeontiefPreference(a=1.0, b=1.0), 
        home_x=2,
        home_y=2
    )
    
    # Agent has goods in home inventory
    agent.home_inventory['good2'] = 2
    
    grid = Grid(5, 5, [(1, 2, 'A'), (3, 2, 'B')])
    
    agent.select_target(grid)
    
    # Even though carrying bundle is (0,0), home inventory should be considered
    # Agent has good2=2 at home, so should prefer good1 to balance
    assert agent.mode == AgentMode.FORAGE
    assert agent.target == (1, 2), f"Should target good1 to balance home inventory, got {agent.target}"


def test_leontief_prospect_score_calculation():
    """Test the mathematical correctness of prospect scoring."""
    agent = Agent(
        id=1,
        x=0,
        y=0,
        preference=LeontiefPreference(a=2.0, b=3.0),  # U = min(x/2, y/3)
        home_x=0,
        home_y=0
    )
    
    grid = Grid(10, 10, [
        (1, 0, 'A'),  # Distance 1, leads to good1
        (0, 2, 'B'),  # Distance 2, complement
        (5, 0, 'A'),  # Distance 5, farther option  
        (0, 6, 'B'),  # Distance 6, farther complement
    ])
    
    # The algorithm should find the resource pair with the best score
    # Score = utility_gain / total_effort where total_effort includes home return
    agent.select_target(grid)
    
    # Should select one of the closer resources
    assert agent.target is not None, "Should have selected a target for prospecting"
    assert agent.target in [(1, 0), (0, 2)], f"Should select a closer resource, got {agent.target}"


def test_leontief_prospecting_integration_with_step_decision():
    """Test that prospecting integrates properly with step_decision method."""
    agent = Agent(
        id=1,
        x=2,
        y=2,
        preference=LeontiefPreference(a=1.0, b=1.0),
        home_x=2,
        home_y=2
    )
    
    grid = Grid(6, 6, [
        (2, 1, 'A'),  # Adjacent resource
        (2, 3, 'B'),  # Complement nearby
    ])
    
    # Initial state
    assert agent.carrying == {'good1': 0, 'good2': 0}
    assert agent.target is None
    
    # Step 1: Should select target via prospecting
    collected = agent.step_decision(grid)
    
    # Should have moved toward or collected the adjacent resource
    if collected:
        # Collected the resource at (2,1)
        assert agent.carrying['good1'] == 1
        assert agent.target is None  # Target cleared after collection
    else:
        # Moved toward resource
        assert agent.target == (2, 1)
        assert (agent.x, agent.y) in [(2, 1), (2, 2)]  # At target or moved toward it
    
    # Ensure agent doesn't get stuck in idle mode
    assert agent.mode != AgentMode.IDLE


def test_leontief_prospecting_empty_grid():
    """Test Leontief agent behavior on empty grid."""
    agent = Agent(
        id=1,
        x=2,
        y=2,
        preference=LeontiefPreference(a=1.0, b=1.0),
        home_x=2,
        home_y=2
    )
    
    # Empty grid
    grid = Grid(5, 5, [])
    
    agent.select_target(grid)
    
    # Should go idle (no resources to prospect)
    assert agent.mode == AgentMode.IDLE
    assert agent.target is None


def test_leontief_helper_methods():
    """Test the helper methods used in prospecting."""
    agent = Agent(
        id=1,
        x=1,
        y=1,
        preference=LeontiefPreference(a=1.0, b=1.0),
        home_x=1,
        home_y=1
    )
    
    grid = Grid(4, 4, [(2, 1, 'A'), (1, 2, 'B')])
    
    # Test _peek_resource_type_at
    assert agent._peek_resource_type_at(grid, 2, 1) == 'A'
    assert agent._peek_resource_type_at(grid, 1, 2) == 'B'
    assert agent._peek_resource_type_at(grid, 0, 0) is None
    
    # Test _find_nearest_complement_resource  
    complement_pos, distance = agent._find_nearest_complement_resource((2, 1), 'A', grid, 10)
    assert complement_pos == (1, 2), f"Should find complement at (1,2), got {complement_pos}"
    assert distance == 2, f"Distance should be 2, got {distance}"  # Manhattan distance from (2,1) to (1,2)
    
    # Test with no complement available
    grid_no_complement = Grid(4, 4, [(2, 1, 'A'), (3, 1, 'A')])  # Only A resources
    complement_pos, distance = agent._find_nearest_complement_resource((2, 1), 'A', grid_no_complement, 10)
    assert complement_pos is None, f"Should find no complement, got {complement_pos}"
    assert distance == 0, f"Distance should be 0 when no complement, got {distance}"