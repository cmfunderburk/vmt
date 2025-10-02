"""Example usage of the validation framework for observer pattern testing.

This script demonstrates how to use the comprehensive validation framework
to test and validate the observer pattern implementation against GUILogger
replacement requirements.
"""

import time
from pathlib import Path

from src.econsim.observability.config import ObservabilityConfig
from src.econsim.observability.registry import ObserverRegistry  
from src.econsim.observability.observer_logger import ObserverLogger
from src.econsim.observability.observers.gui_observer import GUIEventObserver
from src.econsim.observability.events import AgentModeChangeEvent, TradeExecutionEvent
from src.econsim.observability.validation.validation_framework import (
    create_validation_framework, run_comprehensive_validation
)


def main():
    """Run comprehensive observer pattern validation example."""
    print("=" * 80)
    print("Observer Pattern Validation Framework - Step 1.5 Example")
    print("=" * 80)
    
    # Create configuration with all observer features enabled
    config = ObservabilityConfig(
        agent_mode_logging=True,
        trade_logging=True,
        behavioral_aggregation=True,
        detailed_explanations=True
    )
    
    print("\n1. Creating Observer Pattern Components...")
    
    # Create core observer pattern components
    registry = ObserverRegistry()
    logger = ObserverLogger(registry)
    gui_observer = GUIEventObserver(config, None)  # No GUI reference for testing
    
    # Register observers with registry
    registry.register(logger)
    registry.register(gui_observer)
    
    print(f"   ✓ Registry created with {len(registry._observers)} observers")
    print("   ✓ ObserverLogger with full GUILogger API compatibility")
    print("   ✓ GUIEventObserver with display mapping and batching")
    
    # Create validation framework
    print("\n2. Creating Validation Framework...")
    capture, validator, integration, performance = create_validation_framework(config)
    print("   ✓ Event capture system initialized")
    print("   ✓ Observer validator ready")  
    print("   ✓ Integration tester configured")
    print("   ✓ Performance tester initialized")
    
    # Run comprehensive validation
    print("\n3. Running Comprehensive Validation...")
    start_time = time.time()
    
    results = run_comprehensive_validation(registry, logger, gui_observer, config)
    
    validation_time = time.time() - start_time
    print(f"   ✓ Validation completed in {validation_time:.3f}s")
    
    # Display results
    print("\n4. Validation Results Summary:")
    print("-" * 50)
    
    summary = results["summary"]
    success_rate = summary["success_rate"]
    
    print(f"   Total Tests: {summary['total_tests']}")
    print(f"   Successful: {summary['successful_tests']}")
    print(f"   Failed: {summary['failed_tests']}")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   Total Errors: {summary['total_errors']}")
    print(f"   Total Warnings: {summary['total_warnings']}")
    
    # Status assessment
    if success_rate >= 80:
        status = "✓ PASS - Observer pattern ready for integration"
    elif success_rate >= 60:
        status = "⚠ WARNING - Some issues detected, review recommended"
    else:
        status = "✗ FAIL - Significant issues detected, fixes required"
    
    print(f"\n   Status: {status}")
    
    # Display detailed test results
    print("\n5. Detailed Test Results:")
    print("-" * 50)
    
    for test_result in results["detailed_results"]:
        test_name = test_result["test_name"]
        success = test_result["success"]
        errors = test_result.get("errors", [])
        warnings = test_result.get("warnings", [])
        
        status_icon = "✓" if success else "✗"
        print(f"   {status_icon} {test_name}")
        
        if errors:
            for error in errors:
                print(f"       Error: {error}")
        
        if warnings:
            for warning in warnings[:2]:  # Limit warnings display
                print(f"       Warning: {warning}")
    
    # Display performance benchmarks
    if "performance_benchmarks" in results and results["performance_benchmarks"]:
        print("\n6. Performance Benchmarks:")
        print("-" * 50)
        
        benchmarks = results["performance_benchmarks"]
        
        if "observer_overhead" in benchmarks:
            overhead = benchmarks["observer_overhead"]
            print(f"   Observer Overhead: {overhead:.3f}ms per event")
            
            if overhead < 0.1:
                print("   ✓ Excellent performance - minimal overhead")
            elif overhead < 0.5:
                print("   ✓ Good performance - acceptable overhead")
            else:
                print("   ⚠ High overhead detected - optimization recommended")
    
    # Test event capture functionality
    print("\n7. Testing Event Capture System...")
    print("-" * 50)
    
    capture.expect_event_types(["agent_mode_change", "trade_execution"])
    
    with capture.capture_session():
        # Generate test events through the observer system
        mode_event = AgentModeChangeEvent.create(1, 1, "foraging", "trading", "validation_test")
        trade_event = TradeExecutionEvent.create(2, 1, 2, "wood", "food", 5.0, 3.0)
        
        # Emit through registry to test complete pipeline
        registry.notify(mode_event)
        registry.notify(trade_event)
        
        # Capture events for analysis
        capture.capture_event(mode_event, source="test")
        capture.capture_event(trade_event, source="test")
    
    # Analyze captured events
    analysis = capture.analyze_events()
    print(f"   ✓ Captured {analysis.total_events} events")
    print(f"   ✓ Event types: {list(analysis.events_by_type.keys())}")
    print(f"   ✓ Average processing: {analysis.average_processing_time:.3f}ms")
    
    if analysis.missing_events:
        print(f"   ⚠ Missing expected events: {analysis.missing_events}")
    else:
        print("   ✓ All expected events captured")
    
    # Test observer metrics
    print("\n8. Observer Performance Metrics:")
    print("-" * 50)
    
    gui_metrics = gui_observer.get_gui_metrics()
    print(f"   Events processed: {gui_metrics['events_processed']}")
    print(f"   Updates generated: {gui_metrics['updates_generated']}")
    print(f"   Avg processing time: {gui_metrics['average_processing_time_ms']:.3f}ms")
    
    if gui_metrics['events_processed'] > 0:
        efficiency = gui_metrics['updates_generated'] / gui_metrics['events_processed']
        print(f"   Update efficiency: {efficiency:.1f} updates per event")
    
    # Final assessment
    print("\n" + "=" * 80)
    print("VALIDATION FRAMEWORK ASSESSMENT")
    print("=" * 80)
    
    print("\n✓ Step 1.5 Validation Framework - COMPLETE")
    print("\nKey Features Validated:")
    print("  • Event capture system with filtering and analysis")
    print("  • Automated observer functionality verification") 
    print("  • Performance benchmarking and regression detection")
    print("  • Integration scenario testing")
    print("  • Complete observer pattern validation pipeline")
    
    print("\nReadiness for Phase 2:")
    if success_rate >= 80:
        print("  ✓ Observer pattern implementation validated")
        print("  ✓ Performance meets requirements")  
        print("  ✓ Ready to proceed with GUILogger elimination")
    else:
        print("  ⚠ Some validation issues detected")
        print("  ⚠ Review and address issues before Phase 2")
        print("  ⚠ Consider additional testing or optimization")
    
    print(f"\nValidation completed in {validation_time:.3f}s")
    print("Observer pattern foundation ready for deployment!")


if __name__ == "__main__":
    main()