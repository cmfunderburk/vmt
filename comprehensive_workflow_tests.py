#!/usr/bin/env python3
"""Realistic GUI workflow tests for bilateral exchange debugging.

Two comprehensive tests that exactly replicate the GUI workflow:
1. 20 agents, 30x30 grid, 0.25 density, perception 8
2. 40 agents, 64x64 grid, 0.5 density, perception 15

Workflow for both:
- Start paused
- Uncheck bilateral exchange  
- Forage 100 turns
- Turn off foraging
- Wait for agents to return home
- Turn on bilateral exchange
- Exchange 200 turns
- Turn off bilateral exchange
- Return home and deposit
"""

import os
import sys
import random
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, "/home/chris/PROJECTS/vmt/src")

from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
from econsim.preferences.factory import PreferenceFactory

def create_mixed_preference_factory():
    """Create factory that randomly assigns different preference types."""
    preferences = ["cobb_douglas", "leontief", "perfect_substitutes"]
    
    def factory(agent_id: int):
        # Use agent_id as seed for deterministic but varied assignment
        local_rng = random.Random(agent_id * 17 + 42)
        pref_type = local_rng.choice(preferences)
        return PreferenceFactory.create(pref_type)
    
    return factory

def generate_resources_for_grid(grid_width: int, grid_height: int, density: float, seed: int = 42) -> List[tuple]:
    """Generate initial resources at specified density."""
    total_cells = grid_width * grid_height
    num_resources = int(total_cells * density)
    
    rng = random.Random(seed)
    resources = []
    
    for _ in range(num_resources):
        x = rng.randint(0, grid_width - 1)
        y = rng.randint(0, grid_height - 1) 
        good_type = rng.choice(["good1", "good2"])
        resources.append((x, y, good_type))
    
    return resources

def generate_agent_positions(num_agents: int, grid_width: int, grid_height: int, seed: int = 42) -> List[tuple]:
    """Generate random agent starting positions."""
    rng = random.Random(seed + 1000)  # Different seed from resources
    positions = []
    
    for _ in range(num_agents):
        x = rng.randint(0, grid_width - 1)
        y = rng.randint(0, grid_height - 1)
        positions.append((x, y))
    
    return positions

def count_agents_by_state(agents, label: str = "") -> Dict[str, int]:
    """Count agents by mode and location status."""
    counts = {
        "at_home": 0,
        "carrying_goods": 0,
        "home_inventory": 0,
        "forage_mode": 0,
        "return_home_mode": 0,
        "idle_mode": 0
    }
    
    for agent in agents:
        if agent.at_home():
            counts["at_home"] += 1
        if sum(agent.carrying.values()) > 0:
            counts["carrying_goods"] += 1
        if sum(agent.home_inventory.values()) > 0:
            counts["home_inventory"] += 1
        if hasattr(agent, 'mode'):
            if str(agent.mode) == "AgentMode.FORAGE":
                counts["forage_mode"] += 1
            elif str(agent.mode) == "AgentMode.RETURN_HOME":
                counts["return_home_mode"] += 1
            elif str(agent.mode) == "AgentMode.IDLE":
                counts["idle_mode"] += 1
    
    if label:
        print(f"{label}: {counts}")
    
    return counts

def run_workflow_test(test_name: str, num_agents: int, grid_size: tuple, resource_density: float, 
                     perception_radius: int, seed: int = 42):
    """Run complete GUI workflow test."""
    
    print(f"\n{'='*60}")
    print(f"Running {test_name}")
    print(f"Agents: {num_agents}, Grid: {grid_size[0]}x{grid_size[1]}, Density: {resource_density}, Perception: {perception_radius}")
    print(f"{'='*60}")
    
    # Generate resources and positions
    resources = generate_resources_for_grid(grid_size[0], grid_size[1], resource_density, seed)
    positions = generate_agent_positions(num_agents, grid_size[0], grid_size[1], seed)
    
    print(f"Generated {len(resources)} resources and {len(positions)} agent positions")
    
    # Create simulation config
    config = SimConfig(
        grid_size=grid_size,
        initial_resources=resources,
        perception_radius=perception_radius,
        respawn_target_density=resource_density,
        respawn_rate=0.25,
        seed=seed
    )
    
    # Create simulation with mixed preferences
    preference_factory = create_mixed_preference_factory()
    world = Simulation.from_config(config, preference_factory, agent_positions=positions)
    ext_rng = random.Random(seed + 2000)
    
    # Phase 1: Start paused, uncheck bilateral exchange, forage 100 turns
    print(f"\nPhase 1: Foraging (100 turns)")
    os.environ["ECONSIM_FORAGE_ENABLED"] = "1"
    os.environ["ECONSIM_TRADE_DRAFT"] = "0"
    os.environ["ECONSIM_TRADE_EXEC"] = "0"
    
    for step in range(100):
        world.step(ext_rng, use_decision=True)
        if step % 20 == 0:
            count_agents_by_state(world.agents, f"Forage step {step}")
    
    count_agents_by_state(world.agents, "End of foraging")
    
    # Phase 2: Turn off foraging, wait for agents to return home
    print(f"\nPhase 2: Return home after foraging")
    os.environ["ECONSIM_FORAGE_ENABLED"] = "0"
    
    step = 100
    all_home_deposited = False
    max_return_steps = 200  # Safety limit
    
    while not all_home_deposited and (step - 100) < max_return_steps:
        world.step(ext_rng, use_decision=True)
        step += 1
        
        # Check if all agents are home and have deposited
        counts = count_agents_by_state(world.agents)
        all_home_deposited = (counts["at_home"] == num_agents and 
                             counts["carrying_goods"] == 0 and 
                             counts["home_inventory"] > 0)
        
        if step % 10 == 0:
            count_agents_by_state(world.agents, f"Return home step {step}")
            
        if all_home_deposited:
            print(f"All agents home and deposited at step {step}")
            break
    
    if not all_home_deposited:
        print(f"Warning: Not all agents returned home within {max_return_steps} steps")
    
    count_agents_by_state(world.agents, "All agents home")
    
    # Phase 3: Turn on bilateral exchange, run 200 turns
    print(f"\nPhase 3: Bilateral exchange (200 turns)")
    os.environ["ECONSIM_TRADE_DRAFT"] = "1" 
    os.environ["ECONSIM_TRADE_EXEC"] = "1"
    
    trade_stats = {
        "total_intents": 0,
        "steps_with_intents": 0,
        "total_executions": 0,
        "steps_with_executions": 0
    }
    
    exchange_start_step = step
    for exchange_step in range(200):
        current_step = exchange_start_step + exchange_step
        world.step(ext_rng, use_decision=True)
        
        # Track trade activity
        intent_count = len(world.trade_intents) if world.trade_intents else 0
        if intent_count > 0:
            trade_stats["total_intents"] += intent_count
            trade_stats["steps_with_intents"] += 1
        
        # Check for executed trades
        if hasattr(world, 'metrics_collector') and world.metrics_collector:
            mc = world.metrics_collector
            if hasattr(mc, 'last_executed_trade') and mc.last_executed_trade:
                trade_stats["total_executions"] += 1
                if exchange_step % 20 == 0:
                    print(f"  Trade executed at step {current_step}: {mc.last_executed_trade}")
        
        if exchange_step % 20 == 0:
            count_agents_by_state(world.agents, f"Exchange step {current_step}")
            print(f"  Trade intents: {intent_count}")
    
    count_agents_by_state(world.agents, "End of exchange")
    
    # Phase 4: Turn off bilateral exchange, return home
    print(f"\nPhase 4: Final return home")
    os.environ["ECONSIM_TRADE_DRAFT"] = "0"
    os.environ["ECONSIM_TRADE_EXEC"] = "0"
    
    final_step = exchange_start_step + 200
    all_final_home = False
    max_final_steps = 100
    
    while not all_final_home and (final_step - (exchange_start_step + 200)) < max_final_steps:
        world.step(ext_rng, use_decision=True)
        final_step += 1
        
        counts = count_agents_by_state(world.agents)
        all_final_home = (counts["at_home"] == num_agents and counts["carrying_goods"] == 0)
        
        if final_step % 10 == 0:
            count_agents_by_state(world.agents, f"Final return step {final_step}")
            
        if all_final_home:
            print(f"All agents final home at step {final_step}")
            break
    
    count_agents_by_state(world.agents, "Final state")
    
    # Print trade statistics
    print(f"\n{test_name} Trade Statistics:")
    print(f"  Total trade intents generated: {trade_stats['total_intents']}")
    print(f"  Steps with trade intents: {trade_stats['steps_with_intents']}/200")
    print(f"  Total trade executions: {trade_stats['total_executions']}")
    print(f"  Steps with executions: {trade_stats['steps_with_executions']}/200")
    
    # Analyze final inventories
    inventory_summary = {"good1_total": 0, "good2_total": 0, "agents_with_goods": 0}
    for agent in world.agents:
        agent_total = sum(agent.home_inventory.values()) + sum(agent.carrying.values())
        if agent_total > 0:
            inventory_summary["agents_with_goods"] += 1
        inventory_summary["good1_total"] += agent.home_inventory.get("good1", 0) + agent.carrying.get("good1", 0)
        inventory_summary["good2_total"] += agent.home_inventory.get("good2", 0) + agent.carrying.get("good2", 0)
    
    print(f"\nFinal Inventory Summary:")
    print(f"  Total good1: {inventory_summary['good1_total']}")
    print(f"  Total good2: {inventory_summary['good2_total']}")
    print(f"  Agents with goods: {inventory_summary['agents_with_goods']}/{num_agents}")
    
    return trade_stats, inventory_summary

def main():
    """Run both comprehensive workflow tests."""
    
    print("Comprehensive Bilateral Exchange Workflow Tests")
    print("Testing realistic GUI scenarios to debug trade execution")
    
    # Test 1: Smaller scenario
    test1_stats, test1_inventory = run_workflow_test(
        test_name="Test 1 (Small)",
        num_agents=20,
        grid_size=(30, 30),
        resource_density=0.25,
        perception_radius=8,
        seed=42
    )
    
    # Test 2: Larger scenario  
    test2_stats, test2_inventory = run_workflow_test(
        test_name="Test 2 (Large)",
        num_agents=40, 
        grid_size=(64, 64),
        resource_density=0.5,
        perception_radius=15,
        seed=123
    )
    
    # Summary comparison
    print(f"\n{'='*60}")
    print("OVERALL SUMMARY")
    print(f"{'='*60}")
    
    print(f"Test 1 Results:")
    print(f"  Trade intents: {test1_stats['total_intents']} (across {test1_stats['steps_with_intents']} steps)")
    print(f"  Trade executions: {test1_stats['total_executions']} (across {test1_stats['steps_with_executions']} steps)")
    print(f"  Final goods distribution: good1={test1_inventory['good1_total']}, good2={test1_inventory['good2_total']}")
    
    print(f"\nTest 2 Results:")
    print(f"  Trade intents: {test2_stats['total_intents']} (across {test2_stats['steps_with_intents']} steps)")
    print(f"  Trade executions: {test2_stats['total_executions']} (across {test2_stats['steps_with_executions']} steps)")
    print(f"  Final goods distribution: good1={test2_inventory['good1_total']}, good2={test2_inventory['good2_total']}")
    
    # Diagnosis
    if test1_stats['total_intents'] == 0 and test2_stats['total_intents'] == 0:
        print(f"\n🔍 DIAGNOSIS: No trade intents generated in either test!")
        print("Possible causes:")
        print("- Agents don't have goods in carrying inventory during bilateral exchange")
        print("- Agents never co-locate during bilateral exchange phase")
        print("- All agents have similar goods (no complementary preferences)")
        print("- Environment variables not properly checked during simulation")
        
    elif test1_stats['total_executions'] == 0 and test2_stats['total_executions'] == 0:
        print(f"\n🔍 DIAGNOSIS: Trade intents generated but none executed!")
        print("Possible causes:")
        print("- Execute logic failing viability checks")
        print("- Metrics recording issues")
        print("- Environment variable mismatch between draft and exec")
        
    else:
        print(f"\n✅ DIAGNOSIS: Trade system working in test environment!")
        print("Issue likely specific to GUI controller integration")

if __name__ == "__main__":
    main()