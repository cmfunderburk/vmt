"""Event Log panel for displaying real-time simulation events.

Shows a scrolling log of important simulation events including:
- Trade transactions between agents
- Agent target selection decisions in bilateral exchange mode
- Other significant agent behaviors for debugging

Updates via timer to show live events without affecting simulation determinism.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QHBoxLayout, QCheckBox, QFrame
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont

from ..simulation_controller import SimulationController


class EventLogPanel(QWidget):  # pragma: no cover (GUI)
    def __init__(self, controller: SimulationController):
        super().__init__()
        self._controller = controller
        self._debug_enabled = True

        root = QVBoxLayout(self)
        root.setContentsMargins(5, 5, 5, 5)
        root.setSpacing(4)

        # Top: Debug header with enable checkbox
        dbg_header = QHBoxLayout()
        dbg_label = QLabel("Debug Log")
        dbg_label.setStyleSheet("font-weight: bold; padding: 0px;")
        self._debug_toggle = QCheckBox("show")
        self._debug_toggle.setChecked(True)
        self._debug_toggle.stateChanged.connect(self._on_debug_toggled)  # type: ignore[arg-type]
        dbg_header.addWidget(dbg_label)
        dbg_header.addStretch()
        dbg_header.addWidget(self._debug_toggle)
        root.addLayout(dbg_header)

        self._debug_display = QTextEdit()
        self._debug_display.setReadOnly(True)
        self._debug_display.setMinimumHeight(140)
        self._debug_display.setStyleSheet("QTextEdit { background:#f2f2f2; border:1px solid #ccc; padding:2px; }")
        self._debug_display.setFont(QFont("Courier", 8))
        root.addWidget(self._debug_display)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(sep)

        # Event log header
        ev_header = QLabel("Event Log")
        ev_header.setStyleSheet("font-weight: bold; padding: 0px;")
        root.addWidget(ev_header)

        # Event log text area (bottom half)
        self._log_display = QTextEdit()
        self._log_display.setReadOnly(True)
        self._log_display.setMinimumHeight(140)
        self._log_display.setStyleSheet("QTextEdit { background:#fafafa; border:1px solid #ddd; padding:2px; }")
        self._log_display.setFont(QFont("Courier", 8))
        root.addWidget(self._log_display, 1)

        # Internal buffers
        self._last_step = -1
        self._log_entries: list[str] = ["Event log initialized - watching for trades and agent decisions..."]
        self._debug_entries: list[str] = ["Debug log active (toggle 'show' to hide updates)"]
        self._max_entries = 100

        # Timer
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_log)  # type: ignore[arg-type]
        self._update_timer.start(250)

        self._update_log()

    def _on_debug_toggled(self, state: int) -> None:
        self._debug_enabled = bool(state)
        if not self._debug_enabled:
            # Keep contents but visually mute
            self._debug_display.setStyleSheet("QTextEdit { background:#f2f2f2; border:1px solid #eee; color:#888; }")
        else:
            self._debug_display.setStyleSheet("QTextEdit { background:#f2f2f2; border:1px solid #ccc; padding:2px; }")
    
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
                
                # Update displays
                self._refresh_event_display()
                self._refresh_debug_display()
                
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
                # Check for trades in current step and previous step (since trades might be recorded
                # with a slight delay or in the previous step due to timing)
                for check_step in [step, step - 1]:
                    if check_step >= 0:  # Don't check negative steps
                        recent_trades = self._controller.get_recent_trades(check_step)
                        
                        for trade in recent_trades:
                            seller = trade.get('agent_a_id', '?')
                            buyer = trade.get('agent_b_id', '?')
                            give_type = trade.get('goods_a_to_b', '?')
                            take_type = trade.get('goods_b_to_a', '?')
                            delta_u = trade.get('delta_utility', 0)
                            trade_step = trade.get('step', check_step)
                            
                            # Format trade event for display (use actual trade step)
                            event_text = f"Step {trade_step}: TRADE Agent {seller} ⟷ Agent {buyer} | {give_type} ⟷ {take_type} | ΔU={delta_u:.3f}"
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
    
    def _refresh_event_display(self) -> None:
        log_text = "\n".join(self._log_entries)
        self._log_display.setPlainText(log_text)
        cursor = self._log_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._log_display.setTextCursor(cursor)
        self._log_display.ensureCursorVisible()

    def _refresh_debug_display(self) -> None:
        # Append lightweight debug info (only when enabled)
        if self._debug_enabled:
            try:
                # Example debug signals: step, #intents, #agents
                step = self._controller.get_current_step()
                intents = getattr(self._controller.simulation, 'trade_intents', None)
                intent_count = len(intents) if intents else 0
                line = f"Step {step}: intents={intent_count}"
                if not self._debug_entries or self._debug_entries[-1] != line:
                    self._debug_entries.append(line)
                if len(self._debug_entries) > self._max_entries:
                    self._debug_entries = self._debug_entries[-self._max_entries:]
            except Exception:
                pass
        dbg_text = "\n".join(self._debug_entries)
        self._debug_display.setPlainText(dbg_text)
        cur = self._debug_display.textCursor()
        cur.movePosition(cur.MoveOperation.End)
        self._debug_display.setTextCursor(cur)
        self._debug_display.ensureCursorVisible()


__all__ = ["EventLogPanel"]