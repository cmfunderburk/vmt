"""Application entry point for EconSim VMT.

Gate 1 Objective: Launch a PyQt6 window (no embedded pygame yet) to verify
basic event loop and packaging skeleton. Pygame integration will be added in
`gui/embedded_pygame.py` in a subsequent increment.
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt

from econsim.gui.embedded_pygame import EmbeddedPygameWidget
try:  # feature flag import (optional during transition)
    from econsim.gui.main_window import MainWindow, should_use_new_gui
except Exception:  # pragma: no cover - fallback if new GUI not present
    MainWindow = None  # type: ignore
    def should_use_new_gui() -> bool:  # type: ignore
        return False


def create_window() -> QMainWindow:
    # Feature flag path
    if should_use_new_gui():
        if MainWindow is None:  # defensive
            raise RuntimeError("New GUI requested but unavailable")
        return MainWindow()
    # Legacy bootstrap
    window = QMainWindow()
    window.setWindowTitle("EconSim – Gate 1 Bootstrap")
    widget = EmbeddedPygameWidget()
    window.setCentralWidget(widget)
    window.resize(640, 480)
    return window


def _apply_platform_styling(app: QApplication) -> None:
    """Apply platform-specific styling to fix dark mode and cross-platform issues."""
    import os
    import sys
    
    # macOS dark mode compatibility fixes
    if sys.platform == "darwin":
        # Better macOS rendering
        os.environ['QT_MAC_WANTS_LAYER'] = '1'
        
        # Force consistent cross-platform style instead of native macOS
        app.setStyle('Fusion')
        
        # Comprehensive dark theme stylesheet for all platforms
        app.setStyleSheet("""
            /* Main containers - force dark mode for all window elements */
            QMainWindow, QWidget, QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
            }
            
            /* Window frame styling */
            QMainWindow {
                border: 2px solid #555555;
                background-color: #2b2b2b;
            }
            
            /* Ensure all child widgets inherit dark mode */
            QMainWindow > QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            
            /* Text areas and logs */
            QTextEdit, QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Monaco', 'Courier New', 'DejaVu Sans Mono', monospace;
                font-size: 11pt;
                border: 1px solid #555555;
                selection-background-color: #0078d4;
                selection-color: #ffffff;
            }
            
            /* Input fields */
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 4px;
                font-size: 11pt;
            }
            
            /* Slider styling */
            QSlider::groove:horizontal {
                border: 1px solid #666666;
                height: 6px;
                background: #1e1e1e;
                margin: 2px 0;
            }
            
            QSlider::handle:horizontal {
                background: #0078d4;
                border: 1px solid #0078d4;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            
            QSlider::sub-page:horizontal {
                background: #0078d4;
            }
            
            QSlider::add-page:horizontal {
                background: #1e1e1e;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #cccccc;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #666666;
                padding: 6px 12px;
                font-size: 11pt;
                border-radius: 3px;
            }
            
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #888888;
            }
            
            QPushButton:pressed {
                background-color: #353535;
            }
            
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
                border-color: #444444;
            }
            
            /* Group boxes */
            QGroupBox {
                font-weight: bold;
                font-size: 12pt;
                color: #ffffff;
                border: 2px solid #555555;
                border-radius: 3px;
                margin-top: 10px;
                padding-top: 5px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #2b2b2b;
            }
            
            /* Labels */
            QLabel {
                color: #ffffff;
                font-size: 11pt;
            }
            
            /* Checkboxes */
            QCheckBox {
                color: #ffffff;
                font-size: 11pt;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                background-color: #1e1e1e;
                border: 1px solid #666666;
            }
            
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #0078d4;
            }
            
            /* Sliders */
            QSlider::groove:horizontal {
                border: 1px solid #666666;
                height: 6px;
                background: #1e1e1e;
                margin: 2px 0;
            }
            
            QSlider::handle:horizontal {
                background: #0078d4;
                border: 1px solid #0078d4;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            
            /* Menu and menu bar */
            QMenuBar {
                background-color: #2b2b2b;
                color: #ffffff;
                border-bottom: 1px solid #555555;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            
            QMenuBar::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            
            QMenu {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
            }
            
            QMenu::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            
            /* Status bar */
            QStatusBar {
                background-color: #1e1e1e;
                color: #ffffff;
                border-top: 1px solid #555555;
            }
            
            /* Content boxes and frames - force dark mode */
            QFrame, QGroupBox, QScrollArea, QWidget {
                background-color: #2b2b2b !important;
                color: #ffffff !important;
                border: 1px solid #555555 !important;
            }
            
            /* Force all text elements to dark mode */
            QLabel, QTextEdit, QPlainTextEdit {
                background-color: #1e1e1e !important;
                color: #ffffff !important;
                border: 1px solid #555555 !important;
            }
            
            /* Override any external component styling */
            QLabel[objectName*="status"], QLabel[objectName*="info"], QLabel[objectName*="preview"], 
            QLabel[objectName*="validation"], QLabel[objectName*="config"] {
                background-color: #1e1e1e !important;
                color: #ffffff !important;
                border: 1px solid #555555 !important;
                padding: 8px !important;
                border-radius: 4px !important;
            }
            
            QGroupBox::title {
                background-color: #2b2b2b;
                color: #ffffff;
                padding: 0 8px;
            }
            
            /* Validation and status boxes */
            QLabel[class="validation"], QLabel[class="status"] {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 4px 8px;
                border-radius: 3px;
            }
            
            /* Success/error indicators */
            QLabel[class="success"] {
                background-color: #1a3d1a !important;
                color: #81c784 !important;
                border: 1px solid #4caf50 !important;
            }
            
            QLabel[class="error"] {
                background-color: #3d1a1a !important;
                color: #ff6b6b !important;
                border: 1px solid #d32f2f !important;
            }
            
            /* Force dark mode for all display elements */
            QLabel[text*="Expected"], QLabel[text*="Configuration"], QLabel[text*="Information"],
            QLabel[text*="Grid"], QLabel[text*="Agents"], QLabel[text*="Resources"] {
                background-color: #1e1e1e !important;
                color: #ffffff !important;
                border: 1px solid #555555 !important;
                padding: 8px !important;
                border-radius: 4px !important;
            }
            
            /* Override any white backgrounds from external components */
            * {
                background-color: #2b2b2b !important;
                color: #ffffff !important;
            }
            
            /* Specific overrides for common display patterns */
            QLabel[text*="Expected Behavior"], QLabel[text*="Configuration Valid"] {
                background-color: #1e1e1e !important;
                color: #ffffff !important;
                border: 1px solid #555555 !important;
                padding: 8px !important;
            }
        """)
    
    elif sys.platform == "win32":
        # Windows-specific fixes
        # Enable high-DPI support
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        
        # Use Fusion style for consistency (Windows native can have issues)
        app.setStyle('Fusion')
        
        # Dark theme styling for Windows
        app.setStyleSheet("""
            QMainWindow, QWidget, QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
            }
            
            /* Window frame styling for Windows */
            QMainWindow {
                border: 2px solid #555555;
                background-color: #2b2b2b;
            }
            
            QTextEdit, QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
                border: 1px solid #555555;
            }
            
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #666666;
                padding: 4px 8px;
                border-radius: 3px;
            }
            
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            
            QLabel {
                color: #ffffff;
            }
            
            /* Input fields for Windows */
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 4px;
            }
            
            /* Content boxes for Windows - force dark mode */
            QFrame, QGroupBox, QScrollArea, QWidget {
                background-color: #2b2b2b !important;
                color: #ffffff !important;
                border: 1px solid #555555 !important;
            }
            
            /* Force all text elements to dark mode */
            QLabel, QTextEdit, QPlainTextEdit {
                background-color: #1e1e1e !important;
                color: #ffffff !important;
                border: 1px solid #555555 !important;
            }
            
            /* Override any white backgrounds from external components */
            * {
                background-color: #2b2b2b !important;
                color: #ffffff !important;
            }
        """)
    
    else:
        # Linux and other platforms - dark theme styling
        app.setStyle('Fusion')
        
        # Dark theme styling for Linux
        app.setStyleSheet("""
            QMainWindow, QWidget, QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
            }
            
            /* Window frame styling for Linux */
            QMainWindow {
                border: 2px solid #555555;
                background-color: #2b2b2b;
            }
            
            QTextEdit, QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
            }
            
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #666666;
                border-radius: 3px;
            }
            
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            
            QLabel {
                color: #ffffff;
            }
            
            /* Input fields for Linux */
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 4px;
            }
            
            /* Content boxes for Linux - force dark mode */
            QFrame, QGroupBox, QScrollArea, QWidget {
                background-color: #2b2b2b !important;
                color: #ffffff !important;
                border: 1px solid #555555 !important;
            }
            
            /* Force all text elements to dark mode */
            QLabel, QTextEdit, QPlainTextEdit {
                background-color: #1e1e1e !important;
                color: #ffffff !important;
                border: 1px solid #555555 !important;
            }
            
            /* Override any white backgrounds from external components */
            * {
                background-color: #2b2b2b !important;
                color: #ffffff !important;
            }
        """)


def main() -> int:
    # Configure environment for better cross-platform compatibility
    import os
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Apply platform-specific styling fixes
    if isinstance(app, QApplication):
        _apply_platform_styling(app)
    
    window = create_window()
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
