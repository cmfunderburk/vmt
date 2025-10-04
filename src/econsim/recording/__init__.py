"""
Simulation Callbacks Module

This module provides callback functionality for simulation monitoring and progress tracking.
The old recording system has been replaced by the comprehensive delta system.

Key Components:
- SimulationCallbacks: Callback system for real-time monitoring
- Progress and performance tracking during simulation execution
- Integration with the comprehensive delta system for recording

Usage:
    from econsim.recording import SimulationCallbacks, create_simple_progress_callback
    
    # Create callback system for monitoring
    callbacks = SimulationCallbacks()
    callbacks.add_progress_callback(my_progress_handler)
    callbacks.add_performance_callback(my_performance_handler)
"""

from .callbacks import SimulationCallbacks, create_simple_progress_callback, create_performance_callback

__all__ = [
    'SimulationCallbacks',
    'create_simple_progress_callback',
    'create_performance_callback'
]
