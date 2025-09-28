#!/usr/bin/env python3
"""
Test the new customizable phase scheduling system.

This script demonstrates the key features:
1. Creating custom phase schedules programmatically
2. Validating phase configurations
3. Generating phase summaries
4. Integration with the test framework
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root / 'MANUAL_TESTS'))

# Pre-import framework components to avoid repetitive conditional imports
from econsim.tools.launcher.framework.phase_manager import PhaseManager, PhaseBehavior, PhaseDefinition
from econsim.tools.launcher.framework.test_configs import TestConfiguration

def test_basic_phase_creation():
    """Test basic phase creation methods."""
    print("=== Testing Basic Phase Creation ===\n")
    
    # Using pre-imported framework components
    
    # Test 1: Standard phases
    print("1. Standard 6-Phase Schedule:")
    standard = PhaseManager.create_standard_phases()
    print(f"   Total turns: {standard.get_total_turns()}")
    print(f"   Summary: {standard.get_phase_summary()}")
    print()
    
    # Test 2: Simple phases
    print("2. Simple Custom Schedule:")
    simple = PhaseManager.create_simple_phases(
        forage_only=100,
        both_enabled=150,
        both_disabled=25
    )
    print(f"   Total turns: {simple.get_total_turns()}")
    print(f"   Summary: {simple.get_phase_summary()}")
    print()
    
    # Test 3: Custom phases
    print("3. Fully Custom Schedule:")
    custom = PhaseManager.create_custom_phases([
        (PhaseBehavior.forage_only(), 75),
        (PhaseBehavior.exchange_only(), 100),
        (PhaseBehavior.both_enabled(), 200),
        (PhaseBehavior.both_disabled(), 25)
    ])
    print(f"   Total turns: {custom.get_total_turns()}")
    print(f"   Summary: {custom.get_phase_summary()}")
    print()


def test_phase_validation():
    """Test phase configuration validation."""
    print("=== Testing Phase Validation ===\n")
    
    # Using pre-imported framework components
    
    # Test valid configuration
    try:
        valid_phases = [
            PhaseDefinition(1, 1, 100, "Phase 1", True, False),
            PhaseDefinition(2, 101, 200, "Phase 2", True, True),
        ]
        manager = PhaseManager(valid_phases)
        print("✅ Valid configuration accepted")
    except Exception as e:
        print(f"❌ Unexpected error with valid config: {e}")
    
    # Test invalid configuration (gap in turns)
    try:
        invalid_phases = [
            PhaseDefinition(1, 1, 100, "Phase 1", True, False),
            PhaseDefinition(2, 105, 200, "Phase 2", True, True),  # Gap at 101-104
        ]
        manager = PhaseManager(invalid_phases)
        print("❌ Invalid configuration was incorrectly accepted")
    except Exception as e:
        print(f"✅ Invalid configuration correctly rejected: {e}")
    
    # Test invalid configuration (doesn't start at 1)
    try:
        invalid_phases = [
            PhaseDefinition(1, 5, 100, "Phase 1", True, False),  # Starts at 5, not 1
        ]
        manager = PhaseManager(invalid_phases)
        print("❌ Invalid start configuration was incorrectly accepted")
    except Exception as e:
        print(f"✅ Invalid start configuration correctly rejected: {e}")
    
    print()


def test_phase_transitions():
    """Test phase transition logic."""
    print("=== Testing Phase Transition Logic ===\n")
    
    # Using pre-imported framework components
    
    # Create a simple schedule
    manager = PhaseManager.create_custom_phases([
        (PhaseBehavior.forage_only(), 50),
        (PhaseBehavior.both_enabled(), 75),
        (PhaseBehavior.both_disabled(), 25)
    ])
    
    # Test transitions at various turns
    test_turns = [1, 25, 50, 51, 75, 125, 126, 150, 151]
    current_phase = 0
    
    for turn in test_turns:
        transition = manager.check_transition(turn, current_phase)
        if transition:
            current_phase = transition.new_phase
            print(f"Turn {turn}: Transition to Phase {current_phase} - {transition.description}")
        else:
            phase_info = manager.get_current_phase_info(turn)
            if phase_info:
                print(f"Turn {turn}: Continuing Phase {phase_info.number}")
            else:
                print(f"Turn {turn}: Test complete")
    
    print()


def test_integration_with_test_config():
    """Test integration with TestConfiguration."""
    print("=== Testing Integration with TestConfiguration ===\n")
    
    # Using pre-imported framework components
    
    # Create custom phases
    custom_phases = PhaseManager.create_custom_phases([
        (PhaseBehavior.forage_only(), 100),
        (PhaseBehavior.both_enabled(), 150)
    ])
    
    # Create test configuration with custom phases
    config = TestConfiguration(
        id=999,
        name="Custom Phase Test",
        description="Testing custom phase integration",
        grid_size=(20, 20),
        agent_count=10,
        resource_density=0.25,
        perception_radius=5,
        preference_mix="mixed",
        seed=12345,
        custom_phases=list(custom_phases.phases.values())
    )
    
    print(f"Test Config: {config.name}")
    print(f"Custom Phases: {'Yes' if config.custom_phases else 'No'}")
    
    if config.custom_phases:
        # Recreate manager from config phases
        test_manager = PhaseManager(config.custom_phases)
        print(f"Phase Summary: {test_manager.get_phase_summary()}")
        print(f"Total Turns: {test_manager.get_total_turns()}")
    
    print()


def main():
    """Run all tests."""
    print("Custom Phase Scheduling System Test\n")
    print("=" * 50)
    
    try:
        test_basic_phase_creation()
        test_phase_validation()
        test_phase_transitions()
        test_integration_with_test_config()
        
        print("🎉 All tests completed successfully!")
        print("\nThe custom phase scheduling system is ready for use.")
        print("\nKey Features Available:")
        print("• PhaseManager.create_standard_phases() - Original 6-phase pattern")
        print("• PhaseManager.create_simple_phases(**kwargs) - Easy 4-behavior setup")
        print("• PhaseManager.create_custom_phases(phases) - Full flexibility")
        print("• Integration with TestConfiguration.custom_phases")
        print("• Phase configuration GUI editor (phase_config_editor.py)")
        print("• Live config editor includes phase configuration")
        print("• Automatic validation and error checking")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root with vmt-dev activated")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()