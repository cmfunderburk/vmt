"""Tabs container package for Phase 3 extraction.

Provides `LauncherTabs` integrating gallery, comparison panel, and history view.
Gate G13: Modular tabs with clean separation of concerns.
"""
from __future__ import annotations

from .base_tab import AbstractTab  # noqa: F401
from .custom_tests_tab import CustomTestsTab  # noqa: F401
from .launcher_tabs import LauncherTabs, ComparisonTab, HistoryTab  # noqa: F401
from .manager import TabManager  # noqa: F401
from .config_editor_tab import ConfigEditorTab  # noqa: F401
from .batch_runner_tab import BatchRunnerTab  # noqa: F401
from .bookmarks_tab import BookmarksTab  # noqa: F401
from .gallery_tab import GalleryTab  # noqa: F401

__all__ = [
    "AbstractTab", "CustomTestsTab", "LauncherTabs", "ComparisonTab", "HistoryTab", 
    "TabManager", "ConfigEditorTab", "BatchRunnerTab", "BookmarksTab", "GalleryTab"
]
