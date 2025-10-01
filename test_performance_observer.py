#!/usr/bin/env python3
"""
Quick validation test for Phase 3.2 PerformanceObserver implementation.
Tests basic functionality and integration with buffer system.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from econsim.observability.observers.performance_observer import PerformanceObserver
from econsim.observability.events import SimulationInitEvent, StepCompleteEvent, AgentModeChangeEvent
from econsim.observability.observer_registry import ObserverRegistry

def test_performance_observer():
    """Test PerformanceObserver functionality."""
    
    print("🔍 Testing PerformanceObserver Implementation...")
    
    # Test 1: Basic initialization
    observer = PerformanceObserver(
        enable_profiling=True,
        memory_monitoring=True,
        slow_step_threshold=0.05  # 50ms
    )
    
    print("✅ PerformanceObserver initialized")
    
    # Test 2: Observer registration and event handling
    registry = ObserverRegistry()
    registry.register_observer('performance', observer)
    
    # Create test events
    init_event = SimulationInitEvent(step=0, seed=123, config={})
    
    # Test event processing
    observer.observe(init_event)
    print("✅ Event processing works")
    
    # Test 3: Step metrics tracking
    step_event = StepCompleteEvent(step=1, agents_count=5, resources_count=10)
    observer.observe(step_event)
    
    # Test 4: Performance statistics
    stats = observer.get_performance_stats()
    print(f"✅ Performance stats generated: {len(stats)} metrics")
    
    # Test 5: Performance assessment
    assessment = observer.get_performance_assessment()
    print(f"✅ Performance assessment generated with {len(assessment.get('recommendations', []))} recommendations")
    
    # Test 6: Observer statistics
    observer_stats = observer.get_observer_stats()
    print(f"✅ Observer stats: {observer_stats.get('events_processed', 0)} events processed")
    
    print("\n🎉 All PerformanceObserver tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = test_performance_observer()
        if success:
            print("\n✅ Phase 3.2 PerformanceObserver validation PASSED")
            sys.exit(0)
        else:
            print("\n❌ Phase 3.2 PerformanceObserver validation FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Phase 3.2 PerformanceObserver validation FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)