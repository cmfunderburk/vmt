#!/usr/bin/env python3
"""
Manual Test 2: Sparse Long-Range Test (Framework Version)

Demonstrates how easy it is to create new tests with the framework.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Add paths for framework imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(repo_root, "src"))

from econsim.tools.launcher.framework.base_test import StandardPhaseTest  
from econsim.tools.launcher.framework.test_configs import TEST_2_SPARSE


class Test2WindowNew(StandardPhaseTest):
    """Test 2 using framework - 50x50 sparse world with long perception."""
    
    def __init__(self):
        super().__init__(TEST_2_SPARSE)


def main():
    """Run the sparse test."""
    app = QApplication(sys.argv)
    
    test_window = Test2WindowNew()
    test_window.show()
    
    print("=" * 60)
    print("MANUAL TEST 2: SPARSE LONG-RANGE (Framework Version)")
    print("=" * 60)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()