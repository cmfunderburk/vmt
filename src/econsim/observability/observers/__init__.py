"""Modular observer implementations for simulation observability.

This module provides concrete observer implementations that replace the
monolithic GUILogger with focused, testable components. Each observer
handles a specific aspect of simulation monitoring and analysis.

Observer Types:
- FileObserver: High-performance structured file logging
- MemoryObserver: In-memory event collection for testing
- EducationalObserver: Educational analytics and behavioral insights
- PerformanceObserver: Performance monitoring and optimization metrics

Design Principles:
- Single responsibility for each observer type
- Efficient event processing with minimal overhead
- Educational features preserved from legacy GUILogger
- Buffer-based architecture for performance optimization
"""

from .base_observer import BaseObserver
from .file_observer import FileObserver
from .memory_observer import MemoryObserver
from .educational_observer import EducationalObserver
from .performance_observer import PerformanceObserver

__all__ = [
    'BaseObserver',
    'FileObserver',
    'MemoryObserver', 
    'EducationalObserver',
    'PerformanceObserver',
]