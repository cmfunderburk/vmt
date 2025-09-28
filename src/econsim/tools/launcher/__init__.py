"""VMT Launcher modular package (Phase 1 scaffold).

This package is under active refactor (September 2025) extracting the monolithic
`MANUAL_TESTS/enhanced_test_launcher_v2.py` into testable, responsibility-focused
modules. Public APIs in this early scaffold are *provisional* and may change
until Part 1 (utilities + core business logic) is stabilized.

Do NOT import these modules from simulation core paths; they are launcher-only.
"""

from .style import PlatformStyler  # noqa: F401
from .data import DataLocationResolver  # noqa: F401
from .discovery import CustomTestDiscovery  # noqa: F401
from .types import (
    CustomTestInfo,
    TestConfiguration,
    ExecutionResult,
    ExecutionRecord,
    RegistryValidationResult,
)  # noqa: F401
from .registry import TestRegistry  # noqa: F401
from .comparison import ComparisonController  # noqa: F401
from .executor import TestExecutor  # noqa: F401
from .cards import build_card_models, TestCard, TestCardModel, CustomTestCardWidget, TestCardWidget  # noqa: F401
from .gallery import TestGallery  # noqa: F401
from .tabs import LauncherTabs, AbstractTab, CustomTestsTab  # noqa: F401
from .widgets import TestGalleryWidget  # noqa: F401
from .app_window import LauncherWindow, create_launcher_window, VMTLauncherWindow  # noqa: F401

__all__ = [
    "PlatformStyler",
    "DataLocationResolver", 
    "CustomTestDiscovery",
    "CustomTestInfo",
    "TestConfiguration",
    "ExecutionResult",
    "ExecutionRecord",
    "RegistryValidationResult",
    "TestRegistry",
    "ComparisonController", 
    "TestExecutor",
    "build_card_models",
    "TestCard",
    "TestCardModel",
    "TestGallery",
    "LauncherTabs",
    "AbstractTab",
    "CustomTestsTab",
    "TestGalleryWidget",
    "LauncherWindow",
    "create_launcher_window",
    "VMTLauncherWindow",
]

__version_placeholder__ = "0.1.0-dev-scaffold"
