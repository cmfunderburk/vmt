"""Tests for resource collection event recording using raw data architecture.

Verifies that resource collection even    # Assert: No collection events should be emitted using raw data format
    all_events = observer.get_all_events()
    collection_events = [e for e in all_events if e['type'] == 'resource_collection']
    assert len(collection_events) == 0, f"Expected no collection events, got {len(collection_events)}"are recorded correctly when agents
collect resources using the new raw data recording system.
"""

import random
from typing import List, Tuple, Optional

from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
from econsim.observability.observers.memory_observer import MemoryObserver
from econsim.observability.config import ObservabilityConfig


def build_sim_with_observer(agent_positions: List[Tuple[int,int]], resources: Optional[List[Tuple[int, int, str]]] = None) -> Tuple[Simulation, MemoryObserver]:
    """Build simulation with test observer for event capture."""
    cfg = SimConfig(
        grid_size=(6,6),
        initial_resources=resources or [],
        perception_radius=6,
        respawn_target_density=0.0,
        respawn_rate=0.0,
        max_spawn_per_tick=0,
        seed=42,
        enable_respawn=False,
        enable_metrics=True,
    )
    sim = Simulation.from_config(cfg, agent_positions=agent_positions)
    
    # Set up memory observer to capture raw data events
    obs_config = ObservabilityConfig()
    observer = MemoryObserver(obs_config)
    sim._observer_registry.register(observer)
    
    return sim, observer


def test_collection_event_emission_decision_mode():
    """Verify ResourceCollectionEvent is emitted when agent collects resource in decision mode."""
    import os
    
    # Ensure foraging is enabled
    os.environ["ECONSIM_FORAGE_ENABLED"] = "1"
    
    # Setup: agent at (1,1) with resource at (2,2) - away from home 
    resources = [(2, 2, 'A')]
    sim, observer = build_sim_with_observer([(1, 1)], resources=resources)
    
    # Execute multiple steps to allow agent to move to resource and collect
    rng = random.Random(123)
    for step_num in range(5):  # Give agent time to move and collect
        sim.step(rng)
        
        # Check if we got a resource collection event using raw data architecture
        all_events = observer.get_all_events()
        resource_events = [e for e in all_events if e['type'] == 'resource_collection']
        
        if len(resource_events) > 0:
            event = resource_events[0]
            
            # Validate event fields using raw data format
            assert event['agent_id'] == 0, f"Expected agent_id=0, got {event['agent_id']}"
            assert event['x'] == 2, f"Expected x=2, got {event['x']}"
            assert event['y'] == 2, f"Expected y=2, got {event['y']}"
            assert event['resource_type'] == 'A', f"Expected resource_type='A', got {event['resource_type']}"
            assert event['step'] >= 0, f"Expected step >= 0, got {event['step']}"
            return  # Test passed
    
    # If we get here, no events were captured
    assert False, "No ResourceCollectionEvent was emitted during simulation"


# Legacy mode test removed: ECONSIM_LEGACY_RANDOM deprecated, decision system always enabled


def test_collection_event_fields():
    """Verify ResourceCollectionEvent has correct field structure.""" 
    import os
    
    # Ensure foraging is enabled
    os.environ["ECONSIM_FORAGE_ENABLED"] = "1"
    
    # Setup: agent away from home to avoid immediate deposit
    resources = [(3, 3, 'A')]
    sim, observer = build_sim_with_observer([(1, 1)], resources=resources)
    
    # Execute until collection happens
    rng = random.Random(789)
    for _ in range(10):
        sim.step(rng)
        all_events = observer.get_all_events()
        resource_events = [e for e in all_events if e['type'] == 'resource_collection']
        if len(resource_events) > 0:
            break
    
    # Verify event structure using raw data format
    all_events = observer.get_all_events()
    resource_events = [e for e in all_events if e['type'] == 'resource_collection']
    assert len(resource_events) >= 1, "Expected resource collection event"
    event = resource_events[0]
    
    # Test raw data structure (event is already a dictionary)
    expected_keys = {'type', 'step', 'agent_id', 'x', 'y', 'resource_type', 'amount_collected'}
    assert set(event.keys()).issuperset(expected_keys), f"Expected keys {expected_keys}, got {set(event.keys())}"
    assert event['type'] == 'resource_collection', f"Expected type='resource_collection', got {event['type']}"


def test_no_collection_no_event():
    """Verify no ResourceCollectionEvent is emitted when no collection occurs."""
    # Setup: agent at (0,0) with no resources
    sim, observer = build_sim_with_observer([(0, 0)], resources=[])
    
    # Execute
    rng = random.Random(999)
    sim.step(rng)
    
    # Assert: No collection events should be emitted using raw data format
    all_events = observer.get_all_events()
    collection_events = [e for e in all_events if e['type'] == 'resource_collection']
    assert len(collection_events) == 0, f"Expected no resource collection events, got {len(collection_events)}"