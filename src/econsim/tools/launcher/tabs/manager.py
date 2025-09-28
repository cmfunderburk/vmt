"""Tab management system for the enhanced test launcher.

Provides centralized coordination of multiple tabs with lifecycle management,
event handling, and inter-tab communication support.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Any, Callable

try:
    from PyQt6.QtWidgets import QTabWidget, QWidget
    from PyQt6.QtCore import pyqtSignal, QObject
    _QObjectBase = QObject
except Exception:  # pragma: no cover - allows pure tests without Qt plugin
    QTabWidget = QWidget = object  # type: ignore
    pyqtSignal = lambda *args: lambda: None  # type: ignore
    _QObjectBase = object  # type: ignore

from .base_tab import AbstractTab


class TabManager:  # pragma: no cover - GUI coordination class
    """Manages the lifecycle and coordination of launcher tabs.
    
    Provides centralized tab registration, switching, and inter-tab communication.
    Handles tab lifecycle events (activation, deactivation, cleanup) and manages
    the underlying QTabWidget instance.
    """
    
    def __init__(self, tab_widget, parent=None):
        self.tab_widget = tab_widget
        self.registered_tabs: Dict[str, AbstractTab] = {}
        self.tab_order: List[str] = []
        self._current_tab_id: Optional[str] = None
        
        # Event callbacks
        self._on_tab_activated: Optional[Callable[[str], None]] = None
        self._on_tab_deactivated: Optional[Callable[[str], None]] = None
        self._on_tab_added: Optional[Callable[[str], None]] = None
        self._on_tab_removed: Optional[Callable[[str], None]] = None
        
        # Connect tab widget signals
        if hasattr(self.tab_widget, 'currentChanged'):
            self.tab_widget.currentChanged.connect(self._handle_tab_changed)

    def set_tab_activated_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for tab activation events."""
        self._on_tab_activated = callback

    def set_tab_deactivated_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for tab deactivation events."""
        self._on_tab_deactivated = callback

    def set_tab_added_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for tab addition events."""
        self._on_tab_added = callback

    def set_tab_removed_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for tab removal events."""
        self._on_tab_removed = callback
        
    def register_tab(self, tab: AbstractTab, index: Optional[int] = None) -> None:
        """Register a new tab with the manager.
        
        Args:
            tab: The tab instance to register
            index: Optional position to insert the tab (defaults to end)
        """
        if tab.tab_id in self.registered_tabs:
            raise ValueError(f"Tab with ID '{tab.tab_id}' already registered")
            
        self.registered_tabs[tab.tab_id] = tab
        
        # Add to tab widget
        if index is not None:
            self.tab_widget.insertTab(index, tab, tab.tab_title)
            self.tab_order.insert(index, tab.tab_id)
        else:
            self.tab_widget.addTab(tab, tab.tab_title)
            self.tab_order.append(tab.tab_id)
            
        if self._on_tab_added:
            self._on_tab_added(tab.tab_id)
        
    def unregister_tab(self, tab_id: str) -> None:
        """Unregister and remove a tab.
        
        Args:
            tab_id: The ID of the tab to remove
        """
        if tab_id not in self.registered_tabs:
            return
            
        tab = self.registered_tabs[tab_id]
        
        # Find and remove from tab widget
        for i in range(self.tab_widget.count()):
            if self.tab_widget.widget(i) == tab:
                self.tab_widget.removeTab(i)
                break
                
        # Clean up tab
        tab.cleanup()
        
        # Remove from tracking
        del self.registered_tabs[tab_id]
        self.tab_order.remove(tab_id)
        
        if self._current_tab_id == tab_id:
            self._current_tab_id = None
            
        if self._on_tab_removed:
            self._on_tab_removed(tab_id)
        
    def get_tab(self, tab_id: str) -> Optional[AbstractTab]:
        """Get a registered tab by ID.
        
        Args:
            tab_id: The ID of the tab to retrieve
            
        Returns:
            The tab instance or None if not found
        """
        return self.registered_tabs.get(tab_id)
        
    def get_current_tab(self) -> Optional[AbstractTab]:
        """Get the currently active tab.
        
        Returns:
            The current tab instance or None if no tabs
        """
        if self._current_tab_id:
            return self.registered_tabs.get(self._current_tab_id)
        return None
        
    def switch_to_tab(self, tab_id: str) -> bool:
        """Switch to a specific tab.
        
        Args:
            tab_id: The ID of the tab to activate
            
        Returns:
            True if the switch was successful, False otherwise
        """
        if tab_id not in self.registered_tabs:
            return False
            
        tab = self.registered_tabs[tab_id]
        index = self.tab_widget.indexOf(tab)
        if index >= 0:
            self.tab_widget.setCurrentIndex(index)
            return True
        return False
        
    def refresh_current_tab(self) -> None:
        """Refresh the content of the currently active tab."""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.refresh_content()
            
    def refresh_all_tabs(self) -> None:
        """Refresh the content of all registered tabs."""
        for tab in self.registered_tabs.values():
            tab.refresh_content()
            
    def cleanup_all_tabs(self) -> None:
        """Clean up all registered tabs. Call before destroying the manager."""
        for tab_id in list(self.registered_tabs.keys()):
            self.unregister_tab(tab_id)
            
    def get_tab_ids(self) -> List[str]:
        """Get the list of all registered tab IDs in order.
        
        Returns:
            List of tab IDs in display order
        """
        return self.tab_order.copy()
        
    def send_message_to_tab(self, tab_id: str, message: str, data: Any = None) -> bool:
        """Send a message to a specific tab for inter-tab communication.
        
        Args:
            tab_id: The ID of the target tab
            message: The message type/name
            data: Optional data payload
            
        Returns:
            True if message was delivered, False if tab not found
        """
        tab = self.get_tab(tab_id)
        if tab and hasattr(tab, 'handle_message'):
            tab.handle_message(message, data)  # type: ignore[attr-defined]
            return True
        return False
        
    def broadcast_message(self, message: str, data: Any = None, exclude_tab: Optional[str] = None) -> None:
        """Broadcast a message to all tabs.
        
        Args:
            message: The message type/name
            data: Optional data payload
            exclude_tab: Optional tab ID to exclude from broadcast
        """
        for tab_id, tab in self.registered_tabs.items():
            if exclude_tab and tab_id == exclude_tab:
                continue
            if hasattr(tab, 'handle_message'):
                tab.handle_message(message, data)  # type: ignore[attr-defined]
    
    def _handle_tab_changed(self, index: int) -> None:
        """Handle tab change events from the underlying QTabWidget.
        
        Args:
            index: The new tab index
        """
        # Deactivate previous tab
        if self._current_tab_id:
            if self._on_tab_deactivated:
                self._on_tab_deactivated(self._current_tab_id)
            
        # Find new tab ID
        new_tab_id = None
        if 0 <= index < self.tab_widget.count():
            widget = self.tab_widget.widget(index)
            for tab_id, tab in self.registered_tabs.items():
                if tab == widget:
                    new_tab_id = tab_id
                    break
                    
        # Activate new tab
        if new_tab_id:
            self._current_tab_id = new_tab_id
            if self._on_tab_activated:
                self._on_tab_activated(new_tab_id)
            # Refresh content when tab becomes active
            self.refresh_current_tab()
        else:
            self._current_tab_id = None