#!/usr/bin/env python3
"""Deep diagnostic for trade intent generation in bilateral exchange mode."""

import os
import sys
import random
from collections import defaultdict

# Set environment before importing simulation
os.environ["ECONSIM_NEW_GUI"] = "0"
os.environ["ECONSIM_TRADE_DRAFT"] = "1" 
os.environ["ECONSIM_TRADE_EXEC"] = "1"
os.environ["ECONSIM_FORAGE_ENABLED"] = "0"  # Disable foraging to isolate bilateral exchange

# Add src to path
sys.path.insert(0, "/home/chris/PROJECTS/vmt/src")

from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
from econsim.preferences.factory import PreferenceFactory
from econsim.preferences.helpers import marginal_utility

def debug_agent_state(agent, label=""):
    """Print detailed agent state for debugging."""
    print(f"  Agent {agent.id} ({label}):")
    print(f"    Position: ({agent.x}, {agent.y})")
    print(f"    Mode: {agent.mode}")
    print(f"    Carrying: {dict(agent.carrying)}")
    print(f"    Home inventory: {dict(agent.home_inventory)}")
    print(f"    Preference: {type(agent.preference).__name__}")
    
    # Calculate marginal utilities
    mu = marginal_utility(
        agent.preference,
        agent.carrying, 
        agent.home_inventory,
        epsilon_lift=True,
        include_missing_two_goods=True
    )
    print(f"    Marginal utilities: {mu}")

def debug_trade_conditions(agent_i, agent_j):
    """Check specific conditions for trade intent generation."""
    print(f"\n  Checking trade conditions between Agent {agent_i.id} and Agent {agent_j.id}:")
    
    # Get marginal utilities for both agents
    mu_i = marginal_utility(agent_i.preference, agent_i.carrying, agent_i.home_inventory, 
                           epsilon_lift=True, include_missing_two_goods=True)
    mu_j = marginal_utility(agent_j.preference, agent_j.carrying, agent_j.home_inventory,
                           epsilon_lift=True, include_missing_two_goods=True)
    
    print(f"    Agent {agent_i.id} MU: {mu_i}")
    print(f"    Agent {agent_j.id} MU: {mu_j}")
    
    # Check Direction 1: agent_i gives good1, agent_j gives good2
    print(f"\n    Direction 1 (Agent {agent_i.id} gives good1, Agent {agent_j.id} gives good2):")
    has_good1_i = agent_i.carrying.get("good1", 0) > 0
    has_good2_j = agent_j.carrying.get("good2", 0) > 0
    wants_good2_i = mu_i.get("good2", 0.0) > mu_i.get("good1", 0.0)
    wants_good1_j = mu_j.get("good1", 0.0) > mu_j.get("good2", 0.0)
    
    print(f"      Agent {agent_i.id} has good1 in carrying: {has_good1_i} (has {agent_i.carrying.get('good1', 0)})")
    print(f"      Agent {agent_j.id} has good2 in carrying: {has_good2_j} (has {agent_j.carrying.get('good2', 0)})")
    print(f"      Agent {agent_i.id} wants good2 > good1: {wants_good2_i} ({mu_i.get('good2', 0.0)} > {mu_i.get('good1', 0.0)})")
    print(f"      Agent {agent_j.id} wants good1 > good2: {wants_good1_j} ({mu_j.get('good1', 0.0)} > {mu_j.get('good2', 0.0)})")
    print(f"      ALL CONDITIONS MET: {has_good1_i and has_good2_j and wants_good2_i and wants_good1_j}")
    
    # Check Direction 2: agent_i gives good2, agent_j gives good1
    print(f"\n    Direction 2 (Agent {agent_i.id} gives good2, Agent {agent_j.id} gives good1):")
    has_good2_i = agent_i.carrying.get("good2", 0) > 0
    has_good1_j = agent_j.carrying.get("good1", 0) > 0
    wants_good1_i = mu_i.get("good1", 0.0) > mu_i.get("good2", 0.0)
    wants_good2_j = mu_j.get("good2", 0.0) > mu_j.get("good1", 0.0)
    
    print(f"      Agent {agent_i.id} has good2 in carrying: {has_good2_i} (has {agent_i.carrying.get('good2', 0)})")
    print(f"      Agent {agent_j.id} has good1 in carrying: {has_good1_j} (has {agent_j.carrying.get('good1', 0)})")
    print(f"      Agent {agent_i.id} wants good1 > good2: {wants_good1_i} ({mu_i.get('good1', 0.0)} > {mu_i.get('good2', 0.0)})")
    print(f"      Agent {agent_j.id} wants good2 > good1: {wants_good2_j} ({mu_j.get('good2', 0.0)} > {mu_j.get('good1', 0.0)})")
    print(f"      ALL CONDITIONS MET: {has_good2_i and has_good1_j and wants_good1_i and wants_good2_j}")

def main():
    print("=== Trade Intent Generation Deep Debug ===")
    print(f"Environment variables:")
    print(f"  ECONSIM_TRADE_DRAFT={os.environ.get('ECONSIM_TRADE_DRAFT')}")
    print(f"  ECONSIM_TRADE_EXEC={os.environ.get('ECONSIM_TRADE_EXEC')}")
    print(f"  ECONSIM_FORAGE_ENABLED={os.environ.get('ECONSIM_FORAGE_ENABLED')}")
    
    # Create simulation matching your GUI scenario
    config = SimConfig(
        grid_size=(10, 10),
        initial_resources=[],
        respawn_target_density=0.25,
        respawn_rate=1.0,
        seed=42
    )
    
    # Create world with bilateral exchange enabled
    preference_factory = lambda agent_id: PreferenceFactory.create("cobb_douglas")
    world = Simulation.from_config(
        config,
        preference_factory,
        agent_positions=[(2, 2), (2, 2), (7, 7), (7, 7)]  # Two co-located pairs
    )
    
    print(f"\nSimulation setup:")
    print(f"  Grid: {config.grid_size[0]}x{config.grid_size[1]}")
    print(f"  Agents: {len(world.agents)}")
    forage_enabled = os.environ.get("ECONSIM_FORAGE_ENABLED", "1") == "1"
    exchange_any = os.environ.get("ECONSIM_TRADE_DRAFT") == "1" or os.environ.get("ECONSIM_TRADE_EXEC") == "1"
    print(f"  Bilateral exchange enabled: {exchange_any}")
    print(f"  Foraging enabled: {forage_enabled}")
    
    # Set up the scenario: agents forage first, return home, then start bilateral exchange
    print(f"\nStep 1: Initial agent states")
    for i, agent in enumerate(world.agents):
        debug_agent_state(agent, f"initial")
    
    # Simulate foraging phase (even though disabled, we want agents with goods)
    print(f"\nStep 2: Give agents some goods in their home inventory to simulate post-foraging state")
    # Agent 0 gets lots of good1, little good2
    world.agents[0].home_inventory = {"good1": 5, "good2": 1}
    # Agent 1 gets lots of good2, little good1  
    world.agents[1].home_inventory = {"good1": 1, "good2": 5}
    # Agent 2 gets lots of good1, little good2
    world.agents[2].home_inventory = {"good1": 5, "good2": 1}
    # Agent 3 gets lots of good2, little good1
    world.agents[3].home_inventory = {"good1": 1, "good2": 5}
    
    print(f"\nStep 3: Agent states after simulated foraging")
    for i, agent in enumerate(world.agents):
        debug_agent_state(agent, f"post-foraging")
    
    # Now agents need to have goods in carrying to trade
    print(f"\nStep 4: Transfer some goods to carrying inventory (simulate agent taking goods from home)")
    for agent in world.agents:
        # Take 2 units of whatever good they have most of
        if agent.home_inventory.get("good1", 0) > agent.home_inventory.get("good2", 0):
            agent.carrying["good1"] = 2
            agent.home_inventory["good1"] -= 2
        else:
            agent.carrying["good2"] = 2
            agent.home_inventory["good2"] -= 2
    
    print(f"\nStep 5: Agent states with goods in carrying")
    for i, agent in enumerate(world.agents):
        debug_agent_state(agent, f"ready-to-trade")
    
    # Now test trade intent generation manually
    print(f"\nStep 6: Manual trade intent generation test")
    from econsim.simulation.trade import enumerate_intents_for_cell
    
    # Test agents at position (2,2)
    agents_at_2_2 = [a for a in world.agents if a.x == 2 and a.y == 2]
    print(f"\nAgents co-located at (2,2): {len(agents_at_2_2)}")
    if len(agents_at_2_2) >= 2:
        for agent in agents_at_2_2:
            debug_agent_state(agent, f"co-located")
        
        # Check pairwise trade conditions
        if len(agents_at_2_2) == 2:
            debug_trade_conditions(agents_at_2_2[0], agents_at_2_2[1])
        
        # Generate intents
        intents = enumerate_intents_for_cell(agents_at_2_2)
        print(f"\nTrade intents generated for cell (2,2): {len(intents)}")
        for intent in intents:
            print(f"  Intent: Agent {intent.seller_id} gives {intent.give_type} to Agent {intent.buyer_id} for {intent.take_type}")
            print(f"    Delta utility: {intent.delta_utility}")
    
    # Test agents at position (7,7)
    agents_at_7_7 = [a for a in world.agents if a.x == 7 and a.y == 7]
    print(f"\nAgents co-located at (7,7): {len(agents_at_7_7)}")
    if len(agents_at_7_7) >= 2:
        for agent in agents_at_7_7:
            debug_agent_state(agent, f"co-located")
        
        # Check pairwise trade conditions  
        if len(agents_at_7_7) == 2:
            debug_trade_conditions(agents_at_7_7[0], agents_at_7_7[1])
        
        # Generate intents
        intents = enumerate_intents_for_cell(agents_at_7_7)
        print(f"\nTrade intents generated for cell (7,7): {len(intents)}")
        for intent in intents:
            print(f"  Intent: Agent {intent.seller_id} gives {intent.give_type} to Agent {intent.buyer_id} for {intent.take_type}")
            print(f"    Delta utility: {intent.delta_utility}")
    
    # Now test the full simulation step
    print(f"\nStep 7: Full simulation step with trade intent generation")
    
    # Create external RNG 
    ext_rng = random.Random(42)
    
    # Run one step
    world.step(ext_rng, use_decision=True)
    
    print(f"Trade intents after step: {len(world.trade_intents) if world.trade_intents else 0}")
    if world.trade_intents:
        for intent in world.trade_intents:
            print(f"  Intent: Agent {intent.seller_id} gives {intent.give_type} to Agent {intent.buyer_id} for {intent.take_type}")

if __name__ == "__main__":
    main()