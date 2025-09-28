#!/usr/bin/env python3
"""Debug version of enhanced_test_launcher_v2.py to isolate the import issue."""

print("🔍 Debug: Starting enhanced launcher...")

import sys
import os
import subprocess
from pathlib import Path
from typing import Dict, List

print("🔍 Debug: Basic imports successful")

# Transitional launcher module imports (Phase 2.4 integration)
try:  # Soft dependency during refactor; if missing we fall back to legacy logic
    print("🔍 Debug: Attempting launcher module imports...")
    from econsim.tools.launcher.adapters import load_registry_from_monolith
    from econsim.tools.launcher.comparison import ComparisonController
    from econsim.tools.launcher.executor import TestExecutor
    _launcher_modules_available = True
    print("🔍 Debug: Launcher modules imported successfully")
except Exception as e:  # pragma: no cover - fallback path
    print(f"🔍 Debug: Launcher module import failed: {e}")
    _launcher_modules_available = False

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("🔍 Debug: Project root added to path")

try:
    print("🔍 Debug: Attempting PyQt6 imports...")
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QGridLayout, QScrollArea, QLabel, QPushButton,
        QFrame, QMessageBox, QCheckBox, QTextEdit, QTabWidget
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
    print("🔍 Debug: PyQt6 imports successful")
except ImportError as e:
    print(f"❌ PyQt6 import failed: {e}")
    print("Please ensure PyQt6 is installed in your virtual environment.")
    sys.exit(1)

# Import framework components - try new location first, fallback to legacy
try:
    print("🔍 Debug: Attempting new framework location import...")
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(repo_root, "src"))
    print(f"🔍 Debug: Added {os.path.join(repo_root, 'src')} to path")
    from econsim.tools.launcher.framework.test_configs import TestConfiguration, ALL_TEST_CONFIGS
    print("🔍 Debug: New framework import successful!")
except ImportError as e1:
    print(f"🔍 Debug: New framework import failed: {e1}")
    try:
        print("🔍 Debug: Attempting fallback framework import...")
        from framework.test_configs import TestConfiguration, ALL_TEST_CONFIGS
        print("🔍 Debug: Fallback framework import successful!")
    except ImportError as e2:
        print(f"❌ Framework import failed: {e2}")
        print("Please ensure you're running from the MANUAL_TESTS directory.")
        sys.exit(1)

print("✅ All imports successful! Enhanced launcher ready.")
print(f"Found {len(ALL_TEST_CONFIGS)} test configurations")