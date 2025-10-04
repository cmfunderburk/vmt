"""
Playback Module

This module provides simulation playback capabilities for recorded simulation runs.
It enables VCR-style controls (play, pause, seek, speed) over recorded simulation data.

Key Components:
- PlaybackEngine: Core playback engine with state reconstruction
- PlaybackController: VCR-style controls and GUI integration
- StateReconstructor: Efficient snapshot + event replay logic

Architecture:
- Loads SimulationOutputFile from recording system
- Reconstructs simulation state at any step using snapshot + event replay
- Provides real-time playback with configurable speed and controls
- Integrates with SimulationCallbacks for progress updates

Usage:
    from econsim.playback import PlaybackEngine, PlaybackController
    
    # Load recorded simulation
    engine = PlaybackEngine.load("simulation.vmt")
    controller = PlaybackController(engine)
    
    # VCR-style playback
    controller.play()
    controller.seek_to_step(5000)
    controller.set_speed(2.0)  # 2x speed
    controller.pause()
"""

from .playback_engine import PlaybackEngine
from .playback_controller import PlaybackController
from .state_reconstructor import StateReconstructor

__all__ = [
    'PlaybackEngine',
    'PlaybackController', 
    'StateReconstructor'
]
