"""Main Application Window for VMT Enhanced Test Launcher.

Provides the primary window coordination and application lifecycle management,
extracted from the monolithic enhanced_test_launcher_v2.py in Step 2.6.

Legacy Phase 3.4 LauncherWindow preserved below for compatibility.
VMTLauncherWindow is the Step 2.6 extraction target.
"""
from __future__ import annotations

import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

try:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QCheckBox, QTextEdit, QTabWidget, QApplication, QMessageBox
    )
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
except Exception:  # pragma: no cover - allows pure tests without Qt plugin
    QMainWindow = QWidget = QVBoxLayout = QHBoxLayout = object  # type: ignore
    QLabel = QPushButton = QCheckBox = QTextEdit = QTabWidget = object  # type: ignore
    QApplication = QMessageBox = Qt = QFont = object  # type: ignore

# Import extracted components with fallback handling
try:
    from .adapters import load_registry_from_monolith
    from .comparison import ComparisonController
    from .executor import TestExecutor
    from .cards import TestCardWidget
    from .tabs import TabManager, ConfigEditorTab, BatchRunnerTab, BookmarksTab, GalleryTab
    from .widgets import TestGalleryWidget
    from .style import PlatformStyler
    _launcher_modules_available = True
except Exception:  # pragma: no cover - fallback path
    _launcher_modules_available = False

# Legacy imports for Phase 3.4 compatibility
from .registry import TestRegistry
from .cards import build_card_models
from .gallery import TestGallery
from .tabs import LauncherTabs


class VMTLauncherWindow(QMainWindow):  # pragma: no cover - GUI application window
    """Main window for the VMT Enhanced Test Launcher (Step 2.6 extraction).
    
    Coordinates tab management, test execution, comparison mode, and application lifecycle.
    Replaces the monolithic EnhancedTestLauncher class with a more modular architecture.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Core state
        self.test_cards: Dict[str, TestCardWidget] = {}
        self.comparison_selection: List[str] = []
        self.tab_manager: Optional[TabManager] = None
        self.gallery_widget: Optional[TestGalleryWidget] = None
        self.status_area: Optional[QTextEdit] = None
        
        # Controllers and services
        self._comparison_controller: Optional[ComparisonController] = None
        self._registry = None
        self._executor = None
        
        # Initialize the application
        self._setup_window()
        self._setup_ui()
        self._populate_tests()
        
    def _setup_window(self) -> None:
        """Configure the main window properties."""
        self.setWindowTitle("VMT Enhanced Test Launcher")
        self.setMinimumSize(1000, 700)
        
    def _setup_ui(self) -> None:
        """Create the main UI layout and components."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Header
        self._create_header(layout)
        
        # Controls
        self._create_controls(layout)
        
        # Main content area with tabs
        self._create_main_content(layout)
        
        # Status bar
        self.statusBar().showMessage("Ready to launch tests")
        
    def _create_header(self, layout: QVBoxLayout) -> None:
        """Create the application header."""
        header = QLabel("🧪 VMT Enhanced Test Launcher")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                padding: 12px;
                border-radius: 6px;
                color: #333;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(header)
        
    def _create_controls(self, layout: QVBoxLayout) -> None:
        """Create the control buttons and toggles."""
        controls_layout = QHBoxLayout()
        
        # Comparison mode toggle
        self.comparison_toggle = QCheckBox("Comparison Mode")
        self.comparison_toggle.toggled.connect(self.toggle_comparison_mode)
        controls_layout.addWidget(self.comparison_toggle)
        
        # Clear comparison
        self.clear_comparison_btn = QPushButton("Clear Selection") 
        self.clear_comparison_btn.clicked.connect(self.clear_comparison)
        self.clear_comparison_btn.setEnabled(False)
        controls_layout.addWidget(self.clear_comparison_btn)
        
        # Launch comparison
        self.launch_comparison_btn = QPushButton("🔍 Launch Selected")
        self.launch_comparison_btn.clicked.connect(self.launch_comparison)
        self.launch_comparison_btn.setEnabled(False)
        controls_layout.addWidget(self.launch_comparison_btn)
        
        controls_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._populate_tests)
        controls_layout.addWidget(refresh_btn)
        
        layout.addLayout(controls_layout)
        
    def _create_main_content(self, layout: QVBoxLayout) -> None:
        """Create the main tabbed content area."""
        if _launcher_modules_available:
            self._create_modern_tabs(layout)
        else:
            self._create_fallback_content(layout)
            
    def _create_modern_tabs(self, layout: QVBoxLayout) -> None:
        """Create modern tab-managed content using extracted components."""
        # Create tab widget and manager
        main_tabs = QTabWidget()
        self.tab_manager = TabManager(main_tabs)
        
        # Register gallery tab
        gallery_tab = GalleryTab()
        self.tab_manager.register_tab(gallery_tab)
        
        # Get gallery widget for backward compatibility
        self.gallery_widget = gallery_tab.get_gallery_widget() or gallery_tab
        
        # Set up status area reference for compatibility
        if hasattr(self.gallery_widget, 'status_area'):
            self.status_area = self.gallery_widget.status_area
        else:
            # Fallback status area
            self.status_area = QTextEdit()
            self.status_area.setReadOnly(True)
            self.status_area.setMaximumHeight(100)
            self.status_area.setStyleSheet("background-color: #f8f9fa;")
        
        # Register other tab components
        config_tab = ConfigEditorTab()
        self.tab_manager.register_tab(config_tab)
        
        batch_tab = BatchRunnerTab()
        self.tab_manager.register_tab(batch_tab)
        
        bookmarks_tab = BookmarksTab()
        self.tab_manager.register_tab(bookmarks_tab)
        
        # Wire up gallery signals
        if hasattr(self.gallery_widget, 'testLaunchRequested'):
            self.gallery_widget.testLaunchRequested.connect(self.launch_test)
        if hasattr(self.gallery_widget, 'statusUpdate'):
            self.gallery_widget.statusUpdate.connect(self._handle_gallery_status)
            
        layout.addWidget(main_tabs)
        
    def _create_fallback_content(self, layout: QVBoxLayout) -> None:
        """Create fallback content when extracted modules aren't available."""
        # Import fallback implementations
        try:
            from live_config_editor import LiveConfigEditor
            from batch_test_runner import BatchTestRunner  
            from test_bookmarks import TestBookmarkManager
            
            # Create basic tab widget
            main_tabs = QTabWidget()
            
            # Create fallback gallery widget
            self.gallery_widget = TestGalleryWidget()
            main_tabs.addTab(self.gallery_widget, "🖼️ Test Gallery")
            
            # Add other tabs
            config_editor = LiveConfigEditor()
            main_tabs.addTab(config_editor, "⚙️ Configuration Editor")
            
            batch_runner = BatchTestRunner()
            main_tabs.addTab(batch_runner, "🔄 Batch Runner")
            
            bookmark_manager = TestBookmarkManager()
            main_tabs.addTab(bookmark_manager, "⭐ Bookmarks")
            
            layout.addWidget(main_tabs)
            
        except ImportError:
            # Final fallback - just show a basic label
            fallback_label = QLabel("Enhanced Test Launcher components not available")
            fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(fallback_label)
            
        # Set up fallback status area
        self.status_area = QTextEdit()
        self.status_area.setReadOnly(True)
        self.status_area.setMaximumHeight(100)
        self.status_area.setStyleSheet("background-color: #f8f9fa;")
        layout.addWidget(self.status_area)
        
    def _populate_tests(self) -> None:
        """Populate the test gallery with available tests."""
        if _launcher_modules_available and hasattr(self.gallery_widget, 'populate_tests'):
            # Delegate to extracted gallery widget
            if not hasattr(self, "_comparison_controller") or not self._comparison_controller:
                self._comparison_controller = ComparisonController(max_selections=4)
            self.gallery_widget.set_comparison_controller(self._comparison_controller)
            self.gallery_widget.populate_tests()
            
            # Update backward compatibility references
            if hasattr(self.gallery_widget, 'test_cards'):
                self.test_cards = self.gallery_widget.test_cards
            if hasattr(self.gallery_widget, 'get_comparison_selection'):
                self.comparison_selection = self.gallery_widget.get_comparison_selection()
            self._update_comparison_ui()
        else:
            # Fallback logic when extracted modules not available
            self.test_cards.clear()
            self.comparison_selection.clear()
            self._update_comparison_ui()
            
    def _handle_gallery_status(self, message: str) -> None:
        """Handle status updates from the gallery widget."""
        if message == "COMPARISON_LIMIT":
            QMessageBox.information(self, "Comparison Limit", 
                                  "Maximum 4 tests can be compared simultaneously.")
        elif message == "COMPARISON_CHANGED":
            self._update_comparison_ui()
        else:
            # Regular status message
            self.statusBar().showMessage(message)
            
    def launch_test(self, test_name: str, version: str = "framework") -> None:
        """Launch a test (always uses framework version now)."""
        # Version parameter kept for compatibility but ignored
        self._launch_test(test_name)
            
    def _launch_test(self, test_name: str) -> None:
        """Launch test (framework version)."""
        try:
            # Get test configuration
            if not hasattr(self, "_registry") or not self._registry:
                self._init_executor()
                
            # Find config by label to get ID  
            config = None
            for cfg in self._registry.all().values():
                if cfg.label == test_name:
                    config = cfg
                    break
                    
            if not config:
                self.log_status(f"✗ Test configuration not found: {test_name}")
                return
                
            # Map config IDs to framework test files
            id_to_file = {
                1: "test_1_framework_version.py",
                2: "test_2_framework_version.py", 
                3: "test_3_framework_version.py",
                4: "test_4_framework_version.py",
                5: "test_5_framework_version.py",
                6: "test_6_framework_version.py",
                7: "test_7_framework_version.py"
            }
            
            framework_file = id_to_file.get(config.id)
            if not framework_file:
                self.log_status(f"✗ Framework test file not found for: {test_name}")
                return
                
            # Construct test file path
            test_path = Path(__file__).parent.parent.parent.parent / "MANUAL_TESTS" / framework_file
            if not test_path.exists():
                self.log_status(f"✗ Test file not found: {framework_file}")
                return
                
            # Launch test in subprocess
            self.log_status(f"🚀 Launching {test_name}...")
            subprocess.Popen([sys.executable, str(test_path)], cwd=str(test_path.parent))
            self.statusBar().showMessage(f"Launched {test_name}")
            
        except Exception as e:
            self.log_status(f"✗ Exception launching {test_name}: {str(e)}")
            print(f"Launch error: {e}")
            
    def add_to_comparison(self, test_name: str) -> None:
        """Add test to comparison selection."""
        if _launcher_modules_available and self._comparison_controller:
            # Delegate to comparison controller
            add_result = self._comparison_controller.add(test_name)
            if add_result.added:
                self._update_comparison_ui()
            else:
                if add_result.reason == "capacity":
                    QMessageBox.information(self, "Comparison Full", 
                                          "Maximum 4 tests can be compared simultaneously.")
                elif add_result.reason == "duplicate":
                    QMessageBox.information(self, "Already Selected", 
                                          f"Test '{test_name}' is already in comparison selection.")
                else:
                    QMessageBox.warning(self, "Invalid Selection", 
                                      f"Cannot add '{test_name}' to comparison.")
        else:
            # Fallback logic
            if test_name not in self.comparison_selection and len(self.comparison_selection) < 4:
                self.comparison_selection.append(test_name)
                self._update_comparison_ui()
                
    def toggle_comparison_mode(self, enabled: bool) -> None:
        """Toggle comparison mode on/off."""
        # Update UI state based on comparison mode
        for card in self.test_cards.values():
            if hasattr(card, 'set_comparison_mode'):
                card.set_comparison_mode(enabled)
        self._update_comparison_ui()
        
    def clear_comparison(self) -> None:
        """Clear comparison selection."""
        if _launcher_modules_available and self._comparison_controller:
            self._comparison_controller.clear()
        else:
            self.comparison_selection.clear()
            
        # Update card visual states
        for card in self.test_cards.values():
            if hasattr(card, 'set_selected'):
                card.set_selected(False)
                
        self._update_comparison_ui()
        
    def launch_comparison(self) -> None:
        """Launch comparison of selected tests."""
        if _launcher_modules_available and self._comparison_controller:
            selection = self._comparison_controller.selected()
        else:
            selection = self.comparison_selection
            
        if len(selection) < 2:
            QMessageBox.warning(self, "Insufficient Selection", 
                              "Please select at least 2 tests for comparison.")
            return
            
        self._init_executor()
        try:
            # Use TestExecutor for comparison launch
            result = self._executor.launch_comparison(selection)
            
            if result.success:
                labels = [f"{name}({vers})" for name, vers in zip(selection, ["original", "framework"] * len(selection))]
                self.log_status(f"✓ Launched comparison: {', '.join(labels)}")
                self.statusBar().showMessage(f"Launched {len(labels)} tests for comparison")
            else:
                error_msg = "; ".join(result.errors) if result.errors else "Unknown comparison launch error"
                self.log_status(f"✗ Failed to launch comparison: {error_msg}")
                self.statusBar().showMessage(f"Failed to launch comparison")
                
        except Exception as e:
            self.log_status(f"✗ Exception in comparison launch: {str(e)}")
            self.statusBar().showMessage(f"Failed to launch comparison")
            
    def _update_comparison_ui(self) -> None:
        """Update comparison mode UI elements."""
        # Sync with comparison controller if available
        if _launcher_modules_available and self._comparison_controller:
            self.comparison_selection = self._comparison_controller.selected()
            
        count = len(self.comparison_selection)
        self.clear_comparison_btn.setEnabled(count > 0)
        self.launch_comparison_btn.setEnabled(count >= 2)
        
        if count > 0:
            self.statusBar().showMessage(
                f"Selected {count} tests for comparison: {', '.join(self.comparison_selection)}")
        else:
            self.statusBar().showMessage("Ready to launch tests")
            
    def _init_executor(self) -> None:
        """Initialize the test executor if needed."""
        if not _launcher_modules_available:
            return
            
        if not hasattr(self, "_registry") or not self._registry:
            self._registry = load_registry_from_monolith()
        if not hasattr(self, "_executor") or not self._executor:
            # Pass the current file path to maintain command shape consistency
            launcher_script = Path(__file__).parent.parent.parent.parent / "MANUAL_TESTS" / "enhanced_test_launcher_v2.py"
            self._executor = TestExecutor(self._registry, launcher_script=launcher_script)
            
    def log_status(self, message: str) -> None:
        """Add message to status area."""
        if self.status_area:
            self.status_area.append(f"• {message}")
            
            # Keep status area from growing too large
            if hasattr(self.status_area, 'document') and self.status_area.document().lineCount() > 20:
                cursor = self.status_area.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                cursor.select(cursor.SelectionType.LineUnderCursor)
                cursor.removeSelectedText()
                cursor.deletePreviousChar()  # Remove the newline


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