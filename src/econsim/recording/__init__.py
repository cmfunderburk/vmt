"""
Simulation Recording Module

This module provides efficient recording and playback capabilities for simulation runs.
It implements a binary serialization format optimized for fast seeking and minimal memory usage.

Key Components:
- SimulationOutputFile: Binary format for simulation recordings
- Snapshot-based recording with periodic full state captures
- Event-based incremental updates between snapshots
- Fast seeking to any step via snapshot + event replay

Performance Targets:
- File size: < 50MB for 10,000 steps with 100 agents
- Loading time: < 1 second for complete simulation
- Seeking time: < 0.1 seconds to any step
- Memory usage: < 2x simulation memory during playback
- Recording overhead: < 10% of simulation time

Usage:
    from econsim.recording import SimulationOutputFile, create_simulation_output, load_simulation_output
    
    # During simulation recording
    output_file = create_simulation_output("simulation.vmt")
    output_file.record_step(simulation, events)
    output_file.finalize_recording()
    
    # During playback
    output_file = load_simulation_output("simulation.vmt")
    state = output_file.get_state_at_step(5000)
"""

from .simulation_output import (
    SimulationOutputFile,
    SimulationOutputHeader,
    SnapshotRecord,
    create_simulation_output,
    load_simulation_output
)

from .callbacks import SimulationCallbacks, create_simple_progress_callback, create_performance_callback
from .headless_runner import (
    HeadlessSimulationRunner,
    run_headless_simulation,
    run_headless_simulation_no_recording
)

__all__ = [
    'SimulationOutputFile',
    'SimulationOutputHeader', 
    'SnapshotRecord',
    'create_simulation_output',
    'load_simulation_output',
    'SimulationCallbacks',
    'create_simple_progress_callback',
    'create_performance_callback',
    'HeadlessSimulationRunner',
    'run_headless_simulation',
    'run_headless_simulation_no_recording'
]
