# Debug Logger Refactoring Plan

*Generated on 2025-01-27*

## Overview

This document provides a comprehensive step-by-step plan to refactor the `debug_logger.py` file (8.2K tokens, 1,610 lines) into a modular, maintainable logging system while preserving all existing functionality and maintaining backward compatibility.

## Current State Analysis

### Problems Identified
1. **Monolithic Design**: Single 1,610-line class handling all logging concerns
2. **Complex State Management**: Multiple buffer types with intricate flushing logic
3. **Tight Coupling**: Direct environment variable dependencies throughout
4. **Verbose Documentation**: Excessive docstring repetition and examples
5. **Mixed Responsibilities**: Event building, parsing, formatting, and I/O all in one class

### Key Components to Extract
- Event builders (20+ builder methods)
- Buffer management (trade, transition, bundle buffers)
- Configuration management
- Parsing logic (mode, utility, trade, performance)
- Formatting utilities
- File I/O operations

## Refactoring Strategy

### Phase 1: Extract Core Utilities (Week 1)

#### Step 1.1: Create Formatting Utilities Module
**File**: `src/econsim/gui/logging/formatters.py`

```python
"""Logging formatters for consistent output formatting."""

def format_agent_id(agent_id: int) -> str:
    """Format agent ID with zero-padded format."""
    return f"A{agent_id:03d}"

def format_delta(value: float) -> str:
    """Format delta values with consistent sign notation."""
    if abs(value) < 1e-6:
        value = 0.0
    return f"{value:+.3f}"

def format_simulation_time(start_time: datetime, current_time: datetime) -> str:
    """Format elapsed simulation time."""
    elapsed = (current_time - start_time).total_seconds()
    return f"+{elapsed:.1f}s"
```

#### Step 1.2: Create Configuration Module
**File**: `src/econsim/gui/logging/config.py`

```python
"""Centralized logging configuration management."""

from enum import Enum
from typing import Set, Optional
import os

class LogLevel(Enum):
    CRITICAL = "CRITICAL"
    EVENTS = "EVENTS"
    PERIODIC = "PERIODIC"
    VERBOSE = "VERBOSE"

class LoggingConfig:
    """Centralized logging configuration."""
    
    def __init__(self):
        self.level = self._get_log_level()
        self.categories = self._get_enabled_categories()
        self.format = self._get_output_format()
        self.bundle_trades = os.environ.get("ECONSIM_LOG_BUNDLE_TRADES") == "1"
        self.explanations = os.environ.get("ECONSIM_LOG_EXPLANATIONS") == "1"
    
    def _get_log_level(self) -> LogLevel:
        """Get current log level from environment."""
        level_str = os.environ.get("ECONSIM_LOG_LEVEL", "VERBOSE").upper()
        try:
            return LogLevel(level_str)
        except ValueError:
            return LogLevel.VERBOSE
    
    def should_log_category(self, category: str) -> bool:
        """Check if category should be logged."""
        return True  # Simplified for now
    
    def should_log_performance(self, step: int, steps_per_sec: float) -> bool:
        """Check if performance should be logged."""
        if self.level == LogLevel.VERBOSE:
            return True
        if self.level == LogLevel.PERIODIC:
            return step % 25 == 0 or self._significant_performance_change(steps_per_sec)
        return False
```

#### Step 1.3: Create Event Builder Base Classes
**File**: `src/econsim/gui/logging/event_builders.py`

```python
"""Event builders for structured logging."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

class EventBuilder(ABC):
    """Base class for structured event builders."""
    
    @abstractmethod
    def build(self, **kwargs) -> Tuple[str, Dict[str, Any], str]:
        """Build event data.
        
        Returns:
            Tuple of (compact_line, structured_payload, category)
        """

class TradeEventBuilder(EventBuilder):
    """Handles trade-related event construction."""
    
    def build_trade_intent_funnel(self, drafted: int, pruned_micro: int, 
                                 pruned_nonpositive: int, executed: int, 
                                 max_delta_u: float) -> Tuple[str, Dict[str, Any], str]:
        """Build trade intent funnel event."""
        category = "TRADE"
        compact = (f"TI: drafted={drafted} pruned_micro={pruned_micro} "
                  f"pruned_nonpositive={pruned_nonpositive} executed={executed} "
                  f"maxΔU={max_delta_u:.3f}")
        payload = {
            "event": "trade_intent_funnel",
            "drafted": drafted,
            "pruned_micro": pruned_micro,
            "pruned_nonpositive": pruned_nonpositive,
            "executed": executed,
            "max_delta_u": round(max_delta_u, 6),
        }
        return compact, payload, category

class PerformanceEventBuilder(EventBuilder):
    """Handles performance event construction."""
    
    def build_periodic_summary(self, steps_per_sec: float, frame_ms: float,
                              agents: int, resources: int, 
                              phase: Optional[int]) -> Tuple[str, Dict[str, Any], str]:
        """Build periodic summary event."""
        category = "SIMULATION"
        phase_part = f" Ph{phase}" if phase is not None else ""
        compact = f"P: {steps_per_sec:.1f}s/s {frame_ms:.1f}ms A{agents} R{resources}{phase_part}"
        payload = {
            "event": "periodic_summary",
            "steps_per_sec": round(steps_per_sec, 1),
            "frame_ms": round(frame_ms, 1),
            "agents": agents,
            "resources": resources
        }
        if phase is not None:
            payload["phase"] = phase
        return compact, payload, category

class AgentEventBuilder(EventBuilder):
    """Handles agent-related event construction."""
    
    def build_mode_transition(self, agent_id: int, old_mode: str, new_mode: str,
                            reason: str = "", carrying: int = 0, 
                            target: Optional[Tuple[int, int]] = None) -> Tuple[str, Dict[str, Any], str]:
        """Build agent mode transition event."""
        category = "MODE"
        context_parts = []
        if reason:
            context_parts.append(f"({reason})")
        if carrying > 0:
            context_parts.append(f"carrying: {carrying}")
        if target:
            context_parts.append(f"target: ({target[0]},{target[1]})")
        
        context = ", ".join(context_parts)
        compact = f"A{agent_id:03d}: {old_mode}→{new_mode} {context}"
        
        payload = {
            "event": "mode_transition",
            "agent": agent_id,
            "old_mode": old_mode,
            "new_mode": new_mode,
        }
        if reason:
            payload["reason"] = reason
        if carrying > 0:
            payload["carrying"] = carrying
        if target:
            payload["target"] = {"x": target[0], "y": target[1]}
            
        return compact, payload, category
```

### Phase 2: Extract Buffer Management (Week 1-2)

#### Step 2.1: Create Buffer Base Classes
**File**: `src/econsim/gui/logging/buffers.py`

```python
"""Buffer management for different log message types."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

class Buffer(ABC):
    """Base class for log message buffers."""
    
    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self.buffer: Dict[int, List[str]] = {}
        self.last_step = -1
    
    @abstractmethod
    def add_message(self, message: str, step: Optional[int]) -> None:
        """Add message to buffer."""
        pass
    
    @abstractmethod
    def flush(self) -> List[Dict[str, Any]]:
        """Flush buffer and return structured events."""
        pass
    
    def should_flush(self, step: int) -> bool:
        """Check if buffer should be flushed."""
        return (step != self.last_step and self.last_step >= 0) or len(self.buffer) > self.capacity

class TradeBuffer(Buffer):
    """Handles trade message buffering."""
    
    def add_message(self, message: str, step: Optional[int]) -> None:
        """Add trade message to buffer."""
        if step is None:
            step = -1
        if step not in self.buffer:
            self.buffer[step] = []
        self.buffer[step].append(message)
        self.last_step = step
    
    def flush(self) -> List[Dict[str, Any]]:
        """Flush trade buffer."""
        events = []
        for step, trades in self.buffer.items():
            for trade in trades:
                events.append(self._parse_trade(trade, step))
        self.buffer.clear()
        return events
    
    def _parse_trade(self, message: str, step: int) -> Dict[str, Any]:
        """Parse trade message into structured data."""
        # Implementation details...
        return {"event": "trade", "raw": message, "step": step}

class TransitionBuffer(Buffer):
    """Handles agent transition buffering."""
    
    def __init__(self, capacity: int = 50):
        super().__init__(capacity)
        self.dedupe: Dict[Tuple[str, str, str], int] = {}
        self.last_flush_time = datetime.now()
    
    def add_message(self, message: str, step: Optional[int]) -> None:
        """Add transition message to buffer."""
        # Implementation with deduplication logic...
        pass
    
    def flush(self) -> List[Dict[str, Any]]:
        """Flush transition buffer with batching."""
        # Implementation with batching logic...
        pass
```

#### Step 2.2: Create Buffer Manager
**File**: `src/econsim/gui/logging/buffer_manager.py`

```python
"""Centralized buffer management."""

from typing import Dict, List, Any, Optional
from .buffers import Buffer, TradeBuffer, TransitionBuffer

class BufferManager:
    """Manages different types of log buffers."""
    
    def __init__(self):
        self.buffers: Dict[str, Buffer] = {
            'trade': TradeBuffer(),
            'transition': TransitionBuffer(),
        }
    
    def add_message(self, category: str, message: str, step: Optional[int]) -> None:
        """Add message to appropriate buffer."""
        if category == "TRADE":
            self.buffers['trade'].add_message(message, step)
        elif category in ("AGENT_MODE", "MODE"):
            self.buffers['transition'].add_message(message, step)
    
    def flush_all(self) -> List[Dict[str, Any]]:
        """Flush all buffers."""
        all_events = []
        for buffer in self.buffers.values():
            all_events.extend(buffer.flush())
        return all_events
    
    def flush_if_needed(self, step: int) -> List[Dict[str, Any]]:
        """Flush buffers if conditions are met."""
        events = []
        for buffer in self.buffers.values():
            if buffer.should_flush(step):
                events.extend(buffer.flush())
        return events
```

### Phase 3: Extract Parsing Logic (Week 2)

#### Step 3.1: Create Message Parsers
**File**: `src/econsim/gui/logging/parsers.py`

```python
"""Message parsing for structured logging."""

import re
from typing import Dict, Any, Optional

class MessageParser:
    """Base class for message parsing."""
    
    @staticmethod
    def parse_mode_transition(message: str) -> Dict[str, Any]:
        """Parse agent mode transition message."""
        result = {"event": "mode_transition"}
        
        # Support multiple formats
        patterns = [
            r'Agent_(\d+) switched from (\w+) to (\w+)(.*)$',
            r'Agent (\d+) mode: (\w+) -> (\w+)(.*)$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                agent_id, old_mode, new_mode, context = match.groups()
                result.update({
                    "agent": int(agent_id),
                    "old_mode": old_mode,
                    "new_mode": new_mode,
                })
                
                # Extract structured fields from context
                if context:
                    context = context.strip()
                    
                    # Extract reason
                    reason_match = re.search(r'\(([^)]+)\)', context)
                    if reason_match:
                        result["reason"] = reason_match.group(1)
                    
                    # Extract carrying count
                    carry_match = re.search(r'carrying: (\d+)', context)
                    if carry_match:
                        result["carrying"] = int(carry_match.group(1))
                    
                    # Extract target coordinates
                    target_match = re.search(r'target: \((\d+), (\d+)\)', context)
                    if target_match:
                        result["target"] = {
                            "x": int(target_match.group(1)), 
                            "y": int(target_match.group(2))
                        }
                break
        else:
            result["raw"] = message
        
        return result
    
    @staticmethod
    def parse_utility(message: str) -> Dict[str, Any]:
        """Parse utility change message."""
        pattern = r'Agent_(\d+) utility: ([0-9.]+) → ([0-9.]+) \(Δ([+\-][0-9.]+)\)(.*)'
        match = re.search(pattern, message)
        
        data = {"event": "utility_change", "raw": message}
        if match:
            agent_id, old_u, new_u, delta, tail = match.groups()
            data.update({
                "agent": int(agent_id),
                "old": float(old_u),
                "new": float(new_u),
                "delta": float(delta),
            })
            
            # Extract reason if present
            if tail:
                reason_match = re.search(r'\(([^(]*?)\)', tail)
                if reason_match:
                    data["reason"] = reason_match.group(1).strip()
        
        return data
    
    @staticmethod
    def parse_trade(message: str) -> Dict[str, Any]:
        """Parse trade message."""
        data = {"event": "trade", "raw": message}
        
        # New style: Trade: A001↔A009 bread→fish (Δ+0.10, Δ+0.08)
        new_pattern = r'Trade: A(\d+)↔A(\d+) (\w+)→(\w+) \(Δ([+\-][0-9.]+), Δ([+\-][0-9.]+)\)'
        new_match = re.search(new_pattern, message)
        if new_match:
            a1, a2, give, receive, d1, d2 = new_match.groups()
            data.update({
                "agent1": int(a1),
                "agent2": int(a2),
                "give": give,
                "receive": receive,
                "delta_agent1": float(d1),
                "delta_agent2": float(d2)
            })
            return data
        
        # Old style: Agent_001 gives bread to Agent_009; receives fish ... utility: +0.123
        old_pattern = r'Agent_(\d+) gives (\w+) to Agent_(\d+); receives (\w+).*?utility: ([+\-]?[0-9.]+)'
        old_match = re.search(old_pattern, message)
        if old_match:
            a1, give, a2, receive, combined = old_match.groups()
            data.update({
                "agent1": int(a1),
                "agent2": int(a2),
                "give": give,
                "receive": receive,
                "combined_delta": float(combined)
            })
        
        return data
```

### Phase 4: Create File I/O Module (Week 2)

#### Step 4.1: Create Log File Manager
**File**: `src/econsim/gui/logging/file_manager.py`

```python
"""File I/O management for logging."""

import json
import atexit
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import threading

class LogFileManager:
    """Manages log file creation and writing."""
    
    def __init__(self, logs_dir: Path):
        self.logs_dir = logs_dir
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._initialized = False
        self._simulation_start_time: Optional[datetime] = None
        self._structured_buffer: List[str] = []
        self._atexit_registered = False
    
    def initialize_log_file(self) -> None:
        """Initialize structured log file when simulation starts."""
        if self._initialized:
            return
        
        now = datetime.now()
        self._simulation_start_time = now
        
        # Create structured log file
        timestamp = now.strftime("%Y-%m-%d %H-%M-%S")
        structured_dir = self.logs_dir / "structured"
        structured_dir.mkdir(parents=True, exist_ok=True)
        self.structured_log_path = structured_dir / f"{timestamp} GUI.jsonl"
        
        # Register cleanup
        if not self._atexit_registered:
            atexit.register(self._flush_on_exit)
            self._atexit_registered = True
        
        # Write metadata
        meta = {
            "schema": 1,
            "session_started": now.isoformat(timespec='seconds'),
            "log_level": "VERBOSE",
            "selected_format": "STRUCTURED_ONLY",
        }
        self._write_structured_line(json.dumps(meta, separators=(",", ":")) + "\n")
        self._initialized = True
    
    def write_structured_line(self, line: str) -> None:
        """Write structured log line to buffer."""
        if not self._initialized:
            self.initialize_log_file()
        
        with self._lock:
            self._structured_buffer.append(line)
    
    def _write_structured_line(self, line: str) -> None:
        """Internal method to add line to buffer."""
        self._structured_buffer.append(line)
    
    def flush_to_disk(self) -> None:
        """Flush buffered lines to disk."""
        if not self._initialized or not self._structured_buffer:
            return
        
        with self._lock:
            if not self._structured_buffer:
                return
            
            try:
                with open(self.structured_log_path, 'w', encoding='utf-8') as f:
                    f.writelines(self._structured_buffer)
            except Exception:
                pass  # Don't break simulation if logging fails
    
    def _flush_on_exit(self) -> None:
        """Flush buffer on interpreter exit."""
        try:
            self.flush_to_disk()
        except Exception:
            pass
    
    def get_log_path(self) -> Optional[Path]:
        """Get path to current log file."""
        if not self._initialized:
            return None
        return self.structured_log_path
```

### Phase 5: Refactor Main Logger (Week 3)

#### Step 5.1: Create Simplified Main Logger
**File**: `src/econsim/gui/logging/logger.py`

```python
"""Simplified main logger focusing on core responsibilities."""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import threading

from .config import LoggingConfig
from .buffer_manager import BufferManager
from .event_builders import TradeEventBuilder, PerformanceEventBuilder, AgentEventBuilder
from .parsers import MessageParser
from .file_manager import LogFileManager
from .formatters import format_agent_id, format_delta

class GUILogger:
    """Simplified main logger focusing on core responsibilities."""
    
    _instance: Optional["GUILogger"] = None
    _lock = threading.Lock()
    
    def __init__(self):
        if GUILogger._instance is not None:
            raise RuntimeError("GUILogger is a singleton. Use get_instance() instead.")
        
        self.config = LoggingConfig()
        self.buffer_manager = BufferManager()
        self.file_manager = LogFileManager(Path(__file__).parent.parent.parent.parent / "gui_logs")
        
        # Event builders
        self.trade_builder = TradeEventBuilder()
        self.performance_builder = PerformanceEventBuilder()
        self.agent_builder = AgentEventBuilder()
        
        # Parser
        self.parser = MessageParser()
        
        # Performance tracking
        self._last_perf_log_step = 0
        self._last_steps_per_sec = 0.0
    
    @classmethod
    def get_instance(cls) -> "GUILogger":
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def log(self, category: str, message: str, step: Optional[int] = None) -> None:
        """Log a debug message with timestamp and category."""
        if not self.config.should_log_category(category):
            return
        
        # Handle special buffering cases
        if category == "TRADE":
            self.buffer_manager.add_message(category, message, step)
            return
        
        if category in ("AGENT_MODE", "MODE"):
            self.buffer_manager.add_message(category, message, step)
            return
        
        # Direct structured logging for other categories
        payload = self._build_structured_payload(category, message)
        structured = self._emit_structured(category, step, payload)
        self.file_manager.write_structured_line(structured)
    
    def emit_built_event(self, step: Optional[int], builder_result: tuple) -> None:
        """Emit a pre-built event."""
        try:
            _, payload, category = builder_result
        except Exception:
            return
        
        if not self.config.should_log_category(category):
            return
        
        structured_line = self._emit_structured(category, step, payload)
        self.file_manager.write_structured_line(structured_line)
    
    def _build_structured_payload(self, category: str, message: str) -> Dict[str, Any]:
        """Build structured payload for a message."""
        if category in ("MODE", "AGENT_MODE"):
            return self.parser.parse_mode_transition(message)
        if category == "UTILITY":
            return self.parser.parse_utility(message)
        if category == "TRADE":
            return self.parser.parse_trade(message)
        return {"event": category.lower(), "raw": message}
    
    def _emit_structured(self, category: str, step: Optional[int], payload: Dict[str, Any]) -> str:
        """Build a structured JSON line for a logging event."""
        normalized_step = None if step == -1 else step
        
        data = {
            "ts_rel": round(self._relative_seconds(), 3),
            "category": category,
            "step": normalized_step,
        }
        data.update(payload)
        return json.dumps(data, separators=(",", ":")) + "\n"
    
    def _relative_seconds(self) -> float:
        """Return elapsed wall clock time since simulation start."""
        if self.file_manager._simulation_start_time is None:
            return 0.0
        return (datetime.now() - self.file_manager._simulation_start_time).total_seconds()
    
    def finalize_session(self) -> None:
        """Finalize logging session."""
        self.buffer_manager.flush_all()
        self.file_manager.flush_to_disk()
        self._finalized = True
    
    def is_finalized(self) -> bool:
        """Check if logger is finalized."""
        return getattr(self, '_finalized', False)
```

### Phase 6: Create Convenience Functions (Week 3)

#### Step 6.1: Update Convenience Functions
**File**: `src/econsim/gui/logging/convenience.py`

```python
"""Convenience functions for global access."""

import os
from typing import Optional
from .logger import GUILogger
from .formatters import format_agent_id, format_delta

def get_gui_logger() -> GUILogger:
    """Get the singleton GUI logger instance."""
    return GUILogger.get_instance()

def log_agent_mode(agent_id: int, old_mode: str, new_mode: str, 
                   reason: str = "", step: Optional[int] = None) -> None:
    """Log agent mode transition."""
    if os.environ.get("ECONSIM_DEBUG_AGENT_MODES") == "1":
        get_gui_logger().log("AGENT_MODE", 
                           f"Agent {agent_id} mode: {old_mode} -> {new_mode} ({reason})", 
                           step)

def log_trade(message: str, step: Optional[int] = None) -> None:
    """Log trade debug information."""
    if os.environ.get("ECONSIM_DEBUG_TRADES") == "1":
        get_gui_logger().log("TRADE", message, step)

def log_simulation(message: str, step: Optional[int] = None) -> None:
    """Log simulation debug information."""
    if os.environ.get("ECONSIM_DEBUG_SIMULATION") == "1":
        get_gui_logger().log("SIMULATION", message, step)

def log_utility_change(agent_id: int, old_utility: float, new_utility: float, 
                       reason: str = "", step: Optional[int] = None, 
                       good_type: str = "") -> None:
    """Log agent utility changes."""
    if os.environ.get("ECONSIM_DEBUG_ECONOMICS") == "1":
        delta = new_utility - old_utility
        reason_str = f" ({reason})" if reason else ""
        message = f"Agent_{agent_id:03d} utility: {old_utility:.1f} → {new_utility:.1f} (Δ{format_delta(delta)}){reason_str}"
        get_gui_logger().log("UTILITY", message, step)

def log_performance(message: str, step: Optional[int] = None) -> None:
    """Log performance metrics."""
    if os.environ.get("ECONSIM_DEBUG_PERFORMANCE") == "1":
        get_gui_logger().log("PERF", message, step)

def finalize_log_session() -> None:
    """Finalize the current logging session."""
    get_gui_logger().finalize_session()
```

### Phase 7: Update Main Debug Logger (Week 3)

#### Step 7.1: Create New Main File
**File**: `src/econsim/gui/debug_logger.py` (Refactored)

```python
"""Centralized GUI debug logging system for VMT EconSim.

Provides unified logging to timestamped files in gui_logs/ directory.
All debug output from simulation components should use this logging system
instead of direct print statements for better organization and GUI integration.
"""

# Import all functionality from new modules
from .logging.logger import GUILogger
from .logging.convenience import (
    get_gui_logger,
    log_agent_mode,
    log_trade,
    log_simulation,
    log_utility_change,
    log_performance,
    finalize_log_session
)
from .logging.formatters import format_agent_id, format_delta

# Maintain backward compatibility
__all__ = [
    "GUILogger",
    "get_gui_logger", 
    "log_agent_mode",
    "log_trade", 
    "log_simulation",
    "log_utility_change",
    "log_performance",
    "finalize_log_session",
    "format_agent_id",
    "format_delta"
]
```

### Phase 8: Testing and Validation (Week 4)

#### Step 8.1: Create Unit Tests
**File**: `tests/unit/gui/logging/test_logger.py`

```python
"""Unit tests for refactored logging system."""

import pytest
from unittest.mock import Mock, patch
from econsim.gui.logging.logger import GUILogger
from econsim.gui.logging.config import LoggingConfig
from econsim.gui.logging.buffers import TradeBuffer, TransitionBuffer

class TestGUILogger:
    """Test cases for GUILogger."""
    
    def test_singleton_pattern(self):
        """Test that GUILogger is a singleton."""
        logger1 = GUILogger.get_instance()
        logger2 = GUILogger.get_instance()
        assert logger1 is logger2
    
    def test_log_message(self):
        """Test basic message logging."""
        logger = GUILogger.get_instance()
        with patch.object(logger.file_manager, 'write_structured_line') as mock_write:
            logger.log("TEST", "test message", 1)
            mock_write.assert_called_once()
    
    def test_trade_buffering(self):
        """Test trade message buffering."""
        logger = GUILogger.get_instance()
        logger.log("TRADE", "test trade", 1)
        # Verify message was added to trade buffer
        assert len(logger.buffer_manager.buffers['trade'].buffer) > 0

class TestEventBuilders:
    """Test cases for event builders."""
    
    def test_trade_event_builder(self):
        """Test trade event building."""
        from econsim.gui.logging.event_builders import TradeEventBuilder
        builder = TradeEventBuilder()
        compact, payload, category = builder.build_trade_intent_funnel(
            drafted=10, pruned_micro=2, pruned_nonpositive=3, 
            executed=1, max_delta_u=0.5
        )
        assert category == "TRADE"
        assert payload["drafted"] == 10
        assert payload["executed"] == 1
```

#### Step 8.2: Create Integration Tests
**File**: `tests/integration/gui/logging/test_logging_integration.py`

```python
"""Integration tests for logging system."""

import pytest
import tempfile
from pathlib import Path
from econsim.gui.logging.logger import GUILogger
from econsim.gui.logging.convenience import log_agent_mode, log_trade

class TestLoggingIntegration:
    """Integration tests for logging system."""
    
    def test_end_to_end_logging(self):
        """Test complete logging workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Configure logger with temp directory
            logger = GUILogger.get_instance()
            logger.file_manager.logs_dir = Path(temp_dir)
            
            # Log various message types
            log_agent_mode(1, "IDLE", "FORAGE", "test reason", 1)
            log_trade("test trade message", 1)
            
            # Finalize and check output
            logger.finalize_session()
            assert logger.file_manager.structured_log_path.exists()
```

### Phase 9: Documentation Updates (Week 4)

#### Step 9.1: Create Architecture Documentation
**File**: `docs/architecture/logging_system.md`

```markdown
# Logging System Architecture

## Overview
The VMT logging system provides structured, timestamped logging for simulation events.

## Components

### Core Modules
- `logger.py`: Main logger class with simplified interface
- `config.py`: Centralized configuration management
- `formatters.py`: Utility functions for consistent formatting
- `file_manager.py`: File I/O operations

### Event Processing
- `event_builders.py`: Structured event construction
- `parsers.py`: Message parsing and extraction
- `buffers.py`: Message buffering and batching

### Convenience
- `convenience.py`: Global access functions
- `debug_logger.py`: Main entry point with backward compatibility

## Usage

### Basic Logging
```python
from econsim.gui.debug_logger import get_gui_logger

logger = get_gui_logger()
logger.log("CATEGORY", "message", step=1)
```

### Convenience Functions
```python
from econsim.gui.debug_logger import log_agent_mode, log_trade

log_agent_mode(1, "IDLE", "FORAGE", "reason", step=1)
log_trade("trade message", step=1)
```

## Configuration
Environment variables control logging behavior:
- `ECONSIM_LOG_LEVEL`: Log level (VERBOSE, PERIODIC, EVENTS, CRITICAL)
- `ECONSIM_DEBUG_*`: Enable specific debug categories
```

#### Step 9.2: Update Main README
**File**: `README.md` (Update logging section)

```markdown
## Logging System

The VMT logging system provides structured, timestamped logging for simulation events. See [docs/architecture/logging_system.md](docs/architecture/logging_system.md) for detailed information.

### Quick Start
```python
from econsim.gui.debug_logger import log_agent_mode, log_trade

# Log agent mode changes
log_agent_mode(agent_id=1, old_mode="IDLE", new_mode="FORAGE", reason="found resource")

# Log trade events  
log_trade("Agent 1 trades with Agent 2", step=100)
```

### Configuration
Set environment variables to control logging:
```bash
export ECONSIM_LOG_LEVEL=VERBOSE
export ECONSIM_DEBUG_AGENT_MODES=1
export ECONSIM_DEBUG_TRADES=1
```
```

## Implementation Timeline

### Week 1: Core Utilities
- [ ] Create formatting utilities module
- [ ] Create configuration management
- [ ] Create event builder base classes
- [ ] Update imports and dependencies

### Week 2: Buffer Management & Parsing
- [ ] Create buffer management system
- [ ] Create message parsers
- [ ] Create file I/O manager
- [ ] Test individual components

### Week 3: Main Logger Refactoring
- [ ] Create simplified main logger
- [ ] Update convenience functions
- [ ] Refactor main debug_logger.py
- [ ] Integration testing

### Week 4: Testing & Documentation
- [ ] Create comprehensive unit tests
- [ ] Create integration tests
- [ ] Update architecture documentation
- [ ] Performance validation
- [ ] Backward compatibility verification

## Success Criteria

### Code Quality Metrics
- [ ] Reduce main debug_logger.py from 1,610 lines to <200 lines
- [ ] Create 6+ focused modules with single responsibilities
- [ ] Achieve 90%+ test coverage for new modules
- [ ] Maintain all existing functionality

### Performance Metrics
- [ ] No performance regression in logging overhead
- [ ] Maintain <2% logging overhead as specified in copilot instructions
- [ ] Preserve deterministic behavior
- [ ] Maintain FPS targets

### Developer Experience
- [ ] Clear separation of concerns
- [ ] Comprehensive documentation
- [ ] Easy to extend and modify
- [ ] Backward compatibility maintained

## Risk Mitigation

### Backward Compatibility
- Maintain all existing public APIs
- Preserve all convenience functions
- Keep same file structure for imports
- No breaking changes to existing code

### Performance Impact
- Benchmark before and after refactoring
- Maintain deterministic behavior
- Preserve existing performance characteristics
- Monitor logging overhead

### Testing Strategy
- Comprehensive unit tests for all new modules
- Integration tests for complete workflows
- Performance regression testing
- Determinism validation with existing tests

## Conclusion

This refactoring plan transforms the monolithic debug logger into a modular, maintainable system while preserving all existing functionality. The phased approach minimizes risk and ensures each step can be validated before proceeding to the next.

The result will be a cleaner, more maintainable codebase that's easier to understand, test, and extend while maintaining the performance and determinism characteristics required by the VMT project.
