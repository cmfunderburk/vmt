#!/usr/bin/env python3
"""
Manual Test 4: Large World Global Test (Framework Version)

Large sparse world with global awareness for long-distance decisions.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Add current directory to path for framework imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from framework.base_test import StandardPhaseTest  
from framework.test_configs import TEST_4_LARGE_WORLD


class Test4WindowNew(StandardPhaseTest):
    """Test 4 using framework - Large world global optimization."""
    
    def __init__(self):
        super().__init__(TEST_4_LARGE_WORLD)


def main():
    """Run the large world test."""
    app = QApplication(sys.argv)
    
    test_window = Test4WindowNew()
    test_window.show()
    
    print("=" * 60)
    print("MANUAL TEST 4: LARGE WORLD GLOBAL (Framework Version)")
    print("=" * 60)
    print("Testing global optimization with 15 agents in 60x60 grid")
    print("Global perception radius (25) enables long-distance decisions")
    print("=" * 60)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()