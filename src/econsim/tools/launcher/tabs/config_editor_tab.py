"""Config Editor Tab - wrapper for ConfigEditor widget.

Provides configuration editing capabilities as a tab component
conforming to the AbstractTab interface.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QVBoxLayout, QLabel

try:
    from econsim.tools.widgets import ConfigEditor
    _config_editor_available = True
except ImportError as e:
    _config_editor_available = False
    ConfigEditor = None
    print(f"[WARNING] ConfigEditor import failed: {e}")

from .base_tab import AbstractTab


class ConfigEditorTab(AbstractTab):  # pragma: no cover - GUI tab component
    """Configuration editor tab for the enhanced test launcher.
    
    Wraps the ConfigEditor widget to provide tab-compatible interface
    with refresh and cleanup capabilities.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tab_title = "⚙️ Configuration Editor"
        self._tab_id = "config_editor"
        
        if _config_editor_available and ConfigEditor:
            self.config_editor = ConfigEditor()
            
            # Create simple layout to contain the editor
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.config_editor)
        else:
            # Fallback when ConfigEditor not available
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
    
    def handle_message(self, message: str, data=None) -> None:
        """Handle inter-tab communication messages."""
        if self.config_editor and hasattr(self.config_editor, 'handle_message'):
            self.config_editor.handle_message(message, data)