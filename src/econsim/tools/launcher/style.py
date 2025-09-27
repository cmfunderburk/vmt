"""Platform styling utilities.

Extracted from monolithic `enhanced_test_launcher_v2.py` (Step 2, Part 1 plan).
Provides a centralized facade to configure application styling in a
deterministic and idempotent manner across macOS, Windows, and Linux.
"""
from __future__ import annotations

from typing import Any

try:  # Import lazily so non-GUI unit tests can still import module stubs.
    from PyQt6.QtWidgets import QApplication  # type: ignore
except Exception:  # pragma: no cover - fallback for headless environments without PyQt
    QApplication = Any  # type: ignore


class PlatformStyler:
    """Central styling facade (idempotent).

    Public entrypoints:
    - configure_application(app): apply style + stylesheet
    - base_stylesheet(): returns computed stylesheet for current platform
    - apply_post_init_fixes(app): hook for late adjustments (currently none)
    """

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

    # --- Internal stylesheet builders (kept separate for testability) -------
    @staticmethod
    def _mac_stylesheet() -> str:
        return (
            """
            QMainWindow, QWidget, QDialog { background-color: #f8f9fa; color: #1a1a1a; }
            QTextEdit, QPlainTextEdit { background-color:#ffffff; color:#000000; font-family:'Monaco','Courier New','DejaVu Sans Mono',monospace; font-size:11pt; border:1px solid #cccccc; selection-background-color:#316AC5; selection-color:#ffffff; }
            QLabel { color:#1a1a1a; font-size:11pt; }
            QPushButton { background-color:#e8e8e8; color:#1a1a1a; border:1px solid #999999; padding:8px 16px; font-size:11pt; font-weight:bold; border-radius:4px; }
            QPushButton:hover { background-color:#d0d0d0; border-color:#007bff; }
            QPushButton:pressed { background-color:#c0c0c0; }
            QPushButton:disabled { background-color:#f0f0f0; color:#999999; border-color:#cccccc; }
            QFrame { background-color:#ffffff; border:1px solid #dddddd; border-radius:6px; }
            QCheckBox { color:#1a1a1a; font-size:11pt; font-weight:bold; spacing:8px; }
            QCheckBox::indicator { width:16px; height:16px; background-color:#ffffff; border:1px solid #999999; }
            QCheckBox::indicator:checked { background-color:#316AC5; border-color:#316AC5; }
            QScrollArea { background-color:#f8f9fa; border:none; }
            QTabWidget::pane { border:1px solid #cccccc; background-color:#ffffff; }
            QTabBar::tab { background-color:#e8e8e8; color:#1a1a1a; padding:8px 16px; margin-right:2px; border-top-left-radius:3px; border-top-right-radius:3px; }
            QTabBar::tab:selected { background-color:#ffffff; border-bottom:none; }
            QTabBar::tab:hover { background-color:#d0d0d0; }
            """.strip()
        )

    @staticmethod
    def _windows_stylesheet() -> str:
        return (
            """
            QMainWindow { background-color:#f8f9fa; }
            QPushButton { font-weight:bold; padding:8px 16px; border-radius:4px; border:1px solid #ddd; }
            QPushButton:hover { border-color:#007bff; }
            QCheckBox { font-weight:bold; spacing:8px; }
            QTextEdit, QPlainTextEdit { font-family:'Consolas','Courier New',monospace; font-size:10pt; }
            """.strip()
        )

    @staticmethod
    def _linux_stylesheet() -> str:
        return (
            """
            QMainWindow { background-color:#f8f9fa; }
            QPushButton { font-weight:bold; padding:8px 16px; border-radius:4px; border:1px solid #ddd; }
            QPushButton:hover { border-color:#007bff; }
            QCheckBox { font-weight:bold; spacing:8px; }
            """.strip()
        )
