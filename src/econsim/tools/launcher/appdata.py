"""Cross-platform application data directory resolver."""
from pathlib import Path
import os
from typing import Optional


class AppDataResolver:
    """Resolves application data directories following platform conventions."""
    
    @staticmethod
    def get_config_dir(dev_override: Optional[str] = None) -> Path:
        """Get configuration directory (~/.config/econsim on Linux).
        
        Args:
            dev_override: Optional development override path
            
        Returns:
            Path to configuration directory
        """
        if dev_override or os.environ.get('ECONSIM_DEV_APPDATA'):
            return Path(dev_override or os.environ['ECONSIM_DEV_APPDATA']) / 'config'
        
        if os.name == 'nt':  # Windows
            return Path(os.environ.get('APPDATA', '~')) / 'econsim'
        elif os.environ.get('XDG_CONFIG_HOME'):
            return Path(os.environ['XDG_CONFIG_HOME']) / 'econsim'
        else:  # Linux/macOS default
            return Path.home() / '.config' / 'econsim'
    
    @staticmethod
    def get_data_dir(dev_override: Optional[str] = None) -> Path:
        """Get data directory (~/.local/share/econsim on Linux).
        
        Args:
            dev_override: Optional development override path
            
        Returns:
            Path to data directory
        """
        if dev_override or os.environ.get('ECONSIM_DEV_APPDATA'):
            return Path(dev_override or os.environ['ECONSIM_DEV_APPDATA']) / 'data'
        
        if os.name == 'nt':  # Windows
            return Path(os.environ.get('LOCALAPPDATA', '~')) / 'econsim'
        elif os.environ.get('XDG_DATA_HOME'):
            return Path(os.environ['XDG_DATA_HOME']) / 'econsim'
        else:  # Linux/macOS default
            return Path.home() / '.local' / 'share' / 'econsim'
    
    @staticmethod
    def get_state_dir(dev_override: Optional[str] = None) -> Path:
        """Get state directory (~/.local/state/econsim on Linux).
        
        Args:
            dev_override: Optional development override path
            
        Returns:
            Path to state directory
        """
        if dev_override or os.environ.get('ECONSIM_DEV_APPDATA'):
            return Path(dev_override or os.environ['ECONSIM_DEV_APPDATA']) / 'state'
        
        if os.name == 'nt':  # Windows
            return AppDataResolver.get_data_dir() / 'state'
        elif os.environ.get('XDG_STATE_HOME'):
            return Path(os.environ['XDG_STATE_HOME']) / 'econsim'
        else:  # Linux/macOS default
            return Path.home() / '.local' / 'state' / 'econsim'
    
    @staticmethod
    def get_launcher_config_file() -> Path:
        """Get launcher configuration file path."""
        return AppDataResolver.get_config_dir() / 'launcher' / 'config.json'
    
    @staticmethod
    def get_custom_tests_dir() -> Path:
        """Get custom tests directory."""
        return AppDataResolver.get_data_dir() / 'launcher' / 'custom_tests'
    
    @staticmethod
    def get_presets_file() -> Path:
        """Get config presets file path."""
        return AppDataResolver.get_config_dir() / 'launcher' / 'presets.json'
    
    @staticmethod
    def ensure_directories() -> None:
        """Create all necessary directories if they don't exist."""
        directories = [
            AppDataResolver.get_config_dir(),
            AppDataResolver.get_data_dir(),
            AppDataResolver.get_custom_tests_dir(),
            AppDataResolver.get_launcher_config_file().parent,
            AppDataResolver.get_presets_file().parent,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)