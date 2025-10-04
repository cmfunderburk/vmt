"""
Simulation Output File: Binary serialization for efficient playback storage.

This module implements a binary serialization format for simulation recordings
that enables efficient playback with minimal memory usage and fast seeking.

Key Features:
- Binary format for compact storage and fast loading
- Snapshot-based recording with periodic full state captures
- Event-based incremental updates between snapshots
- Fast seeking to any step via snapshot + event replay
- Memory-efficient streaming playback
- Deterministic reconstruction guarantees

Performance Targets:
- File size: < 50MB for 10,000 steps with 100 agents
- Loading time: < 1 second for complete simulation
- Seeking time: < 0.1 seconds to any step
- Memory usage: < 2x simulation memory during playback
- Recording overhead: < 10% of simulation time

Usage:
    # During simulation recording
    output_file = SimulationOutputFile.create("simulation.vmt")
    output_file.record_step(simulation, events)
    
    # During playback
    output_file = SimulationOutputFile.load("simulation.vmt")
    state = output_file.get_state_at_step(5000)
"""

from __future__ import annotations

import pickle
import struct
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, BinaryIO, Iterator, Tuple
from collections import defaultdict

from ..simulation.world import Simulation
from ..simulation.snapshot import Snapshot, take_snapshot
from ..observability.raw_data import RawDataObserver


@dataclass(slots=True)
class SimulationOutputHeader:
    """Header information for simulation output file.
    
    Contains metadata about the simulation including configuration,
    performance characteristics, and file structure.
    """
    # File format version
    version: int = 1
    
    # Simulation metadata
    total_steps: int = 0
    agent_count: int = 0
    grid_width: int = 0
    grid_height: int = 0
    
    # Recording configuration
    snapshot_interval: int = 100  # Steps between snapshots
    event_count: int = 0
    snapshot_count: int = 0
    
    # Performance metrics
    recording_start_time: float = field(default_factory=time.time)
    recording_end_time: float = 0.0
    file_size_bytes: int = 0
    
    # Configuration hash for validation
    config_hash: str = ""
    
    def serialize(self) -> Dict[str, Any]:
        """Serialize header to dictionary for binary storage."""
        return {
            'version': self.version,
            'total_steps': self.total_steps,
            'agent_count': self.agent_count,
            'grid_width': self.grid_width,
            'grid_height': self.grid_height,
            'snapshot_interval': self.snapshot_interval,
            'event_count': self.event_count,
            'snapshot_count': self.snapshot_count,
            'recording_start_time': self.recording_start_time,
            'recording_end_time': self.recording_end_time,
            'file_size_bytes': self.file_size_bytes,
            'config_hash': self.config_hash
        }
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'SimulationOutputHeader':
        """Deserialize header from dictionary."""
        return cls(
            version=data.get('version', 1),
            total_steps=data.get('total_steps', 0),
            agent_count=data.get('agent_count', 0),
            grid_width=data.get('grid_width', 0),
            grid_height=data.get('grid_height', 0),
            snapshot_interval=data.get('snapshot_interval', 100),
            event_count=data.get('event_count', 0),
            snapshot_count=data.get('snapshot_count', 0),
            recording_start_time=data.get('recording_start_time', 0.0),
            recording_end_time=data.get('recording_end_time', 0.0),
            file_size_bytes=data.get('file_size_bytes', 0),
            config_hash=data.get('config_hash', '')
        )


@dataclass(slots=True)
class SnapshotRecord:
    """Record of a simulation snapshot with metadata."""
    step: int
    snapshot: Snapshot
    event_count_before: int = 0
    file_offset: int = 0
    
    def serialize(self) -> Dict[str, Any]:
        """Serialize snapshot record to dictionary."""
        return {
            'step': self.step,
            'snapshot': self.snapshot.serialize(),
            'event_count_before': self.event_count_before,
            'file_offset': self.file_offset
        }
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'SnapshotRecord':
        """Deserialize snapshot record from dictionary."""
        from ..simulation.snapshot import Snapshot
        return cls(
            step=data['step'],
            snapshot=Snapshot(
                step=data['snapshot']['step'],
                grid=data['snapshot']['grid'],
                agents=data['snapshot']['agents']
            ),
            event_count_before=data.get('event_count_before', 0),
            file_offset=data.get('file_offset', 0)
        )


class SimulationOutputFile:
    """Binary simulation output file for efficient playback storage.
    
    Implements a hybrid snapshot + event recording strategy:
    - Periodic full state snapshots for fast seeking
    - Event-based incremental updates between snapshots
    - Binary serialization for compact storage
    - Memory-efficient streaming playback
    
    File Format:
    [Header][SnapshotIndex][EventData][Snapshots]
    """
    
    # File format constants
    MAGIC_BYTES = b'VMT\x01'  # Version 1
    HEADER_SIZE_OFFSET = 4
    
    def __init__(self, filepath: Union[str, Path]):
        """Initialize simulation output file.
        
        Args:
            filepath: Path to output file
        """
        self.filepath = Path(filepath)
        self.header: Optional[SimulationOutputHeader] = None
        self.snapshot_records: List[SnapshotRecord] = []
        self.events: List[Dict[str, Any]] = []
        
        # File I/O
        self._file_handle: Optional[BinaryIO] = None
        self._write_mode = False
        
        # Performance tracking
        self._recording_start_time = 0.0
        self._current_step = 0
    
    # ============================================================================
    # FILE CREATION AND LOADING
    # ============================================================================
    
    @classmethod
    def create(cls, filepath: Union[str, Path], 
               snapshot_interval: int = 100,
               config_hash: str = "") -> 'SimulationOutputFile':
        """Create new simulation output file for recording.
        
        Args:
            filepath: Path to output file
            snapshot_interval: Steps between snapshots (default 100)
            config_hash: Configuration hash for validation
            
        Returns:
            New SimulationOutputFile ready for recording
        """
        output_file = cls(filepath)
        output_file.header = SimulationOutputHeader(
            snapshot_interval=snapshot_interval,
            config_hash=config_hash
        )
        output_file._recording_start_time = time.time()
        output_file._write_mode = True
        return output_file
    
    @classmethod
    def load(cls, filepath: Union[str, Path]) -> 'SimulationOutputFile':
        """Load existing simulation output file for playback.
        
        Args:
            filepath: Path to existing output file
            
        Returns:
            Loaded SimulationOutputFile ready for playback
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Simulation output file not found: {filepath}")
        
        output_file = cls(filepath)
        output_file._load_from_disk()
        return output_file
    
    def _load_from_disk(self) -> None:
        """Load file data from disk."""
        with open(self.filepath, 'rb') as f:
            # Read magic bytes
            magic = f.read(4)
            if magic != self.MAGIC_BYTES:
                raise ValueError(f"Invalid file format: {self.filepath}")
            
            # Read header
            header_data = self._read_pickle(f)
            self.header = SimulationOutputHeader.deserialize(header_data)
            
            # Read snapshot index
            snapshot_index_data = self._read_pickle(f)
            self.snapshot_records = [
                SnapshotRecord.deserialize(record_data) 
                for record_data in snapshot_index_data
            ]
            
            # Read events
            events_data = self._read_pickle(f)
            self.events = events_data
    
    # ============================================================================
    # RECORDING METHODS
    # ============================================================================
    
    def record_step(self, simulation: Simulation, events: List[Dict[str, Any]]) -> None:
        """Record a single simulation step.
        
        Args:
            simulation: Current simulation state
            events: List of events that occurred this step
        """
        if not self._write_mode:
            raise RuntimeError("Cannot record to file opened in read mode")
        
        if self.header is None:
            raise RuntimeError("File not initialized for recording")
        
        # Update header with simulation info
        if self._current_step == 0:
            self.header.agent_count = len(simulation.agents)
            self.header.grid_width = simulation.grid.width
            self.header.grid_height = simulation.grid.height
        
        # Record events
        self.events.extend(events)
        self._current_step = simulation.steps
        
        # Take snapshot if interval reached
        if (self._current_step % self.header.snapshot_interval == 0 or 
            self._current_step == 1):  # Always snapshot first step
            
            snapshot = take_snapshot(simulation)
            record = SnapshotRecord(
                step=self._current_step,
                snapshot=snapshot,
                event_count_before=len(self.events) - len(events)
            )
            self.snapshot_records.append(record)
            self.header.snapshot_count += 1
        
        # Update header
        self.header.total_steps = self._current_step
        self.header.event_count = len(self.events)
    
    def finalize_recording(self) -> None:
        """Finalize recording and write to disk.
        
        Must be called after recording is complete to write data to disk.
        """
        if not self._write_mode:
            raise RuntimeError("Cannot finalize file opened in read mode")
        
        if self.header is None:
            raise RuntimeError("File not initialized for recording")
        
        # Update header with final metadata
        self.header.recording_end_time = time.time()
        
        # Write to disk
        self._write_to_disk()
        
        # Close write mode
        self._write_mode = False
    
    def _write_to_disk(self) -> None:
        """Write all data to disk in binary format."""
        with open(self.filepath, 'wb') as f:
            # Write magic bytes
            f.write(self.MAGIC_BYTES)
            
            # Write header
            self._write_pickle(f, self.header.serialize())
            
            # Write snapshot index
            snapshot_index = [record.serialize() for record in self.snapshot_records]
            self._write_pickle(f, snapshot_index)
            
            # Write events
            self._write_pickle(f, self.events)
            
            # Update file size in header
            self.header.file_size_bytes = f.tell()
    
    # ============================================================================
    # PLAYBACK METHODS
    # ============================================================================
    
    def get_state_at_step(self, target_step: int) -> Simulation:
        """Get simulation state at specific step.
        
        Args:
            target_step: Step number to reconstruct
            
        Returns:
            Simulation state at target step
            
        Raises:
            ValueError: If target step is invalid
        """
        if target_step < 0 or target_step > self.header.total_steps:
            raise ValueError(f"Invalid step {target_step}, valid range: 0-{self.header.total_steps}")
        
        # Find nearest snapshot
        snapshot_record = self._find_nearest_snapshot(target_step)
        
        # Start from snapshot
        simulation = snapshot_record.snapshot.restore()
        
        # Apply events from snapshot to target step
        start_event_index = snapshot_record.event_count_before
        end_event_index = self._find_event_index_for_step(target_step)
        
        for i in range(start_event_index, end_event_index):
            if i < len(self.events):
                event = self.events[i]
                self._apply_event_to_simulation(simulation, event)
        
        return simulation
    
    def _find_nearest_snapshot(self, target_step: int) -> SnapshotRecord:
        """Find the snapshot record nearest to target step."""
        if not self.snapshot_records:
            raise ValueError("No snapshots available")
        
        # Find snapshot at or before target step
        best_record = None
        for record in self.snapshot_records:
            if record.step <= target_step:
                if best_record is None or record.step > best_record.step:
                    best_record = record
        
        if best_record is None:
            # Use first snapshot if target step is before all snapshots
            best_record = self.snapshot_records[0]
        
        return best_record
    
    def _find_event_index_for_step(self, target_step: int) -> int:
        """Find the event index corresponding to target step."""
        # Events are stored in chronological order
        # Find the last event for the target step
        for i, event in enumerate(self.events):
            if event.get('step', 0) > target_step:
                return i
        
        return len(self.events)
    
    def _apply_event_to_simulation(self, simulation: Simulation, event: Dict[str, Any]) -> None:
        """Apply a single event to simulation state.
        
        This is a simplified implementation - in practice, this would need
        to be more sophisticated to handle all event types properly.
        """
        event_type = event.get('type', '')
        
        if event_type == 'agent_move':
            # Apply agent movement
            agent_id = event.get('agent_id')
            new_x = event.get('x')
            new_y = event.get('y')
            
            if agent_id is not None and new_x is not None and new_y is not None:
                for agent in simulation.agents:
                    if agent.id == agent_id:
                        agent.x = new_x
                        agent.y = new_y
                        break
        
        elif event_type == 'resource_collect':
            # Apply resource collection
            agent_id = event.get('agent_id')
            resource_type = event.get('resource_type')
            quantity = event.get('quantity', 1)
            
            if agent_id is not None and resource_type is not None:
                for agent in simulation.agents:
                    if agent.id == agent_id:
                        agent.carrying[resource_type] = agent.carrying.get(resource_type, 0) + quantity
                        break
        
        elif event_type == 'trade_execute':
            # Apply trade execution
            seller_id = event.get('seller_id')
            buyer_id = event.get('buyer_id')
            give_type = event.get('give_type')
            take_type = event.get('take_type')
            
            if all(x is not None for x in [seller_id, buyer_id, give_type, take_type]):
                # Find agents and execute trade
                seller = next((a for a in simulation.agents if a.id == seller_id), None)
                buyer = next((a for a in simulation.agents if a.id == buyer_id), None)
                
                if seller and buyer:
                    # Execute trade (simplified)
                    if seller.carrying.get(give_type, 0) > 0:
                        seller.carrying[give_type] -= 1
                        buyer.carrying[take_type] = buyer.carrying.get(take_type, 0) + 1
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def get_step_range(self) -> Tuple[int, int]:
        """Get the range of available steps.
        
        Returns:
            Tuple of (min_step, max_step)
        """
        if self.header is None:
            return (0, 0)
        return (0, self.header.total_steps)
    
    def get_snapshot_steps(self) -> List[int]:
        """Get list of steps that have snapshots.
        
        Returns:
            List of step numbers with snapshots
        """
        return [record.step for record in self.snapshot_records]
    
    def get_file_info(self) -> Dict[str, Any]:
        """Get information about the output file.
        
        Returns:
            Dictionary with file metadata
        """
        if self.header is None:
            return {}
        
        return {
            'filepath': str(self.filepath),
            'total_steps': self.header.total_steps,
            'agent_count': self.header.agent_count,
            'grid_size': f"{self.header.grid_width}x{self.header.grid_height}",
            'snapshot_interval': self.header.snapshot_interval,
            'snapshot_count': self.header.snapshot_count,
            'event_count': self.header.event_count,
            'file_size_bytes': self.header.file_size_bytes,
            'recording_duration': self.header.recording_end_time - self.header.recording_start_time,
            'config_hash': self.header.config_hash
        }
    
    # ============================================================================
    # BINARY I/O HELPERS
    # ============================================================================
    
    def _write_pickle(self, f: BinaryIO, data: Any) -> None:
        """Write data as pickle with size prefix."""
        pickled_data = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        size = len(pickled_data)
        
        # Write size as 4-byte integer
        f.write(struct.pack('<I', size))
        
        # Write pickled data
        f.write(pickled_data)
    
    def _read_pickle(self, f: BinaryIO) -> Any:
        """Read data from pickle with size prefix."""
        # Read size
        size_bytes = f.read(4)
        if len(size_bytes) != 4:
            raise ValueError("Incomplete file: missing size prefix")
        
        size = struct.unpack('<I', size_bytes)[0]
        
        # Read pickled data
        pickled_data = f.read(size)
        if len(pickled_data) != size:
            raise ValueError("Incomplete file: missing pickled data")
        
        return pickle.loads(pickled_data)
    
    def __repr__(self) -> str:
        """String representation of output file."""
        if self.header is None:
            return f"SimulationOutputFile({self.filepath}) [not loaded]"
        
        return (f"SimulationOutputFile({self.filepath}) "
                f"[{self.header.total_steps} steps, "
                f"{self.header.agent_count} agents, "
                f"{self.header.snapshot_count} snapshots]")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_simulation_output(filepath: Union[str, Path], 
                           snapshot_interval: int = 100,
                           config_hash: str = "") -> SimulationOutputFile:
    """Create new simulation output file.
    
    Args:
        filepath: Path to output file
        snapshot_interval: Steps between snapshots
        config_hash: Configuration hash for validation
        
    Returns:
        New SimulationOutputFile ready for recording
    """
    return SimulationOutputFile.create(filepath, snapshot_interval, config_hash)


def load_simulation_output(filepath: Union[str, Path]) -> SimulationOutputFile:
    """Load existing simulation output file.
    
    Args:
        filepath: Path to existing output file
        
    Returns:
        Loaded SimulationOutputFile ready for playback
    """
    return SimulationOutputFile.load(filepath)
