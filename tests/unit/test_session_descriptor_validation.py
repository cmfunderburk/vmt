"""Validation tests for StartMenuPage input constraints (feature-flagged GUI).

Skips when ECONSIM_NEW_GUI not enabled to avoid affecting legacy pipeline.
"""
from __future__ import annotations

import os
import pytest

from PyQt6.QtWidgets import QApplication

pytestmark = pytest.mark.skipif(os.environ.get("ECONSIM_NEW_GUI") != "1", reason="New GUI flag not enabled")


@pytest.fixture(scope="module")
def app():  # pragma: no cover - Qt harness
    return QApplication.instance() or QApplication([])


def test_validation_success(app):
    from econsim.gui.start_menu import StartMenuPage  # local import under flag

    captured = {}
    page = StartMenuPage(lambda sel: captured.setdefault("ok", sel))
    # Should not raise for bounds defaults
    page._validate_inputs(12, 12, 4, 0.25)  # type: ignore[attr-defined]


def test_validation_grid_bounds(app):
    from econsim.gui.start_menu import StartMenuPage

    page = StartMenuPage(lambda sel: None)
    with pytest.raises(ValueError):
        page._validate_inputs(2, 12, 4, 0.25)  # too small width
    with pytest.raises(ValueError):
        page._validate_inputs(65, 12, 4, 0.25)  # too large width
    with pytest.raises(ValueError):
        page._validate_inputs(12, 2, 4, 0.25)  # too small height
    with pytest.raises(ValueError):
        page._validate_inputs(12, 70, 4, 0.25)  # too large height


def test_validation_agent_bounds(app):
    from econsim.gui.start_menu import StartMenuPage

    page = StartMenuPage(lambda sel: None)
    with pytest.raises(ValueError):
        page._validate_inputs(12, 12, 0, 0.25)  # too few agents
    with pytest.raises(ValueError):
        page._validate_inputs(12, 12, 65, 0.25)  # too many agents


def test_validation_density_bounds(app):
    from econsim.gui.start_menu import StartMenuPage

    page = StartMenuPage(lambda sel: None)
    with pytest.raises(ValueError):
        page._validate_inputs(12, 12, 4, -0.01)
    with pytest.raises(ValueError):
        page._validate_inputs(12, 12, 4, 1.01)

