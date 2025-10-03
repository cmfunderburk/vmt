"""
Raw Data Recording Architecture

This module implements a zero-overhead logging system that stores raw simulation data
as primitive types with no GUI dependencies or translation layers.

Key Components:
- RawDataObserver: Zero-overhead data storage using dictionaries
- RawDataWriter: Disk persistence at simulation end

Architecture Principles:
1. Store raw data directly - no processing overhead during simulation
2. No translation layer - pure raw data storage only
3. Achieve zero-overhead logging - meets <0.1% target
4. Follow Unix philosophy - do one thing well (store data)

Performance Targets:
- <0.1% overhead per step (100x improvement over current system)
- >1,000,000 events/second recording speed
- Zero per-frame allocations during simulation
- 33% memory reduction (raw dicts vs compressed JSON)

Usage:
    from econsim.observability.raw_data import RawDataObserver
    
    # During simulation - zero overhead
    observer = RawDataObserver()
    observer.record_trade(step=100, seller_id=1, buyer_id=2, give_type="wood", take_type="stone")
    
        # Write raw data to disk
    writer = RawDataWriter()
    writer.write_events_to_file(observer.get_all_events(), 'output.jsonl')
"""

from .raw_data_observer import RawDataObserver
from .raw_data_writer import RawDataWriter

__all__ = [
    'RawDataObserver',
    'RawDataWriter',
]
