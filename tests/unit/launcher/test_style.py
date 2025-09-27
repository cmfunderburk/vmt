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


def test_configure_application_idempotent(app: QApplication) -> None:  # type: ignore[name-defined]
    # Ensure clean env state
    flag = PlatformStyler._APPLIED_FLAG_ENV  # type: ignore[attr-defined]
    if flag in os.environ:
        del os.environ[flag]

    # Pre-condition: stylesheet should be empty or something unrelated
    initial_stylesheet = app.styleSheet()

    PlatformStyler.configure_application(app)
    first_applied_stylesheet = app.styleSheet()

    # Basic sanity: stylesheet should now be non-empty and changed (if initial empty)
    assert len(first_applied_stylesheet.strip()) > 10
    if not initial_stylesheet:
        assert first_applied_stylesheet != initial_stylesheet

    # Env flag set
    assert os.environ.get(flag) == "1"

    # Second call should perform no mutation
    PlatformStyler.configure_application(app)
    second_applied_stylesheet = app.styleSheet()
    assert second_applied_stylesheet == first_applied_stylesheet, "Stylesheet changed on second application (not idempotent)"
