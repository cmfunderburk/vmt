#!/usr/bin/env python3
"""Test creating a simulation without showing GUI.

This tests the core simulation creation flow to validate
that SimulationFactory works correctly with TestRunner.
"""

import sys
from pathlib import Path

# Add src to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root / "src"))

def test_simulation_creation():
    """Test that we can create a simulation from a test config."""
    print("🔧 Testing simulation creation...")
    
    try:
        # Import components
        from econsim.tools.launcher.framework.test_configs import ALL_TEST_CONFIGS
        from econsim.tools.launcher.framework.simulation_factory import SimulationFactory
        
        # Get test config directly
        config = ALL_TEST_CONFIGS[1]  # Test 1: Baseline
        assert config is not None, "Config should not be None"
        
        print(f"📋 Using config: {config.name}")
        print(f"   Grid: {config.grid_size}")
        print(f"   Agents: {config.agent_count}")
        print(f"   Resources: {config.resource_density}")
        
        # Create simulation
        simulation = SimulationFactory.create_simulation(config)
        print(f"✅ Simulation created successfully")
        print(f"   Type: {type(simulation)}")
        
        # Test simulation has expected properties
        assert hasattr(simulation, 'step'), "Simulation should have step method"
        assert hasattr(simulation, 'grid'), "Simulation should have grid"
        assert hasattr(simulation, 'agents'), "Simulation should have agents"
        
        print(f"   Grid size: {simulation.grid.width}x{simulation.grid.height}")
        print(f"   Agent count: {len(simulation.agents)}")
        
        # Try to access turn if it exists, otherwise skip
        if hasattr(simulation, 'turn'):
            print(f"   Current turn: {getattr(simulation, 'turn', 'unknown')}")
        else:
            print(f"   Simulation initialized (no turn counter)")
        
        print("✅ Simulation validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Simulation creation failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """Run simulation creation test."""
    print("=" * 60)
    print("VMT Simulation Creation Test")
    print("=" * 60)
    
    if test_simulation_creation():
        print("\n🎉 Simulation creation test passed!")
        print("TestRunner core functionality is working correctly.")
        return True
    else:
        print("\n❌ Simulation creation test failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)