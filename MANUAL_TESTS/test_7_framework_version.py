#!/usr/bin/env python3
"""
Manual Test 7: Pure Perfect Substitutes Test (Framework Version)

All agents have Perfect Substitutes preferences for resource interchangeability.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Add paths for framework imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(repo_root, "src"))

from econsim.tools.launcher.framework.base_test import StandardPhaseTest  
from econsim.tools.launcher.framework.test_configs import TEST_7_PERFECT_SUBSTITUTES


class Test7WindowNew(StandardPhaseTest):
    """Test 7 using framework - Pure Perfect Substitutes preferences."""
    
    def __init__(self):
        super().__init__(TEST_7_PERFECT_SUBSTITUTES)


def main():
    """Run the Perfect Substitutes test."""
    app = QApplication(sys.argv)
    
    test_window = Test7WindowNew()
    test_window.show()
    
    print("=" * 60)
    print("MANUAL TEST 7: PURE PERFECT SUBSTITUTES (Framework Version)")
    print("=" * 60)
    print("Testing resource interchangeability behavior")
    print("All agents have Perfect Substitutes preferences (linear utility)")
    print("Watch for resource type indifference in collection")
    print("=" * 60)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()