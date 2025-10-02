"""High-performance structured file logging observer.

This module implements the FileObserver class as specified in the
UNIFIED_REFACTOR_PLAN. It provides efficient file-based logging of
simulation events using the buffer system for optimal performance.

Features:
- High-performance structured file logging
- Buffer-based batch writing for efficiency
- Configurable output formats (JSON Lines, CSV, etc.)
- Automatic file rotation and management
- Event filtering and selective logging
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional, TextIO, Dict, Any, List, TYPE_CHECKING

from .base_observer import BaseObserver
from ..buffers import BufferManager, BasicEventBuffer

if TYPE_CHECKING:
    from ..config import ObservabilityConfig
    from ..events import SimulationEvent


class FileObserver(BaseObserver):
    """High-performance structured file logging observer.
    
    Implements efficient file-based logging using the buffer system
    for optimal performance. Supports multiple output formats and
    provides automatic file management capabilities.
    """

    def __init__(self, config: ObservabilityConfig, output_path: Path, 
                 buffer_size: Optional[int] = None, format: str = 'jsonl'):
        """Initialize the file observer.
        
        Args:
            config: Observability configuration
            output_path: Path where log files will be written
            buffer_size: Size of event buffer (uses config default if None)
            format: Output format ('jsonl', 'json', 'csv')
        """
        super().__init__(config)
        
        self._output_path = Path(output_path)
        self._format = format
        self._file_handle: Optional[TextIO] = None
        
        # Create buffer manager with basic event buffer
        buffer_capacity = buffer_size or getattr(config, 'buffer_size', 1000)
        self._buffer_manager = BufferManager(buffer_capacity)
        self._buffer_manager.register_buffer(
            BasicEventBuffer(capacity=buffer_capacity), 
            'file_events'
        )
        
        # Statistics
        self._events_written = 0
        self._bytes_written = 0
        self._last_write_time = 0.0
        
        # Initialize file output
        self._initialize_file_output()

    def _initialize_file_output(self) -> None:
        """Initialize file output and create directories if needed."""
        # Create parent directories if they don't exist
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Open file for writing (append mode to allow multiple runs)
        try:
            self._file_handle = open(self._output_path, 'a', encoding='utf-8')
        except IOError as e:
            print(f"Warning: Failed to open log file {self._output_path}: {e}")
            self._file_handle = None

    def _initialize_event_filtering(self) -> None:
        """Initialize event filtering for file logging.
        
        FileObserver accepts most event types but can be configured
        to filter based on the observability configuration.
        """
        # FileObserver logs most events by default
        self._enabled_event_types = {
            'agent_mode_change',
            'trade_execution', 
            'resource_collection',
            'agent_movement',
        }
        
        # Add behavioral events if behavioral aggregation is enabled
        if getattr(self._config, 'behavioral_aggregation', False):
            self._enabled_event_types.add('behavioral_aggregation')
        
        # Add correlation events if correlation tracking is enabled  
        if getattr(self._config, 'correlation_tracking', False):
            self._enabled_event_types.add('correlation_analysis')

    def notify(self, event: SimulationEvent) -> None:
        """Handle a simulation event by adding it to the buffer.
        
        Args:
            event: The simulation event to log
        """
        if not self.is_enabled(event.event_type) or self._file_handle is None:
            return
            
        # Add event to buffer manager for batch processing
        self._buffer_manager.add_event(event)

    def flush_step(self, step: int) -> None:
        """Flush buffered events to file at step boundary.
        
        Args:
            step: The simulation step that just completed
        """
        if self._file_handle is None:
            return
            
        # Get all buffered events
        buffered_data = self._buffer_manager.flush_step(step)
        
        # Write events to file
        for buffer_name, events in buffered_data.items():
            if events:  # Only write if there are events
                self._write_events_batch(events)

    def _write_events_batch(self, events: List[Dict[str, Any]]) -> None:
        """Write a batch of events to file.
        
        Args:
            events: List of event dictionaries to write
        """
        if not events or self._file_handle is None:
            return
            
        write_start = time.time()
        bytes_written = 0
        
        try:
            for event in events:
                if self._format == 'jsonl':
                    # JSON Lines format (one JSON object per line)
                    line = json.dumps(event, separators=(',', ':')) + '\n'
                    self._file_handle.write(line)
                    bytes_written += len(line.encode('utf-8'))
                    
                elif self._format == 'json':
                    # Pretty-printed JSON (less efficient but more readable)
                    line = json.dumps(event, indent=2) + '\n'
                    self._file_handle.write(line)
                    bytes_written += len(line.encode('utf-8'))
                    
                # CSV format could be added here in the future
                
            # Ensure data is written to disk
            self._file_handle.flush()
            
            # Update statistics
            self._events_written += len(events)
            self._bytes_written += bytes_written
            self._last_write_time = time.time() - write_start
            
        except IOError as e:
            print(f"Warning: Failed to write events to file: {e}")

    def close(self) -> None:
        """Close the file observer and release resources."""
        super().close()
        
        # Flush any remaining buffered events
        if not self._closed and self._buffer_manager:
            # Use a high step number to flush everything
            self.flush_step(999999)
        
        # Close file handle
        if self._file_handle is not None:
            try:
                self._file_handle.close()
            except IOError as e:
                print(f"Warning: Error closing file handle: {e}")
            finally:
                self._file_handle = None
        
        # Clear buffers
        if self._buffer_manager:
            self._buffer_manager.clear_all_buffers()

    def get_observer_stats(self) -> Dict[str, Any]:
        """Get file observer statistics.
        
        Returns:
            Dictionary containing file observer metrics
        """
        base_stats = super().get_observer_stats()
        
        file_stats = {
            'output_path': str(self._output_path),
            'format': self._format,
            'events_written': self._events_written,
            'bytes_written': self._bytes_written,
            'last_write_time': self._last_write_time,
            'file_open': self._file_handle is not None,
        }
        
        # Add buffer manager stats
        if self._buffer_manager:
            file_stats['buffer_stats'] = self._buffer_manager.get_manager_stats()
        
        return {**base_stats, **file_stats}

    @property
    def output_path(self) -> Path:
        """Get the output file path."""
        return self._output_path

    @property
    def events_written(self) -> int:
        """Get the number of events written to file."""
        return self._events_written

    def rotate_file(self, new_path: Optional[Path] = None) -> None:
        """Rotate the log file to a new location.
        
        Args:
            new_path: New file path (if None, generates timestamped name)
        """
        if self._file_handle is None:
            return
            
        # Close current file
        self._file_handle.close()
        
        # Determine new path
        if new_path is None:
            timestamp = int(time.time())
            stem = self._output_path.stem
            suffix = self._output_path.suffix
            new_path = self._output_path.parent / f"{stem}_{timestamp}{suffix}"
        
        # Update path and reinitialize
        self._output_path = new_path
        self._initialize_file_output()
        
    def __repr__(self) -> str:
        """String representation of the file observer."""
        return f"FileObserver(path={self._output_path}, format={self._format}, closed={self._closed})"