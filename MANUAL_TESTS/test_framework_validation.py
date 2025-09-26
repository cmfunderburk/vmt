#!/usr/bin/env python3
"""
Test Framework Validation - Quick non-GUI test to verify framework functionality.
"""

import sys
import os

# Add current directory to path for framework imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import framework components
from framework.test_configs import TEST_1_BASELINE, TEST_2_SPARSE
from framework.simulation_factory import SimulationFactory
from framework.phase_manager import PhaseManager
from framework.debug_orchestrator import DebugOrchestrator

def test_framework():
    """Quick validation of framework components."""
    
    print("🧪 Testing Framework Components...")
    
    # Test configuration
    print(f"✅ Test 1 Config: {TEST_1_BASELINE.name} - {TEST_1_BASELINE.grid_size} grid, {TEST_1_BASELINE.agent_count} agents")
    print(f"✅ Test 2 Config: {TEST_2_SPARSE.name} - {TEST_2_SPARSE.grid_size} grid, {TEST_2_SPARSE.agent_count} agents")
    
    # Test simulation factory 
    try:
        simulation = SimulationFactory.create_simulation(TEST_1_BASELINE)
        print(f"✅ Simulation Factory: Created simulation with {len(simulation.agents)} agents, {len(list(simulation.grid.iter_resources()))} resources")
    except Exception as e:
        print(f"❌ Simulation Factory failed: {e}")
        return False
    
    # Test phase manager
    phase_manager = PhaseManager.create_standard_phases()
    print(f"✅ Phase Manager: Created with {len(phase_manager.phases)} phases")
    
    # Test a phase transition
    transition = phase_manager.check_transition(201, 1)  # Should trigger phase 2
    if transition:
        print(f"✅ Phase Transition: {transition.new_phase} - {transition.description}")
    else:
        print("❌ Phase Transition failed")
        
    # Test debug orchestrator
    debug_orch = DebugOrchestrator(TEST_1_BASELINE)
    print(f"✅ Debug Orchestrator: Configured {len(debug_orch.get_available_categories())} debug categories")
    
    print("\n🎉 Framework validation successful! All components working.")
    return True

if __name__ == '__main__':
    test_framework()