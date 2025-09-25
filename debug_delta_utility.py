#!/usr/bin/env python3
"""Debug delta utility calculation for different preference types."""

import os
import sys

# Set environment 
os.environ["ECONSIM_NEW_GUI"] = "0"
os.environ["ECONSIM_FORAGE_ENABLED"] = "0"
os.environ["ECONSIM_TRADE_DRAFT"] = "1" 
os.environ["ECONSIM_TRADE_EXEC"] = "1"

# Add src to path
sys.path.insert(0, "/home/chris/PROJECTS/vmt/src")

from econsim.preferences.factory import PreferenceFactory
from econsim.simulation.trade import _compute_exact_utility_delta
from econsim.simulation.agent import Agent
from econsim.simulation.grid import Grid

def create_test_agent(agent_id: int, pref_type: str, carrying: dict, home_inventory: dict, 
                     position: tuple = (5, 5)) -> Agent:
    """Create test agent with specified preference and inventories."""
    preference = PreferenceFactory.create(pref_type)
    grid = Grid(10, 10)  # Dummy grid
    agent = Agent(agent_id, position[0], position[1], preference, grid)
    
    # Set inventories
    agent.carrying.clear()
    agent.home_inventory.clear()
    for good, amount in carrying.items():
        agent.carrying[good] = amount
    for good, amount in home_inventory.items():
        agent.home_inventory[good] = amount
    
    return agent

def test_delta_utility_calculation():
    """Test delta utility calculation for different scenarios."""
    
    print("=== Delta Utility Calculation Debug ===\n")
    
    # Test different preference types
    pref_types = ["cobb_douglas", "leontief", "perfect_substitutes"]
    
    for pref_type in pref_types:
        print(f"Testing {pref_type} preferences:")
        
        # Test scenario: Agent A has lots of good1, Agent B has lots of good2
        agent_a = create_test_agent(
            agent_id=1, 
            pref_type=pref_type,
            carrying={"good1": 2, "good2": 0},
            home_inventory={"good1": 5, "good2": 1}
        )
        
        agent_b = create_test_agent(
            agent_id=2,
            pref_type=pref_type, 
            carrying={"good1": 0, "good2": 2},
            home_inventory={"good1": 1, "good2": 5}
        )
        
        print(f"  Agent A: carrying={dict(agent_a.carrying)}, home={dict(agent_a.home_inventory)}")
        print(f"  Agent B: carrying={dict(agent_b.carrying)}, home={dict(agent_b.home_inventory)}")
        
        # Calculate utilities before trade
        def total_bundle(agent):
            return (
                agent.carrying.get("good1", 0) + agent.home_inventory.get("good1", 0) + 1e-12,
                agent.carrying.get("good2", 0) + agent.home_inventory.get("good2", 0) + 1e-12
            )
        
        bundle_a_before = total_bundle(agent_a)
        bundle_b_before = total_bundle(agent_b)
        
        util_a_before = agent_a.preference.utility(bundle_a_before)
        util_b_before = agent_b.preference.utility(bundle_b_before)
        
        print(f"  Bundle A before: {bundle_a_before}, utility: {util_a_before:.6f}")
        print(f"  Bundle B before: {bundle_b_before}, utility: {util_b_before:.6f}")
        
        # Test trade: A gives good1, B gives good2
        delta_u = _compute_exact_utility_delta(agent_a, agent_b, "good1", "good2")
        print(f"  Delta utility (A gives good1, B gives good2): {delta_u:.6f}")
        
        # Test opposite trade: A gives good2, B gives good1  
        delta_u_reverse = _compute_exact_utility_delta(agent_a, agent_b, "good2", "good1")
        print(f"  Delta utility (A gives good2, B gives good1): {delta_u_reverse:.6f}")
        
        # Manual calculation for verification
        if pref_type == "cobb_douglas":
            # For Cobb-Douglas: U(x1, x2) = x1^α * x2^(1-α), typically α = 0.5
            # So U(x1, x2) = sqrt(x1 * x2)
            bundle_a_after = (bundle_a_before[0] - 1, bundle_a_before[1] + 1)
            bundle_b_after = (bundle_b_before[0] + 1, bundle_b_before[1] - 1)
            
            util_a_after = agent_a.preference.utility(bundle_a_after)
            util_b_after = agent_b.preference.utility(bundle_b_after)
            
            print(f"  Bundle A after: {bundle_a_after}, utility: {util_a_after:.6f}")
            print(f"  Bundle B after: {bundle_b_after}, utility: {util_b_after:.6f}")
            print(f"  Manual delta calculation: {(util_a_after + util_b_after) - (util_a_before + util_b_before):.6f}")
        
        print()
    
    # Test edge cases
    print("Edge case tests:")
    
    # Test agents with identical inventories (should have delta U = 0)
    agent_identical_1 = create_test_agent(
        1, "cobb_douglas", 
        carrying={"good1": 2, "good2": 2},
        home_inventory={"good1": 3, "good2": 3}
    )
    agent_identical_2 = create_test_agent(
        2, "cobb_douglas",
        carrying={"good1": 2, "good2": 2}, 
        home_inventory={"good1": 3, "good2": 3}
    )
    
    delta_identical = _compute_exact_utility_delta(agent_identical_1, agent_identical_2, "good1", "good2")
    print(f"Identical inventories delta U: {delta_identical:.6f} (should be ~0)")
    
    # Test agents with very unequal inventories (should have high delta U)
    agent_unequal_1 = create_test_agent(
        1, "cobb_douglas",
        carrying={"good1": 10, "good2": 0},
        home_inventory={"good1": 10, "good2": 0}
    )
    agent_unequal_2 = create_test_agent(
        2, "cobb_douglas", 
        carrying={"good1": 0, "good2": 10},
        home_inventory={"good1": 0, "good2": 10}
    )
    
    delta_unequal = _compute_exact_utility_delta(agent_unequal_1, agent_unequal_2, "good1", "good2")
    print(f"Very unequal inventories delta U: {delta_unequal:.6f} (should be positive)")

if __name__ == "__main__":
    test_delta_utility_calculation()