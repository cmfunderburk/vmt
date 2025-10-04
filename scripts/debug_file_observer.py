"""Debug FileObserver file writing."""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from econsim.observability.observers.file_observer import FileObserver
from econsim.observability.config import ObservabilityConfig


def debug_file_observer():
    """Debug FileObserver file writing."""
    
    print("Debugging FileObserver file writing...")
    
    # Create a mock config
    config = Mock(spec=ObservabilityConfig)
    config.behavioral_aggregation = False
    config.correlation_tracking = False
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    output_path = Path(temp_dir) / "debug_events.jsonl"
    
    print(f"Output path: {output_path}")
    print(f"Parent directory: {output_path.parent}")
    print(f"Parent exists: {output_path.parent.exists()}")
    
    try:
        # Create FileObserver
        observer = FileObserver(
            config=config,
            output_path=output_path
        )
        
        print(f"Observer created: {observer}")
        print(f"Observer output path: {observer.output_path}")
        print(f"Observer closed: {observer._closed}")
        
        # Record a simple event
        observer.record_trade(
            step=1,
            seller_id=0,
            buyer_id=1,
            give_type="wood",
            take_type="stone"
        )
        
        print("Recorded trade event")
        
        # Check events in memory
        events = observer.get_all_events()
        print(f"Events in memory: {len(events)}")
        if events:
            print(f"First event: {events[0]}")
        
        # Try to close and write
        print("Closing observer...")
        observer.close()
        print(f"Observer closed: {observer._closed}")
        
        # Check if file was created
        print(f"File exists: {output_path.exists()}")
        if output_path.exists():
            print(f"File size: {output_path.stat().st_size} bytes")
            with open(output_path) as f:
                content = f.read()
                print(f"File content: {repr(content[:200])}")
        else:
            print("File was not created!")
            
            # Check if directory exists
            print(f"Directory exists: {output_path.parent.exists()}")
            if output_path.parent.exists():
                files = list(output_path.parent.iterdir())
                print(f"Files in directory: {files}")
        
        # Check observer stats
        stats = observer.get_observer_stats()
        print(f"Observer stats: {stats}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"Cleaned up: {temp_dir}")


if __name__ == "__main__":
    debug_file_observer()
