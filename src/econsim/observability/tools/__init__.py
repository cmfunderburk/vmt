"""Analysis tools for the observability system.

This package provides tools for working with optimized log formats,
including analysis tools and validation utilities.

Key components:
- OptimizedLogAnalyzer: Comprehensive analysis of optimized log files
- Performance metrics calculation
- Behavioral pattern analysis

Usage:
    from econsim.observability.tools import OptimizedLogAnalyzer
    
    analyzer = OptimizedLogAnalyzer()
    results = analyzer.analyze_log_file("optimized_log.jsonl")
"""

from .optimized_analyzer import OptimizedLogAnalyzer, analyze_optimized_log

__all__ = [
    "OptimizedLogAnalyzer",
    "analyze_optimized_log",
]
