#!/usr/bin/env python3
"""
Batch Test Runner - Compatibility Wrapper
=========================================

This file now imports from the proper location in src/econsim/tools/widgets/
to maintain backwards compatibility for standalone usage.

The actual implementation has been moved to:
    src/econsim/tools/widgets/batch_runner.py

This wrapper allows existing scripts and workflows to continue working.
"""

import sys
from pathlib import Path

# Add src to path to import from proper location
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import from proper location
from econsim.tools.widgets.batch_runner import BatchRunner as BatchTestRunner

# Maintain original interface for compatibility
__all__ = ['BatchTestRunner']

if __name__ == "__main__":
    # Standalone execution support
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    runner = BatchTestRunner()
    runner.show()
    
    sys.exit(app.exec())
