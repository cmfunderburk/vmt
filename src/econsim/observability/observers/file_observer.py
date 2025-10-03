"""High-performance structured file logging observer using raw data architecture.

This module implements the FileObserver class using the new raw data recording
architecture for zero-overhead logging. It provides efficient file-based logging
of simulation events with deferred disk writes and raw data storage.

Features:
- Zero-overhead raw data recording during simulation
- Deferred disk writes at simulation completion
- Configurable output formats (JSON Lines, compressed)
- Automatic file rotation and management
- Event filtering and selective logging
- Raw data dictionaries for maximum performance

Architecture:
- Inherits from RawDataObserver for zero-overhead storage
- Uses RawDataWriter for efficient disk persistence
- No processing overhead during simulation
- Translation deferred to when data is needed
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING

from .base_observer import BaseObserver
from ..raw_data.raw_data_observer import RawDataObserver
from ..raw_data.raw_data_writer import RawDataWriter

if TYPE_CHECKING:
    from ..config import ObservabilityConfig
    from ..events import SimulationEvent


class FileObserver(BaseObserver, RawDataObserver):
    """High-performance structured file logging observer using raw data architecture.
    
    Implements efficient file-based logging using the new raw data recording
    architecture for zero-overhead performance. Stores raw simulation data
    during simulation and writes to disk at completion.
    
    Architecture:
    - Inherits from both BaseObserver (for configuration) and RawDataObserver (for storage)
    - Zero-overhead recording during simulation using raw data dictionaries
    - Deferred disk writes using RawDataWriter at simulation completion
    - No processing overhead during simulation execution
    """

    def __init__(self, config: ObservabilityConfig, output_path: Path, 
                 format: str = 'jsonl', compress: bool = True,
                 compression_level: int = 6, max_file_size_mb: int = 100,
                 enable_rotation: bool = True):
        """Initialize the file observer with raw data architecture.
        
        Args:
            config: Observability configuration
            output_path: Path where log files will be written
            format: Output format ('jsonl' only - raw data format)
            compress: Whether to compress output files with gzip (default True)
            compression_level: Gzip compression level 1-9 (default 6)
            max_file_size_mb: Maximum file size before rotation in MB (default 100)
            enable_rotation: Whether to enable file rotation (default True)
        """
        # Initialize both parent classes
        BaseObserver.__init__(self, config)
        RawDataObserver.__init__(self)
        
        self._output_path = Path(output_path)
        self._format = format  # Only 'jsonl' supported for raw data
        
        # Initialize raw data writer for disk persistence
        self._raw_data_writer = RawDataWriter(
            compress=compress,
            compression_level=compression_level,
            max_file_size_mb=max_file_size_mb,
            enable_rotation=enable_rotation,
            atomic_writes=True
        )
        
        # Statistics (will be updated by raw data writer)
        self._events_written = 0
        self._bytes_written = 0
        self._last_write_time = 0.0
        
        # Initialize file output directory
        self._initialize_file_output()
    
    def _initialize_file_output(self) -> None:
        """Initialize file output directory for raw data writer."""
        # Create parent directories if they don't exist
        self._output_path.parent.mkdir(parents=True, exist_ok=True)

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
            'debug_log',
            'performance_monitor',
            'agent_decision',
            'resource_event',
            'economic_decision'
        }
        
        # Add behavioral events if behavioral aggregation is enabled
        if getattr(self._config, 'behavioral_aggregation', False):
            self._enabled_event_types.add('behavioral_aggregation')
        
        # Add correlation events if correlation tracking is enabled  
        if getattr(self._config, 'correlation_tracking', False):
            self._enabled_event_types.add('correlation_analysis')

    def notify(self, event: SimulationEvent) -> None:
        """Handle a simulation event by recording raw data.
        
        This method now uses the raw data recording architecture for zero-overhead
        performance. Events are stored as raw dictionaries with no processing.
        
        Args:
            event: The simulation event to log
        """
        if not self.is_enabled(event.event_type):
            return
        
        # Extract raw data from event and record using appropriate method
        step = getattr(event, 'step', 0)
        
        if event.event_type == 'trade_execution':
            self.record_trade(
                step=step,
                seller_id=getattr(event, 'seller_id', -1),
                buyer_id=getattr(event, 'buyer_id', -1),
                give_type=getattr(event, 'give_type', ''),
                take_type=getattr(event, 'take_type', ''),
                delta_u_seller=getattr(event, 'delta_u_seller', 0.0),
                delta_u_buyer=getattr(event, 'delta_u_buyer', 0.0),
                trade_location_x=getattr(event, 'trade_location_x', -1),
                trade_location_y=getattr(event, 'trade_location_y', -1)
            )
        elif event.event_type == 'agent_mode_change':
            self.record_mode_change(
                step=step,
                agent_id=getattr(event, 'agent_id', -1),
                old_mode=getattr(event, 'old_mode', ''),
                new_mode=getattr(event, 'new_mode', ''),
                reason=getattr(event, 'reason', '')
            )
        elif event.event_type == 'resource_collection':
            self.record_resource_collection(
                step=step,
                agent_id=getattr(event, 'agent_id', -1),
                x=getattr(event, 'x', -1),
                y=getattr(event, 'y', -1),
                resource_type=getattr(event, 'resource_type', ''),
                amount_collected=getattr(event, 'amount_collected', 1),
                utility_gained=getattr(event, 'utility_gained', 0.0),
                carrying_after=getattr(event, 'carrying_after', None)
            )
        elif event.event_type == 'debug_log':
            self.record_debug_log(
                step=step,
                category=getattr(event, 'category', ''),
                message=getattr(event, 'message', ''),
                agent_id=getattr(event, 'agent_id', -1)
            )
        elif event.event_type == 'performance_monitor':
            self.record_performance_monitor(
                step=step,
                metric_name=getattr(event, 'metric_name', ''),
                metric_value=getattr(event, 'metric_value', 0.0),
                threshold_exceeded=getattr(event, 'threshold_exceeded', False),
                details=getattr(event, 'details', '')
            )
        elif event.event_type == 'agent_decision':
            self.record_agent_decision(
                step=step,
                agent_id=getattr(event, 'agent_id', -1),
                decision_type=getattr(event, 'decision_type', ''),
                decision_details=getattr(event, 'decision_details', ''),
                utility_delta=getattr(event, 'utility_delta', 0.0),
                position_x=getattr(event, 'position_x', -1),
                position_y=getattr(event, 'position_y', -1)
            )
        elif event.event_type == 'resource_event':
            self.record_resource_event(
                step=step,
                event_type_detail=getattr(event, 'event_type_detail', ''),
                position_x=getattr(event, 'position_x', -1),
                position_y=getattr(event, 'position_y', -1),
                resource_type=getattr(event, 'resource_type', ''),
                amount=getattr(event, 'amount', 1),
                agent_id=getattr(event, 'agent_id', -1)
            )
        elif event.event_type == 'economic_decision':
            self.record_economic_decision(
                step=step,
                agent_id=getattr(event, 'agent_id', -1),
                decision_type=getattr(event, 'decision_type', ''),
                decision_context=getattr(event, 'decision_context', ''),
                utility_before=getattr(event, 'utility_before', 0.0),
                utility_after=getattr(event, 'utility_after', 0.0),
                opportunity_cost=getattr(event, 'opportunity_cost', 0.0),
                alternatives_considered=getattr(event, 'alternatives_considered', 0),
                decision_time_ms=getattr(event, 'decision_time_ms', 0.0),
                position_x=getattr(event, 'position_x', -1),
                position_y=getattr(event, 'position_y', -1)
            )
        else:
            # For unknown event types, record as generic debug log
            self.record_debug_log(
                step=step,
                category='UNKNOWN_EVENT',
                message=f"Unknown event type: {event.event_type}",
                agent_id=-1
            )

    def flush_step(self, step: int) -> None:
        """Handle end-of-step boundary with zero overhead.
        
        In the raw data architecture, no processing is done at step boundaries.
        All data is stored in memory and written to disk only at simulation completion.
        
        Args:
            step: The simulation step that just completed
        """
        # Zero overhead - no processing during simulation
        # Raw data is stored in memory and written at simulation end
        pass

    def close(self) -> None:
        """Close the file observer and write raw data to disk."""
        # Write all raw data to disk at simulation completion
        if not self._closed and len(self._events) > 0:
            try:
                # Use raw data writer to flush all events to disk
                write_result = self._raw_data_writer.flush_to_disk(
                    events=self.get_all_events(),
                    filepath=self._output_path,
                    append=False
                )
                
                # Update statistics from write result
                self._events_written = write_result['events_written']
                self._bytes_written = write_result['bytes_written']
                self._last_write_time = time.time()
                
            except Exception as e:
                print(f"Warning: Failed to write raw data to disk: {e}")
        
        # Call parent close method (this sets _closed = True)
        super().close()
        
        # Clear raw data from memory after writing
        self.clear_events()

    def get_observer_stats(self) -> Dict[str, Any]:
        """Get file observer statistics.
        
        Returns:
            Dictionary containing file observer metrics
        """
        base_stats = super().get_observer_stats()
        raw_data_stats = self.get_statistics()
        writer_stats = self._raw_data_writer.get_statistics()
        
        file_stats = {
            'output_path': str(self._output_path),
            'format': self._format,
            'events_written': self._events_written,
            'bytes_written': self._bytes_written,
            'last_write_time': self._last_write_time,
            'raw_data_events': raw_data_stats['total_events'],
            'raw_data_types': list(raw_data_stats['event_types']),
            'writer_files_written': writer_stats['files_written'],
            'writer_compression_ratio': writer_stats['compression_ratio'],
            'writer_config': self._raw_data_writer.get_configuration()
        }
        
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
        # Determine new path
        if new_path is None:
            timestamp = int(time.time())
            stem = self._output_path.stem
            suffix = self._output_path.suffix
            new_path = self._output_path.parent / f"{stem}_{timestamp}{suffix}"
        
        # Update path for future writes
        self._output_path = new_path
        
    def __repr__(self) -> str:
        """String representation of the file observer."""
        return f"FileObserver(path={self._output_path}, format={self._format}, events={len(self._events)}, closed={self._closed})"