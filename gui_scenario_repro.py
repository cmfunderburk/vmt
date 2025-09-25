#!/usr/bin/env python3
"""Reproduce the exact GUI scenario: forage -> return home -> enable bilateral exchange."""

import os
import sys
import random

# Set environment to match GUI
os.environ["ECONSIM_NEW_GUI"] = "0"
os.environ["ECONSIM_FORAGE_ENABLED"] = "1"  # Start with foraging enabled
os.environ["ECONSIM_TRADE_DRAFT"] = "0"     # Start with trade disabled
os.environ["ECONSIM_TRADE_EXEC"] = "0"

# Add src to path
sys.path.insert(0, "/home/chris/PROJECTS/vmt/src")

from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
from econsim.preferences.factory import PreferenceFactory

def print_agent_summary(agents, step_num, label):
    """Print brief agent status."""
    print(f"\n=== Step {step_num}: {label} ===")
    for agent in agents:
        carrying_total = sum(agent.carrying.values())
        home_total = sum(agent.home_inventory.values())
        carrying_detail = dict(agent.carrying)
        home_detail = dict(agent.home_inventory)
        print(f"Agent {agent.id}: pos({agent.x},{agent.y}) mode={agent.mode.name} "
              f"carrying={carrying_detail} home={home_detail} at_home={agent.at_home()}")

def main():
    print("=== Reproducing GUI Scenario: Forage -> Home -> Bilateral Exchange ===")
    
    # Create minimal simulation
    config = SimConfig(
        grid_size=(10, 10),
        initial_resources=[
            (2, 2, "good1"), (2, 3, "good2"),  # Resources near agents
            (7, 7, "good1"), (7, 8, "good2")
        ],
        seed=42
    )
    
    preference_factory = lambda agent_id: PreferenceFactory.create("cobb_douglas")
    world = Simulation.from_config(
        config,
        preference_factory,
        agent_positions=[(2, 2), (2, 2), (7, 7), (7, 7)]  # Two pairs co-located
    )
    
    ext_rng = random.Random(42)
    
    # Phase 1: Foraging enabled, agents collect resources
    print("Phase 1: Foraging for ~50 steps")
    for step in range(50):
        world.step(ext_rng, use_decision=True)
        if step % 10 == 0:
            print_agent_summary(world.agents, step, f"Foraging step {step}")
    
    print_agent_summary(world.agents, 50, "End of foraging phase")
    
    # Phase 2: Disable foraging, agents return home  
    print("\nPhase 2: Disable foraging, agents return home")
    os.environ["ECONSIM_FORAGE_ENABLED"] = "0"
    
    # Run a few steps for agents to return home and deposit
    for step in range(51, 61):
        world.step(ext_rng, use_decision=True)
        if step % 2 == 0:
            print_agent_summary(world.agents, step, f"Return home step {step}")
    
    print_agent_summary(world.agents, 60, "After return home phase")
    
    # Phase 3: Enable bilateral exchange  
    print("\nPhase 3: Enable bilateral exchange")
    os.environ["ECONSIM_TRADE_DRAFT"] = "1"
    os.environ["ECONSIM_TRADE_EXEC"] = "1"
    
    print("Environment after enabling trade:")
    print(f"  ECONSIM_FORAGE_ENABLED={os.environ.get('ECONSIM_FORAGE_ENABLED')}")
    print(f"  ECONSIM_TRADE_DRAFT={os.environ.get('ECONSIM_TRADE_DRAFT')}")
    print(f"  ECONSIM_TRADE_EXEC={os.environ.get('ECONSIM_TRADE_EXEC')}")
    
    # Run bilateral exchange steps
    for step in range(61, 71):
        world.step(ext_rng, use_decision=True)
        
        # Check trade intents
        intent_count = len(world.trade_intents) if world.trade_intents else 0
        if step % 2 == 0:
            print_agent_summary(world.agents, step, f"Bilateral exchange step {step}")
            print(f"  Trade intents: {intent_count}")
            if world.trade_intents:
                for intent in world.trade_intents:
                    print(f"    Intent: Agent {intent.seller_id} -> Agent {intent.buyer_id} "
                          f"({intent.give_type} for {intent.take_type})")
    
    print_agent_summary(world.agents, 70, "Final bilateral exchange state")
    
    # Check if any trades were recorded
    if hasattr(world, 'metrics_collector') and world.metrics_collector:
        mc = world.metrics_collector
        if hasattr(mc, 'last_executed_trade') and mc.last_executed_trade:
            print(f"\nLast executed trade: {mc.last_executed_trade}")
        else:
            print(f"\nNo trades executed")
        
        # Check agent trade histories
        if hasattr(mc, 'agent_trade_histories'):
            total_trades = sum(len(history) for history in mc.agent_trade_histories.values())
            print(f"Total trades in agent histories: {total_trades}")
        else:
            print("No agent trade histories available")

if __name__ == "__main__":
    main()