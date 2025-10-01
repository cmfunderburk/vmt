#!/usr/bin/env python3
"""Quick test of event buffering system to verify basic functionality."""

import sys
from pathlib import Path
from typing import List, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
from econsim.observability.events import AgentModeChangeEvent
from econsim.observability.observers import SimulationObserver


class TestObserver(SimulationObserver):
    """Test observer that captures events."""
    
    def __init__(self):
        self.events: List[Any] = []
    
    def notify(self, event: Any) -> None:
        """Capture all events."""
        self.events.append(event)
    
    def flush_step(self, step: int) -> None:
        """No-op for test observer."""
        pass
    
    def close(self) -> None:
        """No-op for test observer.""" 
        pass


def test_event_buffering():
    """Test that event buffering system works correctly."""
    print("Testing event buffering system...")
    
    # Create a simple simulation
    config = SimConfig(
        grid_size=(4, 4),
        initial_resources=[(1, 1, "A"), (2, 2, "B")],
        seed=123,
        enable_respawn=False,
        enable_metrics=False
    )
    
    sim = Simulation.from_config(config, agent_positions=[(0, 0), (1, 1)])
    
    # Add a test observer to capture events
    observer = TestObserver()
    sim._observer_registry.register(observer)
    
    # Clear any initialization events
    observer.events.clear()
    
    print(f"Initial event count: {len(observer.events)}")
    
    # Run a few steps and check events are buffered and flushed
    import random
    rng = random.Random(42)
    
    for step in range(3):
        print(f"Step {step + 1}:")
        print(f"  Buffer stats before step: {sim._event_buffer.get_stats()}")
        
        # Run step (this should buffer events during step, flush at end)
        sim.step(rng)
        
        print(f"  Buffer stats after step: {sim._event_buffer.get_stats()}")
        print(f"  Total events captured: {len(observer.events)}")
        
        # Verify buffer is empty after step (events were flushed)
        buffer_stats = sim._event_buffer.get_stats()
        assert buffer_stats['is_empty'], f"Buffer should be empty after step execution, got: {buffer_stats}"
        
    print(f"\nFinal results:")
    print(f"  Total events captured: {len(observer.events)}")
    print(f"  Mode change events: {sum(1 for e in observer.events if isinstance(e, AgentModeChangeEvent))}")
    
    # Verify we got some events
    if len(observer.events) > 0:
        print("✅ Event buffering system working correctly")
        return True
    else:
        print("⚠️ No events captured - may need more steps or different scenario")
        return False


if __name__ == "__main__":
    success = test_event_buffering()
    if success:
        print("\n🎉 Event buffering test PASSED!")
    else:
        print("\n❌ Event buffering test needs investigation")
        sys.exit(1)