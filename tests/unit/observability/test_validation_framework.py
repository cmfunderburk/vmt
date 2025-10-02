"""Test suite for observer pattern validation framework.

Tests the comprehensive validation framework including event capture,
automated verification, integration testing, and performance benchmarking.
"""

import pytest
import time
from unittest.mock import Mock, MagicMock
from pathlib import Path
import tempfile
import json

from src.econsim.observability.config import ObservabilityConfig
from src.econsim.observability.registry import ObserverRegistry
from src.econsim.observability.events import (
    AgentModeChangeEvent, TradeExecutionEvent, ResourceCollectionEvent
)
from src.econsim.observability.observer_logger import ObserverLogger
from src.econsim.observability.observers.gui_observer import GUIEventObserver
from src.econsim.observability.validation.validation_framework import (
    EventCaptureSystem, ObserverValidator, IntegrationTester, PerformanceTester,
    CapturedEvent, ValidationResult, EventAnalysis,
    create_validation_framework, run_comprehensive_validation
)


class TestEventCaptureSystem:
    """Test event capture system functionality."""
    
    def test_capture_system_initialization(self):
        """Test capture system initialization."""
        capture = EventCaptureSystem("test_capture")
        
        assert capture.capture_id == "test_capture"
        assert len(capture.captured_events) == 0
        assert not capture.is_capturing
        assert len(capture.expected_events) == 0
    
    def test_event_filtering(self):
        """Test event filtering functionality."""
        capture = EventCaptureSystem()
        
        # Add filter that only captures trade events
        capture.add_event_filter("trade_only", lambda event: event.event_type == "trade_execution")
        
        # Start capturing
        capture.start_capture()
        
        # Capture different event types
        mode_event = AgentModeChangeEvent.create(1, 1, "foraging", "trading")
        trade_event = TradeExecutionEvent.create(2, 1, 2, "wood", "food", 5.0, 3.0)
        
        capture.capture_event(mode_event)
        capture.capture_event(trade_event)
        
        capture.stop_capture()
        
        # Should only have captured trade event
        assert len(capture.captured_events) == 1
        assert capture.captured_events[0].event.event_type == "trade_execution"
    
    def test_capture_session_context(self):
        """Test capture session context manager."""
        capture = EventCaptureSystem()
        
        # Should not be capturing initially
        assert not capture.is_capturing
        
        # Test context manager
        with capture.capture_session():
            assert capture.is_capturing
            
            event = AgentModeChangeEvent.create(1, 1, "foraging", "trading")
            capture.capture_event(event)
        
        # Should stop capturing after context
        assert not capture.is_capturing
        assert len(capture.captured_events) == 1
    
    def test_event_analysis(self):
        """Test event analysis functionality."""
        capture = EventCaptureSystem()
        
        with capture.capture_session():
            # Capture multiple events
            for i in range(5):
                event = AgentModeChangeEvent.create(i, i, "foraging", "trading")
                capture.capture_event(event)
            
            # Capture some trade events
            for i in range(3):
                event = TradeExecutionEvent.create(i, i, i+1, "wood", "food", 5.0, 3.0)
                capture.capture_event(event)
        
        # Analyze events
        analysis = capture.analyze_events()
        
        assert analysis.total_events == 8
        assert analysis.events_by_type["agent_mode_change"] == 5
        assert analysis.events_by_type["trade_execution"] == 3
        assert analysis.average_processing_time >= 0
    
    def test_expected_events_validation(self):
        """Test expected events validation."""
        capture = EventCaptureSystem()
        capture.expect_event_types(["agent_mode_change", "trade_execution", "resource_collection"])
        
        with capture.capture_session():
            # Only capture some expected events
            mode_event = AgentModeChangeEvent.create(1, 1, "foraging", "trading")
            trade_event = TradeExecutionEvent.create(2, 1, 2, "wood", "food", 5.0, 3.0)
            
            capture.capture_event(mode_event)
            capture.capture_event(trade_event)
        
        analysis = capture.analyze_events()
        
        # Should identify missing resource_collection event
        assert "resource_collection" in analysis.missing_events
        assert len(analysis.missing_events) == 1
    
    def test_export_capture(self):
        """Test capture export functionality."""
        capture = EventCaptureSystem("export_test")
        
        with capture.capture_session():
            event = AgentModeChangeEvent.create(1, 1, "foraging", "trading")
            capture.capture_event(event, metadata={"test": "data"})
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            capture.export_capture(temp_path)
            
            # Verify exported data
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            assert data["capture_id"] == "export_test"
            assert data["total_events"] == 1
            assert len(data["events"]) == 1
            assert "analysis" in data
            
        finally:
            temp_path.unlink()  # Clean up


class TestObserverValidator:
    """Test observer validator functionality."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return ObservabilityConfig(
            agent_mode_logging=True,
            trade_logging=True
        )
    
    @pytest.fixture
    def registry(self):
        """Create test observer registry."""
        return ObserverRegistry()
    
    @pytest.fixture
    def logger(self, registry):
        """Create test observer logger."""
        return ObserverLogger(registry)
    
    @pytest.fixture
    def gui_observer(self, config):
        """Create test GUI observer."""
        return GUIEventObserver(config, None)
    
    def test_validator_initialization(self, config):
        """Test validator initialization."""
        validator = ObserverValidator(config)
        
        assert validator.config == config
        assert len(validator.validation_results) == 0
    
    def test_registry_validation(self, config, registry):
        """Test observer registry validation."""
        validator = ObserverValidator(config)
        
        result = validator.validate_observer_registry(registry)
        
        assert isinstance(result, ValidationResult)
        assert result.test_name == "observer_registry_validation"
        # Should succeed if registry works properly
        if result.success:
            assert len(result.errors) == 0
        else:
            assert len(result.errors) > 0
    
    def test_logger_validation(self, config, logger):
        """Test observer logger validation."""
        validator = ObserverValidator(config)
        
        result = validator.validate_observer_logger(logger)
        
        assert isinstance(result, ValidationResult)
        assert result.test_name == "observer_logger_validation"
        assert "api_methods_tested" in result.details
        
        # Should test all required GUILogger methods
        assert result.details["api_methods_tested"] == 12
    
    def test_gui_observer_validation(self, config, gui_observer):
        """Test GUI observer validation."""
        validator = ObserverValidator(config)
        
        result = validator.validate_gui_observer(gui_observer)
        
        assert isinstance(result, ValidationResult)
        assert result.test_name == "gui_observer_validation"
        assert "events_processed" in result.details
        assert "updates_generated" in result.details
    
    def test_validation_summary(self, config, registry, logger, gui_observer):
        """Test validation summary generation."""
        validator = ObserverValidator(config)
        
        # Run multiple validations
        validator.validate_observer_registry(registry)
        validator.validate_observer_logger(logger)
        validator.validate_gui_observer(gui_observer)
        
        summary = validator.get_validation_summary()
        
        assert summary["total_tests"] == 3
        assert "successful_tests" in summary
        assert "success_rate" in summary
        assert "test_results" in summary


class TestIntegrationTester:
    """Test integration tester functionality."""
    
    def test_integration_tester_initialization(self):
        """Test integration tester initialization."""
        config = ObservabilityConfig()
        tester = IntegrationTester(config)
        
        assert tester.config == config
        assert isinstance(tester.capture_system, EventCaptureSystem)
    
    def test_observer_pattern_completeness(self):
        """Test observer pattern completeness testing."""
        config = ObservabilityConfig(agent_mode_logging=True, trade_logging=True)
        tester = IntegrationTester(config)
        
        # Create test components
        registry = ObserverRegistry()
        logger = ObserverLogger(registry)
        gui_observer = GUIEventObserver(config, None)
        
        result = tester.test_observer_pattern_completeness(registry, logger, gui_observer)
        
        assert isinstance(result, ValidationResult)
        assert result.test_name == "observer_pattern_completeness"
        assert "events_emitted" in result.details
        assert "observers_registered" in result.details


class TestPerformanceTester:
    """Test performance tester functionality."""
    
    def test_performance_tester_initialization(self):
        """Test performance tester initialization."""
        tester = PerformanceTester()
        
        assert isinstance(tester.benchmark_results, dict)
        assert len(tester.benchmark_results) == 0
    
    def test_observer_overhead_benchmark(self):
        """Test observer overhead benchmarking."""
        config = ObservabilityConfig()
        registry = ObserverRegistry()
        tester = PerformanceTester()
        
        result = tester.benchmark_observer_overhead(registry, event_count=100)
        
        assert isinstance(result, ValidationResult)
        assert result.test_name == "observer_performance_benchmark"
        assert "total_time_seconds" in result.performance_metrics
        assert "events_per_second" in result.performance_metrics
        assert "time_per_event_ms" in result.performance_metrics
    
    def test_gui_observer_performance_benchmark(self):
        """Test GUI observer performance benchmarking."""
        config = ObservabilityConfig(agent_mode_logging=True, trade_logging=True)
        gui_observer = GUIEventObserver(config, None)
        tester = PerformanceTester()
        
        result = tester.benchmark_gui_observer_performance(gui_observer, event_count=100)
        
        assert isinstance(result, ValidationResult)
        assert result.test_name == "gui_observer_performance"
        assert "events_processed" in result.performance_metrics
        assert "updates_generated" in result.performance_metrics
        assert "time_per_event_ms" in result.performance_metrics


class TestFactoryFunctions:
    """Test validation framework factory functions."""
    
    def test_create_validation_framework(self):
        """Test validation framework creation."""
        config = ObservabilityConfig()
        
        capture, validator, integration, performance = create_validation_framework(config)
        
        assert isinstance(capture, EventCaptureSystem)
        assert isinstance(validator, ObserverValidator)
        assert isinstance(integration, IntegrationTester)
        assert isinstance(performance, PerformanceTester)
        assert validator.config == config
    
    def test_comprehensive_validation(self):
        """Test comprehensive validation runner."""
        config = ObservabilityConfig(agent_mode_logging=True, trade_logging=True)
        
        # Create components to validate
        registry = ObserverRegistry(config)
        logger = ObserverLogger(registry)
        gui_observer = GUIEventObserver(config, None)
        
        # Run comprehensive validation
        results = run_comprehensive_validation(registry, logger, gui_observer, config)
        
        assert "summary" in results
        assert "detailed_results" in results
        assert "performance_benchmarks" in results
        assert "validation_timestamp" in results
        
        # Check summary structure
        summary = results["summary"]
        assert "total_tests" in summary
        assert "successful_tests" in summary
        assert "test_categories" in summary
        
        # Should have multiple test results
        assert len(results["detailed_results"]) >= 5  # Registry, logger, GUI, integration, performance


class TestValidationScenarios:
    """Test complete validation scenarios."""
    
    def test_complete_validation_workflow(self):
        """Test complete validation workflow."""
        config = ObservabilityConfig(
            agent_mode_logging=True,
            trade_logging=True,
            behavioral_aggregation=True
        )
        
        # Create observer pattern components
        registry = ObserverRegistry()
        logger = ObserverLogger(registry)
        gui_observer = GUIEventObserver(config, Mock())  # Mock GUI reference
        
        # Register observers
        registry.register_observer(logger)
        registry.register_observer(gui_observer)
        
        # Create validation framework
        capture, validator, integration, performance = create_validation_framework(config)
        
        # Validate each component
        registry_result = validator.validate_observer_registry(registry)
        logger_result = validator.validate_observer_logger(logger)
        gui_result = validator.validate_gui_observer(gui_observer)
        
        # Integration test
        integration_result = integration.test_observer_pattern_completeness(
            registry, logger, gui_observer
        )
        
        # Performance tests
        perf_result = performance.benchmark_observer_overhead(registry, event_count=50)
        gui_perf_result = performance.benchmark_gui_observer_performance(gui_observer, event_count=50)
        
        # All validations should complete
        results = [registry_result, logger_result, gui_result, integration_result, perf_result, gui_perf_result]
        
        # Check that all tests ran
        assert all(isinstance(r, ValidationResult) for r in results)
        
        # Get validation summary
        summary = validator.get_validation_summary()
        assert summary["total_tests"] >= 3  # At least registry, logger, gui
    
    def test_error_handling_validation(self):
        """Test validation error handling."""
        config = ObservabilityConfig()
        validator = ObserverValidator(config)
        
        # Test with None registry (should handle gracefully)
        try:
            result = validator.validate_observer_registry(None)
            # Should return result with errors
            assert isinstance(result, ValidationResult)
            assert not result.success or len(result.errors) > 0
        except Exception:
            # Should handle exceptions gracefully
            pass
    
    def test_performance_threshold_validation(self):
        """Test performance threshold validation."""
        registry = ObserverRegistry()
        tester = PerformanceTester()
        
        # Run benchmark
        result = tester.benchmark_observer_overhead(registry, event_count=10)
        
        # Check that performance metrics are reasonable
        if result.success:
            metrics = result.performance_metrics
            
            # Time per event should be reasonable (< 1ms for small test)
            assert metrics["time_per_event_ms"] < 1.0
            
            # Should be able to process at least 1000 events/second
            assert metrics["events_per_second"] > 1000


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])