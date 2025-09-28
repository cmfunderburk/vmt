#!/usr/bin/env python3
"""
Manual Test 6: Pure Leontief Test (Framework Version)

All agents have Leontief preferences focusing on complementary resources.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Add paths for framework imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(repo_root, "src"))

from econsim.tools.launcher.framework.base_test import StandardPhaseTest  
from econsim.tools.launcher.framework.test_configs import TEST_6_LEONTIEF


class Test6WindowNew(StandardPhaseTest):
    """Test 6 using framework - Pure Leontief complementary preferences."""
    
    def __init__(self):
        super().__init__(TEST_6_LEONTIEF)


def main():
    """Run the Leontief test."""
    app = QApplication(sys.argv)
    
    test_window = Test6WindowNew()
    test_window.show()
    
    print("=" * 60)
    print("MANUAL TEST 6: PURE LEONTIEF (Framework Version)")
    print("=" * 60)
    print("Testing complementary resource behavior")
    print("All agents have Leontief preferences (min utility)")
    print("Watch for balanced resource collection patterns")
    print("=" * 60)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()