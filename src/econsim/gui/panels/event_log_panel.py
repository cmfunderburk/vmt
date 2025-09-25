"""Event Log panel for displaying real-time simulation events.

Shows a scrolling log of important simulation events including:
- Trade transactions between agents
- Agent target selection decisions in bilateral exchange mode
- Other significant agent behaviors for debugging

Updates via timer to show live events without affecting simulation determinism.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QTextEdit
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont

from ..simulation_controller import SimulationController


class EventLogPanel(QWidget):  # pragma: no cover (GUI)
    def __init__(self, controller: SimulationController):
        super().__init__()
        self._controller = controller
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title = QLabel("Event Log")
        title.setStyleSheet("font-weight: bold; padding: 2px;")
        layout.addWidget(title)
        
        # Log display area with scroll
        self._log_display = QTextEdit()
        self._log_display.setReadOnly(True)
        self._log_display.setMaximumHeight(300)  # Limit height
        
        # Use monospace font for aligned text
        font = QFont("Courier", 8)
        self._log_display.setFont(font)
        
        # Style for log appearance
        self._log_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                padding: 2px;
            }
        """)
        
        layout.addWidget(self._log_display)
        
        # Keep track of last known step to detect new events
        self._last_step = -1
        self._log_entries = ["Event log initialized - watching for trades and agent decisions..."]
        self._max_entries = 100  # Keep only recent events
        
        # Auto-refresh timer (4 Hz to match other panels)
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_log)  # type: ignore[arg-type]
        self._update_timer.start(250)  # 4 Hz
        
        # Initial update
        self._update_log()
    
    def _update_log(self) -> None:
        """Update the event log with new events."""
        try:
            # Get current simulation step
            current_step = self._controller.get_current_step()
            
            # Only process if we have a new step
            if current_step > self._last_step:
                # Get new events since last update
                new_events = self._collect_new_events(current_step)
                
                # Add new events to our log (or a step marker if no events)
                if new_events:
                    for event in new_events:
                        self._log_entries.append(event)
                else:
                    # Show step progression even when no events occur
                    if current_step % 10 == 0:  # Every 10th step
                        self._log_entries.append(f"Step {current_step}: (simulation running...)")
                
                # Trim log to maximum entries
                if len(self._log_entries) > self._max_entries:
                    self._log_entries = self._log_entries[-self._max_entries:]
                
                # Update display
                self._refresh_display()
                
                self._last_step = current_step
                
        except Exception:
            # Graceful fallback if controller methods not available
            pass
    
    def _collect_new_events(self, current_step: int) -> list[str]:
        """Collect new events that occurred this step."""
        events = []
        
        try:
            # Collect trade events
            trade_events = self._collect_trade_events(current_step)
            events.extend(trade_events)
            
            # Collect target selection events  
            target_events = self._collect_target_selection_events(current_step)
            events.extend(target_events)
            
        except Exception:
            pass
        
        return events
    
    def _collect_trade_events(self, step: int) -> list[str]:
        """Collect trade transaction events for this step."""
        events = []
        
        try:
            # Check if controller has trade monitoring capability
            if hasattr(self._controller, 'get_recent_trades'):
                recent_trades = self._controller.get_recent_trades(step)
                
                for trade in recent_trades:
                    seller = trade.get('agent_a_id', '?')
                    buyer = trade.get('agent_b_id', '?')
                    give_type = trade.get('goods_a_to_b', '?')
                    take_type = trade.get('goods_b_to_a', '?')
                    delta_u = trade.get('delta_utility', 0)
                    
                    event_text = f"Step {step}: TRADE A{seller} → A{buyer} (give {give_type} / take {take_type}) ΔU={delta_u:.3f}"
                    events.append(event_text)
                    
        except Exception:
            pass
        
        return events
    
    def _collect_target_selection_events(self, step: int) -> list[str]:
        """Collect agent target selection events for this step."""
        events = []
        
        try:
            # Check if controller has target selection monitoring
            if hasattr(self._controller, 'get_recent_target_selections'):
                selections = self._controller.get_recent_target_selections(step)
                
                for selection in selections:
                    agent_id = selection.get('agent_id', '?')
                    target_type = selection.get('target_type', '?')
                    target_pos = selection.get('target_position', '?')
                    partner_id = selection.get('partner_id', None)
                    
                    if partner_id is not None:
                        event_text = f"Step {step}: A{agent_id} pairs with A{partner_id} → {target_pos}"
                    else:
                        event_text = f"Step {step}: A{agent_id} targets {target_type} at {target_pos}"
                    
                    events.append(event_text)
                    
        except Exception:
            pass
        
        return events
    
    def _refresh_display(self) -> None:
        """Refresh the text display with current log entries."""
        # Join all log entries with newlines, most recent at bottom
        log_text = "\n".join(self._log_entries)
        
        # Update the display
        self._log_display.setPlainText(log_text)
        
        # Auto-scroll to bottom to show latest events
        cursor = self._log_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._log_display.setTextCursor(cursor)
        self._log_display.ensureCursorVisible()


__all__ = ["EventLogPanel"]