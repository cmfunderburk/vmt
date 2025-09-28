"""Programmatic test execution API.

Replaces subprocess-based test launching with direct framework component
instantiation, eliminating hardcoded filename mappings and Python startup overhead.
"""

from __future__ import annotations

import traceback
from typing import Optional, Dict, Any, TYPE_CHECKING

try:
    from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
    _qt_available = True
except ImportError:  # pragma: no cover
    # Fallback types for testing without PyQt6
    QMainWindow = QVBoxLayout = QWidget = object  # type: ignore[misc, assignment]
    _qt_available = False

from .framework.test_configs import TestConfiguration, ALL_TEST_CONFIGS

if TYPE_CHECKING:  # pragma: no cover
    from econsim.simulation.world import Simulation


class TestRunner:
    """Executes tests programmatically without subprocess.
    
    Provides direct framework test execution using TestConfiguration registry
    and SimulationFactory, eliminating brittle filename mappings.
    """
    
    def __init__(self):
        """Initialize test runner and validate framework availability."""
        self.current_test_window = None  # type: ignore[assignment]
        self._last_error: Optional[str] = None
        self._validate_framework()
    
    def _validate_framework(self) -> None:
        """Ensure framework components are available."""
        if not ALL_TEST_CONFIGS:
            raise RuntimeError("No test configurations available in registry")
        
        if not _qt_available:
            raise RuntimeError("PyQt6 not available for GUI components")
        
        # Validate that we can import core framework components
        try:
            from .framework.base_test import StandardPhaseTest
            from .framework.simulation_factory import SimulationFactory
        except ImportError as e:
            raise RuntimeError(f"Framework components not available: {e}")
    
    def run_by_id(self, test_id: int, mode: str = "framework") -> None:
        """Run test by ID using registry lookup.
        
        Args:
            test_id: Test configuration ID (1-7)
            mode: Execution mode - only "framework" supported
            
        Raises:
            ValueError: If test_id not found or mode not supported
            RuntimeError: If test execution fails
        """
        if mode != "framework":
            raise ValueError(f"Only 'framework' mode supported, got: {mode}")
        
        config = self._get_config_by_id(test_id)
        if not config:
            raise ValueError(f"Test ID {test_id} not found in registry")
        
        self.run_config(config)
    
    def run_config(self, config: TestConfiguration) -> None:
        """Run test configuration programmatically.
        
        Args:
            config: TestConfiguration object to execute
            
        Raises:
            RuntimeError: If test execution fails
        """
        try:
            self._last_error = None
            self._run_framework_test(config)
        except Exception as e:
            error_msg = f"Failed to launch test {config.id} ({config.name}): {str(e)}"
            self._last_error = error_msg
            raise RuntimeError(error_msg) from e
    
    def _get_config_by_id(self, test_id: int) -> Optional[TestConfiguration]:
        """Get configuration by ID from registry.
        
        Args:
            test_id: Test configuration ID to look up
            
        Returns:
            TestConfiguration object or None if not found
        """
        return ALL_TEST_CONFIGS.get(test_id)
    
    def _run_framework_test(self, config: TestConfiguration) -> None:
        """Execute framework test with full StandardPhaseTest UI.
        
        Creates the complete test window using StandardPhaseTest framework,
        matching the original subprocess test experience with all controls.
        
        Args:
            config: TestConfiguration to execute
            
        Raises:
            RuntimeError: If test creation or GUI setup fails
        """
        try:
            # Import StandardPhaseTest framework (validated in __init__)
            from .framework.base_test import StandardPhaseTest
            
            # Create test window using StandardPhaseTest framework
            # This gives us the full UI with controls, phase management, etc.
            test_window = StandardPhaseTest(config)
            
            # Configure window properties
            test_window.setWindowTitle(f"VMT Test {config.id}: {config.name}")  # type: ignore[attr-defined]
            test_window.setGeometry(100, 100, 1200, 700)  # type: ignore[attr-defined]
            
            # Store reference to prevent garbage collection
            self.current_test_window = test_window  # type: ignore[assignment]
            
            # Show window - StandardPhaseTest handles simulation start
            test_window.show()  # type: ignore[attr-defined]
            
        except ImportError as e:
            raise RuntimeError(f"StandardPhaseTest framework import failed: {e}")
        except Exception as e:
            # Capture full traceback for debugging
            tb_str = traceback.format_exc()
            print(f"Framework test execution error:\n{tb_str}")
            raise RuntimeError(f"StandardPhaseTest creation failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current runner status for GUI display.
        
        Returns:
            Dictionary with runner status information
        """
        return {
            "available_tests": len(ALL_TEST_CONFIGS),
            "test_ids": list(ALL_TEST_CONFIGS.keys()),
            "current_test": self.current_test_window is not None,
            "current_test_title": (
                self.current_test_window.windowTitle()  # type: ignore[attr-defined]
                if self.current_test_window else None
            ),
            "framework_available": self._check_framework_available(),
            "qt_available": _qt_available,
            "last_error": self._last_error,
        }
    
    def _check_framework_available(self) -> bool:
        """Check if framework components are working.
        
        Returns:
            True if all required components can be imported
        """
        try:
            from .framework.base_test import StandardPhaseTest
            from .framework.simulation_factory import SimulationFactory
            # Also check that we have test configs
            return len(ALL_TEST_CONFIGS) > 0
        except ImportError:
            return False
    
    def close_current_test(self) -> bool:
        """Close currently running test window if any.
        
        Returns:
            True if a window was closed, False if no window was open
        """
        if self.current_test_window:
            try:
                self.current_test_window.close()  # type: ignore[attr-defined]
                self.current_test_window = None
                return True
            except Exception as e:
                self._last_error = f"Error closing test window: {e}"
                return False
        return False
    
    def get_available_tests(self) -> Dict[int, str]:
        """Get mapping of available test IDs to names.
        
        Returns:
            Dictionary mapping test IDs to test names
        """
        return {
            test_id: config.name 
            for test_id, config in ALL_TEST_CONFIGS.items()
        }


def create_test_runner() -> TestRunner:
    """Factory function to create and validate TestRunner.
    
    Returns:
        Initialized TestRunner instance
        
    Raises:
        RuntimeError: If framework validation fails
    """
    return TestRunner()