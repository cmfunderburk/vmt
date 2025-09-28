"""Batch Runner Tab - wrapper for BatchTestRunner.

Provides batch test execution capabilities as a tab component
conforming to the AbstractTab interface.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add MANUAL_TESTS to path to import existing widgets
manual_tests_path = Path(__file__).parent.parent.parent.parent / "MANUAL_TESTS"
sys.path.insert(0, str(manual_tests_path))

try:
    from batch_test_runner import BatchTestRunner
    _batch_runner_available = True
except ImportError:
    _batch_runner_available = False
    BatchTestRunner = None

from .base_tab import AbstractTab


class BatchRunnerTab(AbstractTab):  # pragma: no cover - GUI tab component
    """Batch test runner tab for the enhanced test launcher.
    
    Wraps the BatchTestRunner widget to provide tab-compatible interface
    with refresh and cleanup capabilities.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tab_title = "🔄 Batch Runner"
        self._tab_id = "batch_runner"
        
        if _batch_runner_available and BatchTestRunner:
            self.batch_runner = BatchTestRunner()
            
            # Create simple layout to contain the runner
            from PyQt6.QtWidgets import QVBoxLayout
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.batch_runner)
        else:
            # Fallback when BatchTestRunner not available
            from PyQt6.QtWidgets import QVBoxLayout, QLabel
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Batch Runner not available"))
            self.batch_runner = None
    
    def refresh_content(self) -> None:
        """Refresh the batch runner content."""
        if self.batch_runner and hasattr(self.batch_runner, 'refresh'):
            self.batch_runner.refresh()
        elif self.batch_runner and hasattr(self.batch_runner, 'update_test_list'):
            self.batch_runner.update_test_list()
    
    def cleanup(self) -> None:
        """Clean up resources when tab is being destroyed."""
        if self.batch_runner and hasattr(self.batch_runner, 'cleanup'):
            self.batch_runner.cleanup()
        elif self.batch_runner and hasattr(self.batch_runner, 'stop_batch_execution'):
            self.batch_runner.stop_batch_execution()
        # Remove from sys.path to avoid pollution
        if str(manual_tests_path) in sys.path:
            sys.path.remove(str(manual_tests_path))
    
    def handle_message(self, message: str, data=None) -> None:
        """Handle inter-tab communication messages."""
        if self.batch_runner and hasattr(self.batch_runner, 'handle_message'):
            self.batch_runner.handle_message(message, data)