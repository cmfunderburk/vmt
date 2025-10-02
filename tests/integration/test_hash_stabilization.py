"""Hash stabilization tests for agent refactor validation."""

import pytest
import json
from pathlib import Path
from econsim.tools.launcher.framework.test_configs import ALL_TEST_CONFIGS
from econsim.tools.launcher.framework.simulation_factory import SimulationFactory


class TestHashStabilization:
    """Test that agent refactor maintains determinism hashes."""
    
    def test_hash_equivalence_multiple_seeds(self):
        """Test hash equivalence across multiple seeds after refactor."""
        baseline_path = Path(__file__).parent.parent.parent / "baselines" / "determinism_hashes.json"
        
        if not baseline_path.exists():
            pytest.skip("Baseline determinism_hashes.json not found - run baseline generation first")
        
        with open(baseline_path) as f:
            baseline_data = json.load(f)
        
        # Create lookup for baseline hashes
        baseline_lookup = {}
        for scenario in baseline_data["scenarios"]:
            baseline_lookup[scenario["scenario_name"]] = scenario["determinism_hash"]
        
        # Test first 3 scenarios from baseline
        test_scenario_ids = [1, 2, 3]  # Baseline, Sparse, High Density
        
        for scenario_id in test_scenario_ids:
            if scenario_id not in ALL_TEST_CONFIGS:
                pytest.skip(f"Test configuration not found for scenario {scenario_id}")
            
            test_config = ALL_TEST_CONFIGS[scenario_id]
            scenario_name = test_config.name
            
            if scenario_name not in baseline_lookup:
                pytest.skip(f"Baseline hash not found for scenario: {scenario_name}")
            
            expected_hash = baseline_lookup[scenario_name]
            
            # Create simulation using factory (same as baseline generation)
            sim = SimulationFactory.create_simulation(test_config)
            
            # Run for same number of steps as baseline
            steps_to_run = 500  # From baseline data
            import random
            rng = random.Random(42)  # Use same seed as baseline generation script
            rng.seed(42)  # Reset to known state (same as baseline script)
            
            for _ in range(steps_to_run):
                sim.step(rng)
            
            # Get current hash using same method as baseline generation
            import hashlib
            state_data = []
            
            # Agent positions and inventories (same as baseline script)
            for agent in sim.agents:
                state_data.append(f"agent_{agent.id}_{agent.x}_{agent.y}")
                if hasattr(agent, 'carrying') and agent.carrying:
                    for res_type, count in sorted(agent.carrying.items()):
                        state_data.append(f"carried_{agent.id}_{res_type}_{count}")
                if hasattr(agent, 'home_inventory') and agent.home_inventory:
                    for res_type, count in sorted(agent.home_inventory.items()):
                        state_data.append(f"home_{agent.id}_{res_type}_{count}")
            
            # Resource positions (grid resources - static)
            for x, y, rtype in sim.grid.iter_resources_sorted():
                state_data.append(f"resource_{x}_{y}_{rtype}")
            
            # Create hash from sorted state (same as baseline script)
            state_str = "|".join(sorted(state_data))
            actual_hash = hashlib.md5(state_str.encode()).hexdigest()[:16]
            
            # Compare hashes
            assert actual_hash == expected_hash, (
                f"Hash mismatch for scenario '{scenario_name}':\n"
                f"  Expected: {expected_hash}\n"
                f"  Actual:   {actual_hash}\n"
                f"  This indicates the refactor changed simulation behavior."
            )
    
    def test_agent_state_serialization_consistency(self):
        """Test that agent state serialization is consistent after refactor."""
        # Use a simple test configuration
        if 1 not in ALL_TEST_CONFIGS:
            pytest.skip("Test configuration not available")
        
        test_config = ALL_TEST_CONFIGS[1]  # Use baseline scenario
        sim = SimulationFactory.create_simulation(test_config)
        
        # Run simulation for a few steps
        import random
        rng = random.Random(42)
        
        for _ in range(10):
            sim.step(rng)
        
        # Serialize all agents
        agent_states = []
        for agent in sim.agents:
            # Use the agent's serialize method if available, otherwise manual serialization
            if hasattr(agent, 'serialize'):
                agent_states.append(agent.serialize())
            else:
                # Manual serialization of key fields
                agent_states.append({
                    "id": agent.id,
                    "x": agent.x,
                    "y": agent.y,
                    "mode": agent.mode.value if hasattr(agent.mode, 'value') else str(agent.mode),
                    "carrying": dict(agent.carrying),
                    "home_inventory": dict(agent.home_inventory),
                    "target": agent.target,
                    "trade_partner_id": getattr(agent, 'trade_partner_id', None),
                    "meeting_point": getattr(agent, 'meeting_point', None)
                })
        
        # Verify serialization is deterministic
        agent_states_2 = []
        for agent in sim.agents:
            if hasattr(agent, 'serialize'):
                agent_states_2.append(agent.serialize())
            else:
                agent_states_2.append({
                    "id": agent.id,
                    "x": agent.x,
                    "y": agent.y,
                    "mode": agent.mode.value if hasattr(agent.mode, 'value') else str(agent.mode),
                    "carrying": dict(agent.carrying),
                    "home_inventory": dict(agent.home_inventory),
                    "target": agent.target,
                    "trade_partner_id": getattr(agent, 'trade_partner_id', None),
                    "meeting_point": getattr(agent, 'meeting_point', None)
                })
        
        assert agent_states == agent_states_2, "Agent serialization should be deterministic"
        
        # Verify all agents have consistent state structure
        for i, state in enumerate(agent_states):
            assert "id" in state, f"Agent {i} missing 'id' in serialization"
            assert "x" in state, f"Agent {i} missing 'x' in serialization"
            assert "y" in state, f"Agent {i} missing 'y' in serialization"
            assert "mode" in state, f"Agent {i} missing 'mode' in serialization"
            assert "carrying" in state, f"Agent {i} missing 'carrying' in serialization"
            assert "home_inventory" in state, f"Agent {i} missing 'home_inventory' in serialization"
    
    def test_component_integration_hash_stability(self):
        """Test that component integration doesn't affect hash stability."""
        # Use a simple test configuration
        if 1 not in ALL_TEST_CONFIGS:
            pytest.skip("Test configuration not available")
        
        test_config = ALL_TEST_CONFIGS[1]  # Use baseline scenario
        
        # Run simulation twice with same seed
        sim1 = SimulationFactory.create_simulation(test_config)
        sim2 = SimulationFactory.create_simulation(test_config)
        
        import random
        rng1 = random.Random(999)
        rng2 = random.Random(999)
        
        steps = 50
        for _ in range(steps):
            sim1.step(rng1)
            sim2.step(rng2)
        
        # Hashes should be identical
        hash1 = sim1.metrics_collector.determinism_hash()
        hash2 = sim2.metrics_collector.determinism_hash()
        
        assert hash1 == hash2, (
            f"Identical simulations produced different hashes:\n"
            f"  Hash1: {hash1}\n"
            f"  Hash2: {hash2}\n"
            f"  This indicates non-deterministic behavior."
        )
        
        # Agent states should be identical
        for i, (agent1, agent2) in enumerate(zip(sim1.agents, sim2.agents)):
            assert agent1.x == agent2.x, f"Agent {i} x position differs"
            assert agent1.y == agent2.y, f"Agent {i} y position differs"
            assert agent1.mode == agent2.mode, f"Agent {i} mode differs"
            assert agent1.carrying == agent2.carrying, f"Agent {i} carrying differs"
            assert agent1.home_inventory == agent2.home_inventory, f"Agent {i} home_inventory differs"
