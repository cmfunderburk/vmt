"""Trade Inspector Panel for educational bilateral exchange observation.

Provides detailed trade information including active intents, execution history,
and economic insights for student learning. Complements the existing agent inspector
with trade-specific educational content.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QScrollArea, QFrame, QGroupBox, QPushButton, QCheckBox)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

from ..simulation_controller import SimulationController
from ..debug_logger import format_agent_id, format_delta


class TradeInspectorPanel(QWidget):  # pragma: no cover (GUI)
    """Panel for inspecting bilateral trade activity and economic insights."""
    
    def __init__(self, controller: SimulationController):
        super().__init__()
        self._controller = controller
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Trade Inspector")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Trade Status Group
        status_group = QGroupBox("Current Trade Status")
        status_layout = QVBoxLayout(status_group)
        
        self._trade_enabled_label = QLabel("Trade Features: Disabled")
        self._active_intents_label = QLabel("Active Intents: 0")
        self._last_executed_label = QLabel("Last Executed: None")
        
        status_layout.addWidget(self._trade_enabled_label)
        status_layout.addWidget(self._active_intents_label)
        status_layout.addWidget(self._last_executed_label)
        
        layout.addWidget(status_group)
        
        # Active Intents Group
        intents_group = QGroupBox("Active Trade Intents")
        intents_layout = QVBoxLayout(intents_group)
        
        # Scrollable area for intents
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        
        self._intents_widget = QWidget()
        self._intents_layout = QVBoxLayout(self._intents_widget)
        scroll_area.setWidget(self._intents_widget)
        
        intents_layout.addWidget(scroll_area)
        layout.addWidget(intents_group)
        
        # Economic Insights Group
        insights_group = QGroupBox("Economic Insights")
        insights_layout = QVBoxLayout(insights_group)
        
        self._total_welfare_label = QLabel("Total Welfare Change: —")
        self._trading_pairs_label = QLabel("Trading Pairs: 0")
        self._preference_diversity_label = QLabel("Preference Diversity: —")
        
        insights_layout.addWidget(self._total_welfare_label)
        insights_layout.addWidget(self._trading_pairs_label)
        insights_layout.addWidget(self._preference_diversity_label)
        
        layout.addWidget(insights_group)
        
        # Educational Controls Group
        controls_group = QGroupBox("Educational Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        # Visualization toggles
        viz_layout = QHBoxLayout()
        self._show_arrows_checkbox = QCheckBox("Show Trade Arrows")
        self._show_highlights_checkbox = QCheckBox("Highlight Trading Agents")
        self._show_arrows_checkbox.setChecked(True)
        self._show_highlights_checkbox.setChecked(True)
        
        viz_layout.addWidget(self._show_arrows_checkbox)
        viz_layout.addWidget(self._show_highlights_checkbox)
        controls_layout.addLayout(viz_layout)
        
        # Pause on trade button
        self._pause_on_trade_button = QPushButton("Pause on Next Trade")
        self._pause_on_trade_button.setCheckable(True)
        controls_layout.addWidget(self._pause_on_trade_button)
        
        layout.addWidget(controls_group)
        
        # Stretch to fill remaining space
        layout.addStretch()
        
        # Auto-refresh timer (4 Hz to match agent inspector)
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_display)  # type: ignore[arg-type]
        self._update_timer.start(250)  # 4 Hz
        
        # Wire up controls
        self._show_arrows_checkbox.toggled.connect(self._on_visualization_changed)  # type: ignore[arg-type]
        self._show_highlights_checkbox.toggled.connect(self._on_visualization_changed)  # type: ignore[arg-type]
        self._pause_on_trade_button.toggled.connect(self._on_pause_on_trade_toggled)  # type: ignore[arg-type]
        
        # Initial update
        self._update_display()
    
    def _update_display(self) -> None:
        """Update all trade information displays."""
        try:
            # Update trade status
            self._update_trade_status()
            
            # Update active intents
            self._update_active_intents()
            
            # Update economic insights
            self._update_economic_insights()
            
        except Exception:
            # Graceful fallback for any update errors
            pass
    
    def _update_trade_status(self) -> None:
        """Update current trade feature status."""
        try:
            draft_enabled = self._controller.trade_draft_enabled()
            exec_enabled = self._controller.trade_execution_enabled()
            
            if exec_enabled:
                status = "Execution Enabled"
            elif draft_enabled:
                status = "Draft Only"
            else:
                status = "Disabled"
            
            self._trade_enabled_label.setText(f"Trade Features: {status}")
            
            # Get active intents count
            intents_count = getattr(self._controller, "active_intents_count", lambda: 0)()
            self._active_intents_label.setText(f"Active Intents: {intents_count}")
            
            # Get last executed trade
            last_trade = getattr(self._controller, "last_trade_summary", lambda: None)()
            if last_trade:
                self._last_executed_label.setText(f"Last Executed: {last_trade}")
            else:
                self._last_executed_label.setText("Last Executed: None")
                
        except Exception:
            self._trade_enabled_label.setText("Trade Features: Unknown")
            self._active_intents_label.setText("Active Intents: —")
            self._last_executed_label.setText("Last Executed: —")
    
    def _update_active_intents(self) -> None:
        """Update the list of active trade intents."""
        try:
            # Clear existing intent displays
            for i in reversed(range(self._intents_layout.count())):
                child = self._intents_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)
            
            # Get current intents
            intents = getattr(self._controller, "get_active_intents", lambda: [])()
            
            if not intents:
                no_intents = QLabel("No active trade intents")
                no_intents.setStyleSheet("color: gray; font-style: italic;")
                self._intents_layout.addWidget(no_intents)
                return
            
            # Display each intent
            for i, intent in enumerate(intents[:10]):  # Limit to first 10 for performance
                intent_frame = QFrame()
                intent_frame.setFrameStyle(QFrame.Shape.Box)
                intent_layout = QVBoxLayout(intent_frame)
                
                # Intent summary
                seller_id = getattr(intent, 'seller_id', '?')
                buyer_id = getattr(intent, 'buyer_id', '?')
                give_type = getattr(intent, 'give_type', '?')
                take_type = getattr(intent, 'take_type', '?')
                delta_u = getattr(intent, 'delta_utility', 0.0)
                
                summary = f"{format_agent_id(int(seller_id)) if str(seller_id).isdigit() else f'A{seller_id}'} → {format_agent_id(int(buyer_id)) if str(buyer_id).isdigit() else f'A{buyer_id}'}: {give_type} → {take_type}"
                summary_label = QLabel(summary)
                summary_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                
                # Economic details
                details = f"Utility Gain: {format_delta(delta_u)}"
                details_label = QLabel(details)
                details_label.setFont(QFont("Arial", 8))
                details_label.setStyleSheet("color: #006400;")  # Dark green
                
                intent_layout.addWidget(summary_label)
                intent_layout.addWidget(details_label)
                intent_layout.setContentsMargins(4, 2, 4, 2)
                
                self._intents_layout.addWidget(intent_frame)
            
            if len(intents) > 10:
                more_label = QLabel(f"... and {len(intents) - 10} more intents")
                more_label.setStyleSheet("color: gray; font-style: italic;")
                self._intents_layout.addWidget(more_label)
                
        except Exception:
            # Fallback display
            error_label = QLabel("Unable to load trade intents")
            error_label.setStyleSheet("color: red; font-style: italic;")
            self._intents_layout.addWidget(error_label)
    
    def _update_economic_insights(self) -> None:
        """Update economic insights and educational metrics."""
        try:
            # Total welfare change from current intents
            total_welfare = getattr(self._controller, "calculate_total_welfare_change", lambda: 0.0)()
            self._total_welfare_label.setText(f"Total Welfare Change: {total_welfare:.3f}")
            
            # Number of unique trading pairs
            pairs_count = getattr(self._controller, "count_trading_pairs", lambda: 0)()
            self._trading_pairs_label.setText(f"Trading Pairs: {pairs_count}")
            
            # Preference diversity analysis
            diversity = getattr(self._controller, "analyze_preference_diversity", lambda: "Unknown")()
            self._preference_diversity_label.setText(f"Preference Diversity: {diversity}")
            
        except Exception:
            self._total_welfare_label.setText("Total Welfare Change: —")
            self._trading_pairs_label.setText("Trading Pairs: —")
            self._preference_diversity_label.setText("Preference Diversity: —")
    
    def _on_visualization_changed(self) -> None:
        """Handle changes to visualization options."""
        try:
            show_arrows = self._show_arrows_checkbox.isChecked()
            show_highlights = self._show_highlights_checkbox.isChecked()
            
            # Notify controller about visualization preferences
            if hasattr(self._controller, 'set_trade_visualization_options'):
                self._controller.set_trade_visualization_options(
                    show_arrows=show_arrows,
                    show_highlights=show_highlights
                )
        except Exception:
            pass
    
    def _on_pause_on_trade_toggled(self, checked: bool) -> None:
        """Handle pause on trade toggle."""
        try:
            if hasattr(self._controller, 'set_pause_on_trade'):
                self._controller.set_pause_on_trade(checked)
        except Exception:
            pass
    
    def get_visualization_options(self) -> dict[str, bool]:
        """Get current visualization options for integration with renderer."""
        return {
            'show_arrows': self._show_arrows_checkbox.isChecked(),
            'show_highlights': self._show_highlights_checkbox.isChecked()
        }
    
    def is_pause_on_trade_enabled(self) -> bool:
        """Check if pause on trade is enabled."""
        return self._pause_on_trade_button.isChecked()


__all__ = ["TradeInspectorPanel"]