#!/usr/bin/env python3
"""
Enhanced Test Launcher for VMT Framework
========================================

Simple enhanced test launcher with visual test cards showing both original 
and framework implementations with quick launch capabilities.

Features:
- Visual test cards with configuration details
- Side-by-side original vs framework launch options  
- Test comparison selection

Usage:
    python enhanced_test_launcher.py [options]
    
Options:
    --version       Show version information
    --help         Show this help message
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import Dict, List
import argparse

# Transitional launcher module imports (Phase 2.2 integration)
# Phase 4: Direct imports - only components needed by entry point
from econsim.tools.launcher.style import PlatformStyler
from econsim.tools.launcher.app_window import VMTLauncherWindow

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QGridLayout, QScrollArea, QLabel, QPushButton,
        QFrame, QMessageBox, QCheckBox, QTextEdit, QTabWidget
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
except ImportError as e:
    print(f"❌ PyQt6 import failed: {e}")
    print("Please ensure PyQt6 is installed in your virtual environment.")
    sys.exit(1)

# Import framework components - Phase 4: use extracted location
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(repo_root, "src"))
from econsim.tools.launcher.framework.test_configs import TestConfiguration, ALL_TEST_CONFIGS


# CustomTestsWidget extracted to src/econsim/tools/launcher/tabs/custom_tests_tab.py in Phase 2.3
# CustomTestCardWidget extracted to src/econsim/tools/launcher/cards.py in Phase 2.1
# TestCardWidget extracted to src/econsim/tools/launcher/cards.py in Phase 2.2

# Fallback implementations removed in Phase 4 cleanup - all components now available



# Legacy EnhancedTestLauncher class removed in Phase 4 cleanup (2025-09-28)
# All functionality now handled by VMTLauncherWindow from extracted components

def parse_command_line() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="VMT Enhanced Test Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python enhanced_test_launcher_v2.py           # Launch GUI
  python enhanced_test_launcher_v2.py --version # Show version
        """.strip()
    )
    
    parser.add_argument(
        '--version', 
        action='version',
        version='VMT Enhanced Test Launcher 1.0.0'
    )
    
    return parser.parse_args()


def check_environment():
    """Check virtual environment status and warn if not in venv."""
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not running in a virtual environment")
        print("   It's recommended to activate your vmt-dev environment first")


def configure_qt_environment():
    """Configure Qt environment variables for cross-platform compatibility."""
    import os
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'


def create_application() -> 'QApplication':
    """Create and configure QApplication with proper settings."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("VMT Enhanced Test Launcher")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("VMT Project")
    
    return app


def apply_platform_styling(app: 'QApplication') -> None:
    """Apply platform-specific styling using extracted components."""
    PlatformStyler.configure_application(app)


def create_main_window():
    """Create the main launcher window using extracted components."""
    return VMTLauncherWindow()


def main():
    """Main entry point for enhanced test launcher."""
    # Parse command-line arguments (handles --version and --help automatically)
    args = parse_command_line()
    
    # Check environment and setup
    check_environment()
    configure_qt_environment()
    
    # Create and configure application
    app = create_application()
    apply_platform_styling(app)
    
    # Create and show main window
    launcher = create_main_window()
    launcher.show()
    
    # Start application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()