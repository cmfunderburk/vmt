"""Main Application Window for VMT Enhanced Test Launcher.

Provides programmatic test execution using TestRunner API with comprehensive
error handling, status monitoring, and launcher-specific logging system.

Implements direct framework test execution while maintaining subprocess fallback
for backward compatibility. Features real-time status display and health monitoring.
"""
from __future__ import annotations

import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

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

# Default window sizing configuration
DEFAULT_WINDOW_WIDTH_SCALE = 0.48  # 48% of screen width
DEFAULT_WINDOW_HEIGHT_SCALE = 0.65  # 65% of screen height

# Import TestRunner for programmatic test execution
try:
    from .test_runner import TestRunner
    _test_runner_available = True
except ImportError:  # pragma: no cover - fallback path
    TestRunner = None  # type: ignore
    _test_runner_available = False

# Import launcher-specific logger for file logging
try:
    from .launcher_logger import get_launcher_logger
    _launcher_logger_available = True
except ImportError:  # pragma: no cover - fallback path
    get_launcher_logger = None  # type: ignore
    _launcher_logger_available = False


class VMTLauncherWindow(QMainWindow):  # pragma: no cover - GUI application window
    """Main window for the VMT Enhanced Test Launcher with programmatic execution.
    
    Features:
    - Programmatic test execution via TestRunner API (eliminates subprocess overhead)
    - Comprehensive status monitoring with real-time health indicators
    - Independent launcher logging system (launcher_logs/ directory)
    - Enhanced error handling with detailed component validation
    - Subprocess fallback for backward compatibility
    - Dynamic GUI status display with color-coded health states
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Core state
        self.test_cards: Dict[str, TestCardWidget] = {}
        self.comparison_selection: List[str] = []
        self.tab_manager: Optional[TabManager] = None
        self.gallery_widget: Optional[TestGalleryWidget] = None
        self.status_area: Optional[QTextEdit] = None
        self.status_label: Optional[QLabel] = None
        
        # Controllers and services
        self._comparison_controller: Optional[ComparisonController] = None
        self._registry = None
        self._executor = None
        
        # Initialize launcher file logging first (needed by other init methods)
        self.launcher_logger = None
        self._init_launcher_logging()
        
        # Initialize TestRunner for programmatic test execution
        self.test_runner = None
        self._init_test_runner()
        
        # Initialize the application
        self._setup_window()
        self._setup_ui()
        self._populate_tests()
        
    def _calculate_optimal_window_size(self) -> tuple[int, int]:
        """Calculate optimal window size based on screen dimensions."""
        try:
            # Get primary screen's available geometry (excludes taskbars/docks)
            screen = QApplication.primaryScreen()  # type: ignore[attr-defined]
            if screen:
                available = screen.availableGeometry()  # type: ignore[attr-defined]
                screen_width = available.width()  # type: ignore[attr-defined]
                screen_height = available.height()  # type: ignore[attr-defined]
                
                # Calculate size based on default scaling factors
                width = int(screen_width * DEFAULT_WINDOW_WIDTH_SCALE)
                height = int(screen_height * DEFAULT_WINDOW_HEIGHT_SCALE)
                
                # Apply constraints
                width = max(1000, min(width, 1600))   # Min 1000, max 1600
                height = max(700, min(height, 1200))  # Min 700, max 1200
                
                return width, height
                
        except Exception:
            pass
        
        # Fallback to current default
        return 1200, 800
    
    def _setup_window(self) -> None:
        """Configure the main window properties."""
        self.setWindowTitle("VMT Enhanced Test Launcher")
        self.setMinimumSize(1000, 700)
        
        # Set optimal size based on screen dimensions
        optimal_width, optimal_height = self._calculate_optimal_window_size()
        self.resize(optimal_width, optimal_height)  # type: ignore[attr-defined]
        
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
    
    def _init_test_runner(self) -> None:
        """Initialize TestRunner for direct framework test execution.
        
        Creates programmatic TestRunner instance using TestConfiguration registry
        and framework components. Eliminates subprocess overhead and provides
        comprehensive status monitoring. Logs initialization status to launcher logs.
        """
        if not _test_runner_available or TestRunner is None:
            self.log_status("⚠️ TestRunner not available - using subprocess fallback")
            return
        
        try:
            self.test_runner = TestRunner()  # type: ignore[misc]
            self.log_status("✅ Test runner initialized successfully")
            
            # Log runner initialization to launcher logger
            if self.launcher_logger:
                self.launcher_logger.runner_init("programmatic TestRunner framework")
                
        except Exception as e:
            self.test_runner = None
            self.log_status(f"⚠️ Test runner failed to initialize: {e}")
            
            # Log initialization failure to launcher logger
            if self.launcher_logger:
                self.launcher_logger.error(f"TestRunner initialization failed: {e}")
            
            # Log full error for debugging
            import traceback
            print(f"TestRunner initialization error:\n{traceback.format_exc()}")
    
    def _init_launcher_logging(self) -> None:
        """Initialize launcher file logging."""
        if not _launcher_logger_available or get_launcher_logger is None:
            print("⚠️ Launcher logger not available for file logging")
            return
        
        try:
            self.launcher_logger = get_launcher_logger()  # type: ignore[misc]
            # Log initial launcher startup
            self.log_status("🚀 VMT Enhanced Test Launcher started")
        except Exception as e:
            self.launcher_logger = None
            print(f"⚠️ Launcher logging initialization failed: {e}")
        
    def _create_header(self, layout: QVBoxLayout) -> None:
        """Create the application header."""
        header = QLabel("🧪 VMT Enhanced Test Launcher")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e;
                padding: 12px;
                border-radius: 6px;
                color: #ffffff;
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
        
        # TestRunner status label
        self.status_label = QLabel("📊 Initializing...")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #1e3a5f;
                border: 1px solid #0078d4;
                border-radius: 4px;
                padding: 4px 8px;
                color: #ffffff;
                font-weight: bold;
            }
        """)
        controls_layout.addWidget(self.status_label)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._populate_tests)
        refresh_btn.clicked.connect(self.update_runner_status)  # Update status on refresh
        controls_layout.addWidget(refresh_btn)
        
        layout.addLayout(controls_layout)
        
        # Update status after controls are created
        self.update_runner_status()
        
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
        try:
            main_tabs.setStyleSheet("""
                QTabWidget::pane {
                    border: 1px solid #555555;
                    background-color: #2b2b2b;
                }
                QTabBar::tab {
                    background-color: #404040;
                    color: #ffffff;
                    padding: 8px 16px;
                    margin-right: 2px;
                    border-top-left-radius: 3px;
                    border-top-right-radius: 3px;
                }
                QTabBar::tab:selected {
                    background-color: #2b2b2b;
                    border-bottom: none;
                }
                QTabBar::tab:hover {
                    background-color: #4a4a4a;
                }
            """)
        except Exception:
            pass
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
            self.status_area.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        
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
        self.status_area.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
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
        """Launch test using programmatic TestRunner with comprehensive logging.
        
        Primary execution method using TestRunner API for direct framework
        instantiation. Falls back to subprocess launching if programmatic
        execution fails. All execution attempts logged to launcher_logs/.
        
        Args:
            test_name: Display name of test to launch
        """
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
            
            # Try programmatic TestRunner first
            if self.test_runner:
                try:
                    self.log_status(f"🚀 Launching {test_name} (programmatic)...")
                    
                    # Log test start to launcher logger
                    if self.launcher_logger:
                        self.launcher_logger.test_start(str(config.id), test_name)
                    
                    import time
                    start_time = time.time()
                    self.test_runner.run_by_id(config.id, "framework")
                    execution_time = time.time() - start_time
                    
                    self.log_status(f"✅ Test {test_name} launched successfully")
                    
                    # Log test success to launcher logger
                    if self.launcher_logger:
                        self.launcher_logger.test_success(str(config.id), execution_time)
                    
                    return
                except Exception as e:
                    self.log_status(f"⚠️ Programmatic launch failed: {e}")
                    
                    # Log test error to launcher logger
                    if self.launcher_logger:
                        self.launcher_logger.test_error(str(config.id), str(e))
                    
                    # Continue to subprocess fallback
            
            # Fallback to subprocess launching
            self.log_status(f"🚀 Launching {test_name} (subprocess fallback)...")
            self._launch_test_subprocess_fallback(config, test_name)
            
        except Exception as e:
            self.log_status(f"✗ Exception launching {test_name}: {str(e)}")
            print(f"Launch error: {e}")
    
    def _launch_test_subprocess_fallback(self, config: Any, test_name: str) -> None:
        """Fallback to original subprocess launching if programmatic fails."""
        try:
            # Log fallback usage to launcher logger
            if self.launcher_logger:
                self.launcher_logger.info(f"🔄 Using subprocess fallback for test {config.id}")
            
            # Map config IDs to test files (preserved for fallback)
            id_to_file = {
                1: "test_1.py",
                2: "test_2.py", 
                3: "test_3.py",
                4: "test_4.py",
                5: "test_5.py",
                6: "test_6.py",
                7: "test_7.py"
            }
            
            test_file = id_to_file.get(config.id)
            if not test_file:
                error_msg = f"No test file mapping for config ID {config.id}"
                self.log_status(f"✗ {error_msg}")
                if self.launcher_logger:
                    self.launcher_logger.test_error(str(config.id), error_msg)
                return
                
            # Construct test file path (go up from src/econsim/tools/launcher/ to project root)
            test_path = Path(__file__).parent.parent.parent.parent.parent / "MANUAL_TESTS" / test_file
            if not test_path.exists():
                error_msg = f"Test file not found: {test_path}"
                self.log_status(f"✗ {error_msg}")
                if self.launcher_logger:
                    self.launcher_logger.test_error(str(config.id), error_msg)
                return
            
            # Log subprocess launch attempt
            if self.launcher_logger:
                self.launcher_logger.info(f"🔧 Launching subprocess: {test_file}")
            
            # Launch test in subprocess with proper environment
            import os
            env = os.environ.copy()
            
            import time
            start_time = time.time()
            
            # Use Popen for non-blocking launch (like original behavior)
            process = subprocess.Popen(
                [sys.executable, str(test_path)], 
                cwd=str(test_path.parent),
                env=env,
                stdout=None,  # Let output go to console
                stderr=None
            )
            
            execution_time = time.time() - start_time
            
            self.log_status(f"✅ Test {test_name} launched via subprocess (PID: {process.pid})")
            
            # Log subprocess success to launcher logger
            if self.launcher_logger:
                self.launcher_logger.info(f"✅ Subprocess launched successfully - PID: {process.pid}")
                # Note: We can't easily track subprocess completion time, so we log launch time
                self.launcher_logger.test_success(str(config.id), execution_time)
            
        except Exception as e:
            error_msg = f"Subprocess fallback failed: {e}"
            self.log_status(f"✗ {error_msg}")
            
            # Log subprocess failure to launcher logger
            if self.launcher_logger:
                self.launcher_logger.error(error_msg)
                self.launcher_logger.test_error(str(config.id), str(e))
            
            # Log full traceback for debugging
            import traceback
            print(f"Subprocess fallback error details:\n{traceback.format_exc()}")
            
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
        """Add message to status area and log file."""
        # Add to GUI status area
        if self.status_area:
            self.status_area.append(f"• {message}")
            
            # Keep status area from growing too large
            if hasattr(self.status_area, 'document') and self.status_area.document().lineCount() > 20:
                cursor = self.status_area.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                cursor.select(cursor.SelectionType.LineUnderCursor)
                cursor.removeSelectedText()
                cursor.deletePreviousChar()  # Remove the newline
        
        # Also log to file if launcher logger is available
        if self.launcher_logger:
            try:
                # Use launcher-specific logging method
                self.launcher_logger.info(message)
            except Exception as e:
                # Don't let logging errors crash the GUI
                print(f"⚠️ Launcher logging error: {e}")
        
        # Also print to console for immediate feedback during development
        print(f"[LAUNCHER] {message}")
    
    def update_runner_status(self) -> None:
        """Update GUI with real-time test runner status and health indicators.
        
        Displays dynamic status including test count, framework availability,
        and current execution state. Uses color-coded health indicators:
        - Green: Healthy (framework available, tests loaded)
        - Yellow: Warning (partial functionality)
        - Red: Error (component failures, recent errors)
        
        Integrates with launcher logging for health issue tracking.
        """
        if not self.status_label:
            return  # Status label not created yet
            
        if not self.test_runner:
            self.status_label.setText("❌ TestRunner: Unavailable")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #3d1a1a;
                    border: 1px solid #d32f2f;
                    border-radius: 4px;
                    padding: 4px 8px;
                    color: #ff6b6b;
                    font-weight: bold;
                }
            """)
            return
        
        try:
            status = self.test_runner.get_status()
            
            # Create status text based on runner state
            status_parts = []
            status_parts.append(f"📊 Tests: {status['available_tests']}")
            status_parts.append("Framework: " + ("✅" if status['framework_available'] else "❌"))
            
            if status['current_test']:
                status_parts.append("🚀 Running")
            
            status_text = " | ".join(status_parts)
            
            # Set status text
            self.status_label.setText(status_text)
            
            # Update style based on overall health
            if status['framework_available'] and status['available_tests'] > 0:
                # Healthy state - green
                self.status_label.setStyleSheet("""
                    QLabel {
                        background-color: #1a3d1a;
                        border: 1px solid #4caf50;
                        border-radius: 4px;
                        padding: 4px 8px;
                        color: #81c784;
                        font-weight: bold;
                    }
                """)
            elif status['last_error']:
                # Error state - red
                self.status_label.setStyleSheet("""
                    QLabel {
                        background-color: #3d1a1a;
                        border: 1px solid #d32f2f;
                        border-radius: 4px;
                        padding: 4px 8px;
                        color: #ff6b6b;
                        font-weight: bold;
                    }
                """)
                # Log the error to status area if not already logged
                if status['last_error'] and self.launcher_logger:
                    self.launcher_logger.warning(f"TestRunner error: {status['last_error']}")
            else:
                # Warning state - yellow
                self.status_label.setStyleSheet("""
                    QLabel {
                        background-color: #3d2f1a;
                        border: 1px solid #f57f17;
                        border-radius: 4px;
                        padding: 4px 8px;
                        color: #ffb74d;
                        font-weight: bold;
                    }
                """)
            
            # Log health check on refresh if there are issues
            if not status['framework_available'] or status['available_tests'] == 0:
                try:
                    health = self.test_runner.get_health_check()
                    if not health['overall_healthy'] and self.launcher_logger:
                        for issue in health['issues']:
                            self.launcher_logger.warning(f"Health check: {issue}")
                except Exception:
                    pass  # Don't fail if health check fails
            
        except Exception as e:
            # Fallback error display
            self.status_label.setText("⚠️ Status Error")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #3d1a1a;
                    border: 1px solid #d32f2f;
                    border-radius: 4px;
                    padding: 4px 8px;
                    color: #ff6b6b;
                    font-weight: bold;
                }
            """)
            if self.launcher_logger:
                self.launcher_logger.error(f"Failed to update runner status: {e}")


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
    
    def _calculate_optimal_window_size(self) -> tuple[int, int]:
        """Calculate optimal window size based on screen dimensions."""
        try:
            # Get primary screen's available geometry (excludes taskbars/docks)
            screen = QApplication.primaryScreen()  # type: ignore[attr-defined]
            if screen:
                available = screen.availableGeometry()  # type: ignore[attr-defined]
                screen_width = available.width()  # type: ignore[attr-defined]
                screen_height = available.height()  # type: ignore[attr-defined]
                
                # Calculate size based on default scaling factors
                width = int(screen_width * DEFAULT_WINDOW_WIDTH_SCALE)
                height = int(screen_height * DEFAULT_WINDOW_HEIGHT_SCALE)
                
                # Apply constraints
                width = max(1000, min(width, 1600))   # Min 1000, max 1600
                height = max(700, min(height, 1200))  # Min 700, max 1200
                
                return width, height
                
        except Exception:
            pass
        
        # Fallback to current default
        return 1200, 800

    def _setup_window(self) -> None:
        """Configure main window properties."""
        try:
            self.setWindowTitle("VMT Enhanced Test Launcher")  # type: ignore[attr-defined]
            
            # Calculate optimal size based on screen dimensions
            optimal_width, optimal_height = self._calculate_optimal_window_size()
            self.setGeometry(100, 100, optimal_width, optimal_height)  # type: ignore[attr-defined]
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
            status_area.setStyleSheet("background-color: #1e1e1e; color: #ffffff; font-family: monospace;")  # type: ignore[attr-defined]
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