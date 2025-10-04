"""
Visual Delta System for Pygame Playback

This module provides simple delta-based recording and playback for pygame visualization.
It tracks only the visual changes needed for rendering, avoiding complex simulation reconstruction.

Key Components:
- VisualDelta: Represents visual changes at each step
- VisualDeltaRecorder: Records deltas during simulation
- DeltaPlaybackController: Manages delta-based playback for pygame
"""

from .visual_delta import VisualDelta
from .delta_recorder import VisualDeltaRecorder  
from .delta_controller import DeltaPlaybackController

__all__ = [
    'VisualDelta',
    'VisualDeltaRecorder', 
    'DeltaPlaybackController'
]
