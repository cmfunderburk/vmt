#!/usr/bin/env python3
"""
Manual Test 1: Baseline Unified Target Selection Test (Framework Version)

This is Test 1 reimplemented using the new framework - demonstrating 
the dramatic reduction from ~400 lines to ~30 lines.

Configuration:
- Grid: 30x30
- Agents: 20 with random positions and mixed preferences
- Resource density: 0.25
- Perception radius: 8
- Distance scaling: k=0.0 (default)

Phase Schedule (900 turns total, configurable speed):
1. Turns 1-200: Both foraging and exchange enabled
2. Turns 201-400: Only foraging enabled  
3. Turns 401-600: Only exchange enabled
4. Turns 601-650: Both disabled (agents should idle) - shortened phase
5. Turns 651-850: Both enabled again
6. Turns 851-900: Both disabled (final idle phase)
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Add current directory to path for framework imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from framework.base_test import StandardPhaseTest  
from framework.test_configs import TEST_1_BASELINE


class Test1WindowNew(StandardPhaseTest):
    """Test 1 using the new framework - that's all the code needed!"""
    
    def __init__(self):
        super().__init__(TEST_1_BASELINE)


def main():
    """Run the baseline test using the new framework."""
    app = QApplication(sys.argv)
    
    test_window = Test1WindowNew()
    test_window.show()
    
    print("=" * 60)
    print("MANUAL TEST 1: BASELINE UNIFIED TARGET SELECTION (Framework Version)")
    print("=" * 60)
    print("This test will run 900 simulation turns with phase transitions.")
    print("Speed is configurable via dropdown (default: 1 turn/second).")
    print("Watch the console output for phase transition announcements.")
    print("=" * 60)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()