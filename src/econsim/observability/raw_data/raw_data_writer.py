"""
Raw Data Writer: Disk persistence for raw simulation data.

This module handles writing raw simulation data to disk at simulation completion.
It provides efficient, compressed storage with optional file rotation and statistics tracking.

Key Features:
- JSON lines output format for easy parsing and streaming
- Optional compression for large log files (gzip)
- File rotation support for long simulations
- Statistics tracking (bytes written, events written, compression ratio)
- Atomic writes to prevent corruption
- Configurable output formats and compression levels

Usage:
    writer = RawDataWriter(compress=True, max_file_size_mb=100)
    writer.flush_to_disk(observer.get_all_events(), "simulation_log.jsonl")
    
    # Get statistics
    stats = writer.get_statistics()
    print(f"Wrote {stats['events_written']} events, {stats['bytes_written']} bytes")
"""

from __future__ import annotations

import gzip
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, TextIO
from contextlib import contextmanager


class RawDataWriter:
    """Writes raw simulation data to disk with compression and rotation support.
    
    This writer handles the final step of the raw data recording pipeline:
    persisting raw event dictionaries to disk at simulation completion.
    
    Features:
    - JSON lines format for easy parsing and streaming
    - Optional gzip compression for space efficiency
    - File rotation for large simulations
    - Atomic writes to prevent corruption
    - Comprehensive statistics tracking
    - Configurable compression levels and file sizes
    
    Architecture:
    - Input: List of raw event dictionaries from RawDataObserver
    - Output: Compressed or uncompressed JSON lines file
    - Performance: Deferred disk writes only at simulation end
    - Reliability: Atomic writes with error handling
    """
    
    def __init__(self, 
                 compress: bool = True,
                 compression_level: int = 6,
                 max_file_size_mb: int = 100,
                 enable_rotation: bool = True,
                 atomic_writes: bool = True) -> None:
        """Initialize raw data writer with configuration options.
        
        Args:
            compress: Whether to compress output files with gzip (default True)
            compression_level: Gzip compression level 1-9 (default 6, balanced)
            max_file_size_mb: Maximum file size before rotation in MB (default 100)
            enable_rotation: Whether to enable file rotation (default True)
            atomic_writes: Whether to use atomic writes (default True)
        """
        self.compress = compress
        self.compression_level = max(1, min(9, compression_level))  # Clamp to valid range
        self.max_file_size_mb = max_file_size_mb
        self.enable_rotation = enable_rotation
        self.atomic_writes = atomic_writes
        
        # Statistics tracking
        self._stats = {
            'files_written': 0,
            'events_written': 0,
            'bytes_written': 0,
            'compression_ratio': 0.0,
            'write_time_seconds': 0.0,
            'last_write_time': 0.0
        }
        
        # File rotation tracking
        self._current_file_size = 0
        self._rotation_counter = 0
    
    # ============================================================================
    # MAIN WRITE METHODS
    # ============================================================================
    
    def flush_to_disk(self, 
                     events: List[Dict[str, Any]], 
                     filepath: Union[str, Path],
                     append: bool = False) -> Dict[str, Any]:
        """Write all raw events to disk at simulation completion.
        
        Args:
            events: List of raw event dictionaries from RawDataObserver
            filepath: Output file path (will add .gz extension if compressing)
            append: Whether to append to existing file (default False)
            
        Returns:
            Dictionary with write statistics and file information
            
        Raises:
            IOError: If file write fails
            ValueError: If events list is invalid
        """
        if not events:
            return self._create_empty_write_result(filepath)
        
        # Validate events
        self._validate_events(events)
        
        # Prepare file path
        output_path = self._prepare_file_path(filepath)
        
        # Record start time for statistics
        start_time = time.time()
        
        try:
            if self.atomic_writes:
                result = self._write_atomic(events, output_path, append)
            else:
                result = self._write_direct(events, output_path, append)
            
            # Update statistics
            self._update_write_statistics(result, start_time)
            
            return result
            
        except Exception as e:
            # Clean up partial files on error
            self._cleanup_on_error(output_path)
            raise IOError(f"Failed to write events to {output_path}: {e}") from e
    
    def flush_to_disk_with_rotation(self,
                                  events: List[Dict[str, Any]],
                                  base_filepath: Union[str, Path],
                                  append: bool = False) -> List[Dict[str, Any]]:
        """Write events to disk with automatic file rotation.
        
        Args:
            events: List of raw event dictionaries from RawDataObserver
            base_filepath: Base file path for rotation (e.g., "simulation.jsonl")
            append: Whether to append to existing files (default False)
            
        Returns:
            List of write result dictionaries for each file written
            
        Raises:
            IOError: If file write fails
            ValueError: If events list is invalid
        """
        if not events:
            return [self._create_empty_write_result(base_filepath)]
        
        # Validate events
        self._validate_events(events)
        
        # Prepare base path
        base_path = Path(base_filepath)
        
        # Split events into chunks if rotation is enabled
        if self.enable_rotation:
            event_chunks = self._split_events_for_rotation(events)
        else:
            event_chunks = [events]
        
        # Write each chunk to a separate file
        results = []
        for i, chunk in enumerate(event_chunks):
            if self.enable_rotation and len(event_chunks) > 1:
                # Add rotation suffix
                chunk_path = self._add_rotation_suffix(base_path, i)
            else:
                chunk_path = base_path
            
            result = self.flush_to_disk(chunk, chunk_path, append)
            results.append(result)
        
        return results
    
    # ============================================================================
    # INTERNAL WRITE IMPLEMENTATIONS
    # ============================================================================
    
    def _write_atomic(self, 
                     events: List[Dict[str, Any]], 
                     filepath: Path, 
                     append: bool) -> Dict[str, Any]:
        """Write events using atomic writes (write to temp file, then rename)."""
        # Create temporary file path
        temp_path = filepath.with_suffix(filepath.suffix + '.tmp')
        
        try:
            # Write to temporary file
            result = self._write_direct(events, temp_path, append)
            
            # Atomic rename
            temp_path.rename(filepath)
            
            # Update result with final path
            result['filepath'] = str(filepath)
            result['atomic_write'] = True
            
            return result
            
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise e
    
    def _write_direct(self, 
                     events: List[Dict[str, Any]], 
                     filepath: Path, 
                     append: bool) -> Dict[str, Any]:
        """Write events directly to file."""
        # Open file with appropriate handler
        with self._open_file(filepath, append) as f:
            bytes_written = 0
            events_written = 0
            
            for event in events:
                # Convert event to JSON line
                json_line = json.dumps(event, separators=(',', ':')) + '\n'
                
                # Write to file
                if self.compress:
                    # For gzip files, write as bytes
                    line_bytes = json_line.encode('utf-8')
                    f.write(line_bytes)
                    bytes_written += len(line_bytes)
                else:
                    # For regular files, write as text
                    f.write(json_line)
                    bytes_written += len(json_line.encode('utf-8'))
                
                events_written += 1
        
        # Calculate compression ratio
        if self.compress:
            # For compressed files, get actual file size
            actual_file_size = filepath.stat().st_size
            compression_ratio = self._calculate_compression_ratio(events, actual_file_size)
        else:
            compression_ratio = 1.0  # No compression
        
        return {
            'filepath': str(filepath),
            'events_written': events_written,
            'bytes_written': bytes_written,
            'compression_ratio': compression_ratio,
            'compressed': self.compress,
            'append_mode': append,
            'atomic_write': False
        }
    
    @contextmanager
    def _open_file(self, filepath: Path, append: bool):
        """Context manager for opening files with appropriate compression."""
        if self.compress:
            # Use gzip compression - always binary mode
            mode = 'ab' if append else 'wb'
            with gzip.open(filepath, mode, compresslevel=self.compression_level) as f:
                yield f
        else:
            # Use regular file - text mode
            mode = 'a' if append else 'w'
            with open(filepath, mode, encoding='utf-8') as f:
                yield f
    
    # ============================================================================
    # FILE PATH AND ROTATION HELPERS
    # ============================================================================
    
    def _prepare_file_path(self, filepath: Union[str, Path]) -> Path:
        """Prepare file path with compression extension if needed."""
        path = Path(filepath)
        
        if self.compress and not path.suffix == '.gz':
            # Add .gz extension for compressed files
            path = path.with_suffix(path.suffix + '.gz')
        
        return path
    
    def _add_rotation_suffix(self, base_path: Path, rotation_index: int) -> Path:
        """Add rotation suffix to file path."""
        # Add rotation number before extension
        stem = base_path.stem
        suffix = base_path.suffix
        
        if self.compress and suffix == '.gz':
            # Handle .jsonl.gz case - need to extract the base suffix
            # If stem is "test.jsonl" and suffix is ".gz", we want "test_001.jsonl.gz"
            if stem.endswith('.jsonl'):
                base_stem = stem[:-6]  # Remove .jsonl
                return base_path.parent / f"{base_stem}_{rotation_index:03d}.jsonl.gz"
            else:
                return base_path.parent / f"{stem}_{rotation_index:03d}.jsonl.gz"
        else:
            return base_path.parent / f"{stem}_{rotation_index:03d}{suffix}"
    
    def _split_events_for_rotation(self, events: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Split events into chunks for file rotation based on estimated size."""
        if not self.enable_rotation:
            return [events]
        
        # Calculate actual bytes per event by sampling
        if len(events) > 0:
            # Sample first few events to estimate size
            sample_size = min(10, len(events))
            total_bytes = 0
            for i in range(sample_size):
                json_line = json.dumps(events[i], separators=(',', ':')) + '\n'
                total_bytes += len(json_line.encode('utf-8'))
            
            estimated_bytes_per_event = total_bytes / sample_size
        else:
            estimated_bytes_per_event = 200  # Fallback estimate
        
        # Calculate max events per file
        max_bytes_per_file = self.max_file_size_mb * 1024 * 1024
        max_events_per_file = max(1, int(max_bytes_per_file // estimated_bytes_per_event))
        
        # Split events into chunks
        chunks = []
        for i in range(0, len(events), max_events_per_file):
            chunk = events[i:i + max_events_per_file]
            chunks.append(chunk)
        
        return chunks
    
    # ============================================================================
    # VALIDATION AND ERROR HANDLING
    # ============================================================================
    
    def _validate_events(self, events: List[Dict[str, Any]]) -> None:
        """Validate events list before writing."""
        if not isinstance(events, list):
            raise ValueError("Events must be a list")
        
        if not events:
            return  # Empty list is valid
        
        # Check that all items are dictionaries
        for i, event in enumerate(events):
            if not isinstance(event, dict):
                raise ValueError(f"Event at index {i} is not a dictionary: {type(event)}")
            
            # Check for required fields
            if 'type' not in event:
                raise ValueError(f"Event at index {i} missing required 'type' field")
            
            if 'step' not in event:
                raise ValueError(f"Event at index {i} missing required 'step' field")
    
    def _cleanup_on_error(self, filepath: Path) -> None:
        """Clean up partial files on write error."""
        try:
            if filepath.exists():
                filepath.unlink()
        except Exception:
            pass  # Ignore cleanup errors
    
    def _create_empty_write_result(self, filepath: Union[str, Path]) -> Dict[str, Any]:
        """Create result dictionary for empty events list."""
        path = self._prepare_file_path(filepath)
        
        return {
            'filepath': str(path),
            'events_written': 0,
            'bytes_written': 0,
            'compression_ratio': 0.0,
            'compressed': self.compress,
            'append_mode': False,
            'atomic_write': self.atomic_writes,
            'empty_file': True
        }
    
    # ============================================================================
    # STATISTICS AND METRICS
    # ============================================================================
    
    def _update_write_statistics(self, result: Dict[str, Any], start_time: float) -> None:
        """Update internal statistics with write result."""
        self._stats['files_written'] += 1
        self._stats['events_written'] += result['events_written']
        self._stats['bytes_written'] += result['bytes_written']
        self._stats['write_time_seconds'] += time.time() - start_time
        self._stats['last_write_time'] = time.time()
        
        # Update compression ratio (weighted average)
        if result['events_written'] > 0:
            current_ratio = result['compression_ratio']
            total_events = self._stats['events_written']
            previous_events = total_events - result['events_written']
            
            if previous_events > 0:
                # Weighted average
                self._stats['compression_ratio'] = (
                    (self._stats['compression_ratio'] * previous_events + current_ratio * result['events_written']) 
                    / total_events
                )
            else:
                self._stats['compression_ratio'] = current_ratio
    
    def _calculate_compression_ratio(self, events: List[Dict[str, Any]], compressed_bytes: int) -> float:
        """Calculate compression ratio for events."""
        if not events or compressed_bytes == 0:
            return 0.0
        
        # Calculate uncompressed size
        uncompressed_size = 0
        for event in events:
            json_line = json.dumps(event, separators=(',', ':')) + '\n'
            uncompressed_size += len(json_line.encode('utf-8'))
        
        if uncompressed_size == 0:
            return 0.0
        
        # Compression ratio: compressed_size / uncompressed_size
        # Lower ratio = better compression
        return compressed_bytes / uncompressed_size
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive write statistics.
        
        Returns:
            Dictionary containing write statistics including:
            - files_written: Number of files written
            - events_written: Total events written
            - bytes_written: Total bytes written
            - compression_ratio: Average compression ratio
            - write_time_seconds: Total time spent writing
            - last_write_time: Timestamp of last write
            - average_events_per_file: Average events per file
            - average_bytes_per_event: Average bytes per event
        """
        stats = self._stats.copy()
        
        # Calculate derived statistics
        if stats['files_written'] > 0:
            stats['average_events_per_file'] = stats['events_written'] / stats['files_written']
        else:
            stats['average_events_per_file'] = 0.0
        
        if stats['events_written'] > 0:
            stats['average_bytes_per_event'] = stats['bytes_written'] / stats['events_written']
        else:
            stats['average_bytes_per_event'] = 0.0
        
        if stats['write_time_seconds'] > 0:
            stats['events_per_second'] = stats['events_written'] / stats['write_time_seconds']
        else:
            stats['events_per_second'] = 0.0
        
        return stats
    
    def reset_statistics(self) -> None:
        """Reset all statistics to zero."""
        self._stats = {
            'files_written': 0,
            'events_written': 0,
            'bytes_written': 0,
            'compression_ratio': 0.0,
            'write_time_seconds': 0.0,
            'last_write_time': 0.0
        }
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def estimate_file_size(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Estimate file size for events without writing.
        
        Args:
            events: List of raw event dictionaries
            
        Returns:
            Dictionary with size estimates:
            - uncompressed_bytes: Estimated uncompressed size
            - compressed_bytes: Estimated compressed size (if compression enabled)
            - events_count: Number of events
        """
        if not events:
            return {
                'uncompressed_bytes': 0,
                'compressed_bytes': 0,
                'events_count': 0
            }
        
        # Calculate uncompressed size
        uncompressed_bytes = 0
        for event in events:
            json_line = json.dumps(event, separators=(',', ':')) + '\n'
            uncompressed_bytes += len(json_line.encode('utf-8'))
        
        # Estimate compressed size
        if self.compress:
            # Use current compression ratio if available, otherwise estimate
            if self._stats['compression_ratio'] > 0:
                compression_ratio = self._stats['compression_ratio']
            else:
                compression_ratio = 0.3  # Conservative estimate for JSON
            compressed_bytes = int(uncompressed_bytes * compression_ratio)
        else:
            compressed_bytes = uncompressed_bytes
        
        return {
            'uncompressed_bytes': uncompressed_bytes,
            'compressed_bytes': compressed_bytes,
            'events_count': len(events)
        }
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current writer configuration.
        
        Returns:
            Dictionary with current configuration settings
        """
        return {
            'compress': self.compress,
            'compression_level': self.compression_level,
            'max_file_size_mb': self.max_file_size_mb,
            'enable_rotation': self.enable_rotation,
            'atomic_writes': self.atomic_writes
        }
    
    def __repr__(self) -> str:
        """String representation of writer state."""
        stats = self.get_statistics()
        config = self.get_configuration()
        
        return (f"RawDataWriter(compress={config['compress']}, "
                f"files={stats['files_written']}, "
                f"events={stats['events_written']}, "
                f"bytes={stats['bytes_written']})")
