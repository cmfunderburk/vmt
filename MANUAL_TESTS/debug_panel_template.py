# Debug Panel Template for Manual Tests
# This template shows the code additions needed to add debug log display
# to manual tests similar to test_1_baseline_simple.py

# 1. Add import at the top:
import os
from PyQt6.QtWidgets import QTextEdit

# 2. In the class constructor, add debug display widget to UI:
def __init__(self):
    # ... existing code ...
    
    # Add debug display
    self.debug_display = QTextEdit()
    self.debug_display.setReadOnly(True)
    self.debug_display.setMaximumWidth(300)
    self.debug_display.setFont(QFont("Consolas", 9))
    
    # Update main layout to use QHBoxLayout for debug panel + pygame viewport
    main_container = QWidget()
    main_layout = QHBoxLayout(main_container)
    main_layout.addWidget(self.debug_display)
    main_layout.addWidget(self.embedded_widget)  # or whatever the pygame widget is called
    
    # Update existing layout to use main_container instead of embedded_widget directly
    
    # Add debug timer
    self.debug_timer = QTimer()
    self.debug_timer.timeout.connect(self.update_debug_log)
    self.debug_timer.start(250)

# 3. Add debug log update method:
def update_debug_log(self):
    """Update debug log display with latest content from log files."""
    gui_logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gui_logs")
    
    if not os.path.exists(gui_logs_dir):
        return
    
    log_files = [f for f in os.listdir(gui_logs_dir) if f.endswith('.log')]
    if not log_files:
        return
    
    # Get the most recent log file
    latest_file = max(log_files, key=lambda f: os.path.getctime(os.path.join(gui_logs_dir, f)))
    log_path = os.path.join(gui_logs_dir, latest_file)
    
    try:
        with open(log_path, 'r') as f:
            content = f.read()
        
        # Update display and auto-scroll to bottom
        self.debug_display.setPlainText(content)
        cursor = self.debug_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.debug_display.setTextCursor(cursor)
    except (FileNotFoundError, OSError):
        pass  # Silently ignore file access issues

# 4. Ensure proper cleanup (add to closeEvent if exists):
def closeEvent(self, event):
    if hasattr(self, 'debug_timer'):
        self.debug_timer.stop()
    # ... existing closeEvent code ...
    super().closeEvent(event)