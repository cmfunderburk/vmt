"""Application entry point for EconSim VMT.

Gate 1 Objective: Launch a PyQt6 window (no embedded pygame yet) to verify
basic event loop and packaging skeleton. Pygame integration will be added in
`gui/embedded_pygame.py` in a subsequent increment.
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QMainWindow

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
        
        # Comprehensive light theme stylesheet for dark mode compatibility
        app.setStyleSheet("""
            /* Main containers */
            QMainWindow, QWidget, QDialog {
                background-color: #f5f5f5;
                color: #1a1a1a;
            }
            
            /* Text areas and logs */
            QTextEdit, QPlainTextEdit {
                background-color: #ffffff;
                color: #000000;
                font-family: 'Monaco', 'Courier New', 'DejaVu Sans Mono', monospace;
                font-size: 11pt;
                border: 1px solid #cccccc;
                selection-background-color: #316AC5;
                selection-color: #ffffff;
            }
            
            /* Input fields */
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
                padding: 4px;
                font-size: 11pt;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666666;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #e8e8e8;
                color: #1a1a1a;
                border: 1px solid #999999;
                padding: 6px 12px;
                font-size: 11pt;
                border-radius: 3px;
            }
            
            QPushButton:hover {
                background-color: #d0d0d0;
                border-color: #666666;
            }
            
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
            
            QPushButton:disabled {
                background-color: #f0f0f0;
                color: #999999;
                border-color: #cccccc;
            }
            
            /* Group boxes */
            QGroupBox {
                font-weight: bold;
                font-size: 12pt;
                color: #1a1a1a;
                border: 2px solid #cccccc;
                border-radius: 3px;
                margin-top: 10px;
                padding-top: 5px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #f5f5f5;
            }
            
            /* Labels */
            QLabel {
                color: #1a1a1a;
                font-size: 11pt;
            }
            
            /* Checkboxes */
            QCheckBox {
                color: #1a1a1a;
                font-size: 11pt;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                background-color: #ffffff;
                border: 1px solid #999999;
            }
            
            QCheckBox::indicator:checked {
                background-color: #316AC5;
                border-color: #316AC5;
            }
            
            /* Sliders */
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 6px;
                background: #ffffff;
                margin: 2px 0;
            }
            
            QSlider::handle:horizontal {
                background: #316AC5;
                border: 1px solid #316AC5;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            
            /* Menu and menu bar */
            QMenuBar {
                background-color: #f5f5f5;
                color: #1a1a1a;
                border-bottom: 1px solid #cccccc;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            
            QMenuBar::item:selected {
                background-color: #316AC5;
                color: #ffffff;
            }
            
            QMenu {
                background-color: #ffffff;
                color: #1a1a1a;
                border: 1px solid #cccccc;
            }
            
            QMenu::item:selected {
                background-color: #316AC5;
                color: #ffffff;
            }
            
            /* Status bar */
            QStatusBar {
                background-color: #f0f0f0;
                color: #1a1a1a;
                border-top: 1px solid #cccccc;
            }
        """)
    
    elif sys.platform == "win32":
        # Windows-specific fixes
        # Enable high-DPI support
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        
        # Use Fusion style for consistency (Windows native can have issues)
        app.setStyle('Fusion')
        
        # Lighter styling for Windows - mostly just ensure readability
        app.setStyleSheet("""
            QTextEdit, QPlainTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
            }
            
            QPushButton {
                padding: 4px 8px;
            }
        """)
    
    else:
        # Linux and other platforms - minimal styling
        app.setStyle('Fusion')


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
