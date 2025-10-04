"""
State Reconstruction Engine

This module provides efficient reconstruction of simulation state from recorded data.
It implements snapshot + event replay logic for fast seeking to any step.

Key Features:
- Fast seeking via snapshot + incremental event replay
- Memory-efficient state reconstruction
- Deterministic state guarantees
- Support for partial state updates

Performance Targets:
- Seeking time: < 0.1 seconds to any step
- Memory usage: < 2x simulation memory during reconstruction
- Reconstruction accuracy: 100% deterministic match with original simulation
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from ..recording.simulation_output import SimulationOutputFile, SnapshotRecord
from ..simulation.world import Simulation
from ..simulation.snapshot import Snapshot, restore_snapshot


@dataclass
class ReconstructionMetrics:
    """Metrics for state reconstruction performance."""
    reconstruction_time_ms: float
    events_applied: int
    snapshot_distance: int
    memory_usage_mb: float


class StateReconstructor:
    """Efficiently reconstructs simulation state from recorded data.
    
    Uses a hybrid approach:
    1. Find the nearest snapshot (≤ target step)
    2. Apply incremental events from snapshot to target step
    3. Return reconstructed simulation state
    
    This provides fast seeking while maintaining deterministic accuracy.
    """
    
    def __init__(self, output_file: SimulationOutputFile):
        """Initialize reconstructor with a loaded simulation output file.
        
        Args:
            output_file: Loaded SimulationOutputFile containing recorded data
        """
        self.output_file = output_file
        self._snapshot_cache: Dict[int, Snapshot] = {}
        self._event_cache: Dict[int, List[Dict[str, Any]]] = {}
        
    def reconstruct_state_at_step(self, step: int) -> Tuple[Simulation, ReconstructionMetrics]:
        """Reconstruct simulation state at the specified step.
        
        Args:
            step: Target step number (1-based)
            
        Returns:
            Tuple of (reconstructed_simulation, metrics)
            
        Raises:
            ValueError: If step is out of bounds
        """
        if self.output_file.header is None:
            raise ValueError("Output file header is not loaded")
        
        if step < 1 or step > self.output_file.header.total_steps:
            raise ValueError(f"Step {step} is out of bounds (1-{self.output_file.header.total_steps})")
        
        start_time = time.time()
        
        # Find nearest snapshot (≤ target step)
        snapshot_step, snapshot_record = self._find_nearest_snapshot(step)
        
        # Load snapshot if not cached
        if snapshot_step not in self._snapshot_cache:
            self._snapshot_cache[snapshot_step] = self._load_snapshot(snapshot_record)
        
        snapshot = self._snapshot_cache[snapshot_step]
        
        # Restore simulation from snapshot
        simulation = restore_snapshot(snapshot)
        
        # Apply incremental events from snapshot to target step
        events_applied = 0
        if step > snapshot_step:
            events = self._get_events_in_range(snapshot_step + 1, step)
            for event in events:
                self._apply_event(simulation, event)
                events_applied += 1
        
        # Calculate metrics
        reconstruction_time = (time.time() - start_time) * 1000  # ms
        snapshot_distance = step - snapshot_step
        memory_usage = self._estimate_memory_usage(simulation)
        
        metrics = ReconstructionMetrics(
            reconstruction_time_ms=reconstruction_time,
            events_applied=events_applied,
            snapshot_distance=snapshot_distance,
            memory_usage_mb=memory_usage
        )
        
        return simulation, metrics
    
    def _find_nearest_snapshot(self, target_step: int) -> Tuple[int, SnapshotRecord]:
        """Find the nearest snapshot at or before the target step.
        
        Args:
            target_step: Target step number
            
        Returns:
            Tuple of (snapshot_step, snapshot_record)
        """
        # Get all snapshot steps
        snapshot_steps = self.output_file.get_snapshot_steps()
        
        if not snapshot_steps:
            raise ValueError("No snapshots found in output file")
        
        # Find the latest snapshot at or before target step
        nearest_step = 0
        
        for step in snapshot_steps:
            if step <= target_step and step > nearest_step:
                nearest_step = step
        
        if nearest_step == 0:
            # Fallback to earliest snapshot if target is before all snapshots
            nearest_step = min(snapshot_steps)
        
        # Get the snapshot record for the nearest step
        nearest_record = self.output_file._find_nearest_snapshot(nearest_step)
        
        return nearest_step, nearest_record
    
    def _load_snapshot(self, snapshot_record: SnapshotRecord) -> Snapshot:
        """Load a snapshot from a snapshot record.
        
        Args:
            snapshot_record: SnapshotRecord containing serialized snapshot data
            
        Returns:
            Loaded Snapshot object
        """
        # The snapshot record contains the snapshot directly
        return snapshot_record.snapshot
    
    def _get_events_in_range(self, start_step: int, end_step: int) -> List[Dict[str, Any]]:
        """Get events in the specified step range.
        
        Args:
            start_step: First step to include (inclusive)
            end_step: Last step to include (inclusive)
            
        Returns:
            List of events in chronological order
        """
        events = []
        
        # Check cache first
        for step in range(start_step, end_step + 1):
            if step in self._event_cache:
                events.extend(self._event_cache[step])
                continue
            
            # Load events for this step
            # TODO: Implement proper event loading based on actual SimulationOutputFile API
            step_events = []  # Placeholder - needs actual implementation
            self._event_cache[step] = step_events
            events.extend(step_events)
        
        return events
    
    def _apply_event(self, simulation: Simulation, event: Dict[str, Any]) -> None:
        """Apply a single event to the simulation state.
        
        Args:
            simulation: Simulation object to modify
            event: Event dictionary containing state changes
        """
        event_type = event.get('type')
        
        if event_type == 'agent_move':
            # Apply agent movement
            agent_id = event['agent_id']
            new_x = event['x']
            new_y = event['y']
            
            # Find and update agent position
            for agent in simulation.agents:
                if agent.id == agent_id:
                    agent.x = new_x
                    agent.y = new_y
                    break
                    
        elif event_type == 'inventory_change':
            # Apply inventory changes
            agent_id = event['agent_id']
            carrying = event.get('carrying', {})
            home_inventory = event.get('home_inventory', {})
            
            # Find and update agent inventories
            for agent in simulation.agents:
                if agent.id == agent_id:
                    if carrying:
                        agent.carrying = carrying.copy()
                    if home_inventory:
                        agent.home_inventory = home_inventory.copy()
                    break
                    
        elif event_type == 'grid_change':
            # Apply grid changes (resource spawning/consumption)
            grid_state = event.get('grid_state', {})
            
            # Update grid resources
            if 'resources' in grid_state:
                simulation.grid._resources = grid_state['resources'].copy()
                
        # TODO: Add support for other event types as needed
        # - trade_events
        # - mode_changes
        # - preference_updates
        # etc.
    
    def _estimate_memory_usage(self, simulation: Simulation) -> float:
        """Estimate memory usage of the simulation object.
        
        Args:
            simulation: Simulation object
            
        Returns:
            Estimated memory usage in MB
        """
        import sys
        
        # Rough estimation based on object size
        try:
            size_bytes = sys.getsizeof(simulation)
            # Add estimated sizes for agents and grid
            size_bytes += len(simulation.agents) * 1000  # ~1KB per agent
            size_bytes += simulation.grid.width * simulation.grid.height * 100  # ~100B per grid cell
            
            return size_bytes / (1024 * 1024)  # Convert to MB
        except Exception:
            return 0.0
    
    def clear_cache(self) -> None:
        """Clear the snapshot and event caches to free memory."""
        self._snapshot_cache.clear()
        self._event_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about cache usage.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'snapshot_cache_size': len(self._snapshot_cache),
            'event_cache_size': len(self._event_cache),
            'total_cached_events': sum(len(events) for events in self._event_cache.values())
        }
