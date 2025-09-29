"""Reusable GUI widgets for VMT tools.

This package contains GUI components that can be used across different
VMT tools and applications. These widgets were extracted from MANUAL_TESTS
for proper architectural separation and reusability.

Components:
-----------
- ConfigEditor: Live configuration editing with validation and presets
- BatchRunner: Batch test execution with progress tracking
"""

from .config_editor import ConfigEditor
from .batch_runner import BatchRunner

__all__ = ['ConfigEditor', 'BatchRunner']
