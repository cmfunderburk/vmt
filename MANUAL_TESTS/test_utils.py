"""
Shared utilities for manual tests.
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import QTimer


def create_speed_control(parent, on_speed_changed_callback):
    """Create a speed control layout with dropdown and callback."""
    speed_layout = QHBoxLayout()
    speed_layout.addWidget(QLabel("Test Speed:"))
    
    speed_combo = QComboBox()
    speed_combo.addItems([
        "1 turn/second",
        "3 turns/second", 
        "10 turns/second",
        "20 turns/second",
        "Unlimited"
    ])
    speed_combo.setCurrentIndex(0)  # Default to 1 turn/second
    speed_combo.currentIndexChanged.connect(on_speed_changed_callback)
    
    speed_layout.addWidget(speed_combo)
    
    return speed_layout, speed_combo


def get_timer_interval(speed_index):
    """Get timer interval in milliseconds based on speed index."""
    speed_map = {
        0: 1000,    # 1 turn/second = 1000ms
        1: 333,     # 3 turns/second = 333ms  
        2: 100,     # 10 turns/second = 100ms
        3: 50,      # 20 turns/second = 50ms
        4: 16       # Unlimited = 16ms (~60 FPS)
    }
    return speed_map.get(speed_index, 1000)


def get_estimated_duration(speed_index, total_turns=900):
    """Get estimated test duration in seconds."""
    interval_ms = get_timer_interval(speed_index)
    return (total_turns * interval_ms) / 1000


def format_duration(seconds):
    """Format duration for display."""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"