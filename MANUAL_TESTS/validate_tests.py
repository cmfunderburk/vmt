#!/usr/bin/env python3
"""
Test Validation Script
======================

This script validates that all manual test scripts can import and initialize properly.
Run this to check if the test environment is set up correctly.
"""

import sys
import os
import traceback

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

def validate_imports():
    """Check if all required imports are available."""
    print("Validating imports...")
    
    try:
        from econsim.gui.main_window import MainWindow
        print("✅ MainWindow import: OK")
    except ImportError as e:
        print(f"❌ MainWindow import failed: {e}")
        return False
    
    try:
        from econsim.simulation.config import SimConfig
        print("✅ SimConfig import: OK")
    except ImportError as e:
        print(f"❌ SimConfig import failed: {e}")
        return False
        
    try:
        from econsim.preferences.factory import PreferenceFactory
        print("✅ PreferenceFactory import: OK")
    except ImportError as e:
        print(f"❌ PreferenceFactory import failed: {e}")
        return False
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        print("✅ PyQt6 imports: OK")
    except ImportError as e:
        print(f"❌ PyQt6 import failed: {e}")
        return False
        
    return True

def validate_preference_factories():
    """Check if preference factories work correctly."""
    print("\nValidating preference factories...")
    
    try:
        # Test individual preference types
        from econsim.preferences.cobb_douglas import CobbDouglasPreference
        from econsim.preferences.leontief import LeontiefPreference
        from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference
        
        # Test Cobb-Douglas
        pref_cd = CobbDouglasPreference(alpha=0.5)
        print(f"✅ cobb_douglas preference creation: OK")
        
        # Test Leontief
        pref_leo = LeontiefPreference(a=1.0, b=1.0)
        print(f"✅ leontief preference creation: OK")
        
        # Test Perfect Substitutes
        pref_ps = PerfectSubstitutesPreference(a=1.0, b=1.0)
        print(f"✅ perfect_substitutes preference creation: OK")
        
        # Test random preference factory function
        import random
        def test_random_factory(idx: int):
            pref_rng = random.Random(12345 + idx + 2000)
            pref_types = ['cobb_douglas', 'perfect_substitutes', 'leontief']
            chosen_type = pref_rng.choice(pref_types)
            
            if chosen_type == 'cobb_douglas':
                return CobbDouglasPreference(alpha=0.5)
            elif chosen_type == 'perfect_substitutes':
                return PerfectSubstitutesPreference(a=1.0, b=1.0)
            elif chosen_type == 'leontief':
                return LeontiefPreference(a=1.0, b=1.0)
        
        # Test random factory
        random_pref = test_random_factory(0)
        print(f"✅ random preference factory: OK")
                
    except Exception as e:
        print(f"❌ Preference validation failed: {e}")
        traceback.print_exc()
        return False
        
    return True

def validate_config_creation():
    """Check if SimConfig can be created properly."""
    print("\nValidating SimConfig creation...")
    
    try:
        from econsim.simulation.config import SimConfig
        
        config = SimConfig(
            grid_size=(30, 30),
            initial_resources=[(1, 1, 'A'), (2, 2, 'B')],
            seed=12345,
            enable_respawn=True,
            enable_metrics=True
        )
        print("✅ SimConfig creation: OK")
        return True
        
    except Exception as e:
        print(f"❌ SimConfig creation failed: {e}")
        traceback.print_exc()
        return False

def main():
    print("=" * 50)
    print("MANUAL TEST VALIDATION")
    print("=" * 50)
    
    all_valid = True
    
    all_valid &= validate_imports()
    all_valid &= validate_preference_factories() 
    all_valid &= validate_config_creation()
    
    print("\n" + "=" * 50)
    if all_valid:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("Manual tests are ready to run.")
        print("\nTo run a test:")
        print("  python run_test.py <1-7>")
        print("\nExample:")
        print("  python run_test.py 1")
    else:
        print("❌ VALIDATION FAILED!")
        print("Some components are not working correctly.")
        print("Please check the error messages above.")
    print("=" * 50)
    
    return 0 if all_valid else 1

if __name__ == '__main__':
    sys.exit(main())