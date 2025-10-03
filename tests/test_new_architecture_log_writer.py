"""
Unit tests for the new extensible log writer.

Tests the ExtensibleLogWriter class including buffering, flushing,
context manager support, and thread safety.
"""

import json
import tempfile
import threading
import time
from pathlib import Path
from typing import List

import pytest

from src.econsim.observability.new_architecture.log_writer import ExtensibleLogWriter


class TestExtensibleLogWriter:
    """Test suite for ExtensibleLogWriter."""
    
    def test_context_manager_basic_usage(self):
        """Test basic context manager usage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            
            with ExtensibleLogWriter(log_file) as writer:
                assert writer.is_open()
                writer.write_entry({"test": "data", "step": 1})
            
            # File should be closed after context exit
            assert not writer.is_open()
            
            # Verify content was written
            with open(log_file, 'r') as f:
                content = f.read().strip()
                assert content == '{"test":"data","step":1}'
    
    def test_buffered_writing(self):
        """Test that entries are buffered and written together."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            
            with ExtensibleLogWriter(log_file, buffer_size=3) as writer:
                writer.write_entry({"entry": 1})
                writer.write_entry({"entry": 2})
                writer.write_entry({"entry": 3})  # Should trigger flush
                
                # Add one more entry
                writer.write_entry({"entry": 4})
            
            # Verify all entries were written
            with open(log_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 4
                assert json.loads(lines[0]) == {"entry": 1}
                assert json.loads(lines[1]) == {"entry": 2}
                assert json.loads(lines[2]) == {"entry": 3}
                assert json.loads(lines[3]) == {"entry": 4}
    
    def test_manual_flush(self):
        """Test manual flush functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            
            with ExtensibleLogWriter(log_file, buffer_size=10) as writer:
                writer.write_entry({"entry": 1})
                writer.write_entry({"entry": 2})
                
                # Manual flush should write buffered entries
                writer.flush()
                
                # Verify entries were written despite buffer not being full
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    assert len(lines) == 2
                    assert json.loads(lines[0]) == {"entry": 1}
                    assert json.loads(lines[1]) == {"entry": 2}
    
    def test_time_based_flush(self):
        """Test time-based auto-flush."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            
            with ExtensibleLogWriter(log_file, buffer_size=100, flush_interval_sec=0.1) as writer:
                writer.write_entry({"entry": 1})
                
                # Wait for time-based flush
                time.sleep(0.15)
                
                writer.write_entry({"entry": 2})  # Should trigger another flush
                
                # Give a moment for the flush to complete
                time.sleep(0.05)
            
            # Verify entries were written due to time-based flush
            with open(log_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 2
                assert json.loads(lines[0]) == {"entry": 1}
                assert json.loads(lines[1]) == {"entry": 2}
    
    def test_statistics(self):
        """Test statistics tracking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            
            with ExtensibleLogWriter(log_file, buffer_size=2) as writer:
                writer.write_entry({"test": "data1"})
                writer.write_entry({"test": "data2"})  # Should trigger flush
                writer.write_entry({"test": "data3"})
                
                stats = writer.get_statistics()
                
                assert stats['entries_written'] == 2  # Only flushed entries
                assert stats['flush_count'] == 1
                assert stats['buffer_size'] == 1  # One entry still in buffer
                assert stats['filepath'] == str(log_file)
                assert stats['bytes_written'] > 0
            
            # Verify all entries were written to file
            with open(log_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 3  # All entries should be written after context exit
    
    def test_json_format(self):
        """Test that entries are written in compact JSON format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            
            with ExtensibleLogWriter(log_file) as writer:
                # Test various data types
                writer.write_entry({
                    "string": "value",
                    "number": 42,
                    "float": 3.14,
                    "boolean": True,
                    "null": None,
                    "list": [1, 2, 3],
                    "nested": {"key": "value"}
                })
            
            # Verify compact JSON format (no extra spaces)
            with open(log_file, 'r') as f:
                content = f.read().strip()
                # Should be compact JSON (no spaces after colons/commas)
                assert ' ' not in content
                assert content == '{"string":"value","number":42,"float":3.14,"boolean":true,"null":null,"list":[1,2,3],"nested":{"key":"value"}}'
    
    def test_directory_creation(self):
        """Test that parent directories are created automatically."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested directory structure
            log_file = Path(temp_dir) / "nested" / "dirs" / "test.log"
            
            with ExtensibleLogWriter(log_file) as writer:
                writer.write_entry({"test": "data"})
            
            # Verify file was created in nested directory
            assert log_file.exists()
            assert log_file.parent.exists()
    
    def test_thread_safety(self):
        """Test thread safety of the log writer."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            
            results: List[str] = []
            
            def write_entries(thread_id: int, count: int):
                """Write entries from a specific thread."""
                with ExtensibleLogWriter(log_file) as writer:
                    for i in range(count):
                        writer.write_entry({
                            "thread": thread_id,
                            "entry": i,
                            "data": f"thread_{thread_id}_entry_{i}"
                        })
                        time.sleep(0.001)  # Small delay to encourage race conditions
            
            # Start multiple threads writing simultaneously
            threads = []
            for thread_id in range(3):
                thread = threading.Thread(target=write_entries, args=(thread_id, 10))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify all entries were written without corruption
            with open(log_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 30  # 3 threads × 10 entries each
                
                # Verify each line is valid JSON
                for line in lines:
                    entry = json.loads(line.strip())
                    assert "thread" in entry
                    assert "entry" in entry
                    assert "data" in entry
                    assert entry["thread"] in [0, 1, 2]
                    assert 0 <= entry["entry"] < 10
    
    def test_error_handling(self):
        """Test error handling when file operations fail."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a directory that we'll make read-only to cause write errors
            log_file = Path(temp_dir) / "test.log"
            
            with ExtensibleLogWriter(log_file) as writer:
                # This should not raise an exception
                writer.write_entry({"test": "data"})
                
                # Make the directory read-only (Unix-like systems)
                try:
                    log_file.parent.chmod(0o444)
                    
                    # This should handle the error gracefully
                    writer.write_entry({"test": "data2"})
                    writer.flush()
                    
                finally:
                    # Restore permissions
                    log_file.parent.chmod(0o755)
    
    def test_close_method(self):
        """Test explicit close method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            
            writer = ExtensibleLogWriter(log_file)
            writer.__enter__()
            
            assert writer.is_open()
            writer.write_entry({"test": "data"})
            
            writer.close()
            assert not writer.is_open()
            
            # Verify content was written
            with open(log_file, 'r') as f:
                content = f.read().strip()
                assert content == '{"test":"data"}'
    
    def test_multiple_entries_same_step(self):
        """Test writing multiple entries for the same step (common use case)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            
            with ExtensibleLogWriter(log_file) as writer:
                # Simulate multiple events in the same step
                step = 42
                writer.write_entry({"s": step, "dt": 0.01, "e": "trade", "d": "sid:1,bid:2"})
                writer.write_entry({"s": step, "dt": 0.02, "e": "mode", "d": "aid:1,om:forage,nm:trade"})
                writer.write_entry({"s": step, "dt": 0.03, "e": "collect", "d": "aid:2,rt:good1"})
            
            # Verify all entries were written
            with open(log_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 3
                
                # Verify each entry has the expected structure
                for line in lines:
                    entry = json.loads(line.strip())
                    assert entry["s"] == step
                    assert "dt" in entry
                    assert "e" in entry
                    assert "d" in entry
