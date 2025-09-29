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
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
except Exception:  # pragma: no cover - allows pure tests without Qt plugin
    QWidget = QVBoxLayout = QGridLayout = QScrollArea = QTextEdit = object  # type: ignore
    Qt = pyqtSignal = QTimer = object  # type: ignore

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
        self._last_width: int = 0  # Track width for responsive layout
        self._resize_timer = None  # Timer for delayed resize handling
        
        self.setup_ui()
        
    def setup_ui(self):
        """Create the gallery UI components."""
        layout = QVBoxLayout(self)  # type: ignore[call-arg]
        
        # Set dark mode background for the main widget
        try:
            self.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")  # type: ignore[attr-defined]
        except Exception:
            pass
        
        # Test cards scroll area
        self.scroll = QScrollArea()  # type: ignore[call-arg]
        try:
            self.scroll.setWidgetResizable(True)  # type: ignore[attr-defined]
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # type: ignore[attr-defined]
            self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # type: ignore[attr-defined]
            self.scroll.setStyleSheet("background-color: #2b2b2b;")  # type: ignore[attr-defined]
        except Exception:
            pass
        
        # Grid layout for test cards
        self.cards_widget = QWidget()  # type: ignore[call-arg]
        self.cards_layout = QGridLayout(self.cards_widget)  # type: ignore[call-arg]
        try:
            self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # type: ignore[attr-defined]
            self.cards_widget.setStyleSheet("background-color: #2b2b2b;")  # type: ignore[attr-defined]
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
            self.status_area.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")  # type: ignore[attr-defined]
        except Exception:
            pass
        layout.addWidget(self.status_area)  # type: ignore[arg-type]
        
    def set_comparison_controller(self, controller: ComparisonController):
        """Set the comparison controller for managing selection state."""
        self.comparison_controller = controller
        
    def _get_available_width(self) -> int:
        """Get the available width for card layout."""
        available_width = 0
        
        # Try multiple sources for available width
        # First try the scroll area viewport (most accurate during resize)
        if hasattr(self, 'scroll') and hasattr(self.scroll, 'viewport'):
            try:
                viewport_width = self.scroll.viewport().width()  # type: ignore[attr-defined]
                if viewport_width > 100:  # Reasonable minimum
                    available_width = viewport_width - 20  # Account for small margins
            except Exception:
                pass
                
        # Fallback to scroll area width
        if available_width <= 100 and hasattr(self, 'scroll'):
            try:
                scroll_width = self.scroll.width()  # type: ignore[attr-defined]
                if scroll_width > 100:
                    available_width = scroll_width - 50  # Account for scrollbar and margins
            except Exception:
                pass
        
        # Fallback to widget width
        if available_width <= 100:
            try:
                widget_width = self.width()  # type: ignore[attr-defined]
                if widget_width > 100:
                    available_width = widget_width - 70  # Account for larger margins
            except Exception:
                pass
        
        # Final fallback - use reasonable default
        if available_width <= 100:
            available_width = 800
            
        # Ensure we have a reasonable minimum width
        return max(available_width, 560)  # Minimum for 2 columns at 280px each
    
    def _calculate_optimal_layout(self) -> dict:
        """Calculate optimal column count and card sizing using hybrid approach."""
        try:
            available_width = self._get_available_width()
            
            # Card size constraints
            min_card_width = 280  # Minimum usable card width
            max_card_width = 350  # Maximum before cards look too stretched
            base_card_width = 320  # Preferred card width (300px card + 20px margin)
            
            # Test different column counts and find the best approach
            best_solution = {'columns': 3, 'card_width': base_card_width, 'use_flexible_spacing': False, 'waste_percent': 100}
            
            # Determine appropriate column range based on available width
            min_columns = max(2, available_width // 450)  # Minimum 2 columns, more for very wide screens
            max_columns = min(6, available_width // 280)   # Maximum 6 columns, limited by minimum card width
            
            for cols in range(min_columns, max_columns + 1):  # Test reasonable column range
                # Calculate what card width would be needed to fill space exactly
                ideal_card_width = available_width / cols
                
                # Option 1: Use dynamic card width if within bounds
                if min_card_width <= ideal_card_width <= max_card_width:
                    waste_percent = 0  # Perfect fit
                    solution = {
                        'columns': cols,
                        'card_width': int(ideal_card_width),
                        'use_flexible_spacing': False,
                        'waste_percent': waste_percent
                    }
                    if waste_percent < best_solution['waste_percent']:
                        best_solution = solution
                
                # Option 2: Use base card width with flexible spacing
                used_width = cols * base_card_width
                if used_width <= available_width:
                    waste_percent = ((available_width - used_width) / available_width) * 100
                    # Prefer this if waste is reasonable (<15%) 
                    if waste_percent < 15:
                        solution = {
                            'columns': cols,
                            'card_width': base_card_width,
                            'use_flexible_spacing': True,
                            'extra_spacing': available_width - used_width,
                            'waste_percent': waste_percent
                        }
                        # Prefer more columns if waste is similar
                        if (waste_percent < best_solution['waste_percent'] or 
                            (abs(waste_percent - best_solution['waste_percent']) < 5 and cols > best_solution['columns'])):
                            best_solution = solution
            
            return best_solution
            
        except Exception:
            # Fallback to original behavior if anything goes wrong
            return {'columns': 3, 'card_width': 320, 'use_flexible_spacing': False, 'waste_percent': 0}
    
    def _calculate_optimal_columns(self) -> int:
        """Calculate optimal number of columns based on available width."""
        layout = self._calculate_optimal_layout()
        return layout['columns']
    
    def _apply_layout_styling(self, layout_info) -> None:  # type: ignore[type-arg]
        """Apply layout-specific styling based on the optimal layout."""
        try:
            if layout_info.get('use_flexible_spacing', False) and 'extra_spacing' in layout_info:
                # Set up flexible spacing by adjusting grid layout spacing
                extra_spacing = layout_info['extra_spacing']
                cols = layout_info['columns']
                
                # Distribute extra space as horizontal spacing
                if cols > 1:
                    spacing_per_gap = extra_spacing // (cols - 1)
                    self.cards_layout.setHorizontalSpacing(max(10, spacing_per_gap))  # type: ignore[attr-defined]
                else:
                    self.cards_layout.setHorizontalSpacing(10)  # type: ignore[attr-defined]
            else:
                # Reset to default spacing for dynamic sizing
                self.cards_layout.setHorizontalSpacing(10)  # type: ignore[attr-defined]
                
            # Always set reasonable vertical spacing
            self.cards_layout.setVerticalSpacing(10)  # type: ignore[attr-defined]
            
        except Exception:
            # Fallback to default spacing if anything goes wrong
            try:
                self.cards_layout.setHorizontalSpacing(10)  # type: ignore[attr-defined]
                self.cards_layout.setVerticalSpacing(10)  # type: ignore[attr-defined]
            except Exception:
                pass
    
    def _apply_card_sizing(self, card_widget, target_width: int) -> None:  # type: ignore[type-arg]
        """Apply dynamic sizing to a card widget."""
        try:
            # Set the card's maximum width to the calculated optimal width
            card_widget.setMaximumWidth(target_width)  # type: ignore[attr-defined]
            card_widget.setMinimumWidth(max(280, target_width - 20))  # type: ignore[attr-defined]  
            
            # Optionally set size hint for better layout behavior
            try:
                from PyQt6.QtCore import QSize
                card_widget.setSizeHint(QSize(target_width, card_widget.height()))  # type: ignore[attr-defined]
            except Exception:
                pass
                
        except Exception:
            # Fallback: reset to default sizing
            try:
                card_widget.setMaximumWidth(300)  # type: ignore[attr-defined]
                card_widget.setMinimumWidth(280)  # type: ignore[attr-defined]
            except Exception:
                pass
        
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
            
        # Create test cards with optimal layout
        row, col = 0, 0
        layout_info = self._calculate_optimal_layout()
        max_cols = layout_info['columns']
        
        # Apply layout-specific styling and spacing
        self._apply_layout_styling(layout_info)
        
        # Store current layout info for debugging
        self._current_layout_info = layout_info

        for config in ALL_TEST_CONFIGS.values():  # Builtin list still authoritative for card ordering
            try:
                card_widget = TestCardWidget(config)
                
                # Apply dynamic card sizing if needed
                if not layout_info.get('use_flexible_spacing', False):
                    self._apply_card_sizing(card_widget, layout_info['card_width'])
                
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
        
    def resizeEvent(self, event):  # type: ignore[override]
        """Handle widget resize to adjust column layout."""
        try:
            super().resizeEvent(event)  # type: ignore[attr-defined]
            
            # Use a timer to debounce resize events
            try:
                if self._resize_timer is None:
                    # Import QTimer locally to avoid issues when Qt not available
                    from PyQt6.QtCore import QTimer  
                    self._resize_timer = QTimer()  # type: ignore[call-arg]
                    self._resize_timer.setSingleShot(True)  # type: ignore[attr-defined]
                    self._resize_timer.timeout.connect(self._handle_delayed_resize)  # type: ignore[attr-defined]
                
                # Reset the timer - this debounces rapid resize events
                self._resize_timer.start(150)  # Reduced delay for more responsive updates  # type: ignore[attr-defined]
            except Exception:
                # Fallback to immediate resize if timer setup fails
                self._handle_delayed_resize()
                
        except Exception:
            # Silently ignore resize errors to avoid breaking the UI
            pass
    
    def _handle_delayed_resize(self):
        """Handle the actual resize after debouncing."""
        try:
            if self.test_cards:
                current_width = self.width()  # type: ignore[attr-defined]
                
                # Check if we need to relayout
                should_relayout = False
                
                if hasattr(self, '_last_width'):
                    width_change = abs(current_width - self._last_width)
                    
                    # More sensitive threshold for better responsiveness
                    if width_change > 50:
                        should_relayout = True
                    
                    # Also check if current layout would cause cutoff issues
                    elif self._would_cards_be_cut_off():
                        should_relayout = True
                        
                else:
                    should_relayout = True
                    
                if should_relayout:
                    self.populate_tests()
                    self._last_width = current_width
                    
        except Exception:
            # Silently ignore resize errors to avoid breaking the UI
            pass
    
    def _would_cards_be_cut_off(self) -> bool:
        """Check if current layout would cause cards to be cut off."""
        try:
            available_width = self._get_available_width()
            layout_info = self._calculate_optimal_layout()
            
            # Calculate minimum width needed for current column count
            min_needed_width = layout_info['columns'] * 280  # Minimum card width
            
            # If available width is less than minimum needed, cards would be cut off
            return available_width < min_needed_width
            
        except Exception:
            return False