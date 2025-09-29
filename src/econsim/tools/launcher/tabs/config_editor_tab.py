"""Config Editor Tab - wrapper for LiveConfigEditor.

Provides configuration editing capabilities as a tab component
conforming to the AbstractTab interface.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add MANUAL_TESTS to path to import existing widgets
manual_tests_path = Path(__file__).parent.parent.parent.parent.parent / "MANUAL_TESTS"
sys.path.insert(0, str(manual_tests_path))

# Debug path calculation
print(f"[DEBUG ConfigEditorTab] __file__ = {__file__}")
print(f"[DEBUG ConfigEditorTab] manual_tests_path = {manual_tests_path}")
print(f"[DEBUG ConfigEditorTab] manual_tests_path exists = {manual_tests_path.exists()}")
print(f"[DEBUG ConfigEditorTab] sys.path now includes: {str(manual_tests_path)}")

try:
    from live_config_editor import LiveConfigEditor
    _config_editor_available = True
    print(f"[DEBUG ConfigEditorTab] ✅ LiveConfigEditor imported successfully")
except ImportError as e:
    _config_editor_available = False
    LiveConfigEditor = None
    print(f"[DEBUG ConfigEditorTab] ❌ LiveConfigEditor import failed: {e}")

from .base_tab import AbstractTab


class ConfigEditorTab(AbstractTab):  # pragma: no cover - GUI tab component
    """Configuration editor tab for the enhanced test launcher.
    
    Wraps the LiveConfigEditor widget to provide tab-compatible interface
    with refresh and cleanup capabilities.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tab_title = "⚙️ Configuration Editor"
        self._tab_id = "config_editor"
        
        if _config_editor_available and LiveConfigEditor:
            self.config_editor = LiveConfigEditor()
            
            # Create simple layout to contain the editor
            from PyQt6.QtWidgets import QVBoxLayout
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.config_editor)
        else:
            # Fallback when LiveConfigEditor not available
            from PyQt6.QtWidgets import QVBoxLayout, QLabel
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Configuration Editor not available"))
            self.config_editor = None
    
    def refresh_content(self) -> None:
        """Refresh the configuration editor content."""
        if self.config_editor and hasattr(self.config_editor, 'refresh'):
            self.config_editor.refresh()
        elif self.config_editor and hasattr(self.config_editor, 'load_current_config'):
            self.config_editor.load_current_config()
    
    def cleanup(self) -> None:
        """Clean up resources when tab is being destroyed."""
        if self.config_editor and hasattr(self.config_editor, 'cleanup'):
            self.config_editor.cleanup()
        # Remove from sys.path to avoid pollution
        if str(manual_tests_path) in sys.path:
            sys.path.remove(str(manual_tests_path))
    
    def handle_message(self, message: str, data=None) -> None:
        """Handle inter-tab communication messages."""
        if self.config_editor and hasattr(self.config_editor, 'handle_message'):
            self.config_editor.handle_message(message, data)