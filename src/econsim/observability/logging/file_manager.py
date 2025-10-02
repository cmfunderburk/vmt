"""Economic log file management system.

This module provides comprehensive file management for economic logging,
including session directories, file rotation, and symlink management.
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import EconomicLoggingConfig


class EconomicLogFileManager:
    """Manages economic log file organization and rotation.
    
    Provides timestamped session directories, automatic file rotation,
    and symlink management for easy access to the latest logs.
    """
    
    def __init__(self, config: EconomicLoggingConfig, base_dir: Optional[Path] = None):
        """Initialize the economic log file manager.
        
        Args:
            config: Economic logging configuration
            base_dir: Base directory for log files (optional)
        """
        self.config = config
        self.base_dir = base_dir or Path.cwd()
        self.economic_log_dir = self.config.get_effective_output_dir(self.base_dir)
        
        # Statistics
        self.files_created = 0
        self.bytes_written = 0
        self.sessions_created = 0
        
        # Check if we have a specific output directory (from launcher)
        if config.output_dir is not None:
            # Use the provided directory directly (no nested timestamp)
            self.current_session_dir = Path(config.output_dir)
            self.current_session_dir.mkdir(parents=True, exist_ok=True)
            self.latest_symlink = None  # No symlink needed for specific directories
        else:
            # Create timestamped session directory (for direct simulations)
            self.latest_symlink = self.economic_log_dir / "latest"
            self.current_session_dir = self._create_session_dir()
    
    def _create_session_dir(self) -> Path:
        """Create timestamped session directory.
        
        Returns:
            Path to the new session directory
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = self.economic_log_dir / timestamp
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create latest symlink (only for default directories)
        if self.latest_symlink is not None:
            if self.latest_symlink.exists():
                self.latest_symlink.unlink()
            self.latest_symlink.symlink_to(timestamp)
        
        self.sessions_created += 1
        return session_dir
    
    def get_log_file_path(self, filename: str) -> Path:
        """Get the full path for a log file in the current session.
        
        Args:
            filename: Name of the log file
            
        Returns:
            Full path to the log file
        """
        return self.current_session_dir / filename
    
    def get_economic_events_file(self) -> Path:
        """Get the path for the main economic events log file.
        
        Returns:
            Path to the economic events log file
        """
        if self.config.use_optimized_format:
            return self.get_log_file_path("economic_events.jsonl")
        else:
            return self.get_log_file_path("economic_events_legacy.jsonl")
    
    def get_analysis_file(self) -> Path:
        """Get the path for the economic analysis results file.
        
        Returns:
            Path to the economic analysis file
        """
        return self.get_log_file_path("economic_analysis.json")
    
    def get_summary_file(self) -> Path:
        """Get the path for the economic summary markdown file.
        
        Returns:
            Path to the economic summary file
        """
        return self.get_log_file_path("economic_summary.md")
    
    def get_metrics_file(self) -> Path:
        """Get the path for the economic metrics file.
        
        Returns:
            Path to the economic metrics file
        """
        return self.get_log_file_path("economic_metrics.json")
    
    def get_config_file(self) -> Path:
        """Get the path for the logging configuration file.
        
        Returns:
            Path to the configuration file
        """
        return self.current_session_dir / "config.json"
    
    def write_session_config(self) -> None:
        """Write the current configuration to the session directory.
        
        This creates a record of the configuration used for this session.
        """
        config_file = self.get_config_file()
        config_data = self.config.to_dict()
        
        import json
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
    
    def rotate_session(self) -> Path:
        """Rotate to a new session directory.
        
        Returns:
            Path to the new session directory
        """
        old_session_dir = self.current_session_dir
        
        # Only rotate if we're using automatic timestamp directories
        if self.latest_symlink is not None:
            self.current_session_dir = self._create_session_dir()
            self.write_session_config()
        # For specific directories (from launcher), we don't rotate
        
        return self.current_session_dir
    
    def should_rotate_file(self, file_path: Path) -> bool:
        """Check if a file should be rotated based on size.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file should be rotated
        """
        if not file_path.exists():
            return False
        
        try:
            file_size = file_path.stat().st_size
            return file_size >= self.config.max_file_size
        except (OSError, IOError):
            return False
    
    def rotate_file(self, file_path: Path) -> Path:
        """Rotate a log file to a new name with timestamp.
        
        Args:
            file_path: Path to the file to rotate
            
        Returns:
            Path to the new rotated file
        """
        if not file_path.exists():
            return file_path
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        stem = file_path.stem
        suffix = file_path.suffix
        rotated_path = file_path.parent / f"{stem}_{timestamp}{suffix}"
        
        try:
            file_path.rename(rotated_path)
            self.files_created += 1
            return rotated_path
        except (OSError, IOError) as e:
            print(f"Warning: Failed to rotate file {file_path}: {e}")
            return file_path
    
    def cleanup_old_sessions(self, max_sessions: int = 10) -> None:
        """Clean up old session directories to prevent disk space issues.
        
        Args:
            max_sessions: Maximum number of session directories to keep
        """
        if not self.economic_log_dir.exists():
            return
        
        # Get all session directories (excluding symlinks)
        session_dirs = []
        for item in self.economic_log_dir.iterdir():
            if item.is_dir() and not item.is_symlink():
                try:
                    # Try to parse timestamp from directory name (both old and new formats)
                    try:
                        datetime.strptime(item.name, "%Y-%m-%d_%H-%M-%S")
                    except ValueError:
                        datetime.strptime(item.name, "%Y%m%d_%H%M%S")  # Old format
                    session_dirs.append(item)
                except ValueError:
                    # Skip directories that don't match timestamp format
                    continue
        
        # Sort by modification time (oldest first)
        session_dirs.sort(key=lambda x: x.stat().st_mtime)
        
        # Remove oldest directories if we exceed the limit
        if len(session_dirs) > max_sessions:
            dirs_to_remove = session_dirs[:-max_sessions]
            for session_dir in dirs_to_remove:
                try:
                    import shutil
                    shutil.rmtree(session_dir)
                except (OSError, IOError) as e:
                    print(f"Warning: Failed to remove old session directory {session_dir}: {e}")
    
    def get_session_stats(self) -> dict:
        """Get statistics about the current session.
        
        Returns:
            Dictionary containing session statistics
        """
        stats = {
            "session_dir": str(self.current_session_dir),
            "sessions_created": self.sessions_created,
            "files_created": self.files_created,
            "bytes_written": self.bytes_written,
            "latest_symlink": str(self.latest_symlink),
            "config": self.config.to_dict(),
        }
        
        # Add file size information if files exist
        file_stats = {}
        for filename in ["economic_events.jsonl", "economic_analysis.json", "economic_summary.md", "economic_metrics.json", "config.json"]:
            file_path = self.get_log_file_path(filename)
            if file_path.exists():
                try:
                    file_stats[filename] = {
                        "size_bytes": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    }
                except (OSError, IOError):
                    file_stats[filename] = {"error": "Could not read file stats"}
        
        stats["files"] = file_stats
        return stats
    
    def __repr__(self) -> str:
        """String representation of the file manager."""
        return f"EconomicLogFileManager(session_dir={self.current_session_dir}, sessions={self.sessions_created})"
