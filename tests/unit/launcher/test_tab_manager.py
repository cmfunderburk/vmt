"""Test TabManager functionality."""

import pytest
from unittest.mock import Mock

from econsim.tools.launcher.tabs.manager import TabManager
from econsim.tools.launcher.tabs.base_tab import AbstractTab


class MockTab(AbstractTab):
    """Mock tab for testing."""
    
    def __init__(self, tab_id: str, title: str):
        # Don't call super().__init__() to avoid Qt dependency
        self._tab_id = tab_id
        self._tab_title = title
        self.refresh_called = False
        self.cleanup_called = False
        
    def refresh_content(self) -> None:
        """Mock refresh."""
        self.refresh_called = True
        
    def cleanup(self) -> None:
        """Mock cleanup."""
        self.cleanup_called = True


class MockSignal:
    """Mock PyQt signal."""
    
    def __init__(self, tab_widget):
        self.tab_widget = tab_widget
        
    def connect(self, callback):
        self.tab_widget.current_changed_callback = callback


class MockTabWidget:
    """Mock QTabWidget for testing."""
    
    def __init__(self):
        self.tabs = []
        self.current_index = 0
        self.current_changed_callback = None
        self.currentChanged = MockSignal(self)
        
    def addTab(self, widget, title):
        self.tabs.append((widget, title))
        return len(self.tabs) - 1
        
    def insertTab(self, index, widget, title):
        self.tabs.insert(index, (widget, title))
        return index
        
    def removeTab(self, index):
        if 0 <= index < len(self.tabs):
            self.tabs.pop(index)
            
    def widget(self, index):
        if 0 <= index < len(self.tabs):
            return self.tabs[index][0]
        return None
        
    def indexOf(self, widget):
        for i, (tab_widget, title) in enumerate(self.tabs):
            if tab_widget == widget:
                return i
        return -1
        
    def setCurrentIndex(self, index):
        if 0 <= index < len(self.tabs):
            old_index = self.current_index
            self.current_index = index
            if self.current_changed_callback:
                self.current_changed_callback(index)
                
    def count(self):
        return len(self.tabs)


def test_tab_manager_basic_operations():
    """Test basic tab manager operations."""
    mock_tab_widget = MockTabWidget()
    manager = TabManager(mock_tab_widget)
    
    # Create mock tabs
    tab1 = MockTab("tab1", "Tab 1")
    tab2 = MockTab("tab2", "Tab 2")
    
    # Register tabs
    manager.register_tab(tab1)
    manager.register_tab(tab2)
    
    # Check registration
    assert len(manager.get_tab_ids()) == 2
    assert "tab1" in manager.get_tab_ids()
    assert "tab2" in manager.get_tab_ids()
    
    # Check tab retrieval
    assert manager.get_tab("tab1") == tab1
    assert manager.get_tab("tab2") == tab2
    assert manager.get_tab("nonexistent") is None


def test_tab_manager_lifecycle():
    """Test tab lifecycle management."""
    mock_tab_widget = MockTabWidget()
    manager = TabManager(mock_tab_widget)
    
    tab = MockTab("test_tab", "Test Tab")
    manager.register_tab(tab)
    
    # Test refresh
    manager.refresh_current_tab()  # Should handle no current tab gracefully
    
    # Test cleanup
    manager.unregister_tab("test_tab")
    assert tab.cleanup_called
    assert len(manager.get_tab_ids()) == 0


def test_tab_manager_callbacks():
    """Test tab manager callback system."""
    mock_tab_widget = MockTabWidget()
    manager = TabManager(mock_tab_widget)
    
    # Setup callback tracking
    callbacks_called = {
        'activated': [],
        'deactivated': [],
        'added': [],
        'removed': []
    }
    
    manager.set_tab_activated_callback(lambda tab_id: callbacks_called['activated'].append(tab_id))
    manager.set_tab_deactivated_callback(lambda tab_id: callbacks_called['deactivated'].append(tab_id))
    manager.set_tab_added_callback(lambda tab_id: callbacks_called['added'].append(tab_id))
    manager.set_tab_removed_callback(lambda tab_id: callbacks_called['removed'].append(tab_id))
    
    # Register tab
    tab = MockTab("test_tab", "Test Tab")
    manager.register_tab(tab)
    
    assert "test_tab" in callbacks_called['added']
    
    # Remove tab
    manager.unregister_tab("test_tab")
    
    assert "test_tab" in callbacks_called['removed']


def test_tab_manager_error_cases():
    """Test tab manager error handling."""
    mock_tab_widget = MockTabWidget()
    manager = TabManager(mock_tab_widget)
    
    tab = MockTab("test_tab", "Test Tab")
    manager.register_tab(tab)
    
    # Try to register duplicate
    with pytest.raises(ValueError, match="already registered"):
        manager.register_tab(tab)
    
    # Unregister non-existent tab (should handle gracefully)
    manager.unregister_tab("nonexistent")  # Should not raise
    
    # Switch to non-existent tab
    assert not manager.switch_to_tab("nonexistent")


def test_tab_manager_messaging():
    """Test inter-tab messaging."""
    mock_tab_widget = MockTabWidget()
    manager = TabManager(mock_tab_widget)
    
    # Create tab with message handling
    tab = MockTab("test_tab", "Test Tab")
    tab.messages_received = []
    
    def handle_message(message, data):
        tab.messages_received.append((message, data))
    
    tab.handle_message = handle_message
    
    manager.register_tab(tab)
    
    # Send message
    assert manager.send_message_to_tab("test_tab", "test_message", {"key": "value"})
    assert ("test_message", {"key": "value"}) in tab.messages_received
    
    # Send to non-existent tab
    assert not manager.send_message_to_tab("nonexistent", "test", None)