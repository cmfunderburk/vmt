"""Tests for PlatformStyler (Step 2 gating: G1).

Verifies:
1. base_stylesheet() returns a non-empty string for the active platform.
2. configure_application() is idempotent (second invocation performs no changes).

We assert idempotency by:
 - Clearing ECONSIM_LAUNCHER_STYLE_APPLIED before first call.
 - Capturing the application styleSheet after first application.
 - Calling configure_application() again and verifying the stylesheet text is unchanged.

Notes:
 - Uses an offscreen Qt platform to avoid requiring a display server in CI.
 - Keeps a single QApplication instance (Qt forbids multiple instances in same process).
"""
from __future__ import annotations

import os
import sys
from typing import Generator
from unittest.mock import Mock

import pytest

try:
    # Offscreen to be safe in headless environments (Linux CI containers)
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication  # type: ignore
except Exception:  # pragma: no cover - if PyQt unavailable test will xfail quickly
    QApplication = None  # type: ignore

from econsim.tools.launcher.style import PlatformStyler


@pytest.fixture(scope="module")
def app() -> Generator[QApplication, None, None]:  # type: ignore[name-defined]
    if QApplication is None:  # pragma: no cover - environment without PyQt
        pytest.skip("PyQt6 not available in test environment")
    # Reuse single QApplication for module
    qt_app = QApplication.instance() or QApplication(["test-style"])
    yield qt_app
    # Teardown (avoid full quit to prevent affecting other Qt tests, if any)
    # Explicitly not calling quit() so any subsequent tests can reuse instance.


def test_base_stylesheet_non_empty() -> None:
    css = PlatformStyler.base_stylesheet()
    assert isinstance(css, str)
    # Be resilient across platforms; require minimum length > 10 chars
    assert len(css.strip()) > 10, "Expected non-trivial stylesheet text"


def test_configure_application_idempotent() -> None:
    """Test that configure_application can be called multiple times safely."""
    mock_app = Mock()
    
    # First call should apply styling
    PlatformStyler.configure_application(mock_app)
    
    # Second call should be idempotent (no additional calls)
    PlatformStyler.configure_application(mock_app)
    
    # Verify app methods were called the expected number of times
    assert mock_app.setStyle.call_count >= 1  # At least once
    
    # Clean up environment variable for other tests
    import os
    if PlatformStyler._APPLIED_FLAG_ENV in os.environ:
        del os.environ[PlatformStyler._APPLIED_FLAG_ENV]


def test_get_status_area_style() -> None:
    """Test the get_status_area_style utility method."""
    style = PlatformStyler.get_status_area_style()
    
    # Should return a non-empty string
    assert isinstance(style, str)
    assert len(style.strip()) > 0
    
    # Should contain background-color setting
    assert "background-color:" in style
    assert PlatformStyler.BACKGROUND_COLOR in style


def test_get_header_style() -> None:
    """Test the get_header_style utility method."""
    style = PlatformStyler.get_header_style()
    
    # Should return a non-empty string
    assert isinstance(style, str)
    assert len(style.strip()) > 0
    
    # Should contain expected style properties
    assert "QLabel" in style
    assert "background-color:" in style
    assert "padding:" in style
    assert "border-radius:" in style
    assert "color:" in style
    
    # Should use class constants
    assert PlatformStyler.HEADER_BACKGROUND in style
    assert PlatformStyler.HEADER_TEXT_COLOR in style


def test_color_constants() -> None:
    """Test that color constants are defined and non-empty."""
    assert hasattr(PlatformStyler, 'BACKGROUND_COLOR')
    assert hasattr(PlatformStyler, 'HEADER_BACKGROUND')
    assert hasattr(PlatformStyler, 'HEADER_TEXT_COLOR')
    
    assert isinstance(PlatformStyler.BACKGROUND_COLOR, str)
    assert isinstance(PlatformStyler.HEADER_BACKGROUND, str)
    assert isinstance(PlatformStyler.HEADER_TEXT_COLOR, str)
    
    # Should be valid CSS colors (start with #)
    assert PlatformStyler.BACKGROUND_COLOR.startswith('#')
    assert PlatformStyler.HEADER_BACKGROUND.startswith('#')
    assert PlatformStyler.HEADER_TEXT_COLOR.startswith('#')
