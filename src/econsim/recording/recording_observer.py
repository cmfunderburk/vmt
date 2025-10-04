"""
Recording Observer: Integrates simulation recording with the observability system.

This observer captures simulation state and events for efficient playback storage.
It implements a hybrid snapshot + event recording strategy optimized for fast seeking
and minimal memory usage during playback.

Key Features:
- Integrates with existing observability system
- Captures periodic snapshots for fast seeking
- Records events between snapshots for incremental updates
- Zero-overhead recording during simulation
- Automatic file management and cleanup

Performance Targets:
- Recording overhead: < 10% of simulation time
- Memory usage: < 2x simulation memory during recording
- File size: < 50MB for 10,000 steps with 100 agents
- Snapshot interval: Configurable (default 100 steps)

Usage:
    from econsim.recording import RecordingObserver
    
    # Create observer for recording
    observer = RecordingObserver(
        output_path="simulation.vmt",
        snapshot_interval=100
    )
    
    # Register with simulation
    simulation._observer_registry.register(observer)
    
    # Run simulation - recording happens automatically
    # Finalize recording when done
    observer.finalize_recording()
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..observability.observers import BaseObserver
from ..observability.raw_data import RawDataObserver
from ..simulation.world import Simulation
from .simulation_output import SimulationOutputFile, create_simulation_output

try:
    from ..observability.events import SimulationEvent
except ImportError:
    # Fallback for type checking
    SimulationEvent = Any


class RecordingObserver(BaseObserver, RawDataObserver):
    """Observer that records simulation state and events for playback.
    
    Integrates with the existing observability system to capture simulation
    state and events in an efficient binary format optimized for playback.
    Uses a hybrid snapshot + event recording strategy for fast seeking.
    
    Architecture:
    - Inherits from BaseObserver (for configuration) and RawDataObserver (for storage)
    - Records periodic snapshots for fast seeking to any step
    - Captures events between snapshots for incremental state reconstruction
    - Uses SimulationOutputFile for efficient binary storage
    - Zero-overhead recording during simulation execution
    """
    
    def __init__(self, 
                 output_path: Union[str, Path],
                 snapshot_interval: int = 100,
                 config_hash: str = "",
                 enabled: bool = True):
        """Initialize recording observer.
        
        Args:
            output_path: Path where simulation output file will be saved
            snapshot_interval: Steps between snapshots (default 100)
            config_hash: Configuration hash for validation
            enabled: Whether recording is enabled (default True)
        """
        # Initialize both parent classes
        BaseObserver.__init__(self, enabled=enabled)
        RawDataObserver.__init__(self)
        
        self.output_path = Path(output_path)
        self.snapshot_interval = snapshot_interval
        self.config_hash = config_hash
        
        # Recording state
        self.output_file: Optional[SimulationOutputFile] = None
        self.simulation: Optional[Simulation] = None
        self.current_step = 0
        self.recording_start_time = 0.0
        
        # Performance tracking
        self.total_recording_time = 0.0
        self.snapshot_count = 0
        self.event_count = 0
        
        # Event filtering for recording
        self._initialize_event_filtering()
    
    def _initialize_event_filtering(self) -> None:
        """Initialize event type filtering for recording.
        
        Only records events that are necessary for playback reconstruction.
        Excludes debug and performance events that don't affect simulation state.
        """
        self._enabled_event_types = {
            # Core simulation events
            'agent_move',
            'resource_collect',
            'resource_deposit',
            'trade_execute',
            'agent_mode_change',
            
            # Economic events
            'economic_decision',
            'preference_change',
            
            # Resource events
            'resource_spawn',
            'resource_deplete',
            
            # Trading events
            'trade_intent',
            'trade_negotiation'
        }
    
    def start_recording(self, simulation: Simulation) -> None:
        """Start recording simulation.
        
        Args:
            simulation: Simulation instance to record
        """
        if not self.enabled:
            return
        
        self.simulation = simulation
        self.recording_start_time = time.time()
        
        # Create output file
        self.output_file = create_simulation_output(
            self.output_path,
            snapshot_interval=self.snapshot_interval,
            config_hash=self.config_hash
        )
        
        # Record initial snapshot (step 0)
        self._record_snapshot()
    
    def notify(self, event: SimulationEvent) -> None:
        """Handle simulation event by recording raw data.
        
        Args:
            event: Simulation event to record
        """
        if not self.enabled or not self.output_file:
            return
        
        if not self.is_enabled(event.event_type):
            return
        
        # Extract raw data from event and record using appropriate method
        step = getattr(event, 'step', 0)
        self.current_step = max(self.current_step, step)
        
        if event.event_type == 'agent_move':
            self.record_agent_move(
                step=step,
                agent_id=getattr(event, 'agent_id', -1),
                old_x=getattr(event, 'old_x', -1),
                old_y=getattr(event, 'old_y', -1),
                new_x=getattr(event, 'new_x', -1),
                new_y=getattr(event, 'new_y', -1)
            )
        elif event.event_type == 'resource_collect':
            self.record_resource_collect(
                step=step,
                agent_id=getattr(event, 'agent_id', -1),
                resource_type=getattr(event, 'resource_type', ''),
                quantity=getattr(event, 'quantity', 1),
                position_x=getattr(event, 'position_x', -1),
                position_y=getattr(event, 'position_y', -1)
            )
        elif event.event_type == 'resource_deposit':
            self.record_resource_deposit(
                step=step,
                agent_id=getattr(event, 'agent_id', -1),
                resource_type=getattr(event, 'resource_type', ''),
                quantity=getattr(event, 'quantity', 1)
            )
        elif event.event_type == 'trade_execute':
            self.record_trade_execute(
                step=step,
                seller_id=getattr(event, 'seller_id', -1),
                buyer_id=getattr(event, 'buyer_id', -1),
                give_type=getattr(event, 'give_type', ''),
                take_type=getattr(event, 'take_type', ''),
                give_quantity=getattr(event, 'give_quantity', 1),
                take_quantity=getattr(event, 'take_quantity', 1),
                position_x=getattr(event, 'trade_location_x', -1),
                position_y=getattr(event, 'trade_location_y', -1)
            )
        elif event.event_type == 'agent_mode_change':
            self.record_agent_mode_change(
                step=step,
                agent_id=getattr(event, 'agent_id', -1),
                old_mode=getattr(event, 'old_mode', ''),
                new_mode=getattr(event, 'new_mode', ''),
                reason=getattr(event, 'reason', '')
            )
        elif event.event_type == 'economic_decision':
            self.record_economic_decision(
                step=step,
                agent_id=getattr(event, 'agent_id', -1),
                decision_type=getattr(event, 'decision_type', ''),
                utility_before=getattr(event, 'utility_before', 0.0),
                utility_after=getattr(event, 'utility_after', 0.0),
                position_x=getattr(event, 'position_x', -1),
                position_y=getattr(event, 'position_y', -1)
            )
        elif event.event_type == 'resource_spawn':
            self.record_resource_spawn(
                step=step,
                resource_type=getattr(event, 'resource_type', ''),
                position_x=getattr(event, 'position_x', -1),
                position_y=getattr(event, 'position_y', -1),
                quantity=getattr(event, 'quantity', 1)
            )
        elif event.event_type == 'resource_deplete':
            self.record_resource_deplete(
                step=step,
                resource_type=getattr(event, 'resource_type', ''),
                position_x=getattr(event, 'position_x', -1),
                position_y=getattr(event, 'position_y', -1),
                quantity=getattr(event, 'quantity', 1)
            )
        
        self.event_count += 1
    
    def flush_step(self, step: int) -> None:
        """Handle end-of-step boundary.
        
        Records snapshot if interval reached and captures step completion.
        
        Args:
            step: The simulation step that just completed
        """
        if not self.enabled or not self.output_file:
            return
        
        self.current_step = step
        
        # Record snapshot if interval reached
        if (step % self.snapshot_interval == 0 and step > 0):
            self._record_snapshot()
        
        # Record step completion event
        self.record_step_complete(
            step=step,
            timestamp=time.time(),
            agent_count=len(self.simulation.agents) if self.simulation else 0,
            resource_count=self._count_resources() if self.simulation else 0
        )
    
    def _record_snapshot(self) -> None:
        """Record a simulation snapshot."""
        if not self.simulation or not self.output_file:
            return
        
        # Get events for this step
        step_events = self._get_events_for_current_step()
        
        # Record step with snapshot
        self.output_file.record_step(self.simulation, step_events)
        self.snapshot_count += 1
        
        # Clear events for next step
        self._clear_step_events()
    
    def _get_events_for_current_step(self) -> List[Dict[str, Any]]:
        """Get all events recorded for the current step."""
        # Get events from RawDataObserver that match current step
        step_events = []
        for event in self._events:
            if event.get('step', 0) == self.current_step:
                step_events.append(event)
        
        return step_events
    
    def _clear_step_events(self) -> None:
        """Clear events for current step to prepare for next step."""
        # Remove events for current step
        self._events = [
            event for event in self._events 
            if event.get('step', 0) != self.current_step
        ]
    
    def _count_resources(self) -> int:
        """Count total resources in simulation grid."""
        if not self.simulation:
            return 0
        
        count = 0
        for x in range(self.simulation.grid.width):
            for y in range(self.simulation.grid.height):
                cell = self.simulation.grid.get_cell(x, y)
                if cell and cell.resources:
                    count += sum(cell.resources.values())
        
        return count
    
    def finalize_recording(self) -> None:
        """Finalize recording and write to disk.
        
        Must be called when simulation recording is complete.
        """
        if not self.enabled or not self.output_file:
            return
        
        # Record final snapshot if not already recorded
        if self.current_step > 0 and (self.current_step % self.snapshot_interval != 0):
            self._record_snapshot()
        
        # Finalize output file
        self.output_file.finalize_recording()
        
        # Update performance tracking
        self.total_recording_time = time.time() - self.recording_start_time
    
    def get_recording_stats(self) -> Dict[str, Any]:
        """Get recording statistics.
        
        Returns:
            Dictionary with recording performance metrics
        """
        if not self.output_file:
            return {}
        
        file_info = self.output_file.get_file_info()
        
        return {
            'output_path': str(self.output_path),
            'total_steps': file_info.get('total_steps', 0),
            'snapshot_count': self.snapshot_count,
            'event_count': self.event_count,
            'recording_time_seconds': self.total_recording_time,
            'file_size_bytes': file_info.get('file_size_bytes', 0),
            'snapshot_interval': self.snapshot_interval,
            'config_hash': self.config_hash,
            'enabled': self.enabled
        }
    
    def close(self) -> None:
        """Clean up recording resources."""
        if self.output_file:
            self.finalize_recording()
            self.output_file = None
        
        self.simulation = None
    
    # ============================================================================
    # RAW DATA RECORDING METHODS
    # ============================================================================
    
    def record_agent_move(self, step: int, agent_id: int, old_x: int, old_y: int, 
                         new_x: int, new_y: int) -> None:
        """Record agent movement event."""
        self._events.append({
            'type': 'agent_move',
            'step': step,
            'agent_id': agent_id,
            'old_x': old_x,
            'old_y': old_y,
            'new_x': new_x,
            'new_y': new_y,
            'timestamp': time.time()
        })
    
    def record_resource_collect(self, step: int, agent_id: int, resource_type: str,
                               quantity: int, position_x: int, position_y: int) -> None:
        """Record resource collection event."""
        self._events.append({
            'type': 'resource_collect',
            'step': step,
            'agent_id': agent_id,
            'resource_type': resource_type,
            'quantity': quantity,
            'position_x': position_x,
            'position_y': position_y,
            'timestamp': time.time()
        })
    
    def record_resource_deposit(self, step: int, agent_id: int, resource_type: str,
                               quantity: int) -> None:
        """Record resource deposit event."""
        self._events.append({
            'type': 'resource_deposit',
            'step': step,
            'agent_id': agent_id,
            'resource_type': resource_type,
            'quantity': quantity,
            'timestamp': time.time()
        })
    
    def record_trade_execute(self, step: int, seller_id: int, buyer_id: int,
                            give_type: str, take_type: str, give_quantity: int,
                            take_quantity: int, position_x: int, position_y: int) -> None:
        """Record trade execution event."""
        self._events.append({
            'type': 'trade_execute',
            'step': step,
            'seller_id': seller_id,
            'buyer_id': buyer_id,
            'give_type': give_type,
            'take_type': take_type,
            'give_quantity': give_quantity,
            'take_quantity': take_quantity,
            'position_x': position_x,
            'position_y': position_y,
            'timestamp': time.time()
        })
    
    def record_agent_mode_change(self, step: int, agent_id: int, old_mode: str,
                                new_mode: str, reason: str) -> None:
        """Record agent mode change event."""
        self._events.append({
            'type': 'agent_mode_change',
            'step': step,
            'agent_id': agent_id,
            'old_mode': old_mode,
            'new_mode': new_mode,
            'reason': reason,
            'timestamp': time.time()
        })
    
    def record_economic_decision(self, step: int, agent_id: int, decision_type: str,
                                utility_before: float, utility_after: float,
                                position_x: int, position_y: int) -> None:
        """Record economic decision event."""
        self._events.append({
            'type': 'economic_decision',
            'step': step,
            'agent_id': agent_id,
            'decision_type': decision_type,
            'utility_before': utility_before,
            'utility_after': utility_after,
            'position_x': position_x,
            'position_y': position_y,
            'timestamp': time.time()
        })
    
    def record_resource_spawn(self, step: int, resource_type: str, position_x: int,
                             position_y: int, quantity: int) -> None:
        """Record resource spawn event."""
        self._events.append({
            'type': 'resource_spawn',
            'step': step,
            'resource_type': resource_type,
            'position_x': position_x,
            'position_y': position_y,
            'quantity': quantity,
            'timestamp': time.time()
        })
    
    def record_resource_deplete(self, step: int, resource_type: str, position_x: int,
                               position_y: int, quantity: int) -> None:
        """Record resource depletion event."""
        self._events.append({
            'type': 'resource_deplete',
            'step': step,
            'resource_type': resource_type,
            'position_x': position_x,
            'position_y': position_y,
            'quantity': quantity,
            'timestamp': time.time()
        })
    
    def record_step_complete(self, step: int, timestamp: float, agent_count: int,
                            resource_count: int) -> None:
        """Record step completion event."""
        self._events.append({
            'type': 'step_complete',
            'step': step,
            'timestamp': timestamp,
            'agent_count': agent_count,
            'resource_count': resource_count
        })
    
    def __repr__(self) -> str:
        """String representation of recording observer."""
        return (f"RecordingObserver({self.output_path}, "
                f"interval={self.snapshot_interval}, "
                f"enabled={self.enabled})")
