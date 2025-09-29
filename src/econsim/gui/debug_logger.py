"""Centralized GUI debug logging system for VMT EconSim.

Provides unified logging to timestamped files in gui_logs/ directory.
All debug output from simulation components should use this logging system
instead of direct print statements for better organization and GUI integration.

Environment Variables:
    ECONSIM_LOG_LEVEL: Controls verbosity (CRITICAL|EVENTS|PERIODIC|VERBOSE) [default: EVENTS]
    ECONSIM_LOG_FORMAT: Output format (COMPACT|STRUCTURED) [default: COMPACT]
    ECONSIM_LOG_BUNDLE_TRADES: Bundle trade+utility logs into single line [default: 0]

Logging Levels:
    CRITICAL: Only errors, warnings, phase transitions
    EVENTS: + trades, utility changes, mode switches  
    PERIODIC: + step summaries every 25 steps, performance windows
    VERBOSE: Everything (classic behavior)
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict, List, Sequence, Iterable
import threading
from enum import Enum

# Import enhanced configuration system (safely)
try:  # type: ignore
    from .log_config import LogLevel, LogFormat, get_log_config  # type: ignore  # noqa: F401
    _get_log_config_ref = get_log_config  # touch to avoid unused import warnings
    _has_log_config = True
except Exception:  # pragma: no cover
    _has_log_config = False
    class LogLevel(Enum):  # fallback
        CRITICAL = "CRITICAL"
        EVENTS = "EVENTS"
        PERIODIC = "PERIODIC"
        VERBOSE = "VERBOSE"
    class LogFormat(Enum):  # fallback
        COMPACT = "COMPACT"
        STRUCTURED = "STRUCTURED"

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
    """Centralized debug logger for GUI simulation components."""
    
    _instance: Optional["GUILogger"] = None
    _lock = threading.Lock()
    
    def __init__(self) -> None:
        if GUILogger._instance is not None:
            raise RuntimeError("GUILogger is a singleton. Use get_instance() instead.")
        
        # Parse environment configuration
        # Default elevated to VERBOSE so a fresh run (no env var set) surfaces
        # all available debug events in both compact and structured logs.
        level_str = os.environ.get("ECONSIM_LOG_LEVEL", "VERBOSE").upper()
        format_str = os.environ.get("ECONSIM_LOG_FORMAT", "COMPACT").upper()
        
        try:
            self.log_level = LogLevel(level_str)
        except ValueError:
            self.log_level = LogLevel.EVENTS  # Safe default
        
        try:
            self.log_format = LogFormat(format_str)
        except ValueError:
            self.log_format = LogFormat.COMPACT  # Safe default
            
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
        """Initialize log file when simulation first starts."""
        if self._log_initialized:
            return
            
        # Set simulation start time to now (when first simulation step begins)
        now = datetime.now()
        self._simulation_start_time = now
        
        # Generate timestamped filenames
        timestamp = now.strftime("%Y-%m-%d %H-%M-%S")
        self.log_filename = f"{timestamp} GUI.log"
        self.log_path = self.logs_dir / self.log_filename
        # Structured JSONL side-channel
        structured_dir = self.logs_dir / "structured"
        structured_dir.mkdir(parents=True, exist_ok=True)
        self.structured_log_path = structured_dir / f"{timestamp} GUI.jsonl"  # type: ignore[attr-defined]

        # Write human-readable header
        with open(self.log_path, 'w', encoding='utf-8') as f:
            f.write("VMT EconSim GUI Debug Log\n")
            f.write(f"Session started: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Log Level: {self.log_level.value} | Format: {self.log_format.value}\n")
            f.write("=" * 50 + "\n\n")

        # Write structured metadata record (first JSON line)
        try:
            meta: Dict[str, Any] = {
                "schema": 1,
                "session_started": now.isoformat(timespec='seconds'),
                "log_level": self.log_level.value,
                "selected_format": self.log_format.value,
            }
            with open(self.structured_log_path, 'w', encoding='utf-8') as sf:  # type: ignore[attr-defined]
                sf.write(json.dumps(meta, separators=(",", ":")) + "\n")
        except Exception:
            pass

        self._log_initialized = True
    
    def _write_header(self) -> None:
        """Deprecated method - now handled by _initialize_log_file."""
        pass
    
    def _should_log_category(self, category: str) -> bool:
        """Check if a message category should be logged at current level."""
        # Normalize legacy/extended category aliases
        original_category = category
        if category == "TRADES":  # builder uses plural, core filters expect singular
            category = "TRADE"
        elif category == "PERFORMANCE":  # treat as PERF for filtering purposes
            category = "PERF"
        # Use enhanced configuration if available
        if _has_log_config:
            try:
                from .log_config import get_log_config
                config = get_log_config()
                # Pass normalized; if config relies on original raw category ensure fallback
                if hasattr(config, 'should_log_category'):
                    try:
                        return bool(config.should_log_category(category)) or bool(config.should_log_category(original_category))  # type: ignore[attr-defined]
                    except Exception:
                        return config.should_log_category(category)
                return True
            except Exception:  # pragma: no cover
                pass  # Fall back to original logic
                
        # Original logic as fallback
        if self.log_level == LogLevel.VERBOSE:
            # In verbose mode, log everything except when COMPACT format filters some noise
            return True
        elif self.log_level == LogLevel.PERIODIC:
            return category in [
                "CRITICAL", "ERROR", "WARNING",
                "PHASE", "TRADE", "UTILITY", "MODE",
                "PERIODIC_PERF", "PERIODIC_SIM", "PERF", "SIMULATION",
                # Newly introduced categories (Phase 3) - permit periodic visibility
                "PAIRING", "STAGNATION"
            ]
        elif self.log_level == LogLevel.EVENTS:
            return category in [
                "CRITICAL", "ERROR", "WARNING",
                "PHASE", "TRADE", "UTILITY", "MODE", "SIMULATION",
                # Show partner search + stagnation triggers at EVENTS (they are rare/educational)
                "PAIRING", "STAGNATION"
            ]
        elif self.log_level == LogLevel.CRITICAL:
            return category in ["CRITICAL", "ERROR", "WARNING", "PHASE"]
        return False

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

        Compact log may aggregate; structured log always receives per-trade records.
        """
        if not self._trade_buffer:
            return

        for step, trades in self._trade_buffer.items():
            # Always emit structured records (per trade)
            for trade in trades:
                payload = self._parse_trade(trade)
                structured = self._emit_structured("TRADE", step, payload)
                self._write_structured_line(structured)

            # Human-readable compact aggregation (only if compact selected)
            if self.log_format == LogFormat.COMPACT:
                if len(trades) == 1:
                    formatted = self._format_message("TRADE", trades[0], step)
                    self._write_to_file(formatted)
                else:
                    trade_summaries: list[str] = []
                    for trade in trades:
                        import re
                        match = re.search(r'(?:Agent_|A)(\d+).*?(?:Agent_|A)(\d+)', trade)
                        if match:
                            agent1, agent2 = match.groups()
                            trade_summaries.append(f"{format_agent_id(int(agent1))}↔{format_agent_id(int(agent2))}")
                    if trade_summaries:
                        timestamp_prefix = self._format_simulation_time(step)
                        aggregated = f"{timestamp_prefix} S{step} T: {', '.join(trade_summaries)}\n"
                        self._write_to_file(aggregated)

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
        """Flush buffered agent transitions, batching similar ones for compact output.

        Structured log always receives individual or batch records irrespective of compact formatting.
        """
        if not self._agent_transition_buffer:
            return

        for step, transitions in self._agent_transition_buffer.items():
            transition_groups: dict[tuple[str, str], list[tuple[str, str]]] = {}
            for agent_id, old_mode, new_mode, context in transitions:
                key = (old_mode, new_mode)
                transition_groups.setdefault(key, []).append((agent_id, context))

            timestamp_prefix = self._format_simulation_time(step)
            # step from buffer keys is always an int (may be -1 sentinel)
            step_info = f"S{step}" if step >= 0 else ""

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

                # Compact human-readable output
                if self.log_format == LogFormat.COMPACT:
                    if len(agent_context_pairs) == 1:
                        agent_id, context = agent_context_pairs[0]
                        import re
                        reason_match = re.search(r'^\s*(\([^)]+\))', context) if context else None
                        reason_str = f" {reason_match.group(1)}" if reason_match else ""
                        carry_match = re.search(r'carrying: (\d+)', context) if context else None
                        target_match = re.search(r'target: \((\d+), (\d+)\)', context) if context else None
                        carry_str = f" c{carry_match.group(1)}" if carry_match else ""
                        target_str = f" @({target_match.group(1)},{target_match.group(2)})" if target_match else ""
                        formatted = f"{timestamp_prefix} {agent_id}: {old_mode}→{new_mode}{reason_str}{carry_str}{target_str}\n"
                        self._write_to_file(formatted)
                    else:
                        agent_ids_compact = [agent_id for agent_id, _ in agent_context_pairs]
                        if len(agent_ids_compact) <= 5:
                            agents_list = ",".join(agent_ids_compact)
                            formatted = f"{timestamp_prefix} {step_info} BATCH M: {len(agent_ids_compact)} agents {old_mode}→{new_mode} ids=[{agents_list}]\n"
                        else:
                            formatted = f"{timestamp_prefix} {step_info} BATCH M: {len(agent_ids_compact)} agents {old_mode}→{new_mode}\n"
                        self._write_to_file(formatted)

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
    
    def _write_to_file(self, formatted_message: str) -> None:
        """Write formatted message to log file."""
        # Ensure log file is initialized before writing
        if not self._log_initialized:
            self._initialize_log_file()
        
        with self._lock:
            try:
                assert self.log_path is not None  # Should be set by _initialize_log_file
                with open(self.log_path, 'a', encoding='utf-8') as f:
                    f.write(formatted_message)
                    f.flush()
            except Exception:
                pass

    def _write_structured_line(self, structured_line: str) -> None:
        """Write a structured JSONL line to the structured side-channel file."""
        if not self._log_initialized:
            self._initialize_log_file()
        with self._lock:
            try:
                with open(self.structured_log_path, 'a', encoding='utf-8') as sf:  # type: ignore[attr-defined]
                    sf.write(structured_line)
                    sf.flush()
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

    def build_perf_spike(self, step: int, time_ms: float, rolling_mean_ms: float, agents: int, resources: int, phase: Optional[int]) -> tuple[str, Dict[str, Any], str]:
        # Canonical category token (was PERFORMANCE, now PERF to match filtering & avoid normalization)
        category = "PERF"
        phase_part = f" phase={phase}" if phase is not None else ""
        compact = f"PERF_SPIKE: step={step} time={time_ms:.1f}ms mean={rolling_mean_ms:.1f}ms agents={agents} resources={resources}{phase_part}"
        payload: Dict[str, Any] = {
            "event": "perf_spike",
            "step": step,
            "time_ms": round(time_ms, 3),
            "rolling_mean_ms": round(rolling_mean_ms, 3),
            "agents": agents,
            "resources": resources,
        }
        if phase is not None:
            payload["phase"] = phase
        return compact, payload, category

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
    ) -> tuple[str, Dict[str, Any], str]:
        """Partner search summary (successful selection).

        Returns:
            tuple(compact_line, structured_payload, category)
        """
        category = "PAIRING"
        compact = (
            f"PS: A{agent_id:03d} scanned={scanned} eligible={eligible} "
            f"chosen=A{chosen_id:03d} method={method} cooldowns(g={cooldown_global},p={cooldown_partner})"
        )
        payload: Dict[str, Any] = {
            "event": "partner_search",
            "agent": agent_id,
            "scanned": scanned,
            "eligible": eligible,
            "chosen": chosen_id,
            "method": method,
            "cooldowns": {"global": cooldown_global, "partner": cooldown_partner},
        }
        return compact, payload, category

    def build_partner_reject(
        self,
        agent_id: int,
        candidate_id: int,
        reason: str,
        sampled: bool,
    ) -> tuple[str, Dict[str, Any], str]:
        """Partner rejection sample (only emitted when sampled)."""
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

    def build_trade_intent_funnel(
        self,
        drafted: int,
        pruned_micro: int,
        pruned_nonpositive: int,
        executed: int,
        max_delta_u: float,
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
        agent_id: int,
        k: float,
        candidates: Sequence[Dict[str, Any]],
        top_n: int = 3,
    ) -> tuple[str, Dict[str, Any], str]:
        """Selection ranking sample.

        Args:
            agent_id: Agent sampled.
            k: distance scaling factor.
            candidates: iterable of candidate dicts with keys described in plan.
            top_n: truncate candidate count in compact line (structured keeps all).
        """
        category = "DECISIONS"
        shown: List[Dict[str, Any]] = list(candidates)[:top_n]  # type: ignore[arg-type]
        frag_parts: List[str] = []
        for c in shown:
            ctype = c.get("type")  # type: ignore[assignment]
            d = c.get("d")  # type: ignore[assignment]
            du = c.get("delta_u")  # type: ignore[assignment]
            dud = c.get("delta_u_discounted")  # type: ignore[assignment]
            if ctype == "RESOURCE":
                pos = c.get("pos")  # type: ignore[assignment]
                if isinstance(pos, (list, tuple)) and len(pos) == 2 and isinstance(du, (int, float)) and isinstance(dud, (int, float)):  # type: ignore[arg-type]
                    frag = f"R@({pos[0]},{pos[1]}) d={d} ΔU={du:.2f} ΔU'={dud:.2f}"
                else:
                    frag = f"R d={d}"
            elif ctype == "TRADE":
                partner = c.get("partner")  # type: ignore[assignment]
                if isinstance(partner, int) and isinstance(du, (int, float)) and isinstance(dud, (int, float)):
                    frag = f"TRADE(A{partner:03d}) d={d} ΔU={du:.2f} ΔU'={dud:.2f}"
                elif isinstance(partner, int):
                    frag = f"TRADE(A{partner:03d}) d={d}"
                else:
                    frag = f"TRADE d={d}"
            else:
                frag = "?"
            frag_parts.append(frag)
        cand_compact = ", ".join(frag_parts)
        compact = f"USAMP: A{agent_id:03d} k={k:g} cand=[{cand_compact}]"
        payload: Dict[str, Any] = {
            "event": "selection_sample",
            "agent": agent_id,
            "k": k,
            "candidates": list(candidates),  # preserve provided order & detail
        }
        return compact, payload, category

    def build_respawn_cycle(
        self,
        step: int,
        deficit: int,
        target_density: float,
        planned: int,
        placed: int,
        remaining: int,
    ) -> tuple[str, Dict[str, Any], str]:
        category = "RESOURCES"
        compact = (
            f"RESP: step={step} deficit={deficit} target_density={target_density:g} "
            f"plan={planned} placed={placed} remaining={remaining}"
        )
        payload: Dict[str, Any] = {
            "event": "respawn_cycle",
            "step": step,
            "deficit": deficit,
            "target_density": target_density,
            "planned": planned,
            "placed": placed,
            "remaining": remaining,
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
        window: int,
        retarget_events: int,
        distinct_agents: int,
        top_agent_id: int,
        top_agent_events: int,
    ) -> tuple[str, Dict[str, Any], str]:
        category = "DECISIONS"
        compact = (
            f"CHURN: window={window} retarget_events={retarget_events} distinct_agents={distinct_agents} "
            f"top_agent=A{top_agent_id:03d} count={top_agent_events}"
        )
        payload: Dict[str, Any] = {
            "event": "target_churn",
            "window": window,
            "retarget_events": retarget_events,
            "distinct_agents": distinct_agents,
            "top_agent_id": top_agent_id,
            "top_agent_events": top_agent_events,
        }
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
        """Build a structured JSON line for a logging event.

        All structured lines share a minimal envelope:
            ts_rel: float seconds since session start
            category: original category token
            step: simulation step (may be null)
            event: semantic event type (payload should include or we infer)
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
    
    def _format_message(self, category: str, message: str, step: Optional[int] = None) -> str:
        """Format message according to current format setting."""
        # Calculate simulation timestamp for compact format
        if self.log_format == LogFormat.COMPACT:
            timestamp_prefix = self._format_simulation_time(step)
            step_info = f"S{step}" if step is not None else ""
            if category == "MODE" or "AGENT_MODE" in category:
                # Compact format: +12.3s A002: home→forage c1 @(9,14)  
                import re
                # Handle both "Agent_X switched from Y to Z" and "Agent X mode: Y -> Z" formats
                match1 = re.search(r'Agent_(\d+) switched from (\w+) to (\w+)(.*)$', message)
                match2 = re.search(r'Agent (\d+) mode: (\w+) -> (\w+)', message)
                if match1:
                    agent_id, old_mode, new_mode, context = match1.groups()
                    # Extract reason if present (in parentheses at beginning of context)
                    reason_match = re.search(r'^\s*(\([^)]+\))', context) if context else None
                    reason_str = f" {reason_match.group(1)}" if reason_match else ""
                    # Extract carrying and target info if present
                    carry_match = re.search(r'carrying: (\d+)', context) if context else None
                    target_match = re.search(r'target: \((\d+), (\d+)\)', context) if context else None
                    carry_str = f" c{carry_match.group(1)}" if carry_match else ""
                    target_str = f" @({target_match.group(1)},{target_match.group(2)})" if target_match else ""
                    return f"{timestamp_prefix} {step_info} {format_agent_id(int(agent_id))}: {old_mode}→{new_mode}{reason_str}{carry_str}{target_str}\n"
                elif match2:
                    agent_id, old_mode, new_mode = match2.groups()
                    # Extract reason if present (in parentheses at end)
                    reason_match = re.search(r'\(([^)]+)\)$', message)
                    reason_str = f" ({reason_match.group(1)})" if reason_match else ""
                    return f"{timestamp_prefix} {step_info} {format_agent_id(int(agent_id))}: {old_mode}→{new_mode}{reason_str}\n"
            elif category == "PERF" or category == "PERIODIC_PERF" or category == "SIMULATION":
                # Compact format: +12.3s P: 124.7s/s 5.1ms A20 R122 Ph1 (with phase) or A20 R122 (without phase)  
                import re
                # Try unified format with phase first
                match = re.search(r'([0-9.]+) steps/sec.*?([0-9.]+)ms.*?Agents: (\d+).*?Resources: (\d+).*?Phase: (\d+)', message)
                if match:
                    steps_sec, frame_ms, agents, resources, phase = match.groups()
                    return f"{timestamp_prefix} {step_info} P: {steps_sec}s/s {frame_ms}ms A{agents} R{resources} Ph{phase}\n"
                # Try unified format without phase
                match = re.search(r'([0-9.]+) steps/sec.*?([0-9.]+)ms.*?Agents: (\d+).*?Resources: (\d+)', message)
                if match:
                    steps_sec, frame_ms, agents, resources = match.groups()
                    return f"{timestamp_prefix} {step_info} P: {steps_sec}s/s {frame_ms}ms A{agents} R{resources}\n"
                # Fallback for old format (just performance data)
                match = re.search(r'([0-9.]+) steps/sec.*?([0-9.]+)ms.*?Resources: (\d+)', message)
                if match:
                    steps_sec, frame_ms, resources = match.groups()
                    return f"{timestamp_prefix} {step_info} P: {steps_sec}s/s {frame_ms}ms R{resources}\n"
            elif category == "TRADE" and "gives" in message and "receives" in message:
                # Compact format: +12.3s T: A001↔A009 g2→g1 +0.1
                import re
                match = re.search(r'Agent_(\d+) gives (\w+) to Agent_(\d+); receives (\w+).*?utility: ([+-]?[0-9.-]+)', message)
                if match:
                    agent1, give, agent2, receive, utility = match.groups()
                    return f"{timestamp_prefix} {step_info} T: A{agent1}↔A{agent2} {give}→{receive} {format_delta(float(utility))}\n"
            elif category == "UTILITY":
                # Compact format: +12.3s U: A001 4.42→4.34 Δ-0.08 (trade)
                import re
                match = re.search(r'Agent_(\d+) utility: ([0-9.]+) → ([0-9.]+) \(Δ([+-][0-9.]+)\)(.*)', message)
                if match:
                    agent_id, old_util, new_util, delta, reason = match.groups()
                    reason_str = reason.strip(' ()') if reason.strip() else ""
                    reason_str = f" ({reason_str})" if reason_str else ""
                    return f"{timestamp_prefix} {step_info} U: {format_agent_id(int(agent_id))} {old_util}→{new_util} Δ{delta}{reason_str}\n"
            elif category == "PHASE":
                # Compact format: +12.3s PHASE2@201: Forage only
                import re
                match = re.search(r'Phase (\d+) start \(Turn (\d+)\): (.+)', message)
                if match:
                    phase_num, turn, description = match.groups()
                    # Shorten common descriptions
                    desc = description.replace("Only foraging enabled", "Forage only") \
                                    .replace("Only exchange enabled", "Exchange only") \
                                    .replace("Both foraging and exchange enabled", "Both enabled") \
                                    .replace("Both disabled - agents should idle", "Both disabled")
                    return f"{timestamp_prefix} PHASE{phase_num}@{turn}: {desc}\n"
            # Fallback for other categories in COMPACT format
            clean_message = message
            # For PERIODIC_SIM category, clean up the message
            if category == "PERIODIC_SIM":
                clean_message = message.replace("Agents:", "Agents:").replace("Resources:", "R:").replace("Decision Mode:", "Decision:")
            # Format the prefix properly - avoid just ":" when no step
            prefix_part = step_info if step_info else category.split('_')[0][:3]  # Use first 3 chars of category if no step
            return f"{timestamp_prefix} {prefix_part}: {clean_message}\n"
        elif self.log_format == LogFormat.STRUCTURED:
            # Attempt semantic parsing per category for JSON payload
            payload: Dict[str, Any]
            if category in ("MODE", "AGENT_MODE"):
                payload = self._parse_mode_transition(message)
            elif category == "UTILITY":
                payload = self._parse_utility(message)
            elif category == "TRADE":
                payload = self._parse_trade(message)
            elif category in ("SIMULATION", "PERIODIC_SIM"):
                if "steps/sec | Frame" in message:
                    payload = self._parse_periodic_summary(message)
                else:
                    payload = {"event": "simulation", "raw": message}
            elif category == "PHASE":
                payload = self._parse_phase(message)
            elif category in ("PERF", "PERIODIC_PERF"):
                payload = self._parse_perf(message)
            else:
                payload = {"event": category.lower(), "raw": message}
            return self._emit_structured(category, step, payload)
        
        # Fallback to COMPACT format for any unknown format
        timestamp_prefix = self._format_simulation_time(step)
        step_info = f"S{step}" if step is not None else ""
        clean_message = message
        prefix_part = step_info if step_info else category.split('_')[0][:3]
        return f"{timestamp_prefix} {prefix_part}: {clean_message}\n"

    def log(self, category: str, message: str, step: Optional[int] = None) -> None:
        """Log a debug message with timestamp and category.
        
        Args:
            category: Type of message (e.g., "AGENT_MODE", "TRADE", "SIMULATION")
            message: The debug message
            step: Optional simulation step number
        """
        # Skip logging if session has been finalized or level filtering
        if self.is_finalized() or not self._should_log_category(category):
            return
        
        # Special handling for trade+utility bundling (Phase 3.1)
        if os.environ.get("ECONSIM_LOG_BUNDLE_TRADES") == "1" and category in ("TRADE", "UTILITY"):
            self._buffer_trade_bundle(category, message, step)
            return
            
        # Special handling for trade aggregation (compact human readable only)
        if category == "TRADE" and self.log_format == LogFormat.COMPACT:
            self._buffer_trade(message, step)
            return
        
        # Special handling for agent mode transition batching to prevent spam
        if category in ("AGENT_MODE", "MODE") and self.log_format == LogFormat.COMPACT:
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
        # Normal immediate write path
        formatted_message = self._format_message(category, message, step)
        if self.log_format == LogFormat.COMPACT:
            self._write_to_file(formatted_message)
            # Also emit structured side-channel
            payload = self._build_structured_payload(category, message)
            structured = self._emit_structured(category, step, payload)
            self._write_structured_line(structured)
        else:  # STRUCTURED primary mode already returns JSON text; write to both files
            self._write_to_file(formatted_message)  # JSON in primary log too (unchanged behavior if selected)
            self._write_structured_line(formatted_message)
    
    def emit_built_event(self, step: Optional[int], builder_result: tuple[str, Dict[str, Any], str]) -> None:
        """Emit a pre-built (compact, structured) event tuple.

        Always writes structured side-channel; compact path respects category filtering.
        Safe no-op if finalized or category disabled.
        """
        if self.is_finalized():
            return
        try:
            compact_line, payload, category = builder_result
        except Exception:
            return
        
        # Check if we should log this category
        if not self._should_log_category(category):
            return
            
        # Structured output first (always for builders)
        try:
            structured_line = self._emit_structured(category, step, payload)
            self._write_structured_line(structured_line)
        except Exception:
            pass
            
        # Compact emission - write directly to avoid duplicate structured processing
        try:
            formatted_compact = self._format_message(category, compact_line, step)
            self._write_to_file(formatted_compact)
        except Exception:
            pass

    def log_agent_mode(self, agent_id: int, old_mode: str, new_mode: str, reason: str = "", step: Optional[int] = None) -> None:
        """Log agent mode transitions."""
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
        """Write session end marker and prevent further logging."""
        # Flush any remaining buffered trades and transitions
        self._flush_trade_buffer()
        self._flush_transition_buffer()
        self._flush_bundle_buffer()
        
        # Only write end marker if log was actually initialized
        if self._log_initialized and self.log_path is not None:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            end_message = f"[{timestamp}] SESSION: === LOG SESSION ENDED ===\n"
            
            with self._lock:
                try:
                    with open(self.log_path, 'a', encoding='utf-8') as f:
                        f.write(end_message)
                        f.flush()
                except Exception:
                    pass
        
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
        """Get path to current log file for GUI reading."""
        if not self._log_initialized:
            return None
        return self.log_path


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
        get_gui_logger().log("TRADE", message, step)


def log_enhanced_trade(agent1_id: int, resource1: str, agent1_utility_gain: float,
                      agent2_id: int, resource2: str, agent2_utility_gain: float, 
                      step: Optional[int] = None) -> None:
    """Log trade with educational explanations."""
    if os.environ.get("ECONSIM_DEBUG_TRADES") == "1":
        message = f"Trade: {format_agent_id(agent1_id)}↔{format_agent_id(agent2_id)} {resource1}→{resource2} (Δ{agent1_utility_gain:+.2f}, Δ{agent2_utility_gain:+.2f})"
        
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
        
        # Filter out verbose START/END markers when using COMPACT format
        if "SIMULATION STEP" in message and ("START" in message or "END" in message):
            if logger.log_format == LogFormat.COMPACT:
                return  # Skip these noisy markers in compact mode
        
        # Use PERIODIC_SIM for step summaries when in compact format or periodic mode
        if step is not None and "Agents:" in message and "Resources:" in message:
            # In VERBOSE level we emit every summary (no throttling) regardless of format.
            if logger.log_level == LogLevel.VERBOSE:
                category = "SIMULATION"
            else:
                # Throttle summaries for non-VERBOSE modes or when compact readability matters
                if logger.log_format == LogFormat.COMPACT or logger.log_level == LogLevel.PERIODIC:
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