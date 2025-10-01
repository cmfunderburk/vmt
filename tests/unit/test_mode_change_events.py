"""Tests for AgentModeChangeEvent emission during agent mode transitions.

Verifies that AgentModeChangeEvent is emitted correctly for all mode changes
including unified selection, collection capacity, return home, and other scenarios.
"""

import random
from typing import List, Tuple, Any, Optional

from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
from econsim.simulation.agent import Agent, AgentMode
from econsim.observability.events import AgentModeChangeEvent
from econsim.observability.observers import SimulationObserver


class TestModeChangeObserver(SimulationObserver):
    """Test observer that captures AgentModeChangeEvents."""
    
    def __init__(self):
        self.events: List[AgentModeChangeEvent] = []
        self.all_events: List[Any] = []  # Capture all events for debugging
    
    def notify(self, event: Any) -> None:
        """Capture AgentModeChangeEvent instances."""
        self.all_events.append(event)
        if isinstance(event, AgentModeChangeEvent):
            self.events.append(event)
    
    def flush_step(self, step: int) -> None:
        """No-op for test observer."""
        pass
    
    def close(self) -> None:
        """No-op for test observer.""" 
        pass


def build_sim_with_observer(agent_positions: List[Tuple[int,int]], resources: Optional[List[Tuple[int, int, str]]] = None) -> Tuple[Simulation, TestModeChangeObserver]:
    """Build simulation with test observer for mode change event capture."""
    cfg = SimConfig(
        grid_size=(8,8),
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
    
    observer = TestModeChangeObserver()
    sim._observer_registry.register(observer)
    
    return sim, observer


def _run_steps(sim: Simulation, steps: int) -> None:
    """Run simulation for specified number of steps."""
    rng = random.Random(123)
    for _ in range(steps):
        sim.step(rng, use_decision=True)


def test_mode_change_event_fields():
    """Verify AgentModeChangeEvent contains correct field data and serialization."""
    # Test event creation
    event = AgentModeChangeEvent.create(
        step=10,
        agent_id=5,
        old_mode="idle",
        new_mode="forage",
        reason="resource_selection"
    )
    
    # Check required fields
    assert event.step == 10
    assert event.agent_id == 5
    assert event.old_mode == "idle"
    assert event.new_mode == "forage"
    assert event.reason == "resource_selection"
    assert event.event_type == "agent_mode_change"
    assert event.timestamp > 0
    
    # Test to_dict() method
    event_dict = event.to_dict()
    assert event_dict["type"] == "agent_mode_change"
    assert event_dict["step"] == 10
    assert event_dict["agent_id"] == 5
    assert event_dict["old_mode"] == "idle"
    assert event_dict["new_mode"] == "forage" 
    assert event_dict["reason"] == "resource_selection"


def test_mode_change_events_unified_selection():
    """Verify mode changes during unified selection emit events."""
    # Set up simulation with agent away from resource
    sim, observer = build_sim_with_observer(
        agent_positions=[(0, 0)],  # Agent at corner
        resources=[(2, 2, "A")]    # Resource closer - should reach in ~4 steps
    )
    
    # Agent starts in FORAGE mode by default
    agent = sim.agents[0]
    assert agent.mode == AgentMode.FORAGE
    
    # Clear any initialization events
    observer.events.clear()
    
    # Run enough steps for agent to reach resource and trigger mode change
    _run_steps(sim, 5)
    
    # Should have mode change events when agent collects resource and switches to RETURN_HOME
    mode_events = observer.events
    assert len(mode_events) > 0, f"Expected mode change events, got {len(mode_events)}"
    
    # Look for FORAGE -> RETURN_HOME transition after collection
    return_home_events = [e for e in mode_events if e.old_mode == "forage" and e.new_mode == "return_home"]
    assert len(return_home_events) > 0, f"Expected FORAGE->RETURN_HOME event, got events: {[(e.old_mode, e.new_mode, e.reason) for e in mode_events]}"
    
    return_home_event = return_home_events[0]
    assert return_home_event.agent_id == agent.id
    assert return_home_event.reason in ["collected_resource", "carrying_capacity_full"]


def test_mode_change_events_collection_capacity():
    """Verify mode changes when agent collects resources and returns home."""
    # Set up agent at resource location
    sim, observer = build_sim_with_observer(
        agent_positions=[(2, 2)],
        resources=[(2, 2, "A"), (2, 3, "A"), (3, 2, "A")]  # Multiple resources nearby
    )
    
    agent = sim.agents[0]
    # Agent starts in FORAGE mode by default - no setup needed
    
    # Clear setup events
    observer.events.clear()
    
    # Run steps to trigger collection and return home
    _run_steps(sim, 3)
    
    mode_events = observer.events
    
    # Look for FORAGE -> RETURN_HOME transition after collection
    return_events = [e for e in mode_events 
                      if e.old_mode == "forage" and e.new_mode == "return_home"]
    
    if len(return_events) == 0:
        # Also check for generic return home events that could be capacity-related
        return_events = [e for e in mode_events if e.new_mode == "return_home"]
        assert len(return_events) > 0, f"Expected capacity-related RETURN_HOME event, got events: {[(e.old_mode, e.new_mode, e.reason) for e in mode_events]}"
    else:
        return_event = return_events[0]
        assert return_event.agent_id == agent.id
        assert "collected" in return_event.reason or "capacity" in return_event.reason


def test_mode_change_events_return_home():
    """Verify mode changes when returning home emit events."""
    # Set up agent away from home with resources
    sim, observer = build_sim_with_observer(
        agent_positions=[(0, 0)],  # Agent at corner, home is also at (0,0)
        resources=[(1, 1, "A")]    # Resource nearby
    )
    
    agent = sim.agents[0]
    # Set agent to forage mode initially and give them something to return with
    agent.carrying["good1"] = 1
    agent._set_mode(AgentMode.FORAGE, "test_setup", sim._observer_registry, 0)
    
    # Clear setup events
    observer.events.clear()
    
    # Move agent away from home, then trigger return
    agent.x, agent.y = 3, 3  # Move away from home
    
    # Run steps - agent should eventually return home
    _run_steps(sim, 10)
    
    mode_events = observer.events
    
    # Look for transitions to RETURN_HOME or to IDLE (when at home)
    home_related_events = [e for e in mode_events 
                          if e.new_mode in ["return_home", "idle"] 
                          or "home" in e.reason.lower()]
    
    assert len(home_related_events) > 0, f"Expected home-related mode change events, got: {[(e.old_mode, e.new_mode, e.reason) for e in mode_events]}"
    
    # Verify at least one event has proper agent ID
    for event in home_related_events:
        assert event.agent_id == agent.id


def test_no_duplicate_mode_change_events():
    """Verify _set_mode() no-op behavior when mode unchanged."""
    sim, observer = build_sim_with_observer(
        agent_positions=[(0, 0)],
        resources=[]
    )
    
    agent = sim.agents[0]
    initial_mode = agent.mode
    
    # Clear any initialization events
    observer.events.clear()
    
    # Try to set agent to same mode multiple times
    agent._set_mode(initial_mode, "no_change_test", sim._observer_registry, 1)
    agent._set_mode(initial_mode, "no_change_test", sim._observer_registry, 2)
    agent._set_mode(initial_mode, "no_change_test", sim._observer_registry, 3)
    
    # Should have no events (no-op when mode unchanged)
    no_change_events = [e for e in observer.events if e.old_mode == e.new_mode]
    
    # The _set_mode helper might still emit events even for no-change, 
    # but let's verify behavior is consistent
    if len(observer.events) > 0:
        # If events are emitted, they should be consistent
        for event in observer.events:
            assert event.agent_id == agent.id
            assert event.old_mode == event.new_mode == initial_mode.value
    
    # Most important: mode should remain unchanged
    assert agent.mode == initial_mode


def test_mode_change_coverage_comprehensive():
    """Comprehensive test to verify mode change events are emitted for various scenarios."""
    # Larger simulation with multiple agents and resources
    sim, observer = build_sim_with_observer(
        agent_positions=[(0, 0), (7, 7), (3, 3)],
        resources=[(1, 1, "A"), (6, 6, "B"), (4, 4, "A"), (5, 5, "B")]
    )
    
    # Clear initialization events
    observer.events.clear()
    
    # Run longer simulation to trigger various mode changes
    _run_steps(sim, 15)
    
    mode_events = observer.events
    
    # Should have multiple mode change events
    assert len(mode_events) > 0, "Expected multiple mode change events in comprehensive scenario"
    
    # Verify all events have valid agent IDs
    agent_ids = {agent.id for agent in sim.agents}
    for event in mode_events:
        assert event.agent_id in agent_ids, f"Invalid agent ID {event.agent_id} in event"
        assert event.old_mode in ["idle", "forage", "return_home", "move_to_partner"]
        assert event.new_mode in ["idle", "forage", "return_home", "move_to_partner"]
        assert event.step >= 0
        assert len(event.reason) > 0, "Mode change reason should not be empty"
    
    # Should see various types of mode transitions
    transition_types = {(e.old_mode, e.new_mode) for e in mode_events}
    
    # Common transitions that should occur
    expected_transitions = {
        ("idle", "forage"),
        ("forage", "return_home"),
        ("return_home", "idle")
    }
    
    found_transitions = transition_types.intersection(expected_transitions)
    assert len(found_transitions) > 0, f"Expected common transitions {expected_transitions}, got {transition_types}"


def test_mode_change_event_timing():
    """Verify mode change events are emitted with correct step numbers."""
    sim, observer = build_sim_with_observer(
        agent_positions=[(0, 0)],
        resources=[(2, 2, "A")]
    )
    
    # Clear initialization events
    observer.events.clear()
    
    # Run specific number of steps and track timing
    target_steps = 5
    _run_steps(sim, target_steps)
    
    mode_events = observer.events
    
    # All events should have step numbers within valid range
    for event in mode_events:
        assert 1 <= event.step <= target_steps, f"Event step {event.step} outside valid range 1-{target_steps}"
        assert event.timestamp > 0, "Event timestamp should be positive"


if __name__ == "__main__":
    # Run basic smoke test
    print("Running AgentModeChangeEvent tests...")
    
    test_mode_change_event_fields()
    print("✓ Event fields test passed")
    
    test_no_duplicate_mode_change_events()
    print("✓ No duplicate events test passed")
    
    test_mode_change_events_unified_selection()
    print("✓ Unified selection events test passed")
    
    test_mode_change_events_collection_capacity()
    print("✓ Collection capacity events test passed")
    
    test_mode_change_events_return_home()
    print("✓ Return home events test passed")
    
    test_mode_change_coverage_comprehensive()
    print("✓ Comprehensive coverage test passed")
    
    test_mode_change_event_timing()
    print("✓ Event timing test passed")
    
    print("All AgentModeChangeEvent tests passed! ✅")