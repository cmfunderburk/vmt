#!/usr/bin/env python3
"""Test script for programmatic TestRunner implementation.

Tests the TestRunner API without GUI integration to validate
core functionality before launcher integration.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root / "src"))

def test_test_runner_initialization():
    """Test that TestRunner can be initialized successfully."""
    print("🔧 Testing TestRunner initialization...")
    
    try:
        from econsim.tools.launcher.test_runner import TestRunner
        
        runner = TestRunner()
        print("✅ TestRunner initialized successfully")
        
        # Test status method
        status = runner.get_status()
        print(f"📊 Status: {status}")
        
        assert status['available_tests'] == 7, f"Expected 7 tests, got {status['available_tests']}"
        assert status['test_ids'] == [1, 2, 3, 4, 5, 6, 7], f"Unexpected test IDs: {status['test_ids']}"
        assert status['qt_available'] is True, "PyQt6 should be available"
        assert status['framework_available'] is True, "Framework should be available"
        
        print("✅ Status validation passed")
        return runner
        
    except Exception as e:
        print(f"❌ TestRunner initialization failed: {e}")
        import traceback
        print(traceback.format_exc())
        return None

def test_config_lookup(runner):
    """Test configuration lookup functionality."""
    print("\n🔧 Testing configuration lookup...")
    
    try:
        # Test valid lookups
        for test_id in [1, 2, 3, 4, 5, 6, 7]:
            config = runner._get_config_by_id(test_id)
            assert config is not None, f"Config {test_id} should exist"
            assert config.id == test_id, f"Config ID mismatch: {config.id} != {test_id}"
            print(f"✅ Test {test_id}: {config.name}")
        
        # Test invalid lookup
        invalid_config = runner._get_config_by_id(999)
        assert invalid_config is None, "Invalid config ID should return None"
        
        print("✅ Configuration lookup validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration lookup failed: {e}")
        return False

def test_available_tests(runner):
    """Test available tests mapping."""
    print("\n🔧 Testing available tests mapping...")
    
    try:
        available = runner.get_available_tests()
        print(f"📋 Available tests: {available}")
        
        assert len(available) == 7, f"Expected 7 tests, got {len(available)}"
        
        expected_names = {
            1: "Baseline Unified Target Selection",
            2: "Sparse Long-Range", 
            3: "High Density Local",
            4: "Large World Global",
            5: "Pure Cobb-Douglas",
            6: "Pure Leontief",
            7: "Pure Perfect Substitutes"
        }
        
        for test_id, expected_name in expected_names.items():
            assert test_id in available, f"Test {test_id} not in available tests"
            assert expected_name in available[test_id], f"Name mismatch for test {test_id}"
        
        print("✅ Available tests validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Available tests validation failed: {e}")
        return False

def test_error_handling(runner):
    """Test error handling for invalid inputs."""
    print("\n🔧 Testing error handling...")
    
    try:
        # Test invalid test ID
        try:
            runner.run_by_id(999, "framework")
            assert False, "Should have raised ValueError for invalid test ID"
        except ValueError as e:
            print(f"✅ Invalid test ID correctly rejected: {e}")
        
        # Test invalid mode
        try:
            runner.run_by_id(1, "invalid_mode")
            assert False, "Should have raised ValueError for invalid mode"
        except ValueError as e:
            print(f"✅ Invalid mode correctly rejected: {e}")
        
        print("✅ Error handling validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error handling validation failed: {e}")
        return False

def test_framework_components():
    """Test that framework components can be imported."""
    print("\n🔧 Testing framework component imports...")
    
    try:
        # Test SimulationFactory import
        from econsim.tools.launcher.framework.simulation_factory import SimulationFactory
        print("✅ SimulationFactory imported successfully")
        
        # Test EmbeddedPygameWidget import  
        from econsim.gui.embedded_pygame import EmbeddedPygameWidget
        print("✅ EmbeddedPygameWidget imported successfully")
        
        # Test TestConfiguration import
        from econsim.tools.launcher.framework.test_configs import ALL_TEST_CONFIGS
        print(f"✅ Test configs imported: {len(ALL_TEST_CONFIGS)} configurations")
        
        return True
        
    except Exception as e:
        print(f"❌ Framework component import failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("=" * 60)
    print("VMT TestRunner Validation Script")
    print("=" * 60)
    
    # Test framework components first
    if not test_framework_components():
        print("\n❌ Framework component validation failed - aborting")
        return False
    
    # Test runner initialization
    runner = test_test_runner_initialization()
    if not runner:
        print("\n❌ TestRunner initialization failed - aborting")
        return False
    
    # Run validation tests
    tests = [
        ("Configuration Lookup", lambda: test_config_lookup(runner)),
        ("Available Tests", lambda: test_available_tests(runner)),
        ("Error Handling", lambda: test_error_handling(runner)),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validation tests passed! TestRunner ready for integration.")
        return True
    else:
        print("⚠️  Some validation tests failed. Review before integration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)