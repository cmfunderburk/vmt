"""Test Gallery Widget - extracted from monolithic launcher.

Gallery management component that handles test card creation, layout, and 
comparison mode visualization using TestCardWidget components.
Extracted from enhanced_test_launcher_v2.py in Phase 2.4.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QGridLayout, QScrollArea, QTextEdit
    )
    from PyQt6.QtCore import Qt, pyqtSignal
except Exception:  # pragma: no cover - allows pure tests without Qt plugin
    QWidget = QVBoxLayout = QGridLayout = QScrollArea = QTextEdit = object  # type: ignore
    Qt = pyqtSignal = object  # type: ignore

# Import extracted components
from .cards import TestCardWidget
from .comparison import ComparisonController

# Import framework test configs (using same strategy as monolith)
try:
    # Widget is in src/econsim/tools/launcher/widgets.py
    # We need to import from the same package: src/econsim/tools/launcher/framework/test_configs.py
    from .framework.test_configs import TestConfiguration, ALL_TEST_CONFIGS
except ImportError:
    try:
        # Fallback: try relative import from launcher package
        from econsim.tools.launcher.framework.test_configs import TestConfiguration, ALL_TEST_CONFIGS
    except ImportError:
        # Final fallback when framework not available
        ALL_TEST_CONFIGS = {}
        TestConfiguration = object  # type: ignore


class TestGalleryWidget(QWidget):  # pragma: no cover - GUI component extracted from monolith
    """Gallery widget for managing test card display and comparison selection.
    
    Extracted from enhanced_test_launcher_v2.py in Phase 2.4.
    Handles test card creation, grid layout, and comparison mode visualization.
    """
    
    # Signals for parent window communication
    testLaunchRequested = pyqtSignal(str, str)  # test_name, version  # type: ignore[assignment]
    statusUpdate = pyqtSignal(str)  # status_message  # type: ignore[assignment]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.test_cards: Dict[str, TestCardWidget] = {}
        self.comparison_controller: ComparisonController | None = None
        self.comparison_selection: List[str] = []  # Backward compatibility
        
        self.setup_ui()
        
    def setup_ui(self):
        """Create the gallery UI components."""
        layout = QVBoxLayout(self)  # type: ignore[call-arg]
        
        # Test cards scroll area
        self.scroll = QScrollArea()  # type: ignore[call-arg]
        try:
            self.scroll.setWidgetResizable(True)  # type: ignore[attr-defined]
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # type: ignore[attr-defined]
            self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # type: ignore[attr-defined]
        except Exception:
            pass
        
        # Grid layout for test cards
        self.cards_widget = QWidget()  # type: ignore[call-arg]
        self.cards_layout = QGridLayout(self.cards_widget)  # type: ignore[call-arg]
        try:
            self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # type: ignore[attr-defined]
        except Exception:
            pass
        
        try:
            self.scroll.setWidget(self.cards_widget)  # type: ignore[attr-defined]
        except Exception:
            pass
        layout.addWidget(self.scroll)  # type: ignore[arg-type]
        
        # Status area
        self.status_area = QTextEdit()  # type: ignore[call-arg]
        try:
            self.status_area.setReadOnly(True)  # type: ignore[attr-defined]
            self.status_area.setMaximumHeight(100)  # type: ignore[attr-defined]
            self.status_area.setStyleSheet("background-color: #f8f9fa;")  # type: ignore[attr-defined]
        except Exception:
            pass
        layout.addWidget(self.status_area)  # type: ignore[arg-type]
        
    def set_comparison_controller(self, controller: ComparisonController):
        """Set the comparison controller for managing selection state."""
        self.comparison_controller = controller
        
    def populate_tests(self):
        """Populate the test gallery with available tests."""
        # Clear existing cards
        for card in self.test_cards.values():
            try:
                card.setParent(None)  # type: ignore[attr-defined]
            except Exception:
                pass
        self.test_cards.clear()
        
        # Initialize comparison selection
        if self.comparison_controller:
            self.comparison_controller.clear()
            self.comparison_selection = self.comparison_controller.selected()
        else:
            self.comparison_selection.clear()
            
        # Create test cards
        row, col = 0, 0
        max_cols = 3

        for config in ALL_TEST_CONFIGS.values():  # Builtin list still authoritative for card ordering
            try:
                card_widget = TestCardWidget(config)
                
                # Connect signals
                try:
                    card_widget.launchRequested.connect(self._on_launch_requested)  # type: ignore[attr-defined]
                    card_widget.compareRequested.connect(self._on_compare_requested)  # type: ignore[attr-defined]
                except Exception:
                    pass
                
                self.cards_layout.addWidget(card_widget, row, col)  # type: ignore[attr-defined]
                self.test_cards[config.name] = card_widget

                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
                    
            except Exception as e:
                print(f"Error creating card for {getattr(config, 'name', 'unknown')}: {e}")

        # Update status
        self.statusUpdate.emit(f"Loaded {len(ALL_TEST_CONFIGS)} tests")  # type: ignore[attr-defined]
        self._log_to_status("Enhanced test launcher initialized")
        self._log_to_status(f"Found {len(ALL_TEST_CONFIGS)} test configurations")
        
    def _on_launch_requested(self, test_name: str, version: str):
        """Handle test launch request from card."""
        self.testLaunchRequested.emit(test_name, version)  # type: ignore[attr-defined]
        
    def _on_compare_requested(self, test_name: str):
        """Handle comparison selection request from card."""
        if self.comparison_controller:
            # Toggle semantic: if already present remove
            if self.comparison_controller.contains(test_name):
                self.comparison_controller.remove(test_name)
                self.test_cards[test_name].set_comparison_selected(False)  # type: ignore[attr-defined]
                self._log_to_status(f"Removed {test_name} from comparison")
            else:
                add_res = self.comparison_controller.add(test_name)
                if not add_res.added:
                    if add_res.reason == "capacity":
                        # Let parent handle the message box
                        self.statusUpdate.emit("COMPARISON_LIMIT")  # type: ignore[attr-defined]
                    return
                self.test_cards[test_name].set_comparison_selected(True)  # type: ignore[attr-defined]
                self._log_to_status(f"Added {test_name} to comparison")
            self.comparison_selection = self.comparison_controller.selected()
        else:
            # Fallback logic when comparison controller not available
            if test_name in self.comparison_selection:
                self.comparison_selection.remove(test_name)
                self.test_cards[test_name].set_comparison_selected(False)  # type: ignore[attr-defined]
                self._log_to_status(f"Removed {test_name} from comparison")
            else:
                if len(self.comparison_selection) >= 4:
                    self.statusUpdate.emit("COMPARISON_LIMIT")  # type: ignore[attr-defined]
                    return
                self.comparison_selection.append(test_name)
                self.test_cards[test_name].set_comparison_selected(True)  # type: ignore[attr-defined]
                self._log_to_status(f"Added {test_name} to comparison")
                
        # Notify parent of comparison change
        self.statusUpdate.emit("COMPARISON_CHANGED")  # type: ignore[attr-defined]
        
    def clear_comparison(self):
        """Clear all comparison selections."""
        if self.comparison_controller:
            for test_name in self.comparison_controller.selected():
                self.test_cards[test_name].set_comparison_selected(False)  # type: ignore[attr-defined]
            self.comparison_controller.clear()
            self.comparison_selection = []
        else:
            for test_name in self.comparison_selection.copy():
                self.test_cards[test_name].set_comparison_selected(False)  # type: ignore[attr-defined]
            self.comparison_selection.clear()
        self._log_to_status("Cleared all comparison selections")
        
    def get_comparison_selection(self) -> List[str]:
        """Get current comparison selection."""
        if self.comparison_controller:
            return self.comparison_controller.selected()
        return list(self.comparison_selection)
        
    def _log_to_status(self, message: str):
        """Log message to status area."""
        try:
            if hasattr(self.status_area, 'append'):
                self.status_area.append(message)  # type: ignore[attr-defined]
                # Keep status area from growing too large
                if hasattr(self.status_area, 'document') and self.status_area.document():
                    if hasattr(self.status_area.document(), 'lineCount') and self.status_area.document().lineCount() > 20:  # type: ignore[attr-defined]
                        # Clear some old content
                        cursor = self.status_area.textCursor()  # type: ignore[attr-defined]
                        cursor.movePosition(cursor.MoveOperation.Start)  # type: ignore[attr-defined]
                        for _ in range(5):  # Remove 5 lines
                            cursor.select(cursor.SelectionType.LineUnderCursor)  # type: ignore[attr-defined]
                            cursor.removeSelectedText()  # type: ignore[attr-defined]
                            cursor.deleteChar()  # Remove the newline
        except Exception:
            # Fallback to print if status area not available
            print(f"Gallery: {message}")
            
    def refresh_tests(self):
        """Refresh the test gallery."""
        self.populate_tests()