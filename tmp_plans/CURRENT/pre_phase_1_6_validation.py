#!/usr/bin/env python3
"""
Pre-Phase 1.6 Validation: Comprehensive Framework Migration Test

Tests that the entire system works with the new framework location before
removing the legacy framework directory.
"""
import sys
import os
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "MANUAL_TESTS"))

def test_new_framework_components():
    """Test that all new framework components work."""
    print("🔬 Testing New Framework Components...")
    failures = []
    
    try:
        from econsim.tools.launcher.framework.test_configs import TestConfiguration, ALL_TEST_CONFIGS
        from econsim.tools.launcher.framework.base_test import StandardPhaseTest
        from econsim.tools.launcher.framework.phase_manager import PhaseManager, PhaseBehavior
        from econsim.tools.launcher.framework.simulation_factory import SimulationFactory
        from econsim.tools.launcher.framework.debug_orchestrator import DebugOrchestrator
        from econsim.tools.launcher.framework.ui_components import DebugPanel
        print("  ✅ All framework components importable")
    except Exception as e:
        print(f"  ❌ Framework component import failed: {e}")
        failures.append("framework_components")
    
    return failures

def test_launcher_integration():
    """Test that launcher components work with new framework."""
    print("\n🔬 Testing Launcher Integration...")
    failures = []
    
    try:
        from econsim.tools.launcher.adapters import load_registry_from_monolith
        registry = load_registry_from_monolith()
        print("  ✅ Launcher adapters work with new framework")
    except Exception as e:
        print(f"  ❌ Launcher integration failed: {e}")
        failures.append("launcher_integration")
    
    return failures

def test_critical_consumers():
    """Test critical consumers that were migrated."""
    print("\n🔬 Testing Critical Consumers...")
    failures = []
    
    # Test framework tests
    for i in range(1, 8):
        try:
            exec(f"import test_{i}_framework_version")
            print(f"  ✅ test_{i}_framework_version")
        except Exception as e:
            print(f"  ❌ test_{i}_framework_version: {e}")
            failures.append(f"test_{i}_framework_version")
    
    # Test custom tests
    custom_tests = ["baseline_unified_target_selection", "sample_economic_behavior_study"]
    sys.path.insert(0, str(repo_root / "MANUAL_TESTS" / "custom_tests"))
    
    for test_name in custom_tests:
        try:
            exec(f"import {test_name}")
            print(f"  ✅ {test_name}")
        except Exception as e:
            print(f"  ❌ {test_name}: {e}")
            failures.append(test_name)
    
    # Test enhanced launcher v2
    try:
        import enhanced_test_launcher_v2
        print("  ✅ enhanced_test_launcher_v2")
    except Exception as e:
        print(f"  ❌ enhanced_test_launcher_v2: {e}")
        failures.append("enhanced_test_launcher_v2")
    
    return failures

def test_remaining_files():
    """Test remaining files migrated in Phase 1.5."""
    print("\n🔬 Testing Remaining Files...")
    failures = []
    
    remaining_files = [
        "test_framework_validation",
        "example_custom_phases",
        "phase_config_editor", 
        "test_custom_phases",
        "live_config_editor"
    ]
    
    for file_name in remaining_files:
        try:
            exec(f"import {file_name}")
            print(f"  ✅ {file_name}")
        except Exception as e:
            print(f"  ❌ {file_name}: {e}")
            failures.append(file_name)
    
    return failures

if __name__ == "__main__":
    print("🚀 Pre-Phase 1.6 Comprehensive Validation")
    print(f"Repository: {repo_root}")
    print("Testing complete system before legacy framework removal...\n")
    
    all_failures = []
    
    # Run all tests
    all_failures.extend(test_new_framework_components())
    all_failures.extend(test_launcher_integration()) 
    all_failures.extend(test_critical_consumers())
    all_failures.extend(test_remaining_files())
    
    # Summary
    print(f"\n📊 Comprehensive Validation Summary:")
    if not all_failures:
        print("✅ ALL TESTS PASSED! System ready for legacy framework removal.")
        sys.exit(0)
    else:
        print(f"❌ {len(all_failures)} failures detected:")
        for failure in all_failures:
            print(f"   - {failure}")
        print("\n🛑 DO NOT PROCEED with Phase 1.6 until issues are resolved!")
        sys.exit(1)