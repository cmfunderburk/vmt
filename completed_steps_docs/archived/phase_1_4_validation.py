#!/usr/bin/env python3
"""
Phase 1.4 Validation: Test Framework Migration Consumer Updates

Validates that all manual test consumers now use the new framework location.
"""
import sys
import os
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "MANUAL_TESTS"))

def test_framework_tests():
    """Test all 7 framework test files import correctly."""
    print("🔬 Testing Framework Test Files...")
    
    failures = []
    for i in range(1, 8):
        try:
            module_name = f"test_{i}_framework_version"
            exec(f"import {module_name}")
            print(f"  ✅ {module_name}")
        except Exception as e:
            print(f"  ❌ {module_name}: {e}")
            failures.append(module_name)
    
    return failures

def test_custom_tests():
    """Test custom test files import correctly."""
    print("\n🔬 Testing Custom Test Files...")
    
    sys.path.insert(0, str(repo_root / "MANUAL_TESTS" / "custom_tests"))
    
    custom_tests = [
        "baseline_unified_target_selection",
        "sample_economic_behavior_study",
        "a", 
        "test"
    ]
    
    failures = []
    for test_name in custom_tests:
        try:
            exec(f"import {test_name}")
            print(f"  ✅ {test_name}")
        except Exception as e:
            print(f"  ❌ {test_name}: {e}")
            failures.append(test_name)
    
    return failures

def test_enhanced_launcher():
    """Test enhanced launcher imports correctly."""
    print("\n🔬 Testing Enhanced Launcher...")
    
    try:
        import enhanced_test_launcher_v2
        print("  ✅ enhanced_test_launcher_v2")
        return []
    except Exception as e:
        print(f"  ❌ enhanced_test_launcher_v2: {e}")
        return ["enhanced_test_launcher_v2"]

def test_new_framework_location():
    """Test that new framework location works."""
    print("\n🔬 Testing New Framework Location...")
    
    try:
        from econsim.tools.launcher.framework.test_configs import TestConfiguration
        from econsim.tools.launcher.framework.base_test import StandardPhaseTest
        print("  ✅ New framework location accessible")
        return []
    except Exception as e:
        print(f"  ❌ New framework location: {e}")
        return ["new_framework_location"]

if __name__ == "__main__":
    print("🚀 Phase 1.4 Validation: Framework Migration Consumer Updates")
    print(f"Repository: {repo_root}")
    
    all_failures = []
    
    # Run all tests
    all_failures.extend(test_framework_tests())
    all_failures.extend(test_custom_tests())
    all_failures.extend(test_enhanced_launcher())
    all_failures.extend(test_new_framework_location())
    
    # Summary
    print(f"\n📊 Validation Summary:")
    if not all_failures:
        print("✅ All tests passed! Phase 1.4 migration successful.")
        sys.exit(0)
    else:
        print(f"❌ {len(all_failures)} failures: {', '.join(all_failures)}")
        sys.exit(1)