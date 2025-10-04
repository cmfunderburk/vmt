#!/usr/bin/env python3
"""Basic recording example for VMT EconSim observability.

This example demonstrates how to use the FileObserver to record simulation events
to compressed JSONL files for later analysis.

Usage:
    python basic_recording.py

Output:
    - Creates a compressed JSONL file with all simulation events
    - Shows event count and file size
    - Demonstrates basic observer setup and usage
"""

import sys
import os
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))

from econsim.observability.observers.file_observer import FileObserver
from econsim.observability.config import ObservabilityConfig
from econsim.observability.registry import ObserverRegistry


def create_mock_simulation_events():
    """Create mock simulation events for demonstration.
    
    Returns:
        List of mock event dictionaries
    """
    events = []
    
    # Simulate 100 steps of a small simulation
    for step in range(100):
        # Add some agent movement events
        if step % 5 == 0:
            events.append({
                'event_type': 'agent_mode_change',
                'step': step,
                'agent_id': step % 3,  # 3 agents
                'old_mode': 'IDLE',
                'new_mode': 'FORAGE',
                'reason': 'started foraging'
            })
        
        # Add some trade events
        if step % 7 == 0 and step > 10:
            events.append({
                'event_type': 'trade_execution',
                'step': step,
                'seller_id': 0,
                'buyer_id': 1,
                'give_type': 'wood',
                'take_type': 'stone',
                'delta_u_seller': 0.5,
                'delta_u_buyer': 0.3,
                'trade_location_x': 5,
                'trade_location_y': 5
            })
        
        # Add some resource collection events
        if step % 3 == 0:
            events.append({
                'event_type': 'resource_collection',
                'step': step,
                'agent_id': step % 3,
                'x': (step * 2) % 10,
                'y': (step * 3) % 10,
                'resource_type': 'wood' if step % 2 == 0 else 'stone',
                'amount_collected': 1,
                'utility_gained': 0.1
            })
        
        # Add some debug events
        if step % 10 == 0:
            events.append({
                'event_type': 'debug_log',
                'step': step,
                'category': 'SIMULATION',
                'message': f'Step {step} completed',
                'agent_id': -1
            })
    
    return events


def basic_recording_example():
    """Demonstrate basic recording with FileObserver."""
    print("=== Basic Recording Example ===")
    
    # Create output directory
    output_dir = Path("example_output")
    output_dir.mkdir(exist_ok=True)
    
    # Create observability configuration
    config = ObservabilityConfig.from_environment()
    
    # Create file observer
    output_file = output_dir / "basic_simulation.jsonl.gz"
    observer = FileObserver(
        config=config,
        output_path=output_file,
        compress=True,
        compression_level=6
    )
    
    print(f"Created FileObserver: {observer}")
    print(f"Output file: {output_file}")
    
    # Create observer registry and register observer
    registry = ObserverRegistry()
    registry.register(observer)
    
    print(f"Registered observer with registry")
    
    # Create mock simulation events
    mock_events = create_mock_simulation_events()
    print(f"Created {len(mock_events)} mock simulation events")
    
    # Simulate event processing
    print("Processing events...")
    for i, event_data in enumerate(mock_events):
        # Create a simple event object
        class MockEvent:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        event = MockEvent(**event_data)
        
        # Notify observer
        observer.notify(event)
        
        # Show progress
        if (i + 1) % 20 == 0:
            print(f"  Processed {i + 1}/{len(mock_events)} events")
    
    print("Event processing complete")
    
    # Close observer to write data to disk
    print("Closing observer and writing to disk...")
    observer.close()
    
    # Verify output file was created
    if output_file.exists():
        file_size = output_file.stat().st_size
        print(f"✓ Output file created: {output_file}")
        print(f"  File size: {file_size:,} bytes")
        print(f"  Compression: {'Yes' if output_file.suffix == '.gz' else 'No'}")
        
        # Show observer statistics
        stats = observer.get_observer_stats()
        print(f"  Events written: {stats.get('events_written', 'Unknown')}")
        print(f"  Bytes written: {stats.get('bytes_written', 'Unknown')}")
        
    else:
        print("✗ Output file was not created")
        return False
    
    # Demonstrate reading the output file
    print("\n=== Reading Output File ===")
    try:
        import gzip
        import json
        
        with gzip.open(output_file, 'rt') as f:
            lines = f.readlines()
        
        print(f"File contains {len(lines)} lines")
        
        # Show first few events
        print("First 3 events:")
        for i, line in enumerate(lines[:3]):
            event = json.loads(line.strip())
            print(f"  {i+1}. {event.get('event_type', 'unknown')} at step {event.get('step', '?')}")
        
        # Count events by type
        event_counts = {}
        for line in lines:
            event = json.loads(line.strip())
            event_type = event.get('event_type', 'unknown')
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        print(f"\nEvent type distribution:")
        for event_type, count in sorted(event_counts.items()):
            print(f"  {event_type}: {count}")
        
    except Exception as e:
        print(f"Error reading output file: {e}")
        return False
    
    print("\n=== Example Complete ===")
    print(f"Successfully recorded {len(mock_events)} events to {output_file}")
    print("You can now analyze the data or use it for playback")
    
    return True


if __name__ == "__main__":
    success = basic_recording_example()
    if success:
        print("\n✓ Basic recording example completed successfully!")
    else:
        print("\n✗ Basic recording example failed!")
        sys.exit(1)
