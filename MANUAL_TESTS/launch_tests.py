#!/usr/bin/env python3
"""
Simple launcher script for the Manual Test Start Menu.
This provides a convenient entry point.
"""

import os
import sys
import subprocess

def main():
    """Launch the test start menu."""
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if we're in a virtual environment
    venv_python = os.path.join(script_dir, "..", "vmt-dev", "bin", "python")
    
    if os.path.exists(venv_python):
        # Use virtual environment python
        cmd = [venv_python, os.path.join(script_dir, "test_start_menu.py")]
    else:
        # Use system python
        cmd = ["python3", os.path.join(script_dir, "test_start_menu.py")]
    
    try:
        subprocess.run(cmd, cwd=script_dir)
    except KeyboardInterrupt:
        print("\nTest start menu closed.")
    except Exception as e:
        print(f"Error launching test start menu: {e}")
        print("Make sure you're in the vmt directory and have activated the virtual environment:")
        print("cd /path/to/vmt && source vmt-dev/bin/activate && cd MANUAL_TESTS && python test_start_menu.py")

if __name__ == "__main__":
    main()