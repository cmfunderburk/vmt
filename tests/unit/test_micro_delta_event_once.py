"""Test micro-delta event emission behavior.

This test verifies that the one-shot micro-delta threshold event
is emitted exactly once per process via observer pattern when
trade intents are pruned due to threshold filtering.
"""
import os
import pytest
from typing import List
from unittest.mock import patch

from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
from econsim.observability.raw_data.raw_data_observer import RawDataObserver
from econsim.preferences.cobb_douglas import CobbDouglasPreference


class MicroDeltaEventCapture(RawDataObserver):
    """Test observer that captures micro-delta debug events using raw data recording."""
    
    def __init__(self):
        super().__init__()
        self.micro_delta_events = []
    
    def record_debug_log(self, step: int, category: str, message: str, 
                        agent_id: int = -1, **optional) -> None:
        """Override to capture micro-delta debug logs."""
        super().record_debug_log(step, category, message, agent_id, **optional)
        # Capture micro-delta threshold events
        if 'Micro-delta threshold applied' in message:
            self.micro_delta_events.append({
                'step': step,
                'category': category,
                'message': message,
                'agent_id': agent_id
            })
    
    def flush_step(self, step: int) -> None:
        """Required by observer protocol - no action needed."""
        pass



@pytest.fixture
def reset_micro_delta_flag():
    """Reset the global micro-delta emission flag before and after test."""
    # Import the module to access its globals
    import econsim.simulation.trade
    
    # Store original value
    original_value = econsim.simulation.trade._micro_delta_threshold_emitted
    
    # Reset for test
    econsim.simulation.trade._micro_delta_threshold_emitted = False
    
    yield
    
    # Restore original value  
    econsim.simulation.trade._micro_delta_threshold_emitted = original_value


def test_micro_delta_event_emitted_once(reset_micro_delta_flag):
    """Test that micro-delta threshold event is emitted exactly once per process."""
    
    # Set up environment to trigger micro-delta pruning
    # Increase threshold so that small trade deltas get pruned
    original_override = os.environ.get("ECONSIM_MIN_TRADE_DELTA_OVERRIDE")
    os.environ["ECONSIM_MIN_TRADE_DELTA_OVERRIDE"] = "0.1"  # Much higher threshold
    
    try:
        # Create simulation with agents positioned to generate small-utility trades
        config = SimConfig(
            grid_size=(6, 6),
            initial_resources=[],  # No initial resources needed
            seed=12345,
            enable_respawn=False,
            enable_metrics=False
        )
        
        # Create observer to capture events
        observer = MicroDeltaEventCapture()
        
        # Create simulation with observer attached
        sim = Simulation.from_config(config, agent_positions=[(1, 1), (2, 2)])
        sim._observer_registry.register(observer)
        
        # Assign similar preferences to make trade utility deltas small
        pref1 = CobbDouglasPreference(alpha=0.49)  # Nearly balanced
        pref2 = CobbDouglasPreference(alpha=0.51)  # Slightly different
        sim.agents[0].preference = pref1
        sim.agents[1].preference = pref2
        
        # Give agents goods to enable trades but create small deltas
        sim.agents[0].carrying = {"good1": 5, "good2": 5}
        sim.agents[1].carrying = {"good1": 5, "good2": 5}
        
        # Enable trading system to trigger intent enumeration
        os.environ["ECONSIM_TRADE_DRAFT"] = "1"
        os.environ["ECONSIM_TRADE_EXEC"] = "1"
        
        # Run multiple steps to potentially trigger multiple micro-delta events
        import random
        ext_rng = random.Random(999)
        
        for _ in range(5):  # Multiple steps to test one-shot behavior
            sim.step(ext_rng)
        
        # Should have exactly one micro-delta event despite multiple potential triggers
        micro_delta_events = observer.micro_delta_events
        assert len(micro_delta_events) == 1, f"Expected exactly 1 micro-delta event, got {len(micro_delta_events)}"
        
        # Verify event structure (raw dictionary format)
        event = micro_delta_events[0]
        assert event['category'] == "TRADE_MICRO_DELTA"
        assert "threshold applied" in event['message']
        assert "1.00e-01" in event['message']  # Should reflect our override threshold
        
    finally:
        # Clean up environment
        if original_override is not None:
            os.environ["ECONSIM_MIN_TRADE_DELTA_OVERRIDE"] = original_override
        else:
            os.environ.pop("ECONSIM_MIN_TRADE_DELTA_OVERRIDE", None)
        
        # Clean up trade flags
        os.environ.pop("ECONSIM_TRADE_DRAFT", None)
        os.environ.pop("ECONSIM_TRADE_EXEC", None)


def test_micro_delta_emission_deterministic(reset_micro_delta_flag):
    """Test that micro-delta emission doesn't affect determinism."""
    
    # Set up identical simulations
    config = SimConfig(grid_size=(4, 4), initial_resources=[], seed=42, enable_respawn=False, enable_metrics=True)
    
    # Simulation 1: with observer
    observer1 = MicroDeltaEventCapture()
    sim1 = Simulation.from_config(config, agent_positions=[(1, 1), (2, 2)])
    sim1._observer_registry.register(observer1)
    
    # Simulation 2: without observer (to test hash parity)
    sim2 = Simulation.from_config(config, agent_positions=[(1, 1), (2, 2)])
    
    # Run both for several steps
    import random
    ext_rng1 = random.Random(123)
    ext_rng2 = random.Random(123)  # Same seed
    
    # Set threshold override to potentially trigger emission
    os.environ["ECONSIM_MIN_TRADE_DELTA_OVERRIDE"] = "0.05"
    os.environ["ECONSIM_TRADE_DRAFT"] = "1"
    
    try:
        for _ in range(3):
            sim1.step(ext_rng1)
            sim2.step(ext_rng2)
        
        # Determinism hashes should be identical (micro-delta logging is hash-excluded)
        hash1 = sim1.metrics_collector.determinism_hash() if sim1.metrics_collector else "no_metrics"
        hash2 = sim2.metrics_collector.determinism_hash() if sim2.metrics_collector else "no_metrics"
        
        assert hash1 == hash2, f"Determinism hashes differ: {hash1} != {hash2}"
        
    finally:
        # Clean up
        os.environ.pop("ECONSIM_MIN_TRADE_DELTA_OVERRIDE", None)
        os.environ.pop("ECONSIM_TRADE_DRAFT", None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])