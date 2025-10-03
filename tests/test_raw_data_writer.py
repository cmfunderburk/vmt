"""
Unit tests for RawDataWriter - Disk persistence for raw simulation data.

Tests the disk persistence system that writes raw simulation data to files
with compression, rotation, and statistics tracking.

Test Categories:
- Basic write operations: flush_to_disk() with various configurations
- Compression: gzip compression with different levels
- File rotation: Automatic file splitting for large datasets
- Atomic writes: Safe file writing with temporary files
- Statistics tracking: Write metrics and performance data
- Error handling: Invalid data, file system errors, cleanup
- Edge cases: Empty events, large files, unicode data
"""

import pytest
import tempfile
import gzip
import json
import os
from pathlib import Path
from typing import Dict, List, Any

from src.econsim.observability.raw_data.raw_data_writer import RawDataWriter


class TestRawDataWriterBasicOperations:
    """Test basic write operations and file handling."""
    
    def test_flush_to_disk_basic(self):
        """Test basic disk flush with simple events."""
        writer = RawDataWriter(compress=False, atomic_writes=False)
        
        events = [
            {
                'type': 'trade',
                'step': 100,
                'seller_id': 1,
                'buyer_id': 2,
                'give_type': 'wood',
                'take_type': 'stone'
            },
            {
                'type': 'mode_change',
                'step': 101,
                'agent_id': 1,
                'old_mode': 'foraging',
                'new_mode': 'trading',
                'reason': 'found partner'
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "test_events.jsonl"
            
            result = writer.flush_to_disk(events, filepath)
            
            # Check result
            assert result['events_written'] == 2
            assert result['bytes_written'] > 0
            assert result['compressed'] == False
            assert result['append_mode'] == False
            assert result['atomic_write'] == False
            assert result['filepath'] == str(filepath)
            
            # Check file exists and has correct content
            assert filepath.exists()
            
            with open(filepath, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 2
                
                # Parse first line
                event1 = json.loads(lines[0].strip())
                assert event1['type'] == 'trade'
                assert event1['step'] == 100
                
                # Parse second line
                event2 = json.loads(lines[1].strip())
                assert event2['type'] == 'mode_change'
                assert event2['step'] == 101
    
    def test_flush_to_disk_compressed(self):
        """Test disk flush with gzip compression."""
        writer = RawDataWriter(compress=True, atomic_writes=False)
        
        events = [
            {
                'type': 'trade',
                'step': 100,
                'seller_id': 1,
                'buyer_id': 2,
                'give_type': 'wood',
                'take_type': 'stone'
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "test_events.jsonl"
            
            result = writer.flush_to_disk(events, filepath)
            
            # Check result
            assert result['events_written'] == 1
            assert result['compressed'] == True
            assert result['compression_ratio'] > 0
            assert result['filepath'].endswith('.gz')
            
            # Check compressed file exists
            compressed_path = Path(result['filepath'])
            assert compressed_path.exists()
            
            # Read and verify compressed content
            with gzip.open(compressed_path, 'rt') as f:
                lines = f.readlines()
                assert len(lines) == 1
                
                event = json.loads(lines[0].strip())
                assert event['type'] == 'trade'
                assert event['step'] == 100
    
    def test_flush_to_disk_atomic(self):
        """Test atomic writes with temporary files."""
        writer = RawDataWriter(compress=False, atomic_writes=True)
        
        events = [
            {
                'type': 'debug_log',
                'step': 100,
                'category': 'TEST',
                'message': 'Atomic write test',
                'agent_id': -1
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "test_atomic.jsonl"
            
            result = writer.flush_to_disk(events, filepath)
            
            # Check result
            assert result['atomic_write'] == True
            assert result['events_written'] == 1
            
            # Check file exists and has correct content
            assert filepath.exists()
            
            with open(filepath, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 1
                
                event = json.loads(lines[0].strip())
                assert event['type'] == 'debug_log'
                assert event['message'] == 'Atomic write test'
    
    def test_flush_to_disk_append(self):
        """Test appending to existing file."""
        writer = RawDataWriter(compress=False, atomic_writes=False)
        
        initial_events = [
            {
                'type': 'trade',
                'step': 100,
                'seller_id': 1,
                'buyer_id': 2,
                'give_type': 'wood',
                'take_type': 'stone'
            }
        ]
        
        additional_events = [
            {
                'type': 'mode_change',
                'step': 101,
                'agent_id': 1,
                'old_mode': 'foraging',
                'new_mode': 'trading',
                'reason': 'found partner'
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "test_append.jsonl"
            
            # Write initial events
            result1 = writer.flush_to_disk(initial_events, filepath)
            assert result1['events_written'] == 1
            
            # Append additional events
            result2 = writer.flush_to_disk(additional_events, filepath, append=True)
            assert result2['events_written'] == 1
            assert result2['append_mode'] == True
            
            # Check file has both events
            with open(filepath, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 2
                
                # Parse both events
                event1 = json.loads(lines[0].strip())
                event2 = json.loads(lines[1].strip())
                
                assert event1['type'] == 'trade'
                assert event2['type'] == 'mode_change'
    
    def test_flush_to_disk_empty_events(self):
        """Test writing empty events list."""
        writer = RawDataWriter(compress=False, atomic_writes=False)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "test_empty.jsonl"
            
            result = writer.flush_to_disk([], filepath)
            
            # Check result
            assert result['events_written'] == 0
            assert result['bytes_written'] == 0
            assert result['empty_file'] == True
            
            # File should not exist for empty events
            assert not filepath.exists()


class TestRawDataWriterCompression:
    """Test compression features and configuration."""
    
    def test_compression_levels(self):
        """Test different compression levels."""
        events = [
            {
                'type': 'trade',
                'step': 100,
                'seller_id': 1,
                'buyer_id': 2,
                'give_type': 'wood',
                'take_type': 'stone',
                'data': 'x' * 1000  # Add some data to make compression meaningful
            }
        ]
        
        compression_results = {}
        
        for level in [1, 6, 9]:
            writer = RawDataWriter(compress=True, compression_level=level, atomic_writes=False)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                filepath = Path(temp_dir) / f"test_level_{level}.jsonl"
                
                result = writer.flush_to_disk(events, filepath)
                compression_results[level] = result['compression_ratio']
        
        # Higher compression levels should generally provide better compression
        # (though this isn't guaranteed for all data)
        assert all(0.0 < ratio < 1.0 for ratio in compression_results.values())
    
    def test_compression_ratio_calculation(self):
        """Test compression ratio calculation."""
        # Create events with repetitive data for good compression
        events = []
        for i in range(10):
            events.append({
                'type': 'trade',
                'step': 100 + i,
                'seller_id': 1,
                'buyer_id': 2,
                'give_type': 'wood',
                'take_type': 'stone',
                'repetitive_data': 'same_data_' * 50  # Repetitive for good compression
            })
        
        writer = RawDataWriter(compress=True, atomic_writes=False)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "test_compression.jsonl"
            
            result = writer.flush_to_disk(events, filepath)
            
        # Should have excellent compression ratio for repetitive data
        assert 0.01 < result['compression_ratio'] < 0.5  # 1-50% of original size
    
    def test_compression_disabled(self):
        """Test with compression disabled."""
        events = [
            {
                'type': 'trade',
                'step': 100,
                'seller_id': 1,
                'buyer_id': 2,
                'give_type': 'wood',
                'take_type': 'stone'
            }
        ]
        
        writer = RawDataWriter(compress=False, atomic_writes=False)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "test_no_compression.jsonl"
            
            result = writer.flush_to_disk(events, filepath)
            
            # Check result
            assert result['compressed'] == False
            assert result['compression_ratio'] == 1.0  # No compression
            assert not result['filepath'].endswith('.gz')
            
            # File should be regular text file
            assert filepath.exists()
            with open(filepath, 'r') as f:
                content = f.read()
                assert 'trade' in content


class TestRawDataWriterFileRotation:
    """Test file rotation features."""
    
    def test_file_rotation_basic(self):
        """Test basic file rotation functionality."""
        # Create many events to trigger rotation
        events = []
        for i in range(1000):  # Large number of events
            events.append({
                'type': 'trade',
                'step': 100 + i,
                'seller_id': i % 10,
                'buyer_id': (i + 1) % 10,
                'give_type': 'wood',
                'take_type': 'stone',
                'data': f'event_data_{i}' * 10  # Add data to increase file size
            })
        
        writer = RawDataWriter(
            compress=False,
            max_file_size_mb=0.1,  # Very small file size (100KB) to trigger rotation
            enable_rotation=True,
            atomic_writes=False
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            base_filepath = Path(temp_dir) / "test_rotation.jsonl"
            
            results = writer.flush_to_disk_with_rotation(events, base_filepath)
            
            # Should have created multiple files
            assert len(results) > 1
            
            # Check that all events were written
            total_events = sum(result['events_written'] for result in results)
            assert total_events == 1000
            
            # Check that files exist
            for result in results:
                filepath = Path(result['filepath'])
                assert filepath.exists()
    
    def test_file_rotation_disabled(self):
        """Test with file rotation disabled."""
        events = []
        for i in range(100):  # Many events
            events.append({
                'type': 'trade',
                'step': 100 + i,
                'seller_id': i % 10,
                'buyer_id': (i + 1) % 10,
                'give_type': 'wood',
                'take_type': 'stone'
            })
        
        writer = RawDataWriter(
            compress=False,
            enable_rotation=False,
            atomic_writes=False
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            base_filepath = Path(temp_dir) / "test_no_rotation.jsonl"
            
            results = writer.flush_to_disk_with_rotation(events, base_filepath)
            
            # Should have created only one file
            assert len(results) == 1
            
            # Check that all events were written
            assert results[0]['events_written'] == 100
    
    def test_file_rotation_with_compression(self):
        """Test file rotation with compression enabled."""
        events = []
        for i in range(500):  # Moderate number of events
            events.append({
                'type': 'trade',
                'step': 100 + i,
                'seller_id': i % 10,
                'buyer_id': (i + 1) % 10,
                'give_type': 'wood',
                'take_type': 'stone',
                'data': f'event_data_{i}' * 5
            })
        
        writer = RawDataWriter(
            compress=True,
            max_file_size_mb=0.05,  # Very small file size (50KB) to trigger rotation
            enable_rotation=True,
            atomic_writes=False
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            base_filepath = Path(temp_dir) / "test_rotation_compressed.jsonl"
            
            results = writer.flush_to_disk_with_rotation(events, base_filepath)
            
            # Should have created multiple files
            assert len(results) > 1
            
            # All files should be compressed
            for result in results:
                assert result['compressed'] == True
                assert result['filepath'].endswith('.gz')
                
                # Verify compressed files can be read
                filepath = Path(result['filepath'])
                assert filepath.exists()
                
                with gzip.open(filepath, 'rt') as f:
                    lines = f.readlines()
                    assert len(lines) == result['events_written']


class TestRawDataWriterStatistics:
    """Test statistics tracking and reporting."""
    
    def test_statistics_tracking(self):
        """Test comprehensive statistics tracking."""
        writer = RawDataWriter(compress=False, atomic_writes=False)
        
        events1 = [
            {
                'type': 'trade',
                'step': 100,
                'seller_id': 1,
                'buyer_id': 2,
                'give_type': 'wood',
                'take_type': 'stone'
            }
        ]
        
        events2 = [
            {
                'type': 'mode_change',
                'step': 101,
                'agent_id': 1,
                'old_mode': 'foraging',
                'new_mode': 'trading',
                'reason': 'found partner'
            },
            {
                'type': 'debug_log',
                'step': 102,
                'category': 'TEST',
                'message': 'Test message',
                'agent_id': -1
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath1 = Path(temp_dir) / "test_stats1.jsonl"
            filepath2 = Path(temp_dir) / "test_stats2.jsonl"
            
            # Write first batch
            result1 = writer.flush_to_disk(events1, filepath1)
            
            # Write second batch
            result2 = writer.flush_to_disk(events2, filepath2)
            
            # Get statistics
            stats = writer.get_statistics()
            
            # Check statistics
            assert stats['files_written'] == 2
            assert stats['events_written'] == 3  # 1 + 2
            assert stats['bytes_written'] == result1['bytes_written'] + result2['bytes_written']
            assert stats['write_time_seconds'] > 0
            assert stats['last_write_time'] > 0
            assert stats['average_events_per_file'] == 1.5  # 3 events / 2 files
            assert stats['average_bytes_per_event'] > 0
            assert stats['events_per_second'] > 0
    
    def test_statistics_reset(self):
        """Test resetting statistics."""
        writer = RawDataWriter(compress=False, atomic_writes=False)
        
        events = [
            {
                'type': 'trade',
                'step': 100,
                'seller_id': 1,
                'buyer_id': 2,
                'give_type': 'wood',
                'take_type': 'stone'
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "test_reset.jsonl"
            
            # Write some events
            writer.flush_to_disk(events, filepath)
            
            # Check statistics are non-zero
            stats_before = writer.get_statistics()
            assert stats_before['files_written'] > 0
            assert stats_before['events_written'] > 0
            
            # Reset statistics
            writer.reset_statistics()
            
            # Check statistics are zero
            stats_after = writer.get_statistics()
            assert stats_after['files_written'] == 0
            assert stats_after['events_written'] == 0
            assert stats_after['bytes_written'] == 0
            assert stats_after['write_time_seconds'] == 0.0
    
    def test_estimate_file_size(self):
        """Test file size estimation."""
        writer = RawDataWriter(compress=True, atomic_writes=False)
        
        events = [
            {
                'type': 'trade',
                'step': 100,
                'seller_id': 1,
                'buyer_id': 2,
                'give_type': 'wood',
                'take_type': 'stone',
                'data': 'test_data' * 100
            }
        ]
        
        estimate = writer.estimate_file_size(events)
        
        # Check estimate structure
        assert 'uncompressed_bytes' in estimate
        assert 'compressed_bytes' in estimate
        assert 'events_count' in estimate
        
        # Check values
        assert estimate['events_count'] == 1
        assert estimate['uncompressed_bytes'] > 0
        assert estimate['compressed_bytes'] > 0
        assert estimate['compressed_bytes'] <= estimate['uncompressed_bytes']
    
    def test_get_configuration(self):
        """Test getting writer configuration."""
        writer = RawDataWriter(
            compress=True,
            compression_level=9,
            max_file_size_mb=50,
            enable_rotation=False,
            atomic_writes=True
        )
        
        config = writer.get_configuration()
        
        assert config['compress'] == True
        assert config['compression_level'] == 9
        assert config['max_file_size_mb'] == 50
        assert config['enable_rotation'] == False
        assert config['atomic_writes'] == True


class TestRawDataWriterErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_events_list(self):
        """Test handling of invalid events list."""
        writer = RawDataWriter(compress=False, atomic_writes=False)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "test_invalid.jsonl"
            
            # Test with non-list
            with pytest.raises(ValueError, match="Events must be a list"):
                writer.flush_to_disk("not a list", filepath)
            
            # Test with non-dictionary event
            with pytest.raises(ValueError, match="Event at index 0 is not a dictionary"):
                writer.flush_to_disk(["not a dict"], filepath)
            
            # Test with missing type field
            with pytest.raises(ValueError, match="missing required 'type' field"):
                writer.flush_to_disk([{"step": 100}], filepath)
            
            # Test with missing step field
            with pytest.raises(ValueError, match="missing required 'step' field"):
                writer.flush_to_disk([{"type": "trade"}], filepath)
    
    def test_file_system_errors(self):
        """Test handling of file system errors."""
        writer = RawDataWriter(compress=False, atomic_writes=False)
        
        events = [
            {
                'type': 'trade',
                'step': 100,
                'seller_id': 1,
                'buyer_id': 2,
                'give_type': 'wood',
                'take_type': 'stone'
            }
        ]
        
        # Test with invalid directory
        invalid_path = Path("/invalid/directory/that/does/not/exist/test.jsonl")
        
        with pytest.raises(IOError, match="Failed to write events"):
            writer.flush_to_disk(events, invalid_path)
    
    def test_unicode_handling(self):
        """Test handling of unicode characters in events."""
        writer = RawDataWriter(compress=False, atomic_writes=False)
        
        events = [
            {
                'type': 'debug_log',
                'step': 100,
                'category': 'UNICODE',
                'message': 'Hello 世界 🌍 émojis',
                'agent_id': 1
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "test_unicode.jsonl"
            
            result = writer.flush_to_disk(events, filepath)
            
            # Check result
            assert result['events_written'] == 1
            
            # Read and verify unicode content
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                assert len(lines) == 1
                
                event = json.loads(lines[0].strip())
                assert event['message'] == 'Hello 世界 🌍 émojis'
                assert '世界' in event['message']
                assert '🌍' in event['message']
                assert 'émojis' in event['message']
    
    def test_large_data_handling(self):
        """Test handling of large data in events."""
        writer = RawDataWriter(compress=True, atomic_writes=False)
        
        # Create event with large data
        large_data = "x" * 10000  # 10KB of data
        events = [
            {
                'type': 'debug_log',
                'step': 100,
                'category': 'LARGE',
                'message': large_data,
                'agent_id': 1
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "test_large.jsonl"
            
            result = writer.flush_to_disk(events, filepath)
            
            # Check result
            assert result['events_written'] == 1
            assert result['bytes_written'] > 10000  # Should be larger than original due to JSON overhead
            
            # Read and verify large content
            with gzip.open(filepath.with_suffix('.jsonl.gz'), 'rt') as f:
                lines = f.readlines()
                assert len(lines) == 1
                
                event = json.loads(lines[0].strip())
                assert event['message'] == large_data
                assert len(event['message']) == 10000


class TestRawDataWriterUtilityMethods:
    """Test utility methods and edge cases."""
    
    def test_repr_method(self):
        """Test __repr__ method."""
        writer = RawDataWriter(compress=True, atomic_writes=False)
        
        repr_str = repr(writer)
        
        assert 'RawDataWriter' in repr_str
        assert 'compress=True' in repr_str
        assert 'files=0' in repr_str  # No files written yet
        assert 'events=0' in repr_str  # No events written yet
        assert 'bytes=0' in repr_str   # No bytes written yet
    
    def test_compression_level_clamping(self):
        """Test that compression levels are clamped to valid range."""
        # Test level too low
        writer1 = RawDataWriter(compress=True, compression_level=0)
        assert writer1.compression_level == 1
        
        # Test level too high
        writer2 = RawDataWriter(compress=True, compression_level=10)
        assert writer2.compression_level == 9
        
        # Test valid level
        writer3 = RawDataWriter(compress=True, compression_level=6)
        assert writer3.compression_level == 6
    
    def test_file_path_preparation(self):
        """Test file path preparation with compression."""
        writer_compressed = RawDataWriter(compress=True)
        writer_uncompressed = RawDataWriter(compress=False)
        
        base_path = Path("test.jsonl")
        
        # Test compressed path
        compressed_path = writer_compressed._prepare_file_path(base_path)
        assert compressed_path.suffix == '.gz'
        assert compressed_path.name == 'test.jsonl.gz'
        
        # Test uncompressed path
        uncompressed_path = writer_uncompressed._prepare_file_path(base_path)
        assert uncompressed_path.suffix == '.jsonl'
        assert uncompressed_path.name == 'test.jsonl'
    
    def test_rotation_suffix_generation(self):
        """Test rotation suffix generation."""
        writer = RawDataWriter(compress=True)
        
        # Test with compression - need to prepare the path first
        base_path = Path("test.jsonl")
        prepared_path = writer._prepare_file_path(base_path)  # This adds .gz extension
        rotated_path = writer._add_rotation_suffix(prepared_path, 5)
        assert rotated_path.name == 'test_005.jsonl.gz'
        
        # Test without compression
        writer_uncompressed = RawDataWriter(compress=False)
        rotated_path_uncompressed = writer_uncompressed._add_rotation_suffix(base_path, 12)
        assert rotated_path_uncompressed.name == 'test_012.jsonl'


if __name__ == "__main__":
    pytest.main([__file__])
