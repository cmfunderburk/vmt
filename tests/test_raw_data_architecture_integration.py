"""
Integration tests for the complete raw data architecture.

Tests the end-to-end functionality of the raw data recording system:
RawDataObserver → DataTranslator → RawDataWriter

This validates the complete pipeline from event recording to disk persistence
and human-readable translation.
"""

import pytest
import tempfile
import time
import json
from pathlib import Path
from typing import List, Dict, Any

from src.econsim.observability.raw_data import RawDataObserver, DataTranslator, RawDataWriter


class TestRawDataArchitectureIntegration:
    """Test the complete raw data architecture integration."""
    
    def test_complete_pipeline_basic(self):
        """Test the complete pipeline: record → translate → write."""
        # Initialize components
        observer = RawDataObserver()
        translator = DataTranslator()
        writer = RawDataWriter(compress=False, atomic_writes=False)
        
        # Record various events
        observer.record_trade(step=100, seller_id=1, buyer_id=2, give_type="wood", take_type="stone")
        observer.record_mode_change(step=101, agent_id=1, old_mode="foraging", new_mode="trading", reason="found partner")
        observer.record_resource_collection(step=102, agent_id=1, x=5, y=10, resource_type="wood", amount_collected=2)
        observer.record_debug_log(step=103, category="TRADE", message="Trade completed successfully", agent_id=1)
        
        # Get raw events
        raw_events = observer.get_all_events()
        assert len(raw_events) == 4
        
        # Translate to human-readable format
        translated_events = translator.translate_events(raw_events)
        assert len(translated_events) == 4
        
        # Verify translation quality
        trade_event = translated_events[0]
        assert trade_event['event_type'] == 'Trade Execution'
        assert 'Agent 1' in trade_event['description']
        assert 'wood' in trade_event['description']
        assert 'stone' in trade_event['description']
        
        mode_event = translated_events[1]
        assert mode_event['event_type'] == 'Agent Mode Change'
        assert 'foraging' in mode_event['description']
        assert 'trading' in mode_event['description']
        assert 'found partner' in mode_event['description']
        
        # Write to disk
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "integration_test.jsonl"
            
            write_result = writer.flush_to_disk(raw_events, filepath)
            assert write_result['events_written'] == 4
            assert write_result['bytes_written'] > 0
            
            # Verify file content
            with open(filepath, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 4
                
                # Parse and verify first event
                first_event = json.loads(lines[0].strip())
                assert first_event['type'] == 'trade'
                assert first_event['step'] == 100
                assert first_event['seller_id'] == 1
                assert first_event['buyer_id'] == 2
    
    def test_complete_pipeline_with_compression(self):
        """Test the complete pipeline with compression."""
        # Initialize components
        observer = RawDataObserver()
        translator = DataTranslator()
        writer = RawDataWriter(compress=True, atomic_writes=False)
        
        # Record events with larger data
        for i in range(10):
            observer.record_trade(
                step=100 + i,
                seller_id=i % 5,
                buyer_id=(i + 1) % 5,
                give_type="wood",
                take_type="stone",
                data=f"trade_data_{i}" * 10  # Add data for compression
            )
        
        # Get raw events
        raw_events = observer.get_all_events()
        assert len(raw_events) == 10
        
        # Translate to human-readable format
        translated_events = translator.translate_events(raw_events)
        assert len(translated_events) == 10
        
        # Write to disk with compression
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "compressed_test.jsonl"
            
            write_result = writer.flush_to_disk(raw_events, filepath)
            assert write_result['events_written'] == 10
            assert write_result['compressed'] == True
            assert write_result['compression_ratio'] < 1.0  # Should be compressed
            
            # Verify compressed file can be read
            import gzip
            with gzip.open(write_result['filepath'], 'rt') as f:
                lines = f.readlines()
                assert len(lines) == 10
                
                # Parse and verify events
                for i, line in enumerate(lines):
                    event = json.loads(line.strip())
                    assert event['type'] == 'trade'
                    assert event['step'] == 100 + i
    
    def test_complete_pipeline_with_rotation(self):
        """Test the complete pipeline with file rotation."""
        # Initialize components
        observer = RawDataObserver()
        translator = DataTranslator()
        writer = RawDataWriter(
            compress=False,
            max_file_size_mb=0.01,  # Very small file size to trigger rotation
            enable_rotation=True,
            atomic_writes=False
        )
        
        # Record many events to trigger rotation
        for i in range(50):
            observer.record_trade(
                step=100 + i,
                seller_id=i % 10,
                buyer_id=(i + 1) % 10,
                give_type="wood",
                take_type="stone",
                data=f"rotation_test_data_{i}" * 5  # Add data to increase size
            )
        
        # Get raw events
        raw_events = observer.get_all_events()
        assert len(raw_events) == 50
        
        # Write to disk with rotation
        with tempfile.TemporaryDirectory() as temp_dir:
            base_filepath = Path(temp_dir) / "rotation_test.jsonl"
            
            write_results = writer.flush_to_disk_with_rotation(raw_events, base_filepath)
            assert len(write_results) > 1  # Should have multiple files
            
            # Verify total events written
            total_events = sum(result['events_written'] for result in write_results)
            assert total_events == 50
            
            # Verify all files exist and can be read
            for result in write_results:
                filepath = Path(result['filepath'])
                assert filepath.exists()
                
                with open(filepath, 'r') as f:
                    lines = f.readlines()
                    assert len(lines) == result['events_written']
    
    def test_performance_integration(self):
        """Test performance of the complete pipeline."""
        # Initialize components
        observer = RawDataObserver()
        translator = DataTranslator()
        writer = RawDataWriter(compress=False, atomic_writes=False)
        
        # Record many events for performance testing
        num_events = 1000
        start_time = time.time()
        
        for i in range(num_events):
            observer.record_trade(
                step=100 + i,
                seller_id=i % 10,
                buyer_id=(i + 1) % 10,
                give_type="wood",
                take_type="stone"
            )
        
        recording_time = time.time() - start_time
        
        # Test translation performance
        raw_events = observer.get_all_events()
        assert len(raw_events) == num_events
        
        start_time = time.time()
        translated_events = translator.translate_events(raw_events)
        translation_time = time.time() - start_time
        
        # Test write performance
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "performance_test.jsonl"
            
            start_time = time.time()
            write_result = writer.flush_to_disk(raw_events, filepath)
            write_time = time.time() - start_time
        
        # Performance assertions
        per_event_recording = recording_time / num_events
        per_event_translation = translation_time / num_events
        per_event_write = write_time / num_events
        
        # Recording should be very fast (<0.001ms per event)
        assert per_event_recording < 0.000001, f"Recording too slow: {per_event_recording:.9f}s per event"
        
        # Translation should be reasonable (<0.01ms per event)
        assert per_event_translation < 0.00001, f"Translation too slow: {per_event_translation:.9f}s per event"
        
        # Write should be reasonable (<0.1ms per event)
        assert per_event_write < 0.0001, f"Write too slow: {per_event_write:.9f}s per event"
        
        # Verify results
        assert write_result['events_written'] == num_events
        assert len(translated_events) == num_events
    
    def test_memory_efficiency_integration(self):
        """Test memory efficiency of the complete pipeline."""
        # Initialize components
        observer = RawDataObserver()
        translator = DataTranslator()
        writer = RawDataWriter(compress=False, atomic_writes=False)
        
        # Record events and check memory usage
        for i in range(100):
            observer.record_trade(
                step=100 + i,
                seller_id=i % 10,
                buyer_id=(i + 1) % 10,
                give_type="wood",
                take_type="stone"
            )
        
        # Get memory usage estimate
        memory_stats = observer.get_memory_usage_estimate()
        assert memory_stats['events_count'] == 100
        assert memory_stats['bytes_per_event'] > 0
        assert memory_stats['total_bytes'] > 0
        
        # Test that memory usage is reasonable
        assert memory_stats['bytes_per_event'] < 1000, f"Memory per event too high: {memory_stats['bytes_per_event']} bytes"
        
        # Test translation doesn't cause memory issues
        raw_events = observer.get_all_events()
        translated_events = translator.translate_events(raw_events)
        
        # Verify translation worked
        assert len(translated_events) == 100
        assert all('description' in event for event in translated_events)
    
    def test_error_handling_integration(self):
        """Test error handling across the complete pipeline."""
        # Initialize components
        observer = RawDataObserver()
        translator = DataTranslator()
        writer = RawDataWriter(compress=False, atomic_writes=False)
        
        # Record valid events
        observer.record_trade(step=100, seller_id=1, buyer_id=2, give_type="wood", take_type="stone")
        observer.record_mode_change(step=101, agent_id=1, old_mode="foraging", new_mode="trading", reason="found partner")
        
        # Test translation with missing fields (should handle gracefully)
        raw_events = observer.get_all_events()
        
        # Add an event with missing fields to test error handling
        raw_events.append({
            'type': 'trade',
            'step': 102
            # Missing required fields
        })
        
        # Translation should handle missing fields gracefully
        translated_events = translator.translate_events(raw_events)
        assert len(translated_events) == 3
        
        # The event with missing fields should still be translated
        last_event = translated_events[-1]
        assert last_event['event_type'] == 'Trade Execution'
        assert last_event['seller_id'] == -1  # Default value
        
        # Test write error handling
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with invalid file path
            invalid_path = Path("/invalid/directory/that/does/not/exist/test.jsonl")
            
            with pytest.raises(OSError, match="Failed to write events"):
                writer.flush_to_disk(raw_events, invalid_path)
    
    def test_statistics_integration(self):
        """Test statistics across the complete pipeline."""
        # Initialize components
        observer = RawDataObserver()
        translator = DataTranslator()
        writer = RawDataWriter(compress=False, atomic_writes=False)
        
        # Record events
        for i in range(20):
            observer.record_trade(
                step=100 + i,
                seller_id=i % 5,
                buyer_id=(i + 1) % 5,
                give_type="wood",
                take_type="stone"
            )
        
        # Get observer statistics
        observer_stats = observer.get_statistics()
        assert observer_stats['total_events'] == 20
        assert observer_stats['events_per_second'] > 0
        assert 'trade' in observer_stats['event_types']
        
        # Get event type counts
        type_counts = observer.get_event_type_counts()
        assert type_counts['trade'] == 20
        
        # Test translation statistics
        raw_events = observer.get_all_events()
        translated_events = translator.translate_events(raw_events)
        
        # Count translated event types
        translated_types = [event['event_type'] for event in translated_events]
        assert translated_types.count('Trade Execution') == 20
        
        # Test writer statistics
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "stats_test.jsonl"
            
            write_result = writer.flush_to_disk(raw_events, filepath)
            assert write_result['events_written'] == 20
            
            writer_stats = writer.get_statistics()
            assert writer_stats['files_written'] == 1
            assert writer_stats['events_written'] == 20
            assert writer_stats['bytes_written'] > 0
    
    def test_unicode_integration(self):
        """Test unicode handling across the complete pipeline."""
        # Initialize components
        observer = RawDataObserver()
        translator = DataTranslator()
        writer = RawDataWriter(compress=False, atomic_writes=False)
        
        # Record events with unicode data
        observer.record_debug_log(
            step=100,
            category="UNICODE",
            message="Hello 世界 🌍 émojis",
            agent_id=1
        )
        
        observer.record_trade(
            step=101,
            seller_id=1,
            buyer_id=2,
            give_type="wood",
            take_type="stone",
            unicode_field="测试数据 🎯"
        )
        
        # Test observer handling
        raw_events = observer.get_all_events()
        assert len(raw_events) == 2
        
        # Test translation handling
        translated_events = translator.translate_events(raw_events)
        assert len(translated_events) == 2
        
        # Verify unicode in descriptions
        debug_event = translated_events[0]
        assert "世界" in debug_event['description']
        assert "🌍" in debug_event['description']
        assert "émojis" in debug_event['description']
        
        # Test write handling
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "unicode_test.jsonl"
            
            write_result = writer.flush_to_disk(raw_events, filepath)
            assert write_result['events_written'] == 2
            
            # Verify file can be read and unicode is preserved
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                assert len(lines) == 2
                
                # Parse and verify unicode content
                debug_event = json.loads(lines[0].strip())
                assert "世界" in debug_event['message']
                assert "🌍" in debug_event['message']
                
                trade_event = json.loads(lines[1].strip())
                assert "测试数据" in trade_event['unicode_field']
                assert "🎯" in trade_event['unicode_field']


if __name__ == "__main__":
    pytest.main([__file__])
