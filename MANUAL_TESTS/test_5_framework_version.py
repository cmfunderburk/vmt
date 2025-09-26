#!/usr/bin/env python3
"""
Manual Test 5: Pure Cobb-Douglas Test (Framework Version)  

Shows how specialized preference tests work with the framework.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Add current directory to path for framework imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from framework.base_test import StandardPhaseTest  
from framework.test_configs import TEST_5_COBB_DOUGLAS


class Test5WindowNew(StandardPhaseTest):
    """Test 5 using framework - Pure Cobb-Douglas preferences."""
    
    def __init__(self):
        super().__init__(TEST_5_COBB_DOUGLAS)


def main():
    """Run the Cobb-Douglas test."""
    app = QApplication(sys.argv)
    
    test_window = Test5WindowNew()
    test_window.show()
    
    print("=" * 60)
    print("MANUAL TEST 5: PURE COBB-DOUGLAS (Framework Version)")
    print("=" * 60)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()