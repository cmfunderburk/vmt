"""Bookmarks Tab - wrapper for TestBookmarkManager.

Provides test bookmarking capabilities as a tab component
conforming to the AbstractTab interface.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add MANUAL_TESTS to path to import existing widgets
manual_tests_path = Path(__file__).parent.parent.parent.parent / "MANUAL_TESTS"
sys.path.insert(0, str(manual_tests_path))

try:
    from test_bookmarks import TestBookmarkManager
    _bookmarks_available = True
except ImportError:
    _bookmarks_available = False
    TestBookmarkManager = None

from .base_tab import AbstractTab


class BookmarksTab(AbstractTab):  # pragma: no cover - GUI tab component
    """Test bookmarks tab for the enhanced test launcher.
    
    Wraps the TestBookmarkManager widget to provide tab-compatible interface
    with refresh and cleanup capabilities.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tab_title = "⭐ Bookmarks"
        self._tab_id = "bookmarks"
        
        if _bookmarks_available and TestBookmarkManager:
            self.bookmark_manager = TestBookmarkManager()
            
            # Create simple layout to contain the manager
            from PyQt6.QtWidgets import QVBoxLayout
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.bookmark_manager)
        else:
            # Fallback when TestBookmarkManager not available
            from PyQt6.QtWidgets import QVBoxLayout, QLabel
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Bookmark Manager not available"))
            self.bookmark_manager = None
    
    def refresh_content(self) -> None:
        """Refresh the bookmark manager content."""
        if self.bookmark_manager and hasattr(self.bookmark_manager, 'refresh'):
            self.bookmark_manager.refresh()
        elif self.bookmark_manager and hasattr(self.bookmark_manager, 'reload_bookmarks'):
            self.bookmark_manager.reload_bookmarks()
    
    def cleanup(self) -> None:
        """Clean up resources when tab is being destroyed."""
        if self.bookmark_manager and hasattr(self.bookmark_manager, 'cleanup'):
            self.bookmark_manager.cleanup()
        elif self.bookmark_manager and hasattr(self.bookmark_manager, 'save_bookmarks'):
            self.bookmark_manager.save_bookmarks()
        # Remove from sys.path to avoid pollution
        if str(manual_tests_path) in sys.path:
            sys.path.remove(str(manual_tests_path))
    
    def handle_message(self, message: str, data=None) -> None:
        """Handle inter-tab communication messages."""
        if self.bookmark_manager and hasattr(self.bookmark_manager, 'handle_message'):
            self.bookmark_manager.handle_message(message, data)