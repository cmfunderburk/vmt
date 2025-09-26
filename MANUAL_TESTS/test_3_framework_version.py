#!/usr/bin/env python3
"""
Manual Test 3: High Density Local Test (Framework Version)

Crowded environment with many agents in small space and short perception.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Add current directory to path for framework imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from framework.base_test import StandardPhaseTest  
from framework.test_configs import TEST_3_HIGH_DENSITY


class Test3WindowNew(StandardPhaseTest):
    """Test 3 using framework - High density crowding behavior."""
    
    def __init__(self):
        super().__init__(TEST_3_HIGH_DENSITY)


def main():
    """Run the high density test."""
    app = QApplication(sys.argv)
    
    test_window = Test3WindowNew()
    test_window.show()
    
    print("=" * 60)
    print("MANUAL TEST 3: HIGH DENSITY LOCAL (Framework Version)")
    print("=" * 60)
    print("Testing crowding behavior with 30 agents in 15x15 grid")
    print("Short perception radius (3) creates local competition")
    print("=" * 60)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()