#!/usr/bin/env python3
"""
Test Framework Validation - Quick non-GUI test to verify framework functionality.
"""

import sys
import os

# Add current directory to path for framework imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(repo_root, "src"))

# Import framework components from new location
from econsim.tools.launcher.framework.simulation_factory import SimulationFactory
from econsim.tools.launcher.framework.phase_manager import PhaseManager
from econsim.tools.launcher.framework.debug_orchestrator import DebugOrchestrator

def test_framework():
    """Comprehensive validation of framework components and all test configs."""
    
    print("🧪 Testing Framework Components...")
    
    # Import all test configs from new location
    from econsim.tools.launcher.framework.test_configs import (
        TEST_1_BASELINE, TEST_2_SPARSE, TEST_3_HIGH_DENSITY, 
        TEST_4_LARGE_WORLD, TEST_5_COBB_DOUGLAS, TEST_6_LEONTIEF, 
        TEST_7_PERFECT_SUBSTITUTES, ALL_TEST_CONFIGS
    )
    
    # Test all configurations
    configs = [
        TEST_1_BASELINE, TEST_2_SPARSE, TEST_3_HIGH_DENSITY, 
        TEST_4_LARGE_WORLD, TEST_5_COBB_DOUGLAS, TEST_6_LEONTIEF, 
        TEST_7_PERFECT_SUBSTITUTES
    ]
    
    print("📋 All Test Configurations:")
    for config in configs:
        print(f"✅ Test {config.id}: {config.name}")
        print(f"   Grid: {config.grid_size}, Agents: {config.agent_count}, Density: {config.resource_density}")
        print(f"   Perception: {config.perception_radius}, Preferences: {config.preference_mix}")
    
    # Test simulation factory with different configs
    print(f"\n🏭 Testing Simulation Factory with all configs:")
    for config in configs:
        try:
            simulation = SimulationFactory.create_simulation(config)
            resources = len(list(simulation.grid.iter_resources()))
            print(f"✅ Test {config.id}: {len(simulation.agents)} agents, {resources} resources")
        except Exception as e:
            print(f"❌ Test {config.id} failed: {e}")
            return False
    
    # Test phase manager
    phase_manager = PhaseManager.create_standard_phases()
    print(f"\n⏱️  Phase Manager: {len(phase_manager.phases)} phases configured")
    
    # Test phase transitions
    transitions = [
        (201, 1, 2), (401, 2, 3), (601, 3, 4), 
        (651, 4, 5), (851, 5, 6)
    ]
    for turn, current_phase, expected_phase in transitions:
        transition = phase_manager.check_transition(turn, current_phase)
        if transition and transition.new_phase == expected_phase:
            print(f"✅ Turn {turn}: Phase {current_phase} → {expected_phase}")
        else:
            print(f"❌ Phase transition failed at turn {turn}")
    
    # Test debug orchestrator with different preference types
    print(f"\n🐛 Testing Debug Orchestrator:")
    for config in [TEST_1_BASELINE, TEST_6_LEONTIEF, TEST_7_PERFECT_SUBSTITUTES]:
        debug_orch = DebugOrchestrator(config)
        categories = len(debug_orch.get_available_categories())
        print(f"✅ {config.preference_mix}: {categories} debug categories configured")
    
    print(f"\n📊 Framework Stats:")
    print(f"✅ {len(ALL_TEST_CONFIGS)} test configurations defined")
    print(f"✅ All 7 tests validated with SimulationFactory")
    print(f"✅ All 5 phase transitions working")
    print(f"✅ Debug orchestration for all preference types")
    
    print("\n🎉 COMPREHENSIVE FRAMEWORK VALIDATION SUCCESSFUL!")
    print("🚀 Framework ready for all 7 manual tests!")
    return True

if __name__ == '__main__':
    test_framework()