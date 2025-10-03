"""
New Extensible Log Architecture

This module implements the source-level compression architecture that replaces
the complex 6-layer serialization pipeline with direct emission methods.

Key Components:
- event_schemas.py: Declarative schema definitions for documentation and translation
- extensible_observer.py: Direct emission methods with hardcoded compression
- translator.py: GUI decompression using schemas
- log_writer.py: Simple buffered JSON writer with newline-delimited output

Architecture Benefits:
- Eliminates ~1500 lines of complex serialization code
- Reduces pipeline complexity from 6 layers to 2
- Single responsibility: observers compress, GUI translates
- Extensibility: Add new fields in 2-3 minutes, new event types in ~10 minutes
"""

__version__ = "1.0.0"
__author__ = "VMT Development Team"
__date__ = "2025-10-02"
