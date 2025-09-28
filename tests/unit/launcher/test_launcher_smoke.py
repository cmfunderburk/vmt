"""Headless smoke test for early launcher public API.

Gate G15 (Part 2): Ensures that constructing the registry and invoking runner.main
in headless mode does not raise exceptions and returns 0.

This is intentionally minimal to avoid coupling to forthcoming UI components.
"""
from __future__ import annotations

import os
import sys

import pytest

from econsim.tools.launcher import runner


@pytest.mark.smoke
def test_runner_main_headless_basic():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    # Ensure headless flag works even if no tests requested
    rc = runner.main(["--headless", "--list-tests"])  # should print list then exit 0
    assert rc == 0


@pytest.mark.smoke
def test_runner_json_registry():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    rc = runner.main(["--headless", "--json-registry"])  # prints JSON test list
    assert rc == 0
