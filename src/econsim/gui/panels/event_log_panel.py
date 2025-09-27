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
from ..debug_logger import format_agent_id, format_delta


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
        
        # AGGRESSIVE dark mode fix: Force colors using QPalette AND stylesheet
        from PyQt6.QtGui import QPalette, QColor
        from PyQt6.QtCore import Qt
        
        # Force colors via palette (overrides system themes)
        palette = self._debug_display.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))  # White background
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))        # Black text
        palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255)) # White window
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))   # Black window text
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))  # Slightly gray alternate
        self._debug_display.setPalette(palette)
        
        # Also apply stylesheet for additional properties
        self._debug_display.setStyleSheet("""
            QTextEdit { 
                background-color: rgb(255, 255, 255);
                color: rgb(0, 0, 0);
                border: 2px solid rgb(51, 51, 51);
                padding: 4px;
                font-family: 'Monaco', 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
        
        # Set font for fallback
        font = QFont("Monaco", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self._debug_display.setFont(font)
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
        
        # AGGRESSIVE dark mode fix for log display too
        palette2 = self._log_display.palette()
        palette2.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))  # White background
        palette2.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))        # Black text
        palette2.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255)) # White window
        palette2.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))   # Black window text
        self._log_display.setPalette(palette2)
        
        self._log_display.setStyleSheet("""
            QTextEdit { 
                background-color: rgb(255, 255, 255);
                color: rgb(0, 0, 0);
                border: 2px solid rgb(51, 51, 51);
                padding: 4px;
                font-family: 'Monaco', 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
        
        font2 = QFont("Monaco", 10)
        font2.setStyleHint(QFont.StyleHint.Monospace)
        self._log_display.setFont(font2)
        root.addWidget(self._log_display, 1)

        # Internal buffers
        self._last_step = -1
        self._log_entries: list[str] = ["Event log initialized - watching for trades and agent decisions..."]
        self._debug_entries: list[str] = []  # No longer used - debug content comes from log files
        self._max_entries = 100

        # Timer
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_log)  # type: ignore[arg-type]
        self._update_timer.start(250)

        self._update_log()

    def _on_debug_toggled(self, state: int) -> None:
        from PyQt6.QtGui import QPalette, QColor
        
        self._debug_enabled = bool(state)
        
        # Force palette colors again when toggling
        palette = self._debug_display.palette()
        if not self._debug_enabled:
            # Muted but still readable
            palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Text, QColor(136, 136, 136))
            self._debug_display.setPalette(palette)
            self._debug_display.setStyleSheet("""
                QTextEdit { 
                    background-color: rgb(255, 255, 255);
                    color: rgb(136, 136, 136);
                    border: 1px solid rgb(221, 221, 221);
                    padding: 4px;
                    font-family: 'Monaco', 'Courier New', monospace;
                    font-size: 10pt;
                }
            """)
        else:
            # Full contrast
            palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
            self._debug_display.setPalette(palette)
            self._debug_display.setStyleSheet("""
                QTextEdit { 
                    background-color: rgb(255, 255, 255);
                    color: rgb(0, 0, 0);
                    border: 2px solid rgb(51, 51, 51);
                    padding: 4px;
                    font-family: 'Monaco', 'Courier New', monospace;
                    font-size: 10pt;
                }
            """)
    
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
                            event_text = f"Step {trade_step}: TRADE Agent {seller} ⟷ Agent {buyer} | {give_type} ⟷ {take_type} | ΔU={format_delta(delta_u)}"
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
                        event_text = f"Step {step}: {format_agent_id(int(agent_id)) if str(agent_id).isdigit() else agent_id} pairs with {format_agent_id(int(partner_id)) if str(partner_id).isdigit() else partner_id} → {target_pos}"
                    else:
                        event_text = f"Step {step}: {format_agent_id(int(agent_id)) if str(agent_id).isdigit() else agent_id} targets {target_type} at {target_pos}"
                    
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
        # Display content from centralized debug log files
        if self._debug_enabled:
            try:
                from ..debug_logger import get_gui_logger
                
                # Get the current log file path
                logger = get_gui_logger()
                log_path = logger.get_current_log_path()
                
                if log_path is not None and log_path.exists():
                    # Read the latest log content
                    with open(log_path, 'r', encoding='utf-8') as f:
                        log_content = f.read()
                    
                    # Split into lines and take the last N entries (skip header)
                    lines = log_content.split('\n')
                    # Skip the header lines (first 4 lines: title, timestamp, separator, blank line)
                    content_lines = [line for line in lines[4:] if line.strip()]
                    
                    # Keep only the most recent entries
                    if len(content_lines) > self._max_entries:
                        content_lines = content_lines[-self._max_entries:]
                    
                    # Update the debug display with the log file content
                    dbg_text = '\n'.join(content_lines)
                    self._debug_display.setPlainText(dbg_text)
                    
                    # Auto-scroll to bottom to show latest entries
                    cur = self._debug_display.textCursor()
                    cur.movePosition(cur.MoveOperation.End)
                    self._debug_display.setTextCursor(cur)
                    self._debug_display.ensureCursorVisible()
                    
            except Exception as e:
                # Fallback to show error if log reading fails
                error_text = f"Debug log error: {str(e)}\nFallback: Reading from centralized log files..."
                self._debug_display.setPlainText(error_text)
        else:
            # Clear display when debug is disabled
            self._debug_display.setPlainText("Debug logging disabled (check 'show' to enable)")
            


__all__ = ["EventLogPanel"]