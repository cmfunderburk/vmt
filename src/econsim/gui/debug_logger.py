"""Centralized GUI debug logging system for VMT EconSim.

Provides unified logging to timestamped files in gui_logs/ directory.
All debug output from simulation components should use this logging system
instead of direct print statements for better organization and GUI integration.

Environment Variables:
    (Deprecated) All logging is now always enabled in structured format.
    No environment variables needed for basic logging functionality.

Simplified Logging:
    All events are logged by default in structured JSON format.
    No category filtering or level restrictions.
"""

import os
import json
import atexit
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict, List, Sequence, Iterable
import threading
from enum import Enum

# Import enhanced configuration system (safely)
try:  # type: ignore
    from .log_config import LogLevel, get_log_config  # type: ignore  # noqa: F401
    _get_log_config_ref = get_log_config  # touch to avoid unused import warnings
    _has_log_config = True
except Exception:  # pragma: no cover
    _has_log_config = False
    class LogLevel(Enum):  # fallback
        CRITICAL = "CRITICAL"
        EVENTS = "EVENTS"
        PERIODIC = "PERIODIC"
        VERBOSE = "VERBOSE"

# Import educational context functions
try:  # type: ignore
    from .log_utils import (
        explain_utility_change,
        should_add_educational_context,
    )
    _has_educational_logging = True
except Exception:  # pragma: no cover
    _has_educational_logging = False
    # Provide no-op fallbacks to satisfy type checkers (match real signatures)
    def explain_utility_change(old_utility: float, new_utility: float, reason: str = "", good_type: str = "") -> str:  # type: ignore
        return ""
    def should_add_educational_context() -> bool:  # type: ignore
        return False

try:  # type: ignore
    from .log_config import get_log_manager as _get_log_manager  # noqa: F401
    _ = _get_log_manager  # touch to avoid unused import warnings
    _has_enhanced_config = True
except Exception:  # pragma: no cover
    _has_enhanced_config = False


def format_agent_id(agent_id: int) -> str:
    """Format agent ID with consistent zero-padded format.
    
    Args:
        agent_id: Integer agent identifier
        
    Returns:
        Formatted agent string like "A000", "A001", "A002", etc.
        
    Examples:
        >>> format_agent_id(1)
        'A001'
        >>> format_agent_id(42)
        'A042'
        >>> format_agent_id(123)
        'A123'
    """
    return f"A{agent_id:03d}"





def format_delta(value: float) -> str:
    """Format delta values with consistent sign notation and near-zero handling.
    
    Args:
        value: Numeric delta value (utility change, etc.)
        
    Returns:
        Formatted delta string with consistent sign notation
        
    Behavior:
        - Eliminates `+-` artifacts by normalizing the value first
        - Rounds very small values (< 1e-6) to exactly 0.0 to avoid noise
        - Preserves small but meaningful changes (≥ 0.001) for educational clarity
        - Uses 3 decimal places to capture micro-utility changes in trading
        - Uses consistent `+X.XXX` / `-X.XXX` formatting
        
    Examples:
        >>> format_delta(1.234)
        '+1.234'
        >>> format_delta(-0.456)
        '-0.456'
        >>> format_delta(0.0000001)  # Very small rounds to zero
        '+0.000'
        >>> format_delta(0.001)  # Small but meaningful preserved
        '+0.001'
        >>> format_delta(0.0)
        '+0.000'
    """
    # Handle very small values by rounding to zero (avoid floating point noise)
    if abs(value) < 1e-6:
        value = 0.0
    
    # Format with consistent sign notation (3 decimal places for utility precision)
    return f"{value:+.3f}"





class GUILogger:
    """Thread-safe centralized debug logger for VMT EconSim simulation components.
    
    Singleton logger that provides structured JSON logging with event aggregation,
    behavioral tracking, and performance monitoring. Supports multiple logging
    phases including real-time event emission and step-based batch summarization.
    
    Architecture:
        - Singleton pattern with thread-safe access via threading.Lock
        - Buffered writes with automatic flushing and emergency exit handling
        - Multi-dimensional event aggregation (PAIRING, TRADE, BEHAVIOR)
        - Correlation tracking for bilateral exchange sequences (Phase 3.1)
        - Performance spike detection and logging with configurable thresholds
    
    State Management:
        The logger maintains several concurrent state machines:
        1. Pairing Aggregation: ACCUMULATE (per-search) → FLUSH (per-step) → RESET
        2. Behavior Tracking: COLLECT (100-step window) → ANALYZE → EMIT → RESET  
        3. Trade Buffering: BUFFER (same-step trades) → AGGREGATE → EMIT
        4. Session Lifecycle: UNINITIALIZED → ACTIVE → FINALIZED
    
    Threading:
        Thread-safe via threading.Lock for concurrent simulation access.
        All public methods are safe for multi-threaded environments.
        Buffer management assumes single simulation thread.
    
    Lifecycle:
        1. Lazy initialization on first access via get_instance()
        2. Log file creation deferred until first simulation step
        3. Automatic buffer flushing on interpreter exit via atexit handler
        4. Explicit finalization via finalize_session() to prevent cleanup noise
    
    Performance:
        - O(1) event emission for most categories
        - O(n log n) behavioral analysis due to high-activity agent sorting
        - Automatic buffer size limits prevent memory accumulation
        - Graceful degradation under high event load
    
    Usage:
        logger = GUILogger.get_instance()
        logger.log("TRADE", "Agent trade executed", step=42)
        logger.emit_built_event(step, builder_result)
        
    File Output:
        - Structured JSONL format in gui_logs/structured/
        - Timestamped filenames: "YYYY-MM-DD HH-MM-SS GUI.jsonl"
        - Append-only writes with automatic flushing
        - Compact JSON serialization for efficient storage
    """
    
    _instance: Optional["GUILogger"] = None
    _lock = threading.Lock()
    
    def __init__(self) -> None:
        if GUILogger._instance is not None:
            raise RuntimeError("GUILogger is a singleton. Use get_instance() instead.")
        
        # PHASE 3.3: DEPRECATION WARNING - GUILogger is being migrated to observer pattern
        import warnings
        warnings.warn(
            "GUILogger is deprecated and will be removed in a future version. "
            "Use FileObserver and EducationalObserver from the observer pattern instead. "
            "See migration guide for details.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Initialize observer system internally for backward compatibility
        try:
            from ..observability.legacy_adapter import create_legacy_adapter
            self._legacy_adapter = create_legacy_adapter(enable_warnings=False)  # Disable nested warnings
            self._observer_system_enabled = True
        except Exception as e:
            # Graceful fallback if observer system isn't available
            self._legacy_adapter = None
            self._observer_system_enabled = False
            warnings.warn(f"Observer system unavailable, using legacy implementation: {e}", UserWarning)
        
        # SIMPLIFIED: Always use VERBOSE level and structured format
        self.log_level = LogLevel.VERBOSE
            
        # Performance tracking for conditional logging
        self._last_perf_log_step = 0
        self._last_steps_per_sec = 0.0
        
        # Trade aggregation buffer for grouping trades by step
        self._trade_buffer: dict[int, list[str]] = {}
        self._last_trade_step = -1
        
        # Agent mode transition batching to prevent spam
        self._agent_transition_buffer: dict[int, list[tuple[str, str, str, str]]] = {}  # step -> [(agent_id, old, new, context)]
        self._last_transition_step = -1
        self._transition_dedupe: dict[tuple[str, str, str], int] = {}  # (agent_id, old, new) -> count
        self._last_transition_flush_time = datetime.now()
        
        # Trade+Utility bundling buffers (Phase 3.1)
        self._trade_bundle_buffer: dict[int, dict[str, list[str]]] = {}  # step -> {trades: [], utilities: []}
        self._last_bundle_step = -1
        
        # PAIRING aggregation system for volume reduction
        self._pairing_accumulator: dict[str, Any] = {}  # Current step's PAIRING data
        self._pairing_current_step = -1
        self._pairing_stats_cache: dict[str, Any] = {}  # For anomaly detection
        
        # Phase 3.1: Correlation ID and Causal Chain tracking
        self._correlation_counter = 0
        self._active_chains: Dict[str, Dict[str, Any]] = {}  # correlation_id -> chain_data
        self._agent_to_correlation: Dict[tuple[int, int], str] = {}  # (agent1, agent2) -> correlation_id
        
        # Phase 3.2: Multi-Dimensional Agent Behavior Aggregation
        self._behavior_window_size = 100  # Steps to aggregate over
        self._behavior_current_step = -1
        self._agent_behavior_data: Dict[int, Dict[str, Any]] = {}  # agent_id -> behavioral metrics
        self._behavior_flush_interval = 100  # Flush every N steps
        self._last_behavior_flush = -1
        
        # Phase 3.4: Intra-Step Event Clustering
        self._clustering_current_step = -1
        self._clustering_buffer: Dict[str, List[Dict[str, Any]]] = {}  # category -> [events]
        self._successful_pairings_buffer: List[Dict[str, Any]] = []  # Preserve individual successful pairings
        
        # Always use project-local logs directory
        # Logs stay in the project for development convenience and are excluded via .gitignore
        self.logs_dir = Path(__file__).parent.parent.parent.parent / "gui_logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Defer log file creation until simulation actually starts
        self._simulation_start_time: Optional[datetime] = None  # Set when first simulation step begins
        self.log_filename: Optional[str] = None
        self.log_path: Optional[Path] = None
        self._log_initialized = False
        self._step = None  # Initialize step variable for future use
        # Testing aide: recent structured payload ring (not part of determinism state)
        self._structured_ring: list[dict[str, Any]] = []  # type: ignore[attr-defined]
        self._structured_ring_capacity = 200  # type: ignore[attr-defined]
        self._structured_buffer: list[str] = []
        self._structured_buffer_flushed = False
        self._atexit_registered = False
    
    @classmethod
    def get_instance(cls) -> "GUILogger":
        """Get singleton instance of GUILogger."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # Backward compatibility: legacy call sites referenced GUILogger.inst()
    # Provide a thin alias so older scheduler / respawn modules keep working.
    @classmethod
    def inst(cls) -> "GUILogger":  # pragma: no cover - trivial alias
        return cls.get_instance()

    # Some very old code may have treated 'inst' as an attribute; expose a
    # descriptor-style attribute for defensive compatibility (harmless if unused).
    inst_ref = property(lambda cls: GUILogger.get_instance())  # type: ignore
    

    def _initialize_log_file(self) -> None:
        """Initialize structured log file when simulation first starts."""
        if self._log_initialized:
            return
            
        # Set simulation start time to now (when first simulation step begins)
        now = datetime.now()
        self._simulation_start_time = now
        
        # Generate timestamped filename for structured log only
        timestamp = now.strftime("%Y-%m-%d %H-%M-%S")
        structured_dir = self.logs_dir / "structured"
        structured_dir.mkdir(parents=True, exist_ok=True)
        self.structured_log_path = structured_dir / f"{timestamp} GUI.jsonl"  # type: ignore[attr-defined]
        
        # Keep legacy path references for compatibility but point to structured log
        self.log_filename = f"{timestamp} GUI.jsonl"
        self.log_path = self.structured_log_path

        # Ensure buffered writes flush on interpreter exit as a last resort
        if not self._atexit_registered:
            atexit.register(self._flush_buffer_on_exit)
            self._atexit_registered = True

        # Queue structured metadata record (first JSON line)
        meta: Dict[str, Any] = {
            "schema": 1,
            "session_started": now.isoformat(timespec='seconds'),
            "log_level": self.log_level.value,
            "selected_format": "STRUCTURED_ONLY",
        }
        meta_line = json.dumps(meta, separators=(",", ":")) + "\n"
        self._structured_buffer.append(meta_line)

        self._log_initialized = True
    
    def _write_header(self) -> None:
        """Deprecated method - now handled by _initialize_log_file."""
        pass
    
    def _should_log_category(self, category: str) -> bool:
        """Check if a message category should be logged at current level."""
        # SIMPLIFIED: Always log everything - no category filtering
        return True

    def _buffer_agent_transition(self, agent_id: str, old_mode: str, new_mode: str, context: str, step: Optional[int]) -> None:
        """Buffer agent transitions for potential batching and deduplication."""
        # Use a default step value when None to allow batching to work
        if step is None:
            step = -1  # Use -1 as sentinel for "unknown step"
            
        # Flush previous step's transitions if we've moved to a new step
        if step != self._last_transition_step and self._last_transition_step >= 0:
            self._flush_transition_buffer()
        
        # Check for immediate repetition (same transition from same agent)
        transition_key = (agent_id, old_mode, new_mode)
        if transition_key in self._transition_dedupe:
            self._transition_dedupe[transition_key] += 1
            return  # Skip logging repeated identical transitions
        
        # Add to current step's buffer
        if step not in self._agent_transition_buffer:
            self._agent_transition_buffer[step] = []
        self._agent_transition_buffer[step].append((agent_id, old_mode, new_mode, context))
        self._last_transition_step = step
        
        # Track for deduplication (reset after a short window)
        self._transition_dedupe[transition_key] = 1
        
        # Flush if buffer gets too large or too much time has passed
        total_transitions = sum(len(trans_list) for trans_list in self._agent_transition_buffer.values())
        time_since_flush = (datetime.now() - self._last_transition_flush_time).total_seconds()
        
        if total_transitions > 50 or time_since_flush > 2.0:  # Flush after 50+ transitions OR 2+ seconds
            self._flush_transition_buffer()
            self._last_transition_flush_time = datetime.now()
    
    def _flush_trade_buffer(self) -> None:
        """Flush buffered trades.

        Emits structured records for each individual trade.
        """
        if not self._trade_buffer:
            return

        for step, trades in self._trade_buffer.items():
            # Emit structured records (per trade)
            for trade in trades:
                payload = self._parse_trade(trade)
                structured = self._emit_structured("TRADE", step, payload)
                self._write_structured_line(structured)

        self._trade_buffer.clear()

    def _buffer_trade(self, message: str, step: Optional[int]) -> None:
        """Buffer individual trade lines for same-step aggregation (compact only).

        Structured log still receives per-trade payloads when the buffer flushes;
        this method only delays compact human-readable emission so multiple trades
        in a single step become a single summarized line.
        """
        if step is None:
            step = -1
        # If we've advanced to a new step, flush the previous one first
        if step != self._last_trade_step and self._last_trade_step >= 0:
            self._flush_trade_buffer()
        self._trade_buffer.setdefault(step, []).append(message)
        self._last_trade_step = step

    def _flush_transition_buffer(self) -> None:
        """Flush buffered agent transitions.

        Emits structured records for individual transitions or batch records for multiple similar transitions.
        """
        if not self._agent_transition_buffer:
            return

        for step, transitions in self._agent_transition_buffer.items():
            transition_groups: dict[tuple[str, str], list[tuple[str, str]]] = {}
            for agent_id, old_mode, new_mode, context in transitions:
                key = (old_mode, new_mode)
                transition_groups.setdefault(key, []).append((agent_id, context))

            for (old_mode, new_mode), agent_context_pairs in transition_groups.items():
                # Structured emission
                if len(agent_context_pairs) == 1:
                    agent_id, context = agent_context_pairs[0]
                    payload: Dict[str, Any] = {
                        "event": "mode_transition",
                        "agent": int(agent_id[1:]),
                        "old_mode": old_mode,
                        "new_mode": new_mode,
                    }
                    
                    # Extract structured fields from context if present
                    if context:
                        import re
                        context = context.strip()
                        
                        # Extract reason from parentheses
                        reason_match = re.search(r'\(([^)]+)\)', context)
                        if reason_match:
                            payload["reason"] = reason_match.group(1)
                            
                        # Extract carrying count
                        carry_match = re.search(r'carrying: (\d+)', context)
                        if carry_match:
                            payload["carrying"] = int(carry_match.group(1))
                            
                        # Extract target coordinates
                        target_match = re.search(r'target: \((\d+), (\d+)\)', context)
                        if target_match:
                            payload["target"] = {"x": int(target_match.group(1)), "y": int(target_match.group(2))}
                        
                        # Only include raw context if no structured fields were extracted at all
                        if not (reason_match or carry_match or target_match):
                            payload["context"] = context
                    structured = self._emit_structured("MODE", step, payload)
                    self._write_structured_line(structured)
                else:
                    agent_ids = [int(a[1:]) for a, _ in agent_context_pairs]
                    payload = {
                        "event": "mode_batch",
                        "old_mode": old_mode,
                        "new_mode": new_mode,
                        "agents": agent_ids,
                        "count": len(agent_ids),
                    }
                    structured = self._emit_structured("MODE_BATCH", step, payload)
                    self._write_structured_line(structured)

        self._agent_transition_buffer.clear()
        self._transition_dedupe.clear()
    
    def _buffer_trade_bundle(self, category: str, message: str, step: Optional[int]) -> None:
        """Buffer trade and utility messages for bundling when ECONSIM_LOG_BUNDLE_TRADES=1."""
        if step is None:
            step = -1  # Use sentinel for unknown step
            
        # Flush previous step's bundles if we've moved to a new step
        if step != self._last_bundle_step and self._last_bundle_step >= 0:
            self._flush_bundle_buffer()
        
        # Initialize step buffer if needed
        if step not in self._trade_bundle_buffer:
            self._trade_bundle_buffer[step] = {"trades": [], "utilities": []}
        
        # Add to appropriate buffer
        if category == "TRADE":
            self._trade_bundle_buffer[step]["trades"].append(message)
        elif category == "UTILITY":
            self._trade_bundle_buffer[step]["utilities"].append(message)
        
        self._last_bundle_step = step
        
        # Flush if buffer gets too large
        total_entries = sum(len(data["trades"]) + len(data["utilities"]) for data in self._trade_bundle_buffer.values())
        if total_entries > 100:  # Flush after 100+ entries
            self._flush_bundle_buffer()
    
    def _flush_bundle_buffer(self) -> None:
        """Flush bundled trade+utility messages."""
        if not self._trade_bundle_buffer:
            return
            
        for step, data in self._trade_bundle_buffer.items():
            trades = data["trades"]
            utilities = data["utilities"]
            
            # Create a mapping of agent utilities for this step
            from typing import Tuple
            agent_utilities: dict[int, Tuple[str, str, str]] = {}  # agent_id -> (old_util, new_util, delta)
            for utility_msg in utilities:
                import re
                match = re.search(r'Agent_(\d+) utility: ([0-9.]+) → ([0-9.]+) \(Δ([+-][0-9.]+)\)', utility_msg)
                if match:
                    agent_id, old_util, new_util, delta = match.groups()
                    agent_utilities[int(agent_id)] = (old_util, new_util, delta)
            
            # Process each trade and bundle with utility info
            for trade_msg in trades:
                import re
                match = re.search(r'Agent_(\d+) gives (\w+) to Agent_(\d+); receives (\w+).*?utility: ([+-]?[0-9.-]+)', trade_msg)
                if match:
                    seller_id, give_type, buyer_id, recv_type, combined_delta = match.groups()
                    seller_id, buyer_id = int(seller_id), int(buyer_id)
                    
                    # Build bundled message
                    timestamp_prefix = self._format_simulation_time(step)
                    step_info = f"S{step}" if step >= 0 else ""
                    
                    # Base trade info
                    bundled = f"{timestamp_prefix} {step_info} T: {format_agent_id(seller_id)}↔{format_agent_id(buyer_id)} {give_type}→{recv_type} {format_delta(float(combined_delta))}"
                    
                    # Add utility details if available
                    utility_parts: list[str] = []
                    if seller_id in agent_utilities:
                        old_tuple = agent_utilities[seller_id]
                        old_val_str, new_val_str, delta_val_str = old_tuple[0], old_tuple[1], old_tuple[2]
                        utility_parts.append(f"{format_agent_id(seller_id)}:{old_val_str}→{new_val_str} Δ{delta_val_str}")
                    if buyer_id in agent_utilities:
                        buyer_tuple = agent_utilities[buyer_id]
                        old_val_str, new_val_str, delta_val_str = buyer_tuple[0], buyer_tuple[1], buyer_tuple[2]
                        utility_parts.append(f"{format_agent_id(buyer_id)}:{old_val_str}→{new_val_str} Δ{delta_val_str}")
                    
                    if utility_parts:
                        bundled += f" | U {'; '.join(utility_parts)}"
                    
                    bundled += "\n"
                    self._write_to_file(bundled)

            # Structured emits underlying individual events regardless of bundling choice
            for utility_msg in utilities:
                payload_u = self._parse_utility(utility_msg)
                structured_u = self._emit_structured("UTILITY", step, payload_u)
                self._write_structured_line(structured_u)
            for trade_msg in trades:
                payload_t = self._parse_trade(trade_msg)
                structured_t = self._emit_structured("TRADE", step, payload_t)
                self._write_structured_line(structured_t)
        
        self._trade_bundle_buffer.clear()
    
    def _write_to_file(self, structured_line: str) -> None:
        """Write structured log line to file (legacy method name for compatibility)."""
        self._write_structured_line(structured_line)

    def _write_structured_line(self, structured_line: str) -> None:
        """Write a structured JSONL line to the log file."""
        if not self._log_initialized:
            self._initialize_log_file()
        with self._lock:
            try:
                self._structured_buffer.append(structured_line)
                self._structured_buffer_flushed = False
                # Attempt to parse and append to ring buffer (best effort)
                try:
                    obj = json.loads(structured_line)
                    if isinstance(obj, dict):  # type: ignore[truthy-bool]
                        self._structured_ring.append(obj)  # type: ignore[attr-defined]
                        if len(self._structured_ring) > self._structured_ring_capacity:  # type: ignore[attr-defined]
                            self._structured_ring.pop(0)  # type: ignore[attr-defined]
                except Exception:
                    pass
            except Exception:
                pass

    def _flush_structured_buffer_to_disk(self) -> None:
        """Persist buffered structured log lines to disk."""
        if not self._log_initialized or getattr(self, "structured_log_path", None) is None:
            return
        if self._structured_buffer_flushed:
            return
        with self._lock:
            if not self._structured_buffer:
                return
            try:
                with open(self.structured_log_path, 'w', encoding='utf-8') as sf:  # type: ignore[attr-defined]
                    sf.writelines(self._structured_buffer)
                self._structured_buffer_flushed = True
            except Exception:
                pass

    def _flush_buffer_on_exit(self) -> None:
        """Flush buffered logs when the interpreter exits."""
        try:
            self._flush_structured_buffer_to_disk()
        except Exception:
            pass

    def format_structured_event_for_display(self, event: Dict[str, Any]) -> str:
        """Convert structured event to human-readable format for GUI display."""
        try:
            # Extract common fields
            ts_rel = event.get('ts_rel', 0.0)
            category = event.get('category', '?')
            step = event.get('step', None)
            event_type = event.get('event', '?')
            
            # Format timestamp
            time_prefix = f"+{ts_rel:.1f}s"
            
            # Format step info
            step_info = f"S{step}" if step is not None else ""
            
            # Format event-specific content
            if event_type == "periodic_summary":
                fps = event.get('steps_per_sec', 0)
                frame_ms = event.get('frame_ms', 0)
                agents = event.get('agents', 0)
                resources = event.get('resources', 0)
                phase = event.get('phase', None)
                phase_part = f" Ph{phase}" if phase is not None else ""
                content = f"P: {fps:.1f}s/s {frame_ms:.1f}ms A{agents} R{resources}{phase_part}"
            elif event_type == "mode_transition":
                agent = event.get('agent', '?')
                old_mode = event.get('old_mode', '?')
                new_mode = event.get('new_mode', '?')
                
                # Build context from structured fields
                context_parts: List[str] = []
                if 'reason' in event:
                    context_parts.append(f"({event['reason']})")
                if 'carrying' in event:
                    context_parts.append(f"carrying: {event['carrying']}")
                if 'target' in event:
                    target = event['target']
                    if isinstance(target, dict):
                        context_parts.append(f"target: ({target.get('x', '?')},{target.get('y', '?')})")
                
                context = ", ".join(context_parts) if context_parts else ""
                content = f"{self._format_agent_id(agent)}: {old_mode}→{new_mode} {context}"
            elif event_type == "phase_transition":
                phase = event.get('phase', '?')
                turn = event.get('turn', '?')
                description = event.get('description', '?')
                # Abbreviate common descriptions
                desc = str(description).replace("Only foraging enabled", "Forage only") \
                                      .replace("Only exchange enabled", "Exchange only") \
                                      .replace("Both disabled - agents should idle", "Both disabled") \
                                      .replace("Both foraging and exchange enabled", "Both enabled")
                content = f"PHASE{phase}@{turn}: {desc}"
            elif event_type == "trade":
                # Handle different trade formats
                if 'agent1' in event and 'agent2' in event:
                    a1, a2 = event['agent1'], event['agent2']
                    give = event.get('give', '?')
                    receive = event.get('receive', '?')
                    if 'delta_agent1' in event:
                        delta = self._format_delta(event['delta_agent1'])
                        content = f"T: A{a1:03d}↔A{a2:03d} {give}→{receive} {delta}"
                    else:
                        content = f"T: A{a1:03d}↔A{a2:03d} {give}→{receive}"
                else:
                    content = f"T: {event.get('raw', 'trade event')}"
            elif event_type == "micro_delta_threshold":
                threshold = event.get('threshold', '?')
                content = f"TI: micro_delta_threshold={threshold:g} (activating prune)"
            else:
                # Generic fallback
                content = f"{str(category)[:3]}: {event.get('raw', str(event))}"
            
            # Combine pieces
            if step_info:
                return f"{time_prefix} {step_info}: {content}"
            else:
                return f"{time_prefix} {content}"
                
        except Exception:
            # Fallback to raw JSON if formatting fails
            return f"LOG: {json.dumps(event, separators=(',', ':'))}"
    
    def _format_agent_id(self, agent_id: Any) -> str:
        """Format agent ID for display."""
        try:
            return f"A{int(agent_id):03d}"
        except (ValueError, TypeError):
            return f"A{agent_id}"
    
    def _format_delta(self, delta: Any) -> str:
        """Format utility delta for display."""
        try:
            if isinstance(delta, (int, float)):
                return f"Δ{delta:+.1f}"
            else:
                return f"Δ{delta}"
        except Exception:
            return f"Δ{delta}"

    def _build_structured_payload(self, category: str, message: str) -> Dict[str, Any]:
        """Build structured payload for a message without writing.

        Reuses the same parsing branches used for STRUCTURED format, allowing
        dual emission when COMPACT is selected.
        """
        if category in ("MODE", "AGENT_MODE"):
            return self._parse_mode_transition(message)
        if category == "UTILITY":
            return self._parse_utility(message)
        if category == "TRADE":
            return self._parse_trade(message)
        if category in ("SIMULATION", "PERIODIC_SIM"):
            if "steps/sec | Frame" in message:
                return self._parse_periodic_summary(message)
            return {"event": "simulation", "raw": message}
        if category == "PHASE":
            return self._parse_phase(message)
        if category in ("PERF", "PERIODIC_PERF"):
            return self._parse_perf(message)
        return {"event": category.lower(), "raw": message}

    # ---------------- Phase 3 Event Builder Helpers -----------------
    # Each returns (compact_line: str, structured_payload: Dict[str, Any], category: str)


    def build_micro_delta_threshold(self, threshold: float, first_drop_delta: float | None = None) -> tuple[str, Dict[str, Any], str]:
        category = "TRADE"
        delta_fragment = f" first_drop_delta={first_drop_delta:.6g}" if isinstance(first_drop_delta, (int, float)) else ""
        compact = f"TI: micro_delta_threshold={threshold:g}{delta_fragment} (activating prune)"
        payload: Dict[str, Any] = {
            "event": "micro_delta_threshold",
            "threshold": threshold,
            "activated": True,
        }
        if isinstance(first_drop_delta, (int, float)):
            payload["first_drop_delta"] = first_drop_delta
        return compact, payload, category

    def build_periodic_summary(self, steps_per_sec: float, frame_ms: float, agents: int, resources: int, phase: Optional[int]) -> tuple[str, Dict[str, Any], str]:
        """Build periodic summary event with structured data (no raw text redundancy)."""
        category = "SIMULATION"
        phase_part = f" Ph{phase}" if phase is not None else ""
        compact = f"P: {steps_per_sec:.1f}s/s {frame_ms:.1f}ms A{agents} R{resources}{phase_part}"
        payload: Dict[str, Any] = {
            "event": "periodic_summary",
            "steps_per_sec": round(steps_per_sec, 1),
            "frame_ms": round(frame_ms, 1),
            "agents": agents,
            "resources": resources
        }
        if phase is not None:
            payload["phase"] = phase
        return compact, payload, category

    def build_phase_transition(self, phase: int, turn: int, description: str) -> tuple[str, Dict[str, Any], str]:
        """Build phase transition event with structured data (no raw text redundancy)."""
        category = "PHASE"
        # Shorten common descriptions for compact display
        short_desc = description.replace("Only foraging enabled", "Forage only") \
                                .replace("Only exchange enabled", "Exchange only") \
                                .replace("Both foraging and exchange enabled", "Both enabled") \
                                .replace("Both disabled - agents should idle", "Both disabled")
        compact = f"PHASE{phase}@{turn}: {short_desc}"
        payload: Dict[str, Any] = {
            "event": "phase_transition",
            "phase": phase,
            "turn": turn,
            "description": description
        }
        return compact, payload, category

    def build_config_update(self, changes: Dict[str, Any]) -> tuple[str, Dict[str, Any], str]:
        category = "SIMULATION"
        level_fragment = ""
        added_fragment = ""
        removed_fragment = ""
        explanations_fragment = ""

        level_val = changes.get("level")
        if isinstance(level_val, dict):  # type: ignore[truthy-bool]
            old_v = level_val.get("old")  # type: ignore[attr-defined]
            new_v = level_val.get("new")  # type: ignore[attr-defined]
            if isinstance(old_v, str) and isinstance(new_v, str):
                level_fragment = f"level={old_v}→{new_v}"

        added_raw = changes.get("added_categories")
        removed_raw = changes.get("removed_categories")
        if isinstance(added_raw, list):  # type: ignore[truthy-bool]
            added = [a for a in added_raw if isinstance(a, str)]  # type: ignore[misc]
            if added:
                added_fragment = f"add={{{{ {','.join(added)} }}}}"
        if isinstance(removed_raw, list):  # type: ignore[truthy-bool]
            removed = [r for r in removed_raw if isinstance(r, str)]  # type: ignore[misc]
            if removed:
                removed_fragment = f"remove={{{{ {','.join(removed)} }}}}"

        explanations_val = changes.get("explanations")
        if isinstance(explanations_val, dict):  # type: ignore[truthy-bool]
            new_state = explanations_val.get("new")  # type: ignore[attr-defined]
            if isinstance(new_state, bool):
                explanations_fragment = f"explanations={'on' if new_state else 'off'}"

        parts = [p for p in [level_fragment, added_fragment, removed_fragment, explanations_fragment] if p]
        compact = "CFG: " + " ".join(parts) if parts else "CFG: (no_op)"
        payload: Dict[str, Any] = {"event": "config_update", "changes": changes}
        return compact, payload, category

    # --- Dynamic Config Update Emission ---------------------------------
    def set_logging_config(
        self,
        *,
        level: Optional[str] = None,
        add_categories: Optional[Iterable[str]] = None,
        remove_categories: Optional[Iterable[str]] = None,
        explanations: Optional[bool] = None,
        emit: bool = True,
    ) -> None:
        """Dynamically adjust logging configuration and emit structured diff.

        Args:
            level: New log level name (if provided).
            add_categories: Categories to add to ALWAYS-ALLOW set (future extension placeholder).
            remove_categories: Categories to remove (future extension placeholder).
            explanations: Toggle verbose explanation overlay flag (placeholder; stored on instance).
            emit: If False, apply without emitting config_update (used for bootstrap).

        This method is append-only and safe: unknown categories ignored, mutations idempotent.
        """
        from .debug_logger import LogLevel  # circular safe (same module) but ensures name resolution
        self._step = 0  # Reset step to 0 when logging config is set
        changes: Dict[str, Any] = {}
        if level is not None:
            old_level = self.log_level.value
            try:
                new_level_enum = LogLevel(level.upper())
                if new_level_enum.value != old_level:
                    self.log_level = new_level_enum
                    changes["level"] = {"old": old_level, "new": self.log_level.value}
            except Exception:
                pass
        # Category management (placeholders: categories list not yet first-class; kept for forward compatibility)
        added_cats: list[str] = []
        removed_cats: list[str] = []
        if add_categories:
            for c in add_categories:
                if c:
                    added_cats.append(c)
        if remove_categories:
            for c in remove_categories:
                if c:
                    removed_cats.append(c)
        if added_cats:
            changes["added_categories"] = added_cats
        if removed_cats:
            changes["removed_categories"] = removed_cats
        if explanations is not None:
            prev = getattr(self, "_explanations_enabled", False)
            if explanations != prev:
                setattr(self, "_explanations_enabled", explanations)
                changes["explanations"] = {"old": prev, "new": explanations}
                if emit and changes:
                    builder_tuple = self.build_config_update(changes)
                    self.emit_built_event(None, builder_tuple)

    def build_partner_search(
        self,
        agent_id: int,
        scanned: int,
        eligible: int,
        chosen_id: int,
        method: str,
        cooldown_global: int,
        cooldown_partner: int,
        rejected_partners: list[tuple[int, str]] | None = None,
    ) -> tuple[str, Dict[str, Any], str]:
        """Partner search summary with consolidated rejections (abbreviated format).

        Args:
            agent_id: Agent performing the search
            scanned: Total partners scanned
            eligible: Eligible partners (after filtering)
            chosen_id: ID of chosen partner (-1 if none)
            method: Selection method (unified_selection)
            cooldown_global: Global cooldown counter
            cooldown_partner: Partner cooldown counter
            rejected_partners: Optional list of (partner_id, reason) tuples for rejected candidates

        Returns:
            tuple(compact_line, structured_payload, category)
            
        Note:
            Uses abbreviated field names for compact JSON output:
            - cat: category (PAIR = PAIRING)
            - ev: event (psearch = partner_search)
            - a: agent ID
            - scan: scanned count
            - elig: eligible count
            - cho: chosen partner ID
            - rej: rejected partners array [{c: candidate_id, r: reason_abbrev}]
        """
        category = "PAIRING"
        
        # Build compact human-readable line
        compact = f"PS: A{agent_id:03d} scan={scanned} elig={eligible} cho=A{chosen_id:03d}"
        if rejected_partners:
            compact += f" rej={len(rejected_partners)}"
        
        # Build abbreviated structured payload
        payload: Dict[str, Any] = {
            "ev": "psearch",  # Abbreviated event name
            "a": agent_id,
            "scan": scanned,
            "elig": eligible,
            "cho": chosen_id,
        }
        
        # Add rejection data if provided (consolidated into single event)
        if rejected_partners:
            # Abbreviate rejection reasons for compactness
            reason_map = {
                "negative_utility": "neg_u",
                "already_paired": "paired",
                "cooldown": "cd",
                "not_interested": "no_int",
            }
            payload["rej"] = [
                {
                    "c": partner_id,  # candidate
                    "r": reason_map.get(reason, reason[:8])  # abbreviated reason
                }
                for partner_id, reason in rejected_partners
            ]
        
        return compact, payload, category

    def build_partner_reject(
        self,
        agent_id: int,
        candidate_id: int,
        reason: str,
        sampled: bool,
    ) -> tuple[str, Dict[str, Any], str]:
        """DEPRECATED: Partner rejection sample (consolidated into build_partner_search).
        
        This method is kept for backward compatibility but should not be used.
        Use build_partner_search with rejected_partners parameter instead.
        """
        category = "PAIRING"
        compact = (
            f"PSR: A{agent_id:03d} reject=A{candidate_id:03d} reason={reason}" + (" sampled" if sampled else "")
        )
        payload: Dict[str, Any] = {
            "event": "partner_reject",
            "agent": agent_id,
            "candidate": candidate_id,
            "reason": reason,
            "sampled": sampled,
        }
        return compact, payload, category

    # --- PAIRING Aggregation System ---
    
    def flush_pairing_for_step(self, step: int) -> None:
        """Explicitly flush PAIRING accumulator for the given step.
        
        This should be called at the end of each simulation step to emit
        the PAIRING_SUMMARY for that step.
        """
        if self._pairing_current_step == step and self._pairing_accumulator:
            self._flush_pairing_step()
    
    def accumulate_partner_search(
        self,
        step: int,
        agent_id: int,
        scanned: int,
        eligible: int,
        chosen_id: int,
        rejected_partners: list[tuple[int, str]] | None = None,
    ) -> None:
        """Accumulate partner search data for step-based statistical aggregation.
        
        Replaces immediate per-search logging with batched step summaries to reduce
        log volume while preserving individual anomalous events and successful pairings.
        Core method for PAIRING event aggregation system.
        
        Args:
            step: Current simulation step number
            agent_id: Agent performing partner search
            scanned: Total number of potential partners evaluated
            eligible: Partners remaining after filtering (cooldowns, availability)
            chosen_id: Selected partner ID (≥0 for success, -1 for failure)
            rejected_partners: Optional list of (partner_id, rejection_reason) tuples
            
        Side Effects:
            - Accumulates data in self._pairing_accumulator for current step
            - Emits individual events for successful pairings and anomalies
            - Triggers step flush when step number advances
            - Updates behavioral tracking data for Phase 3.2 analysis
            
        Aggregation Logic:
            - Batches failed searches for statistical summary
            - Preserves individual successful pairings for correlation tracking
            - Detects anomalous scan counts (>2σ from step mean)
            - Tracks rejection reason frequencies
            
        Thread Safety:
            Not thread-safe. Assumes single-threaded simulation execution.
            
        Performance:
            O(1) accumulation, O(n) flush where n = searches per step (typically <100)
        """
        # Initialize accumulator for new step
        if self._pairing_current_step != step:
            self._flush_pairing_step()  # Flush previous step if any
            self._pairing_current_step = step
            self._pairing_accumulator = {
                "step": step,
                "searches": [],
                "rejection_counts": {},
                "successful_pairings": [],
                "anomalies": [],
                "total_scanned": 0,
                "total_eligible": 0,
                "count": 0,
            }
        
        # Add search data
        search_data = {
            "agent_id": agent_id,
            "scanned": scanned,
            "eligible": eligible,
            "chosen_id": chosen_id,
            "rejected_partners": rejected_partners or [],
        }
        
        self._pairing_accumulator["searches"].append(search_data)
        self._pairing_accumulator["total_scanned"] += scanned
        self._pairing_accumulator["total_eligible"] += eligible
        self._pairing_accumulator["count"] += 1
        
        # Count rejections by reason
        if rejected_partners:
            for _, reason in rejected_partners:
                # Use abbreviated reason names from build_partner_search
                reason_map = {
                    "negative_utility": "neg_u",
                    "already_paired": "paired",
                    "cooldown": "cd",
                    "not_interested": "no_int",
                }
                abbrev_reason = reason_map.get(reason, reason[:8])
                self._pairing_accumulator["rejection_counts"][abbrev_reason] = (
                    self._pairing_accumulator["rejection_counts"].get(abbrev_reason, 0) + 1
                )
        
        # Check if this should be logged individually (exceptions)
        should_log_individual = self._should_log_pairing_individually(search_data)
        
        if should_log_individual:
            # Use existing build_partner_search for individual exceptional events
            builder_result = self.build_partner_search(
                agent_id=agent_id,
                scanned=scanned,
                eligible=eligible,
                chosen_id=chosen_id,
                method="unified_selection",
                cooldown_global=0,
                cooldown_partner=0,
                rejected_partners=rejected_partners,
            )
            
            # Phase 3.1: Start causal chain for successful pairings
            if chosen_id >= 0:  # Successful pairing
                correlation_id = self.generate_correlation_id(agent_id, chosen_id, step)
                self.start_causal_chain(correlation_id, step, (agent_id, chosen_id))
                self.add_to_causal_chain(
                    correlation_id, 
                    "pairing_success", 
                    0.0,  # ts_offset
                    agent_pair=[agent_id, chosen_id],
                    scan_count=scanned,
                    eligible_count=eligible
                )
                # Add correlation_id to the payload before emitting
                builder_result = (
                    builder_result[0],  # compact
                    {**builder_result[1], "correlation_id": correlation_id},  # payload with correlation_id
                    builder_result[2]   # category
                )
            
            # Phase 3.4: Use clustering for failed pairings, emit successful ones individually
            self.emit_or_cluster_pairing_event(step, builder_result)
            
            # Track in accumulator for record keeping
            if chosen_id >= 0:
                self._pairing_accumulator["successful_pairings"].append(search_data)
            else:
                self._pairing_accumulator["anomalies"].append(search_data)
        
        # Phase 3.2: Track agent behavior for all search attempts
        if chosen_id >= 0:
            # Successful pairing
            self.track_agent_pairing(step, agent_id, successful=True)
            self.track_agent_partner(step, agent_id, chosen_id)
        else:
            # Failed pairing
            self.track_agent_pairing(step, agent_id, successful=False)
    
    def _should_log_pairing_individually(self, search_data: dict[str, Any]) -> bool:
        """Determine if a PAIRING event should be logged individually."""
        # Always log successful pairings
        if search_data["chosen_id"] >= 0:
            return True
        
        # Log anomalous scan counts (>2σ from current step mean)
        if self._is_scan_count_anomaly(search_data["scanned"]):
            return True
        
        # Log first occurrence of new rejection reasons
        if self._has_new_rejection_reasons(search_data.get("rejected_partners", [])):
            return True
            
        return False
    
    def _is_scan_count_anomaly(self, scan_count: int) -> bool:
        """Check if scan count is anomalous (>2σ from mean)."""
        if self._pairing_accumulator["count"] < 3:  # Need minimum data for statistics
            return False
            
        # Calculate current mean and std deviation
        scan_counts = [s["scanned"] for s in self._pairing_accumulator["searches"]]
        if len(scan_counts) < 2:
            return False
            
        mean_scan = sum(scan_counts) / len(scan_counts)
        variance = sum((x - mean_scan) ** 2 for x in scan_counts) / len(scan_counts)
        std_dev = variance ** 0.5
        
        # Check if current scan count is >2σ from mean
        return abs(scan_count - mean_scan) > (2 * std_dev)
    
    def _has_new_rejection_reasons(self, rejected_partners: list[tuple[int, str]]) -> bool:
        """Check if any rejection reasons are new this step."""
        if not rejected_partners:
            return False
            
        existing_reasons = set(self._pairing_accumulator["rejection_counts"].keys())
        for _, reason in rejected_partners:
            reason_map = {
                "negative_utility": "neg_u", 
                "already_paired": "paired",
                "cooldown": "cd",
                "not_interested": "no_int",
            }
            abbrev_reason = reason_map.get(reason, reason[:8])
            if abbrev_reason not in existing_reasons:
                return True
        return False
    
    def _flush_pairing_step(self) -> None:
        """Flush accumulated PAIRING data as a comprehensive step summary.
        
        Processes all partner search data accumulated during a simulation step and
        emits a statistical summary as PAIRING_SUMMARY event. Critical method for
        step-based aggregation system that reduces log volume while preserving
        essential pairing statistics and anomaly detection.
        
        Side Effects:
            - Emits PAIRING_SUMMARY structured event via emit_built_event()
            - Triggers behavior flush if behavior window is complete
            - Triggers clustered event flush for Phase 3.4 processing
            - Clears self._pairing_accumulator for next step
        
        Statistical Processing:
            - Calculates average scan counts and eligible partner counts
            - Identifies top scanning agents for debugging (top 3 by scan count)
            - Aggregates rejection reason frequencies
            - Counts successful pairings for correlation tracking
            
        Integration Points:
            - Phase 3.2: Checks if behavior data should be flushed
            - Phase 3.4: Flushes any remaining clustered events
            - Correlation tracking: Preserves successful pairings for causal chains
            
        Performance:
            O(n) where n = searches in current step (typically <100).
            Statistical calculations are linear in search count.
            
        Thread Safety:
            Not thread-safe. Should only be called from single simulation thread.
        """
        if not self._pairing_accumulator or self._pairing_accumulator["count"] == 0:
            return
            
        acc = self._pairing_accumulator
        step = acc["step"]
        
        # Calculate statistics
        scan_counts = [s["scanned"] for s in acc["searches"]]
        eligible_counts = [s["eligible"] for s in acc["searches"]]
        
        avg_scan = sum(scan_counts) / len(scan_counts) if scan_counts else 0
        avg_eligible = sum(eligible_counts) / len(eligible_counts) if eligible_counts else 0
        
        # Find top scanners for debugging
        sorted_searches = sorted(acc["searches"], key=lambda x: x["scanned"], reverse=True)
        top_agents_by_scan = [
            {"a": s["agent_id"], "scan": s["scanned"]} 
            for s in sorted_searches[:3]  # Top 3
        ]
        
        # Build PAIRING_SUMMARY event
        builder_result = self.build_pairing_summary(
            step=step,
            total_searches=acc["count"],
            avg_scan=avg_scan,
            avg_eligible=avg_eligible,
            successful_pairings=len(acc["successful_pairings"]),
            rejection_breakdown=acc["rejection_counts"],
            top_agents_by_scan=top_agents_by_scan,
        )
        
        self.emit_built_event(step, builder_result)
        
        # Phase 3.2: Check if we should flush behavior data
        if self.should_flush_behavior_data(step):
            self.flush_agent_behavior_summaries(step)
        
        # Phase 3.4: Flush any remaining clustered events for this step
        if self._clustering_current_step == step:
            self._flush_clustered_step()
        
        # Clear accumulator
        self._pairing_accumulator = {}
    
    def build_pairing_summary(
        self,
        step: int,
        total_searches: int,
        avg_scan: float,
        avg_eligible: float,
        successful_pairings: int,
        rejection_breakdown: dict[str, int],
        top_agents_by_scan: list[dict[str, Any]],
    ) -> tuple[str, Dict[str, Any], str]:
        """Build PAIRING_SUMMARY event with aggregated statistics."""
        category = "PAIRING_SUMMARY"
        
        # Build compact summary
        compact = (
            f"PAIRING_SUMMARY: step={step} searches={total_searches} "
            f"avg_scan={avg_scan:.1f} avg_eligible={avg_eligible:.1f} "
            f"successful={successful_pairings}"
        )
        
        # Build structured payload matching the plan
        payload: Dict[str, Any] = {
            "event": "step_summary",
            "step": step,
            "total_searches": total_searches,
            "avg_scan": round(avg_scan, 1),
            "avg_eligible": round(avg_eligible, 1),
            "successful_pairings": successful_pairings,
            "rejection_breakdown": rejection_breakdown,
            "top_agents_by_scan": top_agents_by_scan,
        }
        
        return compact, payload, category

    # Phase 3.1: Correlation ID and Causal Chain Methods
    
    def generate_correlation_id(self, agent1: int, agent2: int, step: int) -> str:
        """Generate a correlation ID for a bilateral exchange sequence."""
        self._correlation_counter += 1
        return f"bex_{agent1}_{agent2}_step{step}_{self._correlation_counter}"
    
    def start_causal_chain(self, correlation_id: str, step: int, agent_pair: tuple[int, int]) -> None:
        """Start tracking a causal chain for bilateral exchange analysis."""
        self._active_chains[correlation_id] = {
            "step": step,
            "agent_pair": agent_pair,
            "sequence": [],
            "start_time": 0.0,
            "outcome": "pending",
            "educational_note": ""
        }
        # Track agent pair to correlation mapping
        self._agent_to_correlation[agent_pair] = correlation_id
    
    def add_to_causal_chain(
        self, 
        correlation_id: str, 
        event: str, 
        ts_offset: float, 
        **kwargs: Any
    ) -> None:
        """Add an event to an active causal chain."""
        if correlation_id in self._active_chains:
            event_data = {
                "event": event,
                "ts_offset": ts_offset,
                **kwargs
            }
            self._active_chains[correlation_id]["sequence"].append(event_data)
    
    def finalize_causal_chain(
        self, 
        correlation_id: str, 
        outcome: str, 
        educational_note: str = ""
    ) -> None:
        """Complete and emit a causal chain event."""
        if correlation_id not in self._active_chains:
            return
            
        chain_data = self._active_chains[correlation_id]
        chain_data["outcome"] = outcome
        chain_data["educational_note"] = educational_note
        
        # Build the causal chain event
        compact = (
            f"CAUSAL_CHAIN: {correlation_id} outcome={outcome} "
            f"agents={chain_data['agent_pair']} events={len(chain_data['sequence'])}"
        )
        
        payload = {
            "event": "bilateral_exchange_sequence",
            "correlation_id": correlation_id,
            "step": chain_data["step"],
            "sequence": chain_data["sequence"],
            "outcome": outcome,
            "educational_note": educational_note
        }
        
        # Emit the causal chain event
        try:
            builder_result = (compact, payload, "CAUSAL_CHAIN")
            self.emit_built_event(chain_data["step"], builder_result)
        except Exception:
            pass  # Don't break simulation if logging fails
        
        # Clean up
        agent_pair = chain_data["agent_pair"]
        if agent_pair in self._agent_to_correlation:
            del self._agent_to_correlation[agent_pair]
        del self._active_chains[correlation_id]
    
    def get_correlation_for_agents(self, agent1: int, agent2: int) -> Optional[str]:
        """Get existing correlation ID for agent pair (either order)."""
        return (self._agent_to_correlation.get((agent1, agent2)) or 
                self._agent_to_correlation.get((agent2, agent1)))
    
    # Phase 3.2: Multi-Dimensional Agent Behavior Aggregation
    def _init_agent_behavior_data(self, agent_id: int):
        """Initialize behavioral tracking for an agent"""
        if agent_id not in self._agent_behavior_data:
            self._agent_behavior_data[agent_id] = {
                "pairing_count": 0,
                "successful_trades": 0,
                "failed_trades": 0,
                "movement_distance": 0.0,
                "utility_gains": [],
                "mode_changes": 0,
                "resource_acquisitions": 0,
                "partner_diversity": set(),  # Track unique trading partners
                "retarget_events": 0,
                "last_position": None
            }
    
    def track_agent_pairing(self, step: int, agent_id: int, successful: bool = False):
        """Track pairing behavior for behavior aggregation"""
        self._init_agent_behavior_data(agent_id)
        self._agent_behavior_data[agent_id]["pairing_count"] += 1
        if successful:
            self._agent_behavior_data[agent_id]["successful_trades"] += 1
        else:
            self._agent_behavior_data[agent_id]["failed_trades"] += 1
    
    def track_agent_movement(self, step: int, agent_id: int, from_pos: tuple[int, int], to_pos: tuple[int, int]):
        """Track movement behavior for behavior aggregation"""
        self._init_agent_behavior_data(agent_id)
        distance = ((to_pos[0] - from_pos[0])**2 + (to_pos[1] - from_pos[1])**2)**0.5
        self._agent_behavior_data[agent_id]["movement_distance"] += distance
        self._agent_behavior_data[agent_id]["last_position"] = to_pos
    
    def track_agent_utility_gain(self, step: int, agent_id: int, utility_gain: float):
        """Track utility gains for behavior aggregation"""
        self._init_agent_behavior_data(agent_id)
        self._agent_behavior_data[agent_id]["utility_gains"].append(utility_gain)
    
    def track_agent_partner(self, step: int, agent_id: int, partner_id: int):
        """Track trading partner diversity"""
        self._init_agent_behavior_data(agent_id)
        self._agent_behavior_data[agent_id]["partner_diversity"].add(partner_id)
    
    def track_agent_resource_acquisition(self, step: int, agent_id: int):
        """Track resource acquisition events"""
        self._init_agent_behavior_data(agent_id)
        self._agent_behavior_data[agent_id]["resource_acquisitions"] += 1
    
    def track_agent_retargeting(self, step: int, agent_id: int):
        """Track retargeting behavior"""
        self._init_agent_behavior_data(agent_id)
        self._agent_behavior_data[agent_id]["retarget_events"] += 1
    
    def should_flush_behavior_data(self, step: int) -> bool:
        """Check if behavior data should be flushed"""
        return (step - self._last_behavior_flush >= self._behavior_flush_interval) and step > 0
    
    def flush_agent_behavior_summaries(self, step: int):
        """Emit multi-dimensional agent behavior analysis as AGENT_BEHAVIOR_SUMMARY.
        
        Analyzes accumulated behavioral data over the configured window (default 100 steps)
        and emits comprehensive statistics including high-activity agent detection,
        typical behavior patterns, and environmental context.
        
        Args:
            step: Current simulation step triggering the flush
            
        Behavioral Dimensions Analyzed:
            - Pairing attempts and success rates
            - Movement distance and patterns  
            - Utility gains from trading
            - Partner diversity (unique trading partners)
            - Resource acquisition events
            - Target retargeting frequency
            
        Statistical Outputs:
            - Population-level aggregates (means, totals)
            - High-activity agent identification (top 10% by pairing attempts)
            - Success rate calculations and fairness metrics
            - Environmental context (total movement, utility distribution)
            
        Side Effects:
            - Clears self._agent_behavior_data for next window
            - Updates self._last_behavior_flush = step
            - Emits structured AGENT_BEHAVIOR_SUMMARY event
            
        Educational Value:
            Provides insights into agent behavioral patterns, trading effectiveness,
            and emergent economic dynamics over time windows.
            
        Performance:
            O(n log n) where n = active agents, due to sorting for high-activity detection.
            Typical execution <1ms for 100 agents.
        """
        if not self._agent_behavior_data:
            return
        
        # Calculate aggregate statistics
        total_agents = len(self._agent_behavior_data)
        high_activity_agents = []
        typical_behavior = {
            "avg_pairings": 0.0,
            "avg_successful_trades": 0.0,
            "avg_movement_distance": 0.0,
            "avg_utility_gain": 0.0,
            "avg_partner_diversity": 0.0
        }
        
        # Collect metrics and identify high-activity agents
        pairing_counts = []
        successful_trades = []
        movement_distances = []
        all_utility_gains = []
        partner_diversities = []
        
        for agent_id, behavior_data in self._agent_behavior_data.items():
            pairing_count = behavior_data["pairing_count"]
            successful_count = behavior_data["successful_trades"]
            movement_dist = behavior_data["movement_distance"]
            utility_gains = behavior_data["utility_gains"]
            partner_count = len(behavior_data["partner_diversity"])
            
            pairing_counts.append(pairing_count)
            successful_trades.append(successful_count)
            movement_distances.append(movement_dist)
            all_utility_gains.extend(utility_gains)
            partner_diversities.append(partner_count)
            
            # Identify high-activity agents (top 10% by pairing count)
            if pairing_count > 0:
                high_activity_agents.append((agent_id, pairing_count, successful_count, partner_count))
        
        # Calculate typical behavior statistics
        if pairing_counts:
            typical_behavior["avg_pairings"] = sum(pairing_counts) / len(pairing_counts)
        if successful_trades:
            typical_behavior["avg_successful_trades"] = sum(successful_trades) / len(successful_trades)
        if movement_distances:
            typical_behavior["avg_movement_distance"] = sum(movement_distances) / len(movement_distances)
        if all_utility_gains:
            typical_behavior["avg_utility_gain"] = sum(all_utility_gains) / len(all_utility_gains)
        if partner_diversities:
            typical_behavior["avg_partner_diversity"] = sum(partner_diversities) / len(partner_diversities)
        
        # Sort and take top 10% for high activity
        high_activity_agents.sort(key=lambda x: x[1], reverse=True)
        top_count = max(1, len(high_activity_agents) // 10)
        top_high_activity = high_activity_agents[:top_count]
        
        # Build compact summary
        total_pairings = sum(pairing_counts)
        total_successful = sum(successful_trades)
        success_rate = (total_successful / total_pairings * 100) if total_pairings > 0 else 0
        
        compact = f"Agents: {total_agents}, Pairings: {total_pairings}, Success: {success_rate:.1f}%, High-Activity: {len(top_high_activity)}"
        
        # Create full payload
        payload = {
            "step_range": f"{self._last_behavior_flush + 1}-{step}",
            "total_agents": total_agents,
            "total_pairings": total_pairings,
            "total_successful_trades": total_successful,
            "success_rate_percent": round(success_rate, 2),
            "typical_behavior": typical_behavior,
            "high_activity_agents": [
                {
                    "agent_id": agent_id,
                    "pairing_count": pairing_count,
                    "successful_trades": successful_count,
                    "partner_diversity": partner_count,
                    "activity_multiplier": round(pairing_count / typical_behavior["avg_pairings"], 2) if typical_behavior["avg_pairings"] > 0 else 0
                }
                for agent_id, pairing_count, successful_count, partner_count in top_high_activity
            ],
            "environmental_context": {
                "total_movement": sum(movement_distances),
                "total_utility_gained": sum(all_utility_gains),
                "avg_partner_diversity": typical_behavior["avg_partner_diversity"]
            },
            "educational_note": f"Behavioral analysis over {step - self._last_behavior_flush} steps showing agent activity patterns and trading effectiveness"
        }
        
        # Emit the behavior summary
        builder_result = (compact, payload, "AGENT_BEHAVIOR_SUMMARY")
        self.emit_built_event(step, builder_result)
        
        # Reset behavior data for next window
        self._agent_behavior_data.clear()
        self._last_behavior_flush = step

    # Phase 3.4: Intra-Step Event Clustering
    def should_cluster_pairing_event(self, step: int, pairing_data: Dict[str, Any]) -> bool:
        """Determine if a PAIRING event should be clustered or kept individual."""
        # Always preserve successful pairings individually (needed for correlation tracking)
        chosen_id = pairing_data.get("cho", pairing_data.get("chosen_id", -1))
        if chosen_id >= 0:
            return False
        
        # Always preserve anomalous scan counts individually (educational value)
        scan_count = pairing_data.get("scan", pairing_data.get("scanned", 0))
        if self._is_scan_count_anomaly(scan_count):
            return False
            
        # Cluster failed pairings with normal scan counts
        return True

    def accumulate_clustered_event(self, step: int, category: str, event_data: Dict[str, Any]) -> None:
        """Accumulate events for clustering by step and category."""
        # Check if we need to flush previous step
        if self._clustering_current_step != step and self._clustering_current_step >= 0:
            self._flush_clustered_step()
        
        self._clustering_current_step = step
        
        # Initialize category buffer if needed
        if category not in self._clustering_buffer:
            self._clustering_buffer[category] = []
        
        # Add event to clustering buffer
        self._clustering_buffer[category].append(event_data)

    def emit_or_cluster_pairing_event(self, step: int, builder_result: tuple[str, Dict[str, Any], str]) -> None:
        """Either emit PAIRING event individually or accumulate for clustering."""
        compact, payload, category = builder_result
        
        # Check if this should be clustered
        if category == "PAIRING" and self.should_cluster_pairing_event(step, payload):
            # Add to clustering buffer
            self.accumulate_clustered_event(step, "PAIRING_FAILED", payload)
        else:
            # Emit individually (successful pairings, anomalies, etc.)
            self.emit_built_event(step, builder_result)

    def _flush_clustered_step(self) -> None:
        """Flush accumulated clustered events as batch events."""
        if not self._clustering_buffer:
            return
        
        step = self._clustering_current_step
        
        # Process PAIRING_FAILED events into PAIRING_BATCH
        if "PAIRING_FAILED" in self._clustering_buffer:
            failed_pairings = self._clustering_buffer["PAIRING_FAILED"]
            if failed_pairings:
                batch_result = self._build_pairing_batch_event(step, failed_pairings)
                self.emit_built_event(step, batch_result)
        
        # Clear clustering buffer
        self._clustering_buffer.clear()

    def _build_pairing_batch_event(self, step: int, failed_pairings: List[Dict[str, Any]]) -> tuple[str, Dict[str, Any], str]:
        """Build a PAIRING_BATCH event from multiple failed pairing attempts."""
        count = len(failed_pairings)
        
        # Aggregate statistics using correct field names from PAIRING events
        agent_ids = [p.get("a", p.get("agent_id", 0)) for p in failed_pairings]
        scan_counts = [p.get("scan", p.get("scanned", 0)) for p in failed_pairings]  
        eligible_counts = [p.get("elig", p.get("eligible", 0)) for p in failed_pairings]
        
        # Calculate aggregated rejection reasons
        rejection_counts = {}
        total_rejections = 0
        for pairing in failed_pairings:
            rejected_partners = pairing.get("rej", pairing.get("rejected_partners", []))
            for partner_data in rejected_partners:
                reason = partner_data.get("r", "unknown")
                rejection_counts[reason] = rejection_counts.get(reason, 0) + 1
                total_rejections += 1
        
        # Build compact summary
        compact = f"PAIRING_BATCH: step={step} failed={count} agents=[{min(agent_ids)}-{max(agent_ids)}] total_rej={total_rejections}"
        
        # Build detailed payload 
        payload = {
            "event": "failed_pairing_batch",
            "step": step,
            "failed_count": count,
            "agent_ids": sorted(agent_ids),
            "aggregate_stats": {
                "total_scan": sum(scan_counts),
                "avg_scan": sum(scan_counts) / len(scan_counts) if scan_counts else 0,
                "total_eligible": sum(eligible_counts),
                "avg_eligible": sum(eligible_counts) / len(eligible_counts) if eligible_counts else 0,
            },
            "rejection_breakdown": rejection_counts,
            "total_rejections": total_rejections,
            "educational_note": f"Batch of {count} failed pairing attempts showing common rejection patterns"
        }
        
        return compact, payload, "PAIRING_BATCH"

    def build_trade_intent_funnel(
        self,
        drafted: int,
        pruned_micro: int,
        pruned_nonpositive: int,
        executed: int,
        max_delta_u: float,
        agent_pairs: Optional[list[tuple[int, int]]] = None,
    ) -> tuple[str, Dict[str, Any], str]:
        """Trade intent enumeration funnel summary for a step."""
        category = "TRADE"
        compact = (
            f"TI: drafted={drafted} pruned_micro={pruned_micro} pruned_nonpositive={pruned_nonpositive} "
            f"executed={executed} maxΔU={max_delta_u:.3f}"
        )
        payload: Dict[str, Any] = {
            "event": "trade_intent_funnel",
            "drafted": drafted,
            "pruned_micro": pruned_micro,
            "pruned_nonpositive": pruned_nonpositive,
            "executed": executed,
            "max_delta_u": round(max_delta_u, 6),
        }
        
        # Phase 3.1: Continue causal chains for failed trade executions
        if agent_pairs and executed == 0:  # Failed to execute any trades
            for agent1, agent2 in agent_pairs:
                correlation_id = self.get_correlation_for_agents(agent1, agent2)
                if correlation_id:
                    self.add_to_causal_chain(
                        correlation_id,
                        "trade_intent_draft", 
                        0.0,  # ts_offset
                        agent_give=agent1,
                        agent_take=agent2,
                        max_delta_u=max_delta_u
                    )
                    
                    # Determine failure reason
                    if pruned_nonpositive > 0:
                        reason = "nonpositive_utility" 
                        educational_note = "Demonstrates utility calculation vs execution reality - theoretical gains may not materialize"
                    elif pruned_micro > 0:
                        reason = "micro_delta_threshold"
                        educational_note = "Shows how small utility gains are filtered to prevent noise trades"
                    else:
                        reason = "unknown"
                        educational_note = "Trade intent created but not executed"
                        
                    self.add_to_causal_chain(
                        correlation_id,
                        "trade_execution_result",
                        0.015,  # small offset
                        success=False,
                        reason=reason
                    )
                    
                    self.finalize_causal_chain(
                        correlation_id,
                        "failed_exchange",
                        educational_note
                    )
        
        return compact, payload, category

    def build_trade_intent_none(self, cause: str) -> tuple[str, Dict[str, Any], str]:
        category = "TRADE"
        compact = f"TI: none ({cause})"
        payload: Dict[str, Any] = {"event": "trade_intent_none", "cause": cause}
        return compact, payload, category

    def build_trade_intent_none_executed(self, reason: str, drafted: int) -> tuple[str, Dict[str, Any], str]:
        category = "TRADE"
        compact = f"TI: none_executed reason={reason} drafted={drafted}"
        payload: Dict[str, Any] = {
            "event": "trade_intent_none_executed",
            "reason": reason,
            "drafted": drafted,
        }
        return compact, payload, category

    def build_stagnation_trigger(
        self,
        agent_id: int,
        threshold: int,
        last_improve_step: int,
        action: str,
        deposit: bool,
    ) -> tuple[str, Dict[str, Any], str]:
        category = "STAGNATION"
        deposit_fragment = " deposit" if deposit else ""
        compact = (
            f"STAG: A{agent_id:03d} threshold={threshold} last_improve={last_improve_step} "
            f"action={action}{deposit_fragment}"
        )
        payload: Dict[str, Any] = {
            "event": "stagnation_trigger",
            "agent": agent_id,
            "threshold": threshold,
            "last_improve": last_improve_step,
            "action": action,
            "deposit": deposit,
        }
        return compact, payload, category

    def build_selection_sample(
        self,
        step: int,
        resource_candidates: List[Dict[str, Any]],
        partner_candidates: List[Dict[str, Any]],
        total_agents: int,
        active_agents: int,
    ) -> tuple[str, Dict[str, Any], str]:
        """Selection ranking sample for multiple agents.

        Args:
            step: Current simulation step.
            resource_candidates: List of resource candidates with agent info.
            partner_candidates: List of partner candidates with agent info.
            total_agents: Total number of agents in simulation.
            active_agents: Number of agents with current tasks.
        """
        category = "DECISIONS"
        
        # Build compact representation
        frag_parts: List[str] = []
        
        # Add resource candidates
        for i, rc in enumerate(resource_candidates[:3]):  # Top 3 resources
            agent_id = rc.get("agent_id", -1)
            pos = rc.get("pos", (0, 0))
            score = rc.get("score", 0.0)
            delta_u = rc.get("delta_u", 0.0)
            if isinstance(pos, (list, tuple)) and len(pos) == 2:
                frag_parts.append(f"R{i+1}:A{agent_id:03d}@({pos[0]},{pos[1]}) s={score:.2f} ΔU={delta_u:.2f}")
            else:
                frag_parts.append(f"R{i+1}:A{agent_id:03d} s={score:.2f} ΔU={delta_u:.2f}")
        
        # Add partner candidates  
        for i, pc in enumerate(partner_candidates[:3]):  # Top 3 partners
            agent_id = pc.get("agent_id", -1)
            partner_id = pc.get("partner_id", -1)
            score = pc.get("score", 0.0)
            delta_u = pc.get("delta_u", 0.0)
            frag_parts.append(f"P{i+1}:A{agent_id:03d}→A{partner_id:03d} s={score:.2f} ΔU={delta_u:.2f}")
        
        compact = f"SEL: step={step} active={active_agents}/{total_agents} " + " ".join(frag_parts)
        
        payload: Dict[str, Any] = {
            "event": "selection_sample",
            "step": step,
            "resource_candidates": resource_candidates,
            "partner_candidates": partner_candidates,
            "total_agents": total_agents,
            "active_agents": active_agents,
        }
        return compact, payload, category

    def build_respawn_cycle(
        self,
        step: int,
        current_count: int,
        target_count: int,
        current_density: float,
        target_density: float,
        deficit: int,
    ) -> tuple[str, Dict[str, Any], str]:
        category = "RESOURCES"
        compact = (
            f"RESP: step={step} current={current_count} target={target_count} "
            f"density={current_density:.3f}/{target_density:.3f} deficit={deficit}"
        )
        payload: Dict[str, Any] = {
            "event": "respawn_cycle",
            "step": step,
            "current_count": current_count,
            "target_count": target_count,
            "current_density": current_density,
            "target_density": target_density,
            "deficit": deficit,
        }
        return compact, payload, category

    def build_respawn_skipped(self, step: int, reason: str) -> tuple[str, Dict[str, Any], str]:
        category = "RESOURCES"
        compact = f"RESP: step={step} skipped ({reason})"
        payload: Dict[str, Any] = {
            "event": "respawn_skipped",
            "step": step,
            "reason": reason,
        }
        return compact, payload, category

    def build_target_churn(
        self,
        step: int,
        total_retargets: int,
        active_agents: int,
        retarget_data: list[dict],
        window_size: int,
    ) -> tuple[str, Dict[str, Any], str]:
        category = "DECISIONS"
        top_agent_id = retarget_data[0]["agent_id"] if retarget_data else 0
        top_agent_events = retarget_data[0]["retarget_count"] if retarget_data else 0
        
        compact = (
            f"CHURN: step={step} window={window_size} retarget_events={total_retargets} distinct_agents={active_agents} "
            f"top_agent=A{top_agent_id:03d} count={top_agent_events}"
        )
        payload: Dict[str, Any] = {
            "event": "target_churn",
            "step": step,
            "window": window_size,
            "retarget_events": total_retargets,
            "distinct_agents": active_agents,
            "top_agent_id": top_agent_id,
            "top_agent_events": top_agent_events,
            "retarget_data": retarget_data,
        }
        return compact, payload, category

    def build_perf_spike(
        self,
        step: int,
        time_ms: float,
        rolling_mean_ms: float,
        agents: int,
        resources: int,
        phase: Optional[int] = None,
    ) -> tuple[str, Dict[str, Any], str]:
        """Performance spike detection event."""
        category = "PERF"
        phase_fragment = f" phase={phase}" if phase is not None else ""
        compact = (
            f"PERF: spike step={step} time={time_ms:.1f}ms mean={rolling_mean_ms:.1f}ms "
            f"agents={agents} resources={resources}{phase_fragment}"
        )
        payload: Dict[str, Any] = {
            "event": "perf_spike",
            "step": step,
            "time_ms": round(time_ms, 1),
            "rolling_mean_ms": round(rolling_mean_ms, 1),
            "agents": agents,
            "resources": resources,
        }
        if phase is not None:
            payload["phase"] = phase
        return compact, payload, category

    def build_overlay_state(
        self,
        grid: bool,
        ids: bool,
        arrows: bool,
        trades: bool,
        highlight: bool,
    ) -> tuple[str, Dict[str, Any], str]:
        category = "SIMULATION"
        compact = (
            f"OVL: grid={'on' if grid else 'off'} ids={'on' if ids else 'off'} arrows={'on' if arrows else 'off'} "
            f"trades={'on' if trades else 'off'} highlight={'on' if highlight else 'off'}"
        )
        payload: Dict[str, Any] = {
            "event": "overlay_state",
            "grid": grid,
            "ids": ids,
            "arrows": arrows,
            "trades": trades,
            "highlight": highlight,
        }
        return compact, payload, category
    
    def _format_simulation_time(self, step: Optional[int] = None) -> str:
        """Format elapsed wall clock time since simulation start.
        
        Args:
            step: Optional simulation step number (unused, kept for compatibility)
            
        Returns:
            Formatted time string with 1 decimal place (e.g., "+12.3s")
        """
        # If simulation hasn't started yet, return zero time
        if self._simulation_start_time is None:
            return "+0.0s"
        
        # Always use wall clock time elapsed since simulation start
        elapsed_seconds = (datetime.now() - self._simulation_start_time).total_seconds()
        return f"+{elapsed_seconds:.1f}s"

    def _relative_seconds(self) -> float:
        """Return elapsed wall clock time (float seconds) since simulation start."""
        if self._simulation_start_time is None:
            return 0.0
        return (datetime.now() - self._simulation_start_time).total_seconds()

    # ---------------- Structured Logging Helpers -----------------
    def _emit_structured(self, category: str, step: Optional[int], payload: Dict[str, Any]) -> str:
        """Build a structured JSONL line for a logging event with standardized envelope.

        Core JSON formatting method that creates the structured log format used throughout
        the VMT logging system. All events pass through this method for consistent
        formatting and timestamp injection.

        Args:
            category: Event category for filtering/routing ("TRADE", "PAIRING", "SIMULATION", etc.)
            step: Simulation step number (None for non-simulation events, -1 converted to null)
            payload: Event-specific data dictionary to be merged with envelope

        Returns:
            Complete JSONL line string with trailing newline for immediate file writing

        Envelope Structure:
            All structured lines share a minimal standardized envelope:
            - ts_rel: float seconds since session start (3 decimal precision)
            - category: original category token for filtering/analysis
            - step: simulation step number (null for non-simulation events)
            - event: semantic event type (from payload or inferred)
            - [payload fields]: Event-specific data merged after envelope

        Field Semantics:
            - Step normalization: -1 sentinel → null, positive integers preserved
            - Timestamp precision: 3 decimal places (millisecond precision)
            - Key ordering: Deterministic via Python 3.7+ insertion order preservation
            - Payload override: Payload fields can override envelope fields if needed

        Performance:
            O(1) JSON serialization with compact separators for efficient storage.
            Uses json.dumps with separators=(",", ":") for minimal file size.

        Thread Safety:
            Pure function with no side effects. Thread-safe for concurrent calls.
        """
        # Normalize step field semantics: -1 sentinel -> null, positive integers preserved
        normalized_step = None if step == -1 else step
        
        data: Dict[str, Any] = {
            "ts_rel": round(self._relative_seconds(), 3),
            "category": category,
            "step": normalized_step,
        }
        # Ensure deterministic key ordering for readability (Python 3.7+ preserves insertion)
        # Merge payload after envelope so payload can override (event, etc.)
        data.update(payload)
        return json.dumps(data, separators=(",", ":")) + "\n"

    def _parse_mode_transition(self, message: str) -> Dict[str, Any]:
        import re
        # Support both formats used internally
        m1 = re.search(r'Agent_(\d+) switched from (\w+) to (\w+)(.*)$', message)
        m2 = re.search(r'Agent (\d+) mode: (\w+) -> (\w+)(.*)$', message)
        result: Dict[str, Any] = {"event": "mode_transition"}
        match = m1 or m2
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
                
                # Extract reason from parentheses
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
                    result["target"] = {"x": int(target_match.group(1)), "y": int(target_match.group(2))}
                
                # Only include raw context if no structured fields were extracted at all
                if not (reason_match or carry_match or target_match):
                    result["context"] = context
        else:
            # Fallback to raw message if parsing fails
            result["raw"] = message
        return result

    def _parse_utility(self, message: str) -> Dict[str, Any]:
        import re
        # Pattern: Agent_005 utility: 4.2 → 4.8 (Δ+0.600) (reason?) - explanation
        m = re.search(r'Agent_(\d+) utility: ([0-9.]+) → ([0-9.]+) \(Δ([+\-][0-9.]+)\)(.*)', message)
        data: Dict[str, Any] = {"event": "utility_change", "raw": message}
        if m:
            agent_id, old_u, new_u, delta, tail = m.groups()
            data.update({
                "agent": int(agent_id),
                "old": float(old_u),
                "new": float(new_u),
                "delta": float(delta),
            })
            # Reason detection before optional explanation dash
            reason_match = None
            if tail:
                reason_match = re.search(r'\(([^(]*?)\)', tail)
            if reason_match:
                data["reason"] = reason_match.group(1).strip()
        return data

    def _parse_trade(self, message: str) -> Dict[str, Any]:
        import re
        data: Dict[str, Any] = {"event": "trade", "raw": message}
        # New style: Trade: A001↔A009 bread→fish (Δ+0.10, Δ+0.08)
        m_new = re.search(r'Trade: A(\d+)↔A(\d+) (\w+)→(\w+) \(Δ([+\-][0-9.]+), Δ([+\-][0-9.]+)\)', message)
        if m_new:
            a1, a2, give, receive, d1, d2 = m_new.groups()
            data.update({
                "agent1": int(a1),
                "agent2": int(a2),
                "give": give,
                "receive": receive,
                "delta_agent1": float(d1),
                "delta_agent2": float(d2)
            })
            return data
        # Older style: Agent_001 gives bread to Agent_009; receives fish ... utility: +0.123
        m_old = re.search(r'Agent_(\d+) gives (\w+) to Agent_(\d+); receives (\w+).*?utility: ([+\-]?[0-9.]+)', message)
        if m_old:
            a1, give, a2, receive, combined = m_old.groups()
            data.update({
                "agent1": int(a1),
                "agent2": int(a2),
                "give": give,
                "receive": receive,
                "combined_delta": float(combined)
            })
            return data
        # Bundled compact variant already parsed earlier – leave raw
        return data

    def _parse_periodic_summary(self, message: str) -> Dict[str, Any]:
        import re
        # 123.4 steps/sec | Frame: 8.1ms | Agents: 20 | Resources: 120 | Phase: 3
        m = re.search(r'([0-9.]+) steps/sec \| Frame: ([0-9.]+)ms \| Agents: (\d+) \| Resources: (\d+)(?: \| Phase: (\d+))?', message)
        data: Dict[str, Any] = {"event": "periodic_summary", "raw": message}
        if m:
            steps_sec, frame_ms, agents, resources, phase = m.groups()
            data.update({
                "steps_per_sec": float(steps_sec),
                "frame_ms": float(frame_ms),
                "agents": int(agents),
                "resources": int(resources)
            })
            if phase is not None:
                data["phase"] = int(phase)
        return data

    def _parse_phase(self, message: str) -> Dict[str, Any]:
        import re
        m = re.search(r'Phase (\d+) start \(Turn (\d+)\): (.+)', message)
        data: Dict[str, Any] = {"event": "phase_transition", "raw": message}
        if m:
            phase, turn, desc = m.groups()
            data.update({"phase": int(phase), "turn": int(turn), "description": desc})
        return data

    def _parse_perf(self, message: str) -> Dict[str, Any]:
        import re
        # Performance Analysis, Entity Counts, Bottleneck
        data: Dict[str, Any] = {"event": "performance", "raw": message}
        pa = re.search(r'Performance Analysis: FPS=([0-9.]+).*?Step=([0-9.]+)ms.*?Render=([0-9.]+)ms', message)
        if pa:
            fps, step_ms, render_ms = pa.groups()
            data.update({"fps": float(fps), "step_ms": float(step_ms), "render_ms": float(render_ms)})
            return data
        ec = re.search(r'Entity Counts: Agents=(\d+), Resources=(\d+)', message)
        if ec:
            a, r = ec.groups()
            data.update({"entity_counts": {"agents": int(a), "resources": int(r)}})
            return data
        if 'Bottleneck:' in message:
            data.update({"bottleneck": message.split('Bottleneck:')[-1].strip()})
        return data
    


    def log(self, category: str, message: str, step: Optional[int] = None) -> None:
        """Log a debug message with timestamp and category.
        
        DEPRECATED: This method is deprecated in favor of the observer pattern.
        Use specific event types with FileObserver and EducationalObserver instead.
        
        Args:
            category: Type of message (e.g., "AGENT_MODE", "TRADE", "SIMULATION")
            message: The debug message
            step: Optional simulation step number
        """
        # Route to observer system if available
        if self._observer_system_enabled and self._legacy_adapter:
            try:
                self._legacy_adapter.log(category, message, step)
            except Exception:
                pass  # Fall back to legacy implementation
        
        # Skip logging if session has been finalized or level filtering
        if self.is_finalized() or not self._should_log_category(category):
            return
        
        # Special handling for trade+utility bundling (Phase 3.1)
        if os.environ.get("ECONSIM_LOG_BUNDLE_TRADES") == "1" and category in ("TRADE", "UTILITY"):
            self._buffer_trade_bundle(category, message, step)
            return
            
        # Special handling for trade aggregation (structured output)
        if category == "TRADE":
            self._buffer_trade(message, step)
            return
        
        # Special handling for agent mode transition batching to prevent spam
        if category in ("AGENT_MODE", "MODE"):
            # Extract agent info for batching
            import re
            match1 = re.search(r'Agent_(\d+) switched from (\w+) to (\w+)(.*)$', message)
            match2 = re.search(r'Agent (\d+) mode: (\w+) -> (\w+)(.*)$', message)
            if match1:
                agent_id, old_mode, new_mode, context = match1.groups()
                context = context.strip() if context else ""
                self._buffer_agent_transition(format_agent_id(int(agent_id)), old_mode, new_mode, context, step)
                return
            elif match2:
                agent_id, old_mode, new_mode, context = match2.groups()
                context = context.strip() if context else ""
                self._buffer_agent_transition(format_agent_id(int(agent_id)), old_mode, new_mode, context, step)
                return
        # Structured-only logging path
        payload = self._build_structured_payload(category, message)
        structured = self._emit_structured(category, step, payload)
        self._write_structured_line(structured)
    
    def emit_built_event(self, step: Optional[int], builder_result: tuple[str, Dict[str, Any], str]) -> None:
        """Emit a pre-built structured event with automatic buffering and formatting.
        
        Central emission point for all structured logging events. Handles automatic
        JSON formatting, timestamp injection, and intelligent buffering based on
        event category and system load.
        
        Args:
            step: Simulation step number (None for non-simulation events)
            builder_result: Pre-built event tuple from build_*() methods containing:
                - compact_line: Human-readable display format (unused in current implementation)
                - structured_payload: Complete event data dictionary  
                - category: Event classification for routing/filtering
                
        Automatic Processing:
            - Injects relative timestamp (seconds since session start)
            - Normalizes step field (-1 → null, preserves positive integers)
            - Routes to appropriate buffer based on category
            - Applies clustering logic for volume-sensitive events (PAIRING)
            - Handles immediate vs deferred emission based on system load
            
        Buffering Strategy:
            - TRADE events: Buffered by step for aggregation
            - PAIRING events: Clustered for volume reduction
            - SIMULATION events: Immediate emission
            - BEHAVIOR events: Deferred emission on flush cycles
            
        Thread Safety:
            Thread-safe via internal locking. Safe for concurrent calls.
            
        Performance:
            O(1) for most events, O(log n) for events requiring sorted buffers.
            Automatic buffer flushing prevents memory accumulation.
        """
        if self.is_finalized():
            return
        try:
            _, payload, category = builder_result  # compact_line no longer needed
        except Exception:
            return
        
        # Check if we should log this category
        if not self._should_log_category(category):
            return
            
        # Structured-only output for builders
        try:
            structured_line = self._emit_structured(category, step, payload)
            self._write_structured_line(structured_line)
        except Exception:
            pass

    def log_agent_mode(self, agent_id: int, old_mode: str, new_mode: str, reason: str = "", step: Optional[int] = None) -> None:
        """Log agent mode transitions.
        
        DEPRECATED: This method is deprecated in favor of the observer pattern.
        Use AgentModeChangeEvent with FileObserver and EducationalObserver instead.
        """
        # Route to observer system if available
        if self._observer_system_enabled and self._legacy_adapter:
            try:
                self._legacy_adapter.log_agent_mode(agent_id, old_mode, new_mode, reason, step)
            except Exception:
                pass  # Fall back to legacy implementation
        
        # Legacy implementation for backward compatibility
        reason_str = f" ({reason})" if reason else ""
        message = f"Agent {agent_id} mode: {old_mode} -> {new_mode}{reason_str}"
        self.log("AGENT_MODE", message, step)
    
    # ---------------- Testing Helpers ----------------
    def recent_structured_events(self) -> list[dict[str, Any]]:
        try:
            return list(self._structured_ring)  # type: ignore[attr-defined]
        except Exception:
            return []
    
    def finalize_session(self) -> None:
        """Write session end marker and prevent further logging.
        
        DEPRECATED: This method is deprecated in favor of the observer pattern.
        Use observer cleanup methods instead.
        """
        # Close observer system if enabled
        if self._observer_system_enabled and self._legacy_adapter:
            try:
                self._legacy_adapter.finalize_session()
            except Exception:
                pass  # Continue with legacy cleanup
        
        # Legacy cleanup - flush any remaining buffered trades and transitions
        self._flush_trade_buffer()
        self._flush_transition_buffer()
        self._flush_bundle_buffer()
        
        # Flush any remaining PAIRING accumulator data
        self._flush_pairing_step()
        
        # Write structured session end marker if log was initialized
        if self._log_initialized:
            payload = {
                "event": "session_end",
                "timestamp": datetime.now().isoformat()
            }
            structured = self._emit_structured("SESSION", None, payload)
            self._write_structured_line(structured)
            self._flush_structured_buffer_to_disk()

        # Mark logger as finalized to prevent further logging
        self._finalized = True
    
    def is_finalized(self) -> bool:
        """Check if the logger session has been finalized."""
        return getattr(self, '_finalized', False)
    
    def should_log_performance(self, step: int, steps_per_sec: float) -> bool:
        """Check if performance should be logged based on step interval and rate changes."""
        # Use enhanced configuration if available
        if _has_log_config:
            try:
                from .log_config import get_log_config
                config = get_log_config()
                return config.should_log_performance(step, steps_per_sec, self._last_steps_per_sec)
            except Exception:  # pragma: no cover
                pass  # Fall back to original logic
                
        # Original logic as fallback
        if self.log_level == LogLevel.VERBOSE:
            return True  # Always log in verbose mode
        
        # Log every 25 steps in PERIODIC mode
        if self.log_level == LogLevel.PERIODIC:
            if step % 25 == 0:
                return True
            # Also log if significant performance change (>10%)
            if abs(steps_per_sec - self._last_steps_per_sec) / max(self._last_steps_per_sec, 1) > 0.1:
                self._last_steps_per_sec = steps_per_sec
                return True
        
        return False
    
    def log_trade(self, message: str, step: Optional[int] = None) -> None:
        """Log trade-related debug information."""
        self.log("TRADE", message, step)
    
    def log_simulation(self, message: str, step: Optional[int] = None) -> None:
        """Log general simulation debug information."""
        self.log("SIMULATION", message, step)
    
    def get_current_log_path(self) -> Optional[Path]:
        """Get path to current log file for GUI reading (legacy method, returns structured log path)."""
        if not self._log_initialized:
            return None
        return self.structured_log_path
    
    def get_structured_log_path(self) -> Optional[Path]:
        """Get path to current structured log file for GUI reading."""
        if not self._log_initialized:
            return None
        return self.structured_log_path


# Convenience functions for global access
def get_gui_logger() -> GUILogger:
    """Get the singleton GUI logger instance."""
    return GUILogger.get_instance()


def log_agent_mode(agent_id: int, old_mode: str, new_mode: str, reason: str = "", step: Optional[int] = None) -> None:
    """Log agent mode transition."""
    if os.environ.get("ECONSIM_DEBUG_AGENT_MODES") == "1":
        get_gui_logger().log_agent_mode(agent_id, old_mode, new_mode, reason, step)


def log_trade(message: str, step: Optional[int] = None) -> None:
    """Log trade debug information."""
    if os.environ.get("ECONSIM_DEBUG_TRADES") == "1":
        get_gui_logger().log_trade(message, step)


def log_simulation(message: str, step: Optional[int] = None) -> None:
    """Log simulation debug information."""
    if os.environ.get("ECONSIM_DEBUG_SIMULATION") == "1":
        get_gui_logger().log_simulation(message, step)


def log_phase_transition(phase: int, turn: int, description: str) -> None:
    """Log phase transition events."""
    if os.environ.get("ECONSIM_DEBUG_PHASES") == "1":
        builder_result = get_gui_logger().build_phase_transition(phase, turn, description)
        get_gui_logger().emit_built_event(turn, builder_result)


def log_agent_decision(agent_id: int, decision_type: str, details: str, step: Optional[int] = None) -> None:
    """Log agent decision-making details."""
    if os.environ.get("ECONSIM_DEBUG_DECISIONS") == "1":
        get_gui_logger().log_simulation(f"Agent {agent_id} {decision_type}: {details}", step)


def log_resource_event(event_type: str, position: tuple[int, int], resource_type: str, agent_id: Optional[int] = None, step: Optional[int] = None) -> None:
    """Log resource-related events (pickup, deposit, spawn)."""
    if os.environ.get("ECONSIM_DEBUG_RESOURCES") == "1":
        agent_info = f" by Agent {agent_id}" if agent_id is not None else ""
        get_gui_logger().log_simulation(f"Resource {event_type}: {resource_type} at {position}{agent_info}", step)


def log_performance(message: str, step: Optional[int] = None) -> None:
    """Log performance metrics (steps/sec, frame timing)."""
    if os.environ.get("ECONSIM_DEBUG_PERFORMANCE") == "1":
        # Extract steps/sec for conditional logging
        import re
        match = re.search(r'([0-9.]+) steps/sec', message)
        steps_per_sec = float(match.group(1)) if match else 0.0
        
        logger = get_gui_logger()
        if step is None or logger.should_log_performance(step, steps_per_sec):
            # Use PERIODIC_PERF category for filtering
            category = "PERIODIC_PERF" if logger.log_level == LogLevel.PERIODIC else "PERF"
            logger.log(category, message, step)


def log_trade_detail(agent1_id: int, resource1: str, agent2_id: int, resource2: str, utility_change: Optional[float] = None, step: Optional[int] = None) -> None:
    """Log formatted trade details with agent IDs and resources."""
    if os.environ.get("ECONSIM_DEBUG_TRADES") == "1":
        utility_str = f" (Δ{utility_change:+.2f})" if utility_change is not None else ""
        message = f"Trade: {format_agent_id(agent1_id)} gives {resource1} to {format_agent_id(agent2_id)}; receives {resource2}{utility_str}"
        
        # Phase 3.1: Continue causal chain if correlation exists
        logger = get_gui_logger()
        correlation_id = logger.get_correlation_for_agents(agent1_id, agent2_id)
        if correlation_id:
            logger.add_to_causal_chain(
                correlation_id,
                "trade_execution_result",
                0.0,  # ts_offset - would need actual timing
                success=True,
                agent_give=agent1_id,
                agent_take=agent2_id,
                goods=[resource1, resource2],
                utility_change=utility_change
            )
            logger.finalize_causal_chain(
                correlation_id,
                "successful_exchange",
                "Demonstrates successful bilateral trade with mutual utility gain"
            )
        
        # Phase 3.2: Track utility gains for behavior aggregation
        if utility_change is not None and step is not None:
            # Assuming equal utility gain for both agents (could be refined with actual per-agent gains)
            half_utility = utility_change / 2.0
            logger.track_agent_utility_gain(step, agent1_id, half_utility)
            logger.track_agent_utility_gain(step, agent2_id, half_utility)
        
        logger.log("TRADE", message, step)


def log_enhanced_trade(agent1_id: int, resource1: str, agent1_utility_gain: float,
                      agent2_id: int, resource2: str, agent2_utility_gain: float, 
                      step: Optional[int] = None) -> None:
    """Log trade with educational explanations."""
    if os.environ.get("ECONSIM_DEBUG_TRADES") == "1":
        message = f"Trade: {format_agent_id(agent1_id)}↔{format_agent_id(agent2_id)} {resource1}→{resource2} (Δ{agent1_utility_gain:+.2f}, Δ{agent2_utility_gain:+.2f})"
        
        # Phase 3.2: Track individual utility gains for behavior aggregation
        if step is not None:
            logger = get_gui_logger()
            logger.track_agent_utility_gain(step, agent1_id, agent1_utility_gain)
            logger.track_agent_utility_gain(step, agent2_id, agent2_utility_gain)
        
        # Add educational explanation if enabled
        if _has_educational_logging:
            try:
                from .log_utils import should_add_educational_context, explain_trade_decision
                if should_add_educational_context():
                    explanation = explain_trade_decision(agent1_utility_gain, agent2_utility_gain, resource1, resource2)
                    message += f" - {explanation}"
            except Exception:  # pragma: no cover
                pass  # Fall back to basic message
                
        get_gui_logger().log("TRADE", message, step)


def log_periodic_summary(steps_per_sec: float, frame_ms: float, agent_count: int, resource_count: int, phase: Optional[int], step: int) -> None:
    """Log unified periodic summary using structured builder (eliminates raw text redundancy)."""
    logger = get_gui_logger()
    if step % 25 == 0 or logger.should_log_performance(step, steps_per_sec):
        # Use structured builder instead of formatted string + parsing
        builder_result = logger.build_periodic_summary(steps_per_sec, frame_ms, agent_count, resource_count, phase)
        logger.emit_built_event(step, builder_result)


def log_mode_switch(agent_id: int, old_mode: str, new_mode: str, context: str = "", step: Optional[int] = None) -> None:
    """Log agent mode transitions with context.""" 
    if os.environ.get("ECONSIM_DEBUG_AGENT_MODES") == "1":
        context_str = f" {context}" if context else ""
        message = f"Agent_{agent_id:03d} switched from {old_mode} to {new_mode}{context_str}"
        get_gui_logger().log("MODE", message, step)


def log_economics(message: str, step: Optional[int] = None) -> None:
    """Log economic metrics (utility changes, trade volume, market efficiency)."""
    if os.environ.get("ECONSIM_DEBUG_ECONOMICS") == "1":
        get_gui_logger().log("ECON", message, step)


def log_spatial(message: str, step: Optional[int] = None) -> None:
    """Log spatial analytics (clustering, movement patterns, density)."""
    if os.environ.get("ECONSIM_DEBUG_SPATIAL") == "1":
        get_gui_logger().log("SPATIAL", message, step)


def log_utility_change(agent_id: int, old_utility: float, new_utility: float, reason: str = "", step: Optional[int] = None, good_type: str = "") -> None:
    """Log agent utility changes from trades or other economic events."""
    if os.environ.get("ECONSIM_DEBUG_ECONOMICS") == "1":
        delta = new_utility - old_utility
        reason_str = f" ({reason})" if reason else ""
        message = f"Agent_{agent_id:03d} utility: {old_utility:.1f} → {new_utility:.1f} (Δ{format_delta(delta)}){reason_str}"
        
        # Add educational explanation if enabled
        if _has_educational_logging:
            try:
                if should_add_educational_context():
                    explanation = explain_utility_change(old_utility, new_utility, reason, good_type)
                    message += f" - {explanation}"
            except Exception:  # pragma: no cover
                pass  # Fall back to basic message
                
        get_gui_logger().log("UTILITY", message, step)


def log_comprehensive(message: str, step: Optional[int] = None) -> None:
    """Log general debug information (always enabled when any debug flag is set)."""
    debug_flags = [
        "ECONSIM_DEBUG_AGENT_MODES", "ECONSIM_DEBUG_TRADES", "ECONSIM_DEBUG_SIMULATION",
        "ECONSIM_DEBUG_PHASES", "ECONSIM_DEBUG_DECISIONS", "ECONSIM_DEBUG_RESOURCES",
        "ECONSIM_DEBUG_PERFORMANCE", "ECONSIM_DEBUG_ECONOMICS", "ECONSIM_DEBUG_SPATIAL"
    ]
    if any(os.environ.get(flag) == "1" for flag in debug_flags):
        logger = get_gui_logger()
        
        # Filter out verbose START/END markers
        if "SIMULATION STEP" in message and ("START" in message or "END" in message):
            return  # Skip these noisy markers
        
        # Use PERIODIC_SIM for step summaries in periodic mode
        if step is not None and "Agents:" in message and "Resources:" in message:
            # In VERBOSE level we emit every summary (no throttling)
            if logger.log_level == LogLevel.VERBOSE:
                category = "SIMULATION"
            else:
                # Throttle summaries for non-VERBOSE modes
                if logger.log_level == LogLevel.PERIODIC:
                    if step % 25 == 0:
                        category = "PERIODIC_SIM"
                    else:
                        return
                else:
                    category = "SIMULATION"
        else:
            category = "SIMULATION"
            
        logger.log(category, message, step)


def log_performance_analysis(fps: float, step_time: float, render_time: float, 
                           agent_count: int, resource_count: int, 
                           step: Optional[int] = None) -> None:
    """Log comprehensive performance analysis with bottleneck identification."""
    logger = get_gui_logger()
    
    if _has_enhanced_config:
        try:
            from .log_config import get_log_manager
            config = get_log_manager().config
            performance_logging = getattr(config, 'log_performance_details', False)
            perf_thresholds = getattr(config, 'performance_thresholds', {})
            fps_threshold = perf_thresholds.get('fps', 30.0) if perf_thresholds else 30.0
            step_threshold = perf_thresholds.get('step_time', 0.02) if perf_thresholds else 0.02
        except Exception:  # pragma: no cover
            performance_logging = os.environ.get("ECONSIM_DEBUG_PERFORMANCE") == "1"
            fps_threshold = 30.0
            step_threshold = 0.02
    else:
        performance_logging = os.environ.get("ECONSIM_DEBUG_PERFORMANCE") == "1"
        fps_threshold = 30.0
        step_threshold = 0.02
    
    if performance_logging:
        # Basic performance metrics
        fps_warning = " ⚠️" if fps < fps_threshold else ""
        step_warning = " ⚠️" if step_time > step_threshold else ""
        
        message = f"Performance Analysis: FPS={fps:.1f}{fps_warning}, Step={step_time*1000:.1f}ms{step_warning}, Render={render_time*1000:.1f}ms"
        logger.log("PERF", message, step)
        
        # Entity counts
        if agent_count > 100 or resource_count > 200:
            entity_warning = " ⚠️"
        else:
            entity_warning = ""
        message = f"Entity Counts: Agents={agent_count}, Resources={resource_count}{entity_warning}"
        logger.log("PERF", message, step)
        
        # Bottleneck identification
        render_ratio = render_time / step_time if step_time > 0 else 0
        if render_ratio > 0.7:
            logger.log("PERF", "Bottleneck: Rendering consuming >70% of frame time", step)
        elif step_time - render_time > 0.01:
            logger.log("PERF", "Bottleneck: Simulation logic taking significant time", step)


def finalize_log_session() -> None:
    """Finalize the current logging session to prevent further logging noise.
    
    Call this when a test or simulation session completes to mark the end
    of useful logging data and prevent cleanup/exit noise from being recorded.
    """
    get_gui_logger().finalize_session()
