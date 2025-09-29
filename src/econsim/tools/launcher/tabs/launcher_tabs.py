"""Launcher UI – Tabs Container (Phase 3.3).

Implements modular tab container integrating gallery, comparison, and history views.
Gate G13: Tabs modular with clean separation of concerns.

Follows Breakdown Plan Phase 3.3 architecture: AbstractTab base with specific implementations.
"""
from __future__ import annotations

from typing import List, Protocol

try:
    from PyQt6.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem, QHBoxLayout
    from PyQt6.QtCore import Qt
    _qt_available = True
except Exception:  # pragma: no cover
    _qt_available = False
    # Type stubs for headless operation
    QTabWidget = QWidget = QVBoxLayout = QLabel = QPushButton = QTextEdit = object  # type: ignore
    QTableWidget = QTableWidgetItem = QHBoxLayout = object  # type: ignore

from .custom_tests_tab import CustomTestsTab


class TabContent(Protocol):  # pragma: no cover - typing only
    """Protocol for tab content widgets."""
    def refresh(self) -> None: ...


class ComparisonTab(QWidget):  # type: ignore[misc] # pragma: no cover - GUI component
    """Comparison mode summary and launch controls."""
    
    def __init__(self, comparison_controller, executor):  # type: ignore[no-untyped-def]
        super().__init__()  # type: ignore[misc]
        self._comparison = comparison_controller
        self._executor = executor
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout()  # type: ignore[call-arg]
        
        # Set dark mode background for the main widget
        try:
            self.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")  # type: ignore[attr-defined]
        except Exception:
            pass
        
        # Header
        header = QLabel("Test Comparison")  # type: ignore[call-arg]
        try:
            header.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")  # type: ignore[attr-defined]
        except Exception:
            pass
        layout.addWidget(header)  # type: ignore[arg-type]
        
        # Selected tests display
        self._selected_label = QLabel("No tests selected")  # type: ignore[call-arg]
        layout.addWidget(self._selected_label)  # type: ignore[arg-type]
        
        # Controls
        controls_layout = QHBoxLayout()  # type: ignore[call-arg]
        
        self._launch_btn = QPushButton("Launch Comparison")  # type: ignore[call-arg]
        self._clear_btn = QPushButton("Clear Selection")  # type: ignore[call-arg]
        
        try:
            self._launch_btn.clicked.connect(self._launch_comparison)  # type: ignore[attr-defined]
            self._clear_btn.clicked.connect(self._clear_selection)  # type: ignore[attr-defined]
        except Exception:
            pass
        
        controls_layout.addWidget(self._launch_btn)  # type: ignore[arg-type]
        controls_layout.addWidget(self._clear_btn)  # type: ignore[arg-type]
        controls_layout.addStretch()  # type: ignore[call-arg]
        
        layout.addLayout(controls_layout)  # type: ignore[arg-type]
        layout.addStretch()  # type: ignore[call-arg]
        
        try:
            self.setLayout(layout)  # type: ignore[attr-defined]
        except Exception:
            pass
    
    def refresh(self) -> None:
        """Update display with current comparison state."""
        try:
            selected = self._comparison.selected()
            if selected:
                self._selected_label.setText(f"Selected: {', '.join(selected)}")  # type: ignore[attr-defined]
                self._launch_btn.setEnabled(self._comparison.can_launch())  # type: ignore[attr-defined]
            else:
                self._selected_label.setText("No tests selected")  # type: ignore[attr-defined]
                self._launch_btn.setEnabled(False)  # type: ignore[attr-defined]
        except Exception:
            pass
    
    def _launch_comparison(self) -> None:
        """Launch selected tests for comparison."""
        try:
            selected = self._comparison.selected()
            if len(selected) >= 2:
                self._executor.launch_comparison(selected)
        except Exception:
            pass
    
    def _clear_selection(self) -> None:
        """Clear comparison selection."""
        try:
            self._comparison.clear()
            self.refresh()
        except Exception:
            pass


class HistoryTab(QWidget):  # type: ignore[misc] # pragma: no cover - GUI component
    """Execution history view."""
    
    def __init__(self, executor):  # type: ignore[no-untyped-def]
        super().__init__()  # type: ignore[misc]
        self._executor = executor
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout()  # type: ignore[call-arg]
        
        # Set dark mode background for the main widget
        try:
            self.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")  # type: ignore[attr-defined]
        except Exception:
            pass
        
        # Header
        header = QLabel("Execution History")  # type: ignore[call-arg]
        try:
            header.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")  # type: ignore[attr-defined]
        except Exception:
            pass
        layout.addWidget(header)  # type: ignore[arg-type]
        
        # History table
        self._table = QTableWidget()  # type: ignore[call-arg]
        try:
            self._table.setColumnCount(3)  # type: ignore[attr-defined]
            self._table.setHorizontalHeaderLabels(["Test", "Mode", "Time"])  # type: ignore[attr-defined]
        except Exception:
            pass
        
        layout.addWidget(self._table)  # type: ignore[arg-type]
        
        try:
            self.setLayout(layout)  # type: ignore[attr-defined]
        except Exception:
            pass
    
    def refresh(self) -> None:
        """Update history display."""
        try:
            history = self._executor.history()
            self._table.setRowCount(len(history))  # type: ignore[attr-defined]
            
            for row, record in enumerate(history[-10:]):  # Show last 10 entries
                # Test names (joined if multiple)
                test_item = QTableWidgetItem(", ".join(record.test_ids))  # type: ignore[call-arg]
                self._table.setItem(row, 0, test_item)  # type: ignore[attr-defined]
                
                # Mode
                mode_item = QTableWidgetItem(record.mode)  # type: ignore[call-arg]
                self._table.setItem(row, 1, mode_item)  # type: ignore[attr-defined]
                
                # Timestamp (simplified)
                time_item = QTableWidgetItem(f"{record.timestamp:.0f}")  # type: ignore[call-arg]
                self._table.setItem(row, 2, time_item)  # type: ignore[attr-defined]
        except Exception:
            pass


class LauncherTabs(QTabWidget):  # type: ignore[misc] # pragma: no cover - GUI component
    """Main tabs container for launcher UI.
    
    Gate G13 implementation: Modular tabs with clean interfaces.
    Tabs: (1) Gallery (tests), (2) Comparison, (3) History
    """
    
    def __init__(self, gallery, comparison_controller, executor):  # type: ignore[no-untyped-def]
        super().__init__()  # type: ignore[misc]
        self._gallery = gallery
        self._comparison = comparison_controller
        self._executor = executor
        
        self._comparison_tab: ComparisonTab | None = None
        self._history_tab: HistoryTab | None = None
        
        self._setup_tabs()
    
    def _setup_tabs(self) -> None:
        """Initialize all tabs."""
        try:
            # Tab 1: Test Gallery
            self.addTab(self._gallery, "🖼️ Tests")  # type: ignore[attr-defined]
            
            # Tab 2: Custom Tests
            self._custom_tests_tab = CustomTestsTab()
            self.addTab(self._custom_tests_tab, "🔧 Custom Tests")  # type: ignore[attr-defined]
            
            # Tab 3: Comparison
            self._comparison_tab = ComparisonTab(self._comparison, self._executor)
            self.addTab(self._comparison_tab, "⚖️ Comparison")  # type: ignore[attr-defined]
            
            # Tab 4: History
            self._history_tab = HistoryTab(self._executor)
            self.addTab(self._history_tab, "📝 History")  # type: ignore[attr-defined]
            
            # Connect tab change to refresh
            self.currentChanged.connect(self._on_tab_changed)  # type: ignore[attr-defined]
        except Exception:
            pass
    
    def _on_tab_changed(self, index: int) -> None:
        """Refresh tab content when switched."""
        try:
            current_widget = self.widget(index)  # type: ignore[attr-defined]
            if hasattr(current_widget, 'refresh_content'):
                current_widget.refresh_content()
            elif hasattr(current_widget, 'refresh'):
                current_widget.refresh()
        except Exception:
            pass
    
    def refresh_all(self) -> None:
        """Refresh all tab contents."""
        try:
            if hasattr(self, '_custom_tests_tab') and self._custom_tests_tab:
                self._custom_tests_tab.refresh_content()
            if self._comparison_tab:
                self._comparison_tab.refresh()
            if self._history_tab:
                self._history_tab.refresh()
        except Exception:
            pass