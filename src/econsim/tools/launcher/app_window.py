"""Launcher Main Window Shell (Phase 3.4).

Gate G14: Slim main window coordinating components with ≤30% LOC reduction vs original.
Follows Breakdown Plan Phase 4: Streamlined main class focusing on composition and coordination.

This is the "VMTLauncher" referenced in Critical Review, but named LauncherWindow 
for Part 2 compatibility. Architectural cleanup prioritized over naming.
"""
from __future__ import annotations

from typing import List

try:
    from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
except Exception:  # pragma: no cover
    QMainWindow = QWidget = QVBoxLayout = QHBoxLayout = QLabel = QTextEdit = object  # type: ignore

from .registry import TestRegistry
from .comparison import ComparisonController
from .executor import TestExecutor
from .cards import build_card_models
from .gallery import TestGallery
from .tabs import LauncherTabs


class LauncherWindow(QMainWindow):  # type: ignore[misc] # pragma: no cover - GUI component
    """Slim main window shell coordinating launcher components.
    
    Architecture follows Breakdown Plan principle: Pure composition and delegation.
    No business logic - all responsibilities handled by injected components.
    
    Gate G14 target: ≤30% LOC vs original monolith core (~350 lines → ~245 max).
    """
    
    def __init__(self, registry: TestRegistry):
        super().__init__()  # type: ignore[misc]
        
        # Injected dependencies (no internal creation of business objects)
        self._registry = registry
        self._comparison = ComparisonController(max_selections=4)
        self._executor = TestExecutor(registry=registry, launcher_script="")  # Empty path for now
        
        # UI components (created but not wired until setup)
        self._gallery: TestGallery | None = None
        self._tabs: LauncherTabs | None = None
        self._status_area = None  # QTextEdit when created
        
        self._setup_window()
        self._setup_ui()
        self._wire_signals()
    
    def _setup_window(self) -> None:
        """Configure main window properties."""
        try:
            self.setWindowTitle("VMT Enhanced Test Launcher")  # type: ignore[attr-defined]
            self.setGeometry(100, 100, 1200, 800)  # type: ignore[attr-defined]
        except Exception:
            pass
    
    def _setup_ui(self) -> None:
        """Compose UI from modular components."""
        try:
            central_widget = QWidget()
            self.setCentralWidget(central_widget)  # type: ignore[attr-defined]
            
            layout = QVBoxLayout()  # type: ignore[call-arg]
            central_widget.setLayout(layout)  # type: ignore[attr-defined]
            
            # Header
            header = self._create_header()
            layout.addWidget(header)  # type: ignore[arg-type]
            
            # Main content: Tabs container
            self._gallery = self._create_gallery()
            self._tabs = LauncherTabs(self._gallery, self._comparison, self._executor)
            layout.addWidget(self._tabs)  # type: ignore[arg-type]
            
            # Status area
            self._status_area = self._create_status_area()
            layout.addWidget(self._status_area)  # type: ignore[arg-type]
            
        except Exception:
            pass
    
    def _create_header(self) -> QWidget:  # type: ignore[type-arg]
        """Create header section."""
        header_widget = QWidget()  # type: ignore[call-arg]
        layout = QHBoxLayout()  # type: ignore[call-arg]
        
        title = QLabel("VMT Enhanced Test Launcher")  # type: ignore[call-arg]
        try:
            font = QFont()  # type: ignore[call-arg]
            font.setPointSize(16)  # type: ignore[attr-defined]
            font.setBold(True)  # type: ignore[attr-defined]
            title.setFont(font)  # type: ignore[attr-defined]
        except Exception:
            pass
        
        layout.addWidget(title)  # type: ignore[arg-type]
        layout.addStretch()  # type: ignore[call-arg]
        
        try:
            header_widget.setLayout(layout)  # type: ignore[attr-defined]
        except Exception:
            pass
        
        return header_widget
    
    def _create_gallery(self) -> TestGallery:
        """Create gallery component with current registry data."""
        card_models = build_card_models(self._registry)
        return TestGallery(card_models, self._comparison, self._executor)
    
    def _create_status_area(self) -> QTextEdit:  # type: ignore[type-arg]
        """Create status/log area."""
        status_area = QTextEdit()  # type: ignore[call-arg]
        try:
            status_area.setReadOnly(True)  # type: ignore[attr-defined]
            status_area.setMaximumHeight(100)  # type: ignore[attr-defined]
            status_area.setStyleSheet("background-color: #f8f9fa; font-family: monospace;")  # type: ignore[attr-defined]
            status_area.append("Enhanced Test Launcher initialized.")  # type: ignore[attr-defined]
        except Exception:
            pass
        return status_area
    
    def _wire_signals(self) -> None:
        """Connect component signals for coordination."""
        # Minimal signal wiring - components mostly self-contained
        # In a full implementation, we'd connect:
        # - Gallery selection changes → Comparison updates
        # - Test launches → Status area messages
        # - Comparison changes → Tab refresh triggers
        pass
    
    def log_status(self, message: str) -> None:
        """Add message to status area (public API for components)."""
        try:
            if self._status_area:
                self._status_area.append(f"• {message}")  # type: ignore[attr-defined]
                
                # Keep status area manageable
                if self._status_area.document().lineCount() > 20:  # type: ignore[attr-defined]
                    cursor = self._status_area.textCursor()  # type: ignore[attr-defined]
                    cursor.movePosition(cursor.MoveOperation.Start)  # type: ignore[attr-defined]
                    cursor.select(cursor.SelectionType.LineUnderCursor)  # type: ignore[attr-defined]
                    cursor.removeSelectedText()  # type: ignore[attr-defined]
                    cursor.deletePreviousChar()  # type: ignore[attr-defined]
        except Exception:
            pass
    
    def refresh_all(self) -> None:
        """Refresh all component states (useful after external changes)."""
        try:
            if self._tabs:
                self._tabs.refresh_all()  # type: ignore[attr-defined]
        except Exception:
            pass
    
    def closeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        """Clean shutdown - no lingering resources."""
        try:
            # Components should handle their own cleanup
            super().closeEvent(event)  # type: ignore[misc]
        except Exception:
            pass


def create_launcher_window(registry: TestRegistry | None = None) -> LauncherWindow:
    """Factory function for creating launcher window with dependencies.
    
    Follows dependency injection pattern from Breakdown Plan.
    """
    if registry is None:
        # Import here to avoid circular dependencies during extraction
        from .adapters import load_registry_from_monolith
        registry = load_registry_from_monolith()
    
    return LauncherWindow(registry)