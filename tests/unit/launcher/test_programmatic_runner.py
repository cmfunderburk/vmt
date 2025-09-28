"""Test suite for programmatic TestRunner implementation.

Validates TestRunner API functionality, error handling, configuration lookup,
status monitoring, and health check capabilities introduced in Phase 6.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
from pathlib import Path

# Test imports with fallback handling
try:
    from src.econsim.tools.launcher.test_runner import TestRunner, create_test_runner
    from src.econsim.tools.launcher.framework.test_configs import ALL_TEST_CONFIGS
    _test_runner_available = True
except ImportError:
    TestRunner = None  # type: ignore
    create_test_runner = None  # type: ignore
    ALL_TEST_CONFIGS = {}  # type: ignore
    _test_runner_available = False


class TestProgrammaticRunner:
    """Test suite for TestRunner programmatic execution API."""
    
    @pytest.fixture
    def mock_qt_available(self):
        """Mock PyQt6 availability for testing."""
        with patch('src.econsim.tools.launcher.test_runner._qt_available', True):
            yield
    
    @pytest.fixture
    def mock_framework_components(self):
        """Mock framework components for testing."""
        # Create proper Mock objects with name attribute
        mock_config_1 = Mock()
        mock_config_1.id = 1
        mock_config_1.name = "Test Config 1"
        
        mock_config_2 = Mock()
        mock_config_2.id = 2
        mock_config_2.name = "Test Config 2"
        
        mock_config_3 = Mock()
        mock_config_3.id = 3
        mock_config_3.name = "Test Config 3"
        
        with patch('src.econsim.tools.launcher.test_runner.ALL_TEST_CONFIGS', {
            1: mock_config_1,
            2: mock_config_2,
            3: mock_config_3
        }):
            yield
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available")
    def test_runner_initialization(self, mock_qt_available, mock_framework_components):
        """Test runner initializes correctly with framework validation."""
        with patch.object(TestRunner, '_validate_framework'):
            runner = TestRunner()
            assert runner is not None
            assert runner.current_test_window is None
            assert runner._last_error is None
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available")
    def test_runner_initialization_failure_no_configs(self, mock_qt_available):
        """Test runner initialization fails with no test configurations."""
        with patch('src.econsim.tools.launcher.test_runner.ALL_TEST_CONFIGS', {}):
            with pytest.raises(RuntimeError, match="No test configurations available"):
                TestRunner()
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available")
    def test_runner_initialization_failure_no_qt(self, mock_framework_components):
        """Test runner initialization fails without PyQt6."""
        with patch('src.econsim.tools.launcher.test_runner._qt_available', False):
            with pytest.raises(RuntimeError, match="PyQt6 not available"):
                TestRunner()
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available")
    def test_config_lookup_valid_id(self, mock_qt_available, mock_framework_components):
        """Test configuration lookup by valid ID."""
        with patch.object(TestRunner, '_validate_framework'):
            runner = TestRunner()
            config = runner._get_config_by_id(1)
            assert config is not None
            assert config.id == 1
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available") 
    def test_config_lookup_invalid_id(self, mock_qt_available, mock_framework_components):
        """Test configuration lookup with invalid ID returns None."""
        with patch.object(TestRunner, '_validate_framework'):
            runner = TestRunner()
            config = runner._get_config_by_id(999)
            assert config is None
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available")
    def test_run_by_id_invalid_config(self, mock_qt_available, mock_framework_components):
        """Test error handling for invalid configuration ID."""
        with patch.object(TestRunner, '_validate_framework'):
            runner = TestRunner()
            with pytest.raises(ValueError, match="Test ID 999 not found in registry"):
                runner.run_by_id(999, "framework")
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available")
    def test_run_by_id_invalid_mode(self, mock_qt_available, mock_framework_components):
        """Test error handling for invalid execution mode."""
        with patch.object(TestRunner, '_validate_framework'):
            runner = TestRunner()
            with pytest.raises(ValueError, match="Only 'framework' mode supported"):
                runner.run_by_id(1, "invalid_mode")
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available")
    def test_get_status_basic(self, mock_qt_available, mock_framework_components):
        """Test basic status reporting functionality."""
        with patch.object(TestRunner, '_validate_framework'):
            runner = TestRunner()
            status = runner.get_status()
            
            # Verify status structure
            assert isinstance(status, dict)
            assert 'available_tests' in status
            assert 'current_test' in status
            assert 'framework_available' in status
            assert 'last_error' in status
            assert 'qt_available' in status
            assert 'test_configs_loaded' in status
            
            # Verify expected values
            assert status['available_tests'] == 3  # From mock
            assert status['current_test'] is False
            assert status['last_error'] is None
            assert status['qt_available'] is True
            assert status['test_configs_loaded'] is True
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available")
    def test_get_status_with_error(self, mock_qt_available, mock_framework_components):
        """Test status reporting with error state."""
        with patch.object(TestRunner, '_validate_framework'):
            runner = TestRunner()
            runner._last_error = "Test error message"
            
            status = runner.get_status()
            assert status['last_error'] == "Test error message"
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available") 
    def test_get_health_check_healthy(self, mock_qt_available, mock_framework_components):
        """Test health check with healthy system state."""
        with patch.object(TestRunner, '_validate_framework'):
            with patch.object(TestRunner, '_check_framework_available', return_value=True):
                runner = TestRunner()
                health = runner.get_health_check()
                
                assert isinstance(health, dict)
                assert 'overall_healthy' in health
                assert 'components' in health
                assert 'issues' in health
                
                # Should be healthy with mocked components
                assert health['overall_healthy'] is True
                assert len(health['issues']) == 0
                
                # Check component structure
                components = health['components']
                assert 'qt' in components
                assert 'test_configs' in components
                assert 'framework' in components
                assert 'active_test' in components
                assert 'error_state' in components
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available")
    def test_get_health_check_unhealthy(self, mock_framework_components):
        """Test health check with unhealthy system state."""
        with patch('src.econsim.tools.launcher.test_runner._qt_available', False):
            with patch('src.econsim.tools.launcher.test_runner.ALL_TEST_CONFIGS', {}):
                with patch.object(TestRunner, '_validate_framework'):
                    runner = TestRunner()
                    runner._last_error = "System error"
                    
                    health = runner.get_health_check()
                    
                    # Should be unhealthy
                    assert health['overall_healthy'] is False
                    assert len(health['issues']) > 0
                    
                    # Check specific issues
                    issues = health['issues']
                    assert any("PyQt6 not available" in issue for issue in issues)
                    assert any("No test configurations" in issue for issue in issues)
                    assert any("Recent error" in issue for issue in issues)
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available")
    def test_framework_availability_check(self, mock_qt_available, mock_framework_components):
        """Test framework availability checking."""
        with patch.object(TestRunner, '_validate_framework'):
            runner = TestRunner()
            
            # Mock successful imports
            with patch('src.econsim.tools.launcher.test_runner.ALL_TEST_CONFIGS', {1: Mock()}):
                assert runner._check_framework_available() is True
            
            # Mock import failure
            with patch('src.econsim.tools.launcher.test_runner.ALL_TEST_CONFIGS', {}):
                assert runner._check_framework_available() is False
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available")
    def test_close_current_test_no_window(self, mock_qt_available, mock_framework_components):
        """Test closing current test when no window is open."""
        with patch.object(TestRunner, '_validate_framework'):
            runner = TestRunner()
            result = runner.close_current_test()
            assert result is False
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available")
    def test_close_current_test_with_window(self, mock_qt_available, mock_framework_components):
        """Test closing current test window."""
        with patch.object(TestRunner, '_validate_framework'):
            runner = TestRunner()
            
            # Mock window
            mock_window = Mock()
            runner.current_test_window = mock_window
            
            result = runner.close_current_test()
            assert result is True
            assert runner.current_test_window is None
            mock_window.close.assert_called_once()
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available")
    def test_get_available_tests(self, mock_qt_available, mock_framework_components):
        """Test retrieving available test mappings."""
        with patch.object(TestRunner, '_validate_framework'):
            runner = TestRunner()
            tests = runner.get_available_tests()
            
            assert isinstance(tests, dict)
            assert len(tests) == 3  # From mock
            assert 1 in tests
            assert 2 in tests
            assert 3 in tests
            assert tests[1] == "Test Config 1"
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available")
    def test_factory_function(self, mock_qt_available, mock_framework_components):
        """Test create_test_runner factory function."""
        with patch.object(TestRunner, '_validate_framework'):
            runner = create_test_runner()
            assert isinstance(runner, TestRunner)
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available")
    def test_run_config_framework_mode_success(self, mock_qt_available, mock_framework_components):
        """Test successful framework mode execution."""
        with patch.object(TestRunner, '_validate_framework'):
            with patch.object(TestRunner, '_run_framework_test') as mock_run:
                runner = TestRunner()
                config = Mock(id=1, name="Test Config")
                
                runner.run_config(config)
                mock_run.assert_called_once_with(config)
                assert runner._last_error is None
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available")
    def test_run_config_framework_mode_failure(self, mock_qt_available, mock_framework_components):
        """Test framework mode execution failure handling."""
        with patch.object(TestRunner, '_validate_framework'):
            with patch.object(TestRunner, '_run_framework_test', side_effect=Exception("Test failure")):
                runner = TestRunner()
                config = Mock(id=1, name="Test Config")
                
                with pytest.raises(RuntimeError, match="Failed to launch test 1"):
                    runner.run_config(config)
                
                assert runner._last_error is not None
                assert "Test failure" in runner._last_error


class TestProgrammaticRunnerIntegration:
    """Integration tests for programmatic runner with real components."""
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available")
    def test_real_config_registry_access(self):
        """Test access to real test configuration registry."""
        # This test uses the actual registry if available
        if ALL_TEST_CONFIGS:
            assert len(ALL_TEST_CONFIGS) > 0
            # Check that config IDs are reasonable (1-7 range)
            for config_id in ALL_TEST_CONFIGS.keys():
                assert isinstance(config_id, int)
                assert 1 <= config_id <= 10  # Reasonable range
    
    @pytest.mark.skipif(not _test_runner_available, reason="TestRunner not available")
    def test_runner_with_real_registry(self):
        """Test runner initialization with real test registry."""
        if not ALL_TEST_CONFIGS:
            pytest.skip("No test configurations available in registry")
        
        with patch('src.econsim.tools.launcher.test_runner._qt_available', True):
            with patch.object(TestRunner, '_validate_framework'):
                runner = TestRunner()
                status = runner.get_status()
                
                assert status['available_tests'] == len(ALL_TEST_CONFIGS)
                assert status['test_configs_loaded'] is True