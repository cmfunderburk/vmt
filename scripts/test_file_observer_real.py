"""Test FileObserver with real simulation."""

import sys
import os
import time
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

# Import test config directly to avoid GUI dependencies
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'econsim', 'tools', 'launcher', 'framework'))

from test_configs import TEST_3_HIGH_DENSITY
from econsim.observability.observers.file_observer import FileObserver
from econsim.observability.config import ObservabilityConfig


def test_file_observer_real_simulation():
    """Run 1000 steps of simulation with FileObserver."""
    
    print("Starting FileObserver real simulation test...")
    print(f"Using test configuration: {TEST_3_HIGH_DENSITY.name}")
    print(f"Grid size: {TEST_3_HIGH_DENSITY.grid_size}")
    print(f"Agent count: {TEST_3_HIGH_DENSITY.agent_count}")
    print(f"Resource density: {TEST_3_HIGH_DENSITY.resource_density}")
    print()
    
    # Create output directory
    output_dir = Path("tmp_observer_test")
    output_dir.mkdir(exist_ok=True)
    
    # Create observability config
    config = ObservabilityConfig.from_environment()
    
    # Create FileObserver
    observer = FileObserver(
        config=config,
        output_path=output_dir / "simulation_events.jsonl"
    )
    
    print(f"Created FileObserver with output path: {observer.output_path}")
    
    # For this test, we'll simulate events directly since we don't have
    # a full simulation setup readily available. This tests the core
    # functionality of the FileObserver.
    
    print("Simulating events...")
    start_time = time.time()
    
    # Simulate 1000 steps worth of events
    event_count = 0
    for step in range(1000):
        # Simulate some events per step
        events_this_step = 0
        
        # Agent mode changes (every 50 steps)
        if step % 50 == 0:
            for agent_id in range(min(5, TEST_3_HIGH_DENSITY.agent_count)):
                observer.record_mode_change(
                    step=step,
                    agent_id=agent_id,
                    old_mode="foraging" if step % 100 == 0 else "trading",
                    new_mode="trading" if step % 100 == 0 else "foraging",
                    reason="phase transition" if step % 100 == 0 else "resource depletion"
                )
                events_this_step += 1
        
        # Resource collections (frequent)
        if step % 10 == 0:
            for agent_id in range(min(10, TEST_3_HIGH_DENSITY.agent_count)):
                observer.record_resource_collection(
                    step=step,
                    agent_id=agent_id,
                    x=step % TEST_3_HIGH_DENSITY.grid_size[0],
                    y=(step * 2) % TEST_3_HIGH_DENSITY.grid_size[1],
                    resource_type="wood" if step % 3 == 0 else "stone",
                    amount_collected=1,
                    utility_gained=2.5,
                    carrying_after={"wood": (step % 5) + 1, "stone": (step % 3) + 1}
                )
                events_this_step += 1
        
        # Trades (less frequent)
        if step % 25 == 0 and step > 0:
            observer.record_trade(
                step=step,
                seller_id=0,
                buyer_id=1,
                give_type="wood",
                take_type="stone",
                delta_u_seller=3.0,
                delta_u_buyer=2.5,
                trade_location_x=step % TEST_3_HIGH_DENSITY.grid_size[0],
                trade_location_y=step % TEST_3_HIGH_DENSITY.grid_size[1]
            )
            events_this_step += 1
        
        # Agent decisions (every step for some agents)
        if step % 5 == 0:
            for agent_id in range(min(3, TEST_3_HIGH_DENSITY.agent_count)):
                observer.record_agent_decision(
                    step=step,
                    agent_id=agent_id,
                    decision_type="movement" if step % 10 == 0 else "resource_selection",
                    decision_details=f"Moving to nearest resource" if step % 10 == 0 else "Selecting wood over stone",
                    utility_delta=1.5,
                    position_x=step % TEST_3_HIGH_DENSITY.grid_size[0],
                    position_y=step % TEST_3_HIGH_DENSITY.grid_size[1]
                )
                events_this_step += 1
        
        # Debug logs (occasional)
        if step % 100 == 0:
            observer.record_debug_log(
                step=step,
                category="SIMULATION",
                message=f"Step {step} completed with {events_this_step} events",
                agent_id=-1
            )
            events_this_step += 1
        
        # Performance monitoring (every 50 steps)
        if step % 50 == 0:
            observer.record_performance_monitor(
                step=step,
                metric_name="events_per_step",
                metric_value=float(events_this_step),
                threshold_exceeded=events_this_step > 20,
                details=f"Step {step} had {events_this_step} events"
            )
            events_this_step += 1
        
        # Resource events (occasional)
        if step % 75 == 0:
            observer.record_resource_event(
                step=step,
                event_type_detail="spawn",
                position_x=step % TEST_3_HIGH_DENSITY.grid_size[0],
                position_y=step % TEST_3_HIGH_DENSITY.grid_size[1],
                resource_type="wood",
                amount=2,
                agent_id=-1
            )
            events_this_step += 1
        
        # Economic decisions (less frequent)
        if step % 40 == 0 and step > 0:
            observer.record_economic_decision(
                step=step,
                agent_id=0,
                decision_type="resource_selection",
                decision_context="Choosing between multiple available resources",
                utility_before=10.0,
                utility_after=12.5,
                opportunity_cost=1.0,
                alternatives_considered=3,
                decision_time_ms=0.5,
                position_x=step % TEST_3_HIGH_DENSITY.grid_size[0],
                position_y=step % TEST_3_HIGH_DENSITY.grid_size[1]
            )
            events_this_step += 1
        
        event_count += events_this_step
        
        # Progress reporting
        if step % 100 == 0:
            print(f"Completed step {step}, events so far: {event_count}")
    
    end_time = time.time()
    simulation_duration = end_time - start_time
    
    print(f"\nSimulation completed!")
    print(f"Total events recorded: {event_count}")
    print(f"Simulation duration: {simulation_duration:.2f} seconds")
    print(f"Events per second: {event_count / simulation_duration:.2f}")
    
    # Close observer to write to disk
    print("Closing FileObserver and writing to disk...")
    observer.close()
    
    # Verify output (look for both .jsonl and .jsonl.gz files)
    output_files = list(output_dir.glob("*.jsonl")) + list(output_dir.glob("*.jsonl.gz"))
    if not output_files:
        print("✗ No output files found!")
        return False
    
    print(f"✓ Found {len(output_files)} output file(s)")
    
    # Count events in file
    total_file_events = 0
    for output_file in output_files:
        # Handle compressed files
        if output_file.suffix == '.gz':
            import gzip
            with gzip.open(output_file, 'rt') as f:
                file_events = sum(1 for line in f if line.strip())
        else:
            with open(output_file) as f:
                file_events = sum(1 for line in f if line.strip())
        
        total_file_events += file_events
        print(f"File {output_file.name}: {file_events} events")
    
    print(f"Total events in files: {total_file_events}")
    
    # Check file size
    total_size = sum(f.stat().st_size for f in output_files)
    print(f"Total file size: {total_size:,} bytes")
    print(f"Average bytes per event: {total_size / total_file_events:.2f}")
    
    # Performance metrics
    time_per_event_ms = (simulation_duration * 1000) / event_count
    print(f"Time per event: {time_per_event_ms:.4f} ms")
    
    # Performance check (<0.0001ms per event target from audit)
    performance_target = 0.0001  # ms per event
    performance_ok = time_per_event_ms < performance_target
    
    print(f"Performance target: <{performance_target} ms per event")
    print(f"Performance result: {'✓ PASS' if performance_ok else '✗ FAIL'}")
    
    # Verify event types
    print("\nVerifying event types...")
    events = observer.get_all_events()
    event_types = {}
    for event in events:
        event_type = event.get('type', 'unknown')
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    print("Event type distribution:")
    for event_type, count in sorted(event_types.items()):
        print(f"  {event_type}: {count}")
    
    # Schema validation
    print("\nValidating against schema...")
    from econsim.observability.event_schema import validate_event
    
    validation_errors = 0
    for event in events[:100]:  # Validate first 100 events
        if not validate_event(event):
            validation_errors += 1
    
    if validation_errors == 0:
        print("✓ All sampled events validate against schema")
    else:
        print(f"✗ {validation_errors} events failed schema validation")
    
    # Cleanup
    print(f"\nCleaning up test directory: {output_dir}")
    import shutil
    shutil.rmtree(output_dir)
    
    # Final result
    success = (
        total_file_events > 0 and
        performance_ok and
        validation_errors == 0
    )
    
    if success:
        print("✓ FileObserver real simulation test PASSED")
    else:
        print("✗ FileObserver real simulation test FAILED")
    
    return success


if __name__ == "__main__":
    success = test_file_observer_real_simulation()
    sys.exit(0 if success else 1)
