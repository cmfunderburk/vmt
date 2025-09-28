"""Test modular entry point functions from Step 2.8."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import argparse


# Mock the Qt imports for headless testing
sys.modules['PyQt6'] = MagicMock()
sys.modules['PyQt6.QtWidgets'] = MagicMock()
sys.modules['PyQt6.QtCore'] = MagicMock()
sys.modules['PyQt6.QtGui'] = MagicMock()

# Import after mocking Qt
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'MANUAL_TESTS'))
import enhanced_test_launcher_v2


class TestModularEntryPoint:
    """Test the modular entry point functions."""
    
    def test_parse_command_line_default(self):
        """Test default command-line parsing (no arguments)."""
        with patch('sys.argv', ['enhanced_test_launcher_v2.py']):
            args = enhanced_test_launcher_v2.parse_command_line()
            assert isinstance(args, argparse.Namespace)
    
    def test_parse_command_line_version(self):
        """Test --version argument parsing."""
        with patch('sys.argv', ['enhanced_test_launcher_v2.py', '--version']):
            with pytest.raises(SystemExit) as exc_info:
                enhanced_test_launcher_v2.parse_command_line()
            # argparse exits with code 0 for --version
            assert exc_info.value.code == 0
    
    def test_parse_command_line_help(self):
        """Test --help argument parsing."""
        with patch('sys.argv', ['enhanced_test_launcher_v2.py', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                enhanced_test_launcher_v2.parse_command_line()
            # argparse exits with code 0 for --help
            assert exc_info.value.code == 0
    
    def test_check_environment_in_venv(self):
        """Test environment check when in virtual environment."""
        # Mock being in a virtual environment
        with patch.object(sys, 'real_prefix', 'some_prefix', create=True):
            # Should not print warning when in venv
            with patch('builtins.print') as mock_print:
                enhanced_test_launcher_v2.check_environment()
                mock_print.assert_not_called()
    
    def test_check_environment_not_in_venv(self):
        """Test environment check when not in virtual environment."""
        # Mock not being in a virtual environment
        if hasattr(sys, 'real_prefix'):
            delattr(sys, 'real_prefix')
        
        with patch.object(sys, 'base_prefix', sys.prefix):
            with patch('builtins.print') as mock_print:
                enhanced_test_launcher_v2.check_environment()
                # Should print warning when not in venv
                assert mock_print.call_count >= 1
                warning_call = mock_print.call_args_list[0]
                assert "Warning" in str(warning_call)
    
    def test_configure_qt_environment(self):
        """Test Qt environment configuration."""
        with patch.dict(os.environ, {}, clear=True):
            enhanced_test_launcher_v2.configure_qt_environment()
            assert os.environ.get('QT_AUTO_SCREEN_SCALE_FACTOR') == '1'
    
    @patch('enhanced_test_launcher_v2.QApplication')
    def test_create_application(self, mock_qapp_class):
        """Test QApplication creation and configuration."""
        mock_app = Mock()
        mock_qapp_class.return_value = mock_app
        
        with patch('sys.argv', ['test']):
            app = enhanced_test_launcher_v2.create_application()
            
            # Verify QApplication was created
            mock_qapp_class.assert_called_once_with(['test'])
            
            # Verify application properties were set
            mock_app.setApplicationName.assert_called_once_with("VMT Enhanced Test Launcher")
            mock_app.setApplicationVersion.assert_called_once_with("1.0.0")
            mock_app.setOrganizationName.assert_called_once_with("VMT Project")
            
            assert app == mock_app
    
    def test_apply_platform_styling_with_modules(self):
        """Test platform styling when modules are available."""
        mock_app = Mock()
        
        with patch('enhanced_test_launcher_v2._launcher_modules_available', True), \
             patch('enhanced_test_launcher_v2.PlatformStyler') as mock_styler:
            
            enhanced_test_launcher_v2.apply_platform_styling(mock_app)
            mock_styler.configure_application.assert_called_once_with(mock_app)
    
    def test_apply_platform_styling_fallback(self):
        """Test platform styling fallback when modules not available."""
        mock_app = Mock()
        
        with patch('enhanced_test_launcher_v2._launcher_modules_available', False), \
             patch('builtins.__import__') as mock_import:
            
            # Mock the fallback import
            mock_styler = Mock()
            mock_import.return_value = mock_styler
            
            enhanced_test_launcher_v2.apply_platform_styling(mock_app)
            # Should not raise an exception
    
    def test_apply_platform_styling_exception_handling(self):
        """Test platform styling exception handling."""
        mock_app = Mock()
        
        with patch('enhanced_test_launcher_v2._launcher_modules_available', True), \
             patch('enhanced_test_launcher_v2.PlatformStyler') as mock_styler, \
             patch('builtins.print') as mock_print:
            
            # Make PlatformStyler raise an exception
            mock_styler.configure_application.side_effect = Exception("Test error")
            
            enhanced_test_launcher_v2.apply_platform_styling(mock_app)
            
            # Should print warning message
            mock_print.assert_called_once()
            warning_call = str(mock_print.call_args_list[0])
            assert "Launcher Styling Warning" in warning_call
            assert "Test error" in warning_call
    
    def test_create_main_window_with_modules(self):
        """Test main window creation when modules are available."""
        with patch('enhanced_test_launcher_v2._launcher_modules_available', True), \
             patch('enhanced_test_launcher_v2.VMTLauncherWindow') as mock_window_class:
            
            mock_window = Mock()
            mock_window_class.return_value = mock_window
            
            window = enhanced_test_launcher_v2.create_main_window()
            
            mock_window_class.assert_called_once()
            assert window == mock_window
    
    def test_create_main_window_fallback(self):
        """Test main window creation fallback when modules not available."""
        with patch('enhanced_test_launcher_v2._launcher_modules_available', False), \
             patch('enhanced_test_launcher_v2.EnhancedTestLauncher') as mock_window_class:
            
            mock_window = Mock()
            mock_window_class.return_value = mock_window
            
            window = enhanced_test_launcher_v2.create_main_window()
            
            mock_window_class.assert_called_once()
            assert window == mock_window
    
    @patch('enhanced_test_launcher_v2.create_main_window')
    @patch('enhanced_test_launcher_v2.apply_platform_styling')
    @patch('enhanced_test_launcher_v2.create_application')
    @patch('enhanced_test_launcher_v2.configure_qt_environment')
    @patch('enhanced_test_launcher_v2.check_environment')
    @patch('enhanced_test_launcher_v2.parse_command_line')
    @patch('sys.exit')
    def test_main_function_integration(self, mock_exit, mock_parse, mock_check_env,
                                     mock_configure_qt, mock_create_app, mock_apply_styling,
                                     mock_create_window):
        """Test main function integration of all components."""
        # Setup mocks
        mock_args = Mock()
        mock_parse.return_value = mock_args
        
        mock_app = Mock()
        mock_create_app.return_value = mock_app
        
        mock_window = Mock()
        mock_create_window.return_value = mock_window
        
        # Call main function
        enhanced_test_launcher_v2.main()
        
        # Verify call sequence
        mock_parse.assert_called_once()
        mock_check_env.assert_called_once()
        mock_configure_qt.assert_called_once()
        mock_create_app.assert_called_once()
        mock_apply_styling.assert_called_once_with(mock_app)
        mock_create_window.assert_called_once()
        mock_window.show.assert_called_once()
        mock_exit.assert_called_once()