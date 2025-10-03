"""Platform styling utilities.

Extracted from monolithic `enhanced_test_launcher_v2.py` (Step 2, Part 1 plan).
Provides a centralized facade to configure application styling in a
deterministic and idempotent manner across macOS, Windows, and Linux.
"""
from __future__ import annotations

from typing import Any

try:  # Import lazily so non-GUI unit tests can still import module stubs.
    from PyQt6.QtWidgets import QApplication  # type: ignore
    from PyQt6.QtCore import Qt  # type: ignore
except Exception:  # pragma: no cover - fallback for headless environments without PyQt
    QApplication = Any  # type: ignore
    Qt = Any  # type: ignore


class PlatformStyler:
    """Central styling facade (idempotent).

    Public entrypoints:
    - configure_application(app): apply style + stylesheet
    - base_stylesheet(): returns computed stylesheet for current platform
    - apply_post_init_fixes(app): hook for late adjustments (currently none)
    - get_status_area_style(): common status area styling
    - get_header_style(): common header styling
    """

    # Common color constants - Dark mode
    BACKGROUND_COLOR = "#2b2b2b"
    HEADER_BACKGROUND = "#1e1e1e"
    HEADER_TEXT_COLOR = "#ffffff"
    
    _APPLIED_FLAG_ENV = "ECONSIM_LAUNCHER_STYLE_APPLIED"

    @staticmethod
    def configure_application(app: Any) -> None:  # pragma: no cover - GUI side-effect
        import os, sys
        # Idempotency guard
        if os.environ.get(PlatformStyler._APPLIED_FLAG_ENV) == "1":
            return

        if sys.platform == "darwin":
            os.environ['QT_MAC_WANTS_LAYER'] = '1'
            app.setStyle('Fusion')
        elif sys.platform == "win32":
            try:
                from PyQt6.QtCore import Qt  # type: ignore
                app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
                app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
            except Exception:  # pragma: no cover
                pass
            app.setStyle('Fusion')
        else:
            # Linux / Other
            app.setStyle('Fusion')

        stylesheet = PlatformStyler.base_stylesheet()
        if stylesheet:
            app.setStyleSheet(stylesheet)
        os.environ[PlatformStyler._APPLIED_FLAG_ENV] = "1"

    @staticmethod
    def base_stylesheet() -> str:
        import sys
        if sys.platform == "darwin":
            return PlatformStyler._mac_stylesheet()
        if sys.platform == "win32":
            return PlatformStyler._windows_stylesheet()
        return PlatformStyler._linux_stylesheet()

    @staticmethod
    def apply_post_init_fixes(app: Any) -> None:  # pragma: no cover - placeholder for future
        # Reserved for future dark-mode or DPI adjustments after widgets shown.
        return None
    
    @staticmethod
    def get_status_area_style() -> str:
        """Get standardized status area styling."""
        return f"background-color: {PlatformStyler.BACKGROUND_COLOR};"
    
    @staticmethod
    def get_header_style() -> str:
        """Get standardized header styling."""
        return f"""
            QLabel {{
                background-color: {PlatformStyler.HEADER_BACKGROUND};
                padding: 12px;
                border-radius: 6px;
                color: {PlatformStyler.HEADER_TEXT_COLOR};
                margin-bottom: 10px;
            }}
        """

    # --- Internal stylesheet builders (kept separate for testability) -------
    @staticmethod
    def _mac_stylesheet() -> str:
        return (
            """
            QMainWindow, QWidget, QDialog { background-color: #2b2b2b; color: #ffffff; border: 1px solid #555555; }
            QMainWindow { border: 2px solid #555555; background-color: #2b2b2b; }
            QTextEdit, QPlainTextEdit { background-color:#1e1e1e; color:#ffffff; font-family:'Monaco','Menlo','Courier New','DejaVu Sans Mono',monospace; font-size:11pt; border:1px solid #555555; selection-background-color:#0078d4; selection-color:#ffffff; }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background-color:#1e1e1e !important; color:#ffffff !important; border:1px solid #555555 !important; padding:4px; }
            QFrame, QGroupBox, QScrollArea, QWidget { background-color:#2b2b2b !important; color:#ffffff !important; border:1px solid #555555 !important; }
            QLabel, QTextEdit, QPlainTextEdit { background-color:#1e1e1e !important; color:#ffffff !important; border:1px solid #555555 !important; }
            * { background-color:#2b2b2b !important; color:#ffffff !important; }
            QLabel { color:#ffffff; font-size:11pt; }
            QPushButton { background-color:#404040; color:#ffffff; border:1px solid #666666; padding:8px 16px; font-size:11pt; font-weight:bold; border-radius:4px; }
            QPushButton:hover { background-color:#4a4a4a; border-color:#888888; }
            QPushButton:pressed { background-color:#353535; }
            QPushButton:disabled { background-color:#2a2a2a; color:#666666; border-color:#444444; }
            QFrame { background-color:#1e1e1e; border:1px solid #555555; border-radius:6px; }
            QCheckBox { color:#ffffff; font-size:11pt; font-weight:bold; spacing:8px; }
            QCheckBox::indicator { width:16px; height:16px; background-color:#1e1e1e; border:1px solid #666666; }
            QCheckBox::indicator:checked { background-color:#0078d4; border-color:#0078d4; }
            QScrollArea { background-color:#2b2b2b; border:none; }
            QTabWidget::pane { border:1px solid #555555; background-color:#1e1e1e; }
            QTabBar::tab { background-color:#404040; color:#ffffff; padding:8px 16px; margin-right:2px; border-top-left-radius:3px; border-top-right-radius:3px; }
            QTabBar::tab:selected { background-color:#1e1e1e; border-bottom:none; }
            QTabBar::tab:hover { background-color:#4a4a4a; }
            """.strip()
        )

    @staticmethod
    def _windows_stylesheet() -> str:
        return (
            """
            QMainWindow { background-color:#2b2b2b; color:#ffffff; border: 2px solid #555555; }
            QPushButton { background-color:#404040; color:#ffffff; font-weight:bold; padding:8px 16px; border-radius:4px; border:1px solid #666666; }
            QPushButton:hover { background-color:#4a4a4a; border-color:#888888; }
            QCheckBox { color:#ffffff; font-weight:bold; spacing:8px; }
            QTextEdit, QPlainTextEdit { background-color:#1e1e1e; color:#ffffff; font-family:'Monaco','Menlo','Consolas','Courier New',monospace; font-size:10pt; border:1px solid #555555; }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background-color:#1e1e1e !important; color:#ffffff !important; border:1px solid #555555 !important; padding:4px; }
            QFrame, QGroupBox, QScrollArea, QWidget { background-color:#2b2b2b !important; color:#ffffff !important; border:1px solid #555555 !important; }
            QLabel, QTextEdit, QPlainTextEdit { background-color:#1e1e1e !important; color:#ffffff !important; border:1px solid #555555 !important; }
            * { background-color:#2b2b2b !important; color:#ffffff !important; }
            QLabel { color:#ffffff; }
            """.strip()
        )

    @staticmethod
    def _linux_stylesheet() -> str:
        return (
            """
            QMainWindow { background-color:#2b2b2b; color:#ffffff; border: 2px solid #555555; }
            QPushButton { background-color:#404040; color:#ffffff; font-weight:bold; padding:8px 16px; border-radius:4px; border:1px solid #666666; }
            QPushButton:hover { background-color:#4a4a4a; border-color:#888888; }
            QCheckBox { color:#ffffff; font-weight:bold; spacing:8px; }
            QLabel { color:#ffffff; }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background-color:#1e1e1e !important; color:#ffffff !important; border:1px solid #555555 !important; padding:4px; }
            QFrame, QGroupBox, QScrollArea, QWidget { background-color:#2b2b2b !important; color:#ffffff !important; border:1px solid #555555 !important; }
            QLabel, QTextEdit, QPlainTextEdit { background-color:#1e1e1e !important; color:#ffffff !important; border:1px solid #555555 !important; }
            * { background-color:#2b2b2b !important; color:#ffffff !important; }
            """.strip()
        )
