"""
Simple buffered log writer for the new extensible architecture.

This module provides a lightweight, high-performance log writer that replaces
the complex 6-layer serialization pipeline with direct JSON output.

Key Features:
- Buffered writing with configurable buffer size and flush intervals
- Newline-delimited JSON for easy parsing
- Context manager support for automatic resource cleanup
- Thread-safe operations
- Minimal memory overhead with no intermediate transformations
"""

import json
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional, TextIO


class ExtensibleLogWriter:
    """Simple buffered log writer with context manager support.
    
    Provides efficient writing of log entries with automatic buffering,
    time-based flushing, and proper resource management. Designed to
    replace the complex serialization pipeline with direct JSON output.
    
    Features:
    - Buffered writes (flush every N events or M seconds)
    - Newline-delimited JSON for easy parsing
    - File handle management with context manager support
    - Thread-safe operations
    - No complex optimization - let filesystem buffering handle I/O
    """
    
    def __init__(self, filepath: Path, buffer_size: int = 100, flush_interval_sec: float = 1.0):
        """Initialize the extensible log writer.
        
        Args:
            filepath: Path to the output log file
            buffer_size: Number of entries to buffer before auto-flush
            flush_interval_sec: Maximum seconds between flushes
        """
        self.filepath = Path(filepath)
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval_sec
        
        # Internal state
        self._buffer: list[Dict[str, Any]] = []
        self._file: Optional[TextIO] = None
        self._last_flush: float = time.time()
        self._lock = threading.Lock()  # Thread safety
        
        # Statistics
        self._entries_written = 0
        self._bytes_written = 0
        self._flush_count = 0
        
        # Ensure parent directory exists
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
    
    def __enter__(self) -> 'ExtensibleLogWriter':
        """Context manager entry - open file for writing."""
        if self._file is None:
            # Use OS-level buffering for efficiency
            self._file = open(self.filepath, 'a', buffering=8192, encoding='utf-8')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - flush buffer and close file."""
        self.flush()
        if self._file:
            self._file.close()
            self._file = None
    
    def write_entry(self, entry_dict: Dict[str, Any]) -> None:
        """Write a log entry (dict) to buffer.
        
        Args:
            entry_dict: Dictionary to write as JSON log entry
        """
        with self._lock:
            self._buffer.append(entry_dict)
            
            # Auto-flush conditions
            should_flush = (
                len(self._buffer) >= self.buffer_size or
                (time.time() - self._last_flush) >= self.flush_interval
            )
            
            if should_flush:
                self._flush_internal()
    
    def flush(self) -> None:
        """Flush buffer to disk (thread-safe)."""
        with self._lock:
            self._flush_internal()
    
    def _flush_internal(self) -> None:
        """Internal flush method (assumes lock is held)."""
        if not self._buffer or self._file is None:
            return
        
        try:
            for entry in self._buffer:
                # Compact JSON format for efficiency
                json_line = json.dumps(entry, separators=(',', ':'))
                self._file.write(json_line + '\n')
                
                # Track bytes written
                self._bytes_written += len(json_line.encode('utf-8')) + 1  # +1 for newline
            
            # Ensure data is written to disk
            self._file.flush()
            
            # Update statistics
            self._entries_written += len(self._buffer)
            self._flush_count += 1
            
            # Clear buffer and update flush time
            self._buffer.clear()
            self._last_flush = time.time()
            
        except IOError as e:
            # Log error but don't crash - this is a logging system
            print(f"Warning: Failed to flush log buffer to {self.filepath}: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get writer statistics.
        
        Returns:
            Dictionary with statistics about entries written, bytes written, etc.
        """
        with self._lock:
            return {
                'entries_written': self._entries_written,
                'bytes_written': self._bytes_written,
                'flush_count': self._flush_count,
                'buffer_size': len(self._buffer),
                'filepath': str(self.filepath)
            }
    
    def is_open(self) -> bool:
        """Check if the writer is open and ready for writing.
        
        Returns:
            True if file is open and ready for writing
        """
        return self._file is not None
    
    def close(self) -> None:
        """Close the writer and release resources.
        
        Note: This method is automatically called by the context manager.
        """
        if self._file:
            self.flush()  # Ensure all buffered data is written
            self._file.close()
            self._file = None
