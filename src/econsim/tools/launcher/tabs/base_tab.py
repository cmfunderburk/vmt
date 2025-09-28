"""Abstract base class for launcher tabs.

Defines the common interface for all tabbed components in the enhanced test launcher.
Each tab should be a self-contained widget that can be managed by the TabManager.
"""
from __future__ import annotations

from abc import abstractmethod

try:
    from PyQt6.QtWidgets import QWidget
except Exception:  # pragma: no cover - allows pure tests without Qt plugin
    QWidget = object  # type: ignore


class AbstractTab(QWidget):  # pragma: no cover - GUI base class for tab components
    """Abstract base class for launcher tab components.
    
    All tab widgets should inherit from this class and implement the required methods.
    This ensures consistent interface for tab management and lifecycle handling.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)  # type: ignore[misc]
        self._tab_title = "Unknown Tab"
        self._tab_id = "unknown"
    
    @property
    def tab_title(self) -> str:
        """Return the display title for this tab."""
        return self._tab_title
    
    @property 
    def tab_id(self) -> str:
        """Return the unique identifier for this tab."""
        return self._tab_id
    
    @abstractmethod
    def refresh_content(self) -> None:
        """Refresh the tab content. Called when tab becomes active or data changes."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources when tab is being destroyed."""
        pass