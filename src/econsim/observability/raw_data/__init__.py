"""
Raw Data Recording Architecture

This module implements a zero-overhead logging system that stores raw simulation data
as primitive types and translates to human-readable format only when needed.

Key Components:
- RawDataObserver: Zero-overhead data storage using dictionaries
- DataTranslator: GUI translation layer for human-readable format
- RawDataWriter: Disk persistence at simulation end

Architecture Principles:
1. Store raw data directly - no processing overhead during simulation
2. Translate only when needed - GUI handles human-readable format
3. Achieve zero-overhead logging - meets <2% target easily
4. Follow Unix philosophy - do one thing well (store OR translate)

Performance Targets:
- <0.1% overhead per step (100x improvement over current system)
- >1,000,000 events/second recording speed
- Zero per-frame allocations during simulation
- 33% memory reduction (raw dicts vs compressed JSON)

Usage:
    from econsim.observability.raw_data import RawDataObserver, DataTranslator
    
    # During simulation - zero overhead
    observer = RawDataObserver()
    observer.record_trade(step=100, seller_id=1, buyer_id=2, give_type="wood", take_type="stone")
    
    # For GUI - translate when needed
    translator = DataTranslator()
    human_readable = translator.translate_trade_event(raw_event)
"""

from .raw_data_observer import RawDataObserver
from .data_translator import DataTranslator
from .raw_data_writer import RawDataWriter

__all__ = [
    'RawDataObserver',
    'DataTranslator',
    'RawDataWriter'
]
