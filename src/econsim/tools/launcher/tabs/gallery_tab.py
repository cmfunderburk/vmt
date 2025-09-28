"""Gallery Tab - wrapper for TestGalleryWidget.

Provides test gallery capabilities as a tab component
conforming to the AbstractTab interface.
"""
from __future__ import annotations

from .base_tab import AbstractTab

try:
    from ..widgets import TestGalleryWidget
    _gallery_available = True
except ImportError:
    _gallery_available = False
    TestGalleryWidget = None


class GalleryTab(AbstractTab):  # pragma: no cover - GUI tab component
    """Test gallery tab for the enhanced test launcher.
    
    Wraps the TestGalleryWidget to provide tab-compatible interface
    with refresh and cleanup capabilities.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tab_title = "🖼️ Test Gallery"
        self._tab_id = "gallery"
        
        if _gallery_available and TestGalleryWidget:
            self.gallery_widget = TestGalleryWidget()
            
            # Create simple layout to contain the gallery
            from PyQt6.QtWidgets import QVBoxLayout
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.gallery_widget)
        else:
            # Fallback when TestGalleryWidget not available
            from PyQt6.QtWidgets import QVBoxLayout, QLabel
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Test Gallery not available"))
            self.gallery_widget = None
    
    def refresh_content(self) -> None:
        """Refresh the gallery content."""
        if self.gallery_widget and hasattr(self.gallery_widget, 'populate_tests'):
            self.gallery_widget.populate_tests()
    
    def cleanup(self) -> None:
        """Clean up resources when tab is being destroyed."""
        if self.gallery_widget and hasattr(self.gallery_widget, 'cleanup'):
            self.gallery_widget.cleanup()
    
    def handle_message(self, message: str, data=None) -> None:
        """Handle inter-tab communication messages."""
        if self.gallery_widget and hasattr(self.gallery_widget, 'handle_message'):
            self.gallery_widget.handle_message(message, data)
    
    def get_gallery_widget(self):
        """Get the underlying gallery widget for direct access."""
        return self.gallery_widget