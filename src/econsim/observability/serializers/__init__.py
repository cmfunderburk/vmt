"""Optimized serialization modules for the observability system.

This package provides optimized event serialization capabilities that achieve
73% size reduction while retaining all information content, as specified in
the log_behavior_plan.md analysis.

Key components:
- OptimizedEventSerializer: Core serialization with field abbreviations and compression
- OptimizedLogWriter: High-performance writer for optimized log format
- Factory functions for easy integration with existing observers

Usage:
    from econsim.observability.serializers import create_optimized_log_writer
    
    writer = create_optimized_log_writer(Path("logs/optimized.jsonl"))
    writer.open()
    writer.write_event(my_event)
    writer.close()
"""

from .optimized_serializer import (
    OptimizedEventSerializer,
    OptimizedLogWriter,
    create_optimized_serializer,
    create_optimized_log_writer,
)

__all__ = [
    "OptimizedEventSerializer",
    "OptimizedLogWriter", 
    "create_optimized_serializer",
    "create_optimized_log_writer",
]
