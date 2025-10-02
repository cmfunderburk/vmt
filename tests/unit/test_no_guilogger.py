"""Test ensuring GUILogger has been completely removed.

This test enforces that the legacy GUILogger module cannot be imported,
ensuring the elimination process is complete and preventing regression.
"""
import importlib
import pytest


def test_guilogger_import_fails():
    """Test that attempting to import GUILogger raises ModuleNotFoundError."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module('econsim.gui.debug_logger')


def test_legacy_adapter_import_fails():
    """Test that attempting to import LegacyLoggerAdapter raises ModuleNotFoundError."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module('econsim.observability.legacy_adapter')


def test_get_gui_logger_unavailable():
    """Test that get_gui_logger function is no longer available."""
    with pytest.raises((ModuleNotFoundError, ImportError, AttributeError)):
        from econsim.gui.debug_logger import get_gui_logger
        get_gui_logger()