#!/usr/bin/env python3
"""
Manual Test Runner
==================

This script helps you run the unified target selection manual tests.
Each test must be run individually to observe GUI behavior.

Usage:
    python run_test.py <test_number>
    
Where test_number is 1-7:
    1: Baseline behavior (20 agents, 30x30, 0.25 density, radius 8, random)
    2: Sparse long-range (10 agents, 40x40, 0.05 density, radius 15, random)  
    3: High density local (100 agents, 30x30, 0.5 density, radius 2, random)
    4: Large world global (10 agents, 64x64, 0.5 density, radius 20, random)
    5: Cobb-Douglas only (20 agents, 30x30, 0.25 density, radius 8, cobb_douglas)
    6: Leontief only (20 agents, 30x30, 0.25 density, radius 8, leontief)
    7: Perfect Substitutes only (20 agents, 30x30, 0.25 density, radius 8, perfect_substitutes)

Each test runs for 1050 turns with phase transitions at turns 201, 401, 601, 801, 1001.
"""

import sys
import os
import subprocess

def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    
    try:
        test_num = int(sys.argv[1])
        if test_num < 1 or test_num > 7:
            raise ValueError()
    except ValueError:
        print("Error: Test number must be between 1 and 7")
        print(__doc__)
        sys.exit(1)
    
    # Map test numbers to script names
    test_scripts = {
        1: "test_1_baseline.py",
        2: "test_2_sparse_longrange.py", 
        3: "test_3_highdensity_local.py",
        4: "test_4_large_global.py",
        5: "test_5_cobb_douglas.py",
        6: "test_6_leontief.py",
        7: "test_7_perfect_substitutes.py"
    }
    
    test_descriptions = {
        1: "Baseline Behavior (20 agents, random preferences)",
        2: "Sparse Resources with Long Perception (10 agents, 40x40)",
        3: "High Density with Local Perception (100 agents, radius 2)", 
        4: "Large World with Global Perception (64x64, radius 20)",
        5: "Pure Cobb-Douglas Preferences (20 agents)",
        6: "Pure Leontief Preferences (20 agents)",
        7: "Pure Perfect Substitutes Preferences (20 agents)"
    }
    
    script_name = test_scripts[test_num]
    description = test_descriptions[test_num]
    
    print("=" * 60)
    print(f"RUNNING MANUAL TEST {test_num}")
    print("=" * 60)
    print(f"Test: {description}")
    print(f"Script: {script_name}")
    print()
    print("This test will run for 1050 turns with the following phases:")
    print("  1-200: Both foraging and exchange enabled")
    print("  201-400: Only foraging enabled")
    print("  401-600: Only exchange enabled") 
    print("  601-800: Both disabled")
    print("  801-1000: Both enabled")
    print("  1001-1050: Both disabled")
    print()
    print("Watch for phase transitions and agent behavior changes.")
    print("Press Ctrl+C to interrupt the test if needed.")
    print("=" * 60)
    
    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    test_script_path = os.path.join(script_dir, script_name)
    
    if not os.path.exists(test_script_path):
        print(f"Error: Test script {script_name} not found!")
        sys.exit(1)
    
    try:
        # Run the test script
        subprocess.run([sys.executable, test_script_path], cwd=script_dir)
    except KeyboardInterrupt:
        print(f"\\nTest {test_num} interrupted by user.")
    except Exception as e:
        print(f"\\nError running test {test_num}: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()