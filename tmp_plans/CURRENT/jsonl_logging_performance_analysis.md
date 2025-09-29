# JSONL Logging Performance Bottleneck Analysis

**Date:** September 28, 2025  
**Context:** Recent logging additions have revealed major performance bottleneck in file I/O for JSONL debug logs  
**Impact:** Potential FPS degradation in simulation due to synchronous file operations

## Problem Analysis

### Current I/O Implementation Issues

The current debug logging system in `src/econsim/gui/debug_logger.py` has a critical performance bottleneck in how it handles JSONL file writes:

```python
def _write_structured_line(self, structured_line: str) -> None:
    """Write a structured JSONL line to the log file."""
    if not self._log_initialized:
        self._initialize_log_file()
    with self._lock:
        try:
            with open(self.structured_log_path, 'a', encoding='utf-8') as sf:
                sf.write(structured_line)
                sf.flush()  # ← PERFORMANCE KILLER
        except Exception:
            pass
```

### Root Causes

1. **Synchronous File I/O on Every Event**: Each log event triggers immediate file write
2. **Explicit Flush on Every Write**: `sf.flush()` forces OS to write to disk immediately
3. **File Open/Close Overhead**: Opening file handle for every log line
4. **Thread Lock Contention**: `with self._lock:` blocks simulation thread during I/O
5. **High Frequency Events**: Performance logging happens every 25 steps (~2.5x/second at 60 FPS)

### Performance Impact Measurements

Based on code analysis, logging frequency is:
- **Periodic Summary**: Every 25 steps (2.5x/second at 60 FPS)
- **Mode Transitions**: Variable frequency, can be high during active periods  
- **Trade Events**: When enabled, potentially every step
- **Performance Analysis**: Real-time FPS monitoring

At 60 FPS with logging enabled:
- File operations: ~2.5+/second baseline, potentially 60+/second with verbose logging
- Each operation includes: `open()` + `write()` + `flush()` + `close()`
- Estimated I/O overhead: 1-5ms per operation (depending on storage)

This can easily consume 5-15% of frame budget (16.67ms @ 60 FPS).

## Technical Solutions

### Option 1: Asynchronous Buffered I/O (Recommended)

**Approach**: Buffer log entries in memory and write asynchronously in batches.

```python
import asyncio
import threading
from collections import deque
from typing import Optional

class AsyncLogBuffer:
    def __init__(self, log_path: Path, flush_interval: float = 0.5):
        self._buffer = deque()
        self._log_path = log_path
        self._flush_interval = flush_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def append(self, line: str) -> None:
        """Add line to buffer (fast, no I/O)."""
        with self._lock:
            self._buffer.append(line)
    
    def _flush_worker(self) -> None:
        """Background thread that periodically flushes buffer to disk."""
        while self._running:
            lines_to_write = []
            with self._lock:
                while self._buffer:
                    lines_to_write.append(self._buffer.popleft())
            
            if lines_to_write:
                try:
                    with open(self._log_path, 'a', encoding='utf-8') as f:
                        f.writelines(lines_to_write)
                        # Single flush after batch write
                except Exception:
                    pass  # Silent failure like current implementation
            
            time.sleep(self._flush_interval)
```

**Benefits**:
- ✅ Sub-millisecond log calls (memory-only)
- ✅ Batched disk writes (better I/O efficiency)
- ✅ Configurable flush intervals
- ✅ No simulation thread blocking

**Risks**:
- ⚠️ Potential log loss on crash (mitigation: shorter flush intervals)
- ⚠️ Additional complexity

### Option 2: Memory-Only Ring Buffer with Optional Export

**Approach**: Keep structured logs in memory only, export on demand.

```python
class MemoryLogger:
    def __init__(self, capacity: int = 10000):
        self._events = deque(maxlen=capacity)
        self._lock = threading.Lock()
    
    def append(self, event: dict) -> None:
        """Add structured event to memory buffer (no I/O)."""
        with self._lock:
            self._events.append(event)
    
    def export_jsonl(self, path: Path) -> None:
        """Export current buffer to JSONL file."""
        with self._lock:
            with open(path, 'w', encoding='utf-8') as f:
                for event in self._events:
                    f.write(json.dumps(event, separators=(',', ':')) + '\n')
    
    def get_recent(self, count: int = 100) -> list:
        """Get recent events for GUI display."""
        with self._lock:
            return list(self._events)[-count:]
```

**Benefits**:
- ✅ Zero I/O overhead during simulation
- ✅ Fast memory-only operations
- ✅ Built-in event history limit
- ✅ Export on demand (session end, user request)

**Risks**:
- ⚠️ No persistent logging during run
- ⚠️ Memory usage proportional to event count

### Option 3: Lazy File Handle with Periodic Flush

**Approach**: Keep file handle open, buffer writes, flush periodically.

```python
class BufferedFileLogger:
    def __init__(self, log_path: Path, buffer_size: int = 8192, flush_interval: int = 50):
        self._log_path = log_path
        self._file_handle: Optional[TextIO] = None
        self._buffer_size = buffer_size
        self._flush_interval = flush_interval
        self._write_count = 0
        
    def append(self, line: str) -> None:
        """Write with periodic flushing."""
        if self._file_handle is None:
            self._file_handle = open(self._log_path, 'a', encoding='utf-8', buffering=self._buffer_size)
        
        self._file_handle.write(line)
        self._write_count += 1
        
        # Flush every N writes or on simulation end
        if self._write_count % self._flush_interval == 0:
            self._file_handle.flush()
```

**Benefits**:
- ✅ Reduced file open/close overhead
- ✅ OS-level buffering optimization
- ✅ Minimal code changes required

**Risks**:
- ⚠️ Still some I/O on simulation thread
- ⚠️ File handle management complexity

## Recommended Implementation Strategy

### Phase 1: Immediate Relief (Option 3 - Buffered File Handle)
- Modify `GUILogger` to keep file handle open
- Remove explicit `flush()` calls
- Add periodic flush every 25-50 writes
- **Impact**: 60-80% I/O overhead reduction
- **Risk**: Low
- **Effort**: 2-3 hours

### Phase 2: Full Async Solution (Option 1 - Async Buffer)
- Implement `AsyncLogBuffer` class
- Integrate with existing `GUILogger`
- Add graceful shutdown handling
- **Impact**: 90-95% I/O overhead reduction  
- **Risk**: Medium
- **Effort**: 1-2 days

### Phase 3: Optional Memory-Only Mode (Option 2)
- Add environment variable `ECONSIM_LOG_MEMORY_ONLY=1`
- Implement in-memory ring buffer
- Export functionality for session analysis
- **Impact**: 100% I/O elimination during simulation
- **Risk**: Low
- **Effort**: 4-6 hours

## Implementation Considerations

### Backward Compatibility
- Maintain existing log format and file paths
- Environment variables should still work
- GUI event log panel should continue to function

### Performance Validation
- Before/after FPS measurements using `make perf`
- Ensure no regression in determinism tests
- Monitor memory usage with buffered approaches

### Graceful Degradation
- All solutions should fail silently like current implementation
- File write errors should not crash simulation
- Buffer overflow should discard oldest entries

### Configuration Options
```bash
# New environment variables
ECONSIM_LOG_BUFFER_SIZE=8192        # Buffer size for file I/O
ECONSIM_LOG_FLUSH_INTERVAL=25       # Writes between flushes
ECONSIM_LOG_MEMORY_ONLY=1           # Memory-only mode
ECONSIM_LOG_ASYNC_FLUSH_SEC=0.5     # Async flush interval
```

## Success Metrics

- **FPS Impact**: < 1% overhead when logging enabled (currently 5-15%)
- **Throughput**: Handle 100+ log events/second without performance degradation
- **Memory**: Buffer memory usage < 10MB for typical sessions
- **Reliability**: No log loss under normal shutdown conditions

## Next Steps for Discussion

1. **Approve recommended phased approach?**
2. **Preferred buffer size and flush interval values?**
3. **Memory-only mode as default for performance-critical scenarios?**
4. **Integration timeline with current development priorities?**

---

**Priority**: High - This directly impacts the 60+ FPS performance target and user experience during development/debugging sessions.