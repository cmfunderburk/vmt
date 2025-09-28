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
from datetime import datetime
from pathlib import Path
from typing import Optional
import threading
from enum import Enum

# Import enhanced configuration system
try:
    from .log_config import LogConfig, LogLevel, LogFormat, get_log_config
    _has_log_config = True
except ImportError:  # pragma: no cover
    _has_log_config = False
    # Fallback enum definitions when config module unavailable
    class LogLevel(Enum):
        CRITICAL = "CRITICAL"
        EVENTS = "EVENTS" 
        PERIODIC = "PERIODIC"
        VERBOSE = "VERBOSE"

    class LogFormat(Enum):
        COMPACT = "COMPACT"
        STRUCTURED = "STRUCTURED"

# Import educational context functions
try:
    from .log_utils import (
        explain_utility_change, explain_trade_decision, explain_agent_mode,
        explain_decision_logic, get_economic_context, 
        should_add_educational_context, should_explain_decisions
    )
    _has_educational_logging = True
except ImportError:  # pragma: no cover
    _has_educational_logging = False

try:
    from .log_config import get_log_manager
    _has_enhanced_config = True
except ImportError:  # pragma: no cover
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
        level_str = os.environ.get("ECONSIM_LOG_LEVEL", "EVENTS").upper()
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
    
    @classmethod
    def get_instance(cls) -> "GUILogger":
        """Get singleton instance of GUILogger."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    

    def _initialize_log_file(self) -> None:
        """Initialize log file when simulation first starts."""
        if self._log_initialized:
            return
            
        # Set simulation start time to now (when first simulation step begins)
        now = datetime.now()
        self._simulation_start_time = now
        
        # Generate timestamped filename
        timestamp = now.strftime("%Y-%m-%d %H-%M-%S")
        self.log_filename = f"{timestamp} GUI.log"
        self.log_path = self.logs_dir / self.log_filename
        
        # Write log file header
        with open(self.log_path, 'w', encoding='utf-8') as f:
            f.write(f"VMT EconSim GUI Debug Log\n")
            f.write(f"Session started: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Log Level: {self.log_level.value} | Format: {self.log_format.value}\n")
            f.write("=" * 50 + "\n\n")
        
        self._log_initialized = True
    
    def _write_header(self) -> None:
        """Deprecated method - now handled by _initialize_log_file."""
        pass
    
    def _should_log_category(self, category: str) -> bool:
        """Check if a message category should be logged at current level."""
        # Use enhanced configuration if available
        if _has_log_config:
            try:
                from .log_config import get_log_config
                config = get_log_config()
                return config.should_log_category(category)
            except Exception:  # pragma: no cover
                pass  # Fall back to original logic
                
        # Original logic as fallback
        if self.log_level == LogLevel.VERBOSE:
            # In verbose mode, log everything except when COMPACT format filters some noise
            return True
        elif self.log_level == LogLevel.PERIODIC:
            return category in ["CRITICAL", "ERROR", "WARNING", "PHASE", "TRADE", "UTILITY", "MODE", "PERIODIC_PERF", "PERIODIC_SIM", "PERF", "SIMULATION"]
        elif self.log_level == LogLevel.EVENTS:
            return category in ["CRITICAL", "ERROR", "WARNING", "PHASE", "TRADE", "UTILITY", "MODE", "SIMULATION"]
        elif self.log_level == LogLevel.CRITICAL:
            return category in ["CRITICAL", "ERROR", "WARNING", "PHASE"]
        return False
    
    def _buffer_trade(self, message: str, step: Optional[int]) -> None:
        """Buffer trade messages for potential aggregation."""
        if step is None:
            return
            
        # Flush previous step's trades if we've moved to a new step
        if step != self._last_trade_step and self._last_trade_step >= 0:
            self._flush_trade_buffer()
        
        # Add to current step's buffer
        if step not in self._trade_buffer:
            self._trade_buffer[step] = []
        self._trade_buffer[step].append(message)
        self._last_trade_step = step

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
        """Flush buffered trades, potentially aggregating them."""
        if not self._trade_buffer:
            return
            
        for step, trades in self._trade_buffer.items():
            if len(trades) == 1:
                # Single trade - log normally
                formatted = self._format_message("TRADE", trades[0], step)
                self._write_to_file(formatted)
            else:
                # Multiple trades - aggregate if compact format
                if self.log_format == LogFormat.COMPACT:
                    trade_summaries: list[str] = []
                    for trade in trades:
                        import re
                        # Match both "Agent_001" and "A001" formats
                        match = re.search(r'(?:Agent_|A)(\d+).*?(?:Agent_|A)(\d+)', trade)
                        if match:
                            agent1, agent2 = match.groups()
                            trade_summaries.append(f"{format_agent_id(int(agent1))}↔{format_agent_id(int(agent2))}")
                    if trade_summaries:
                        timestamp_prefix = self._format_simulation_time(step)
                        aggregated = f"{timestamp_prefix} S{step} T: {', '.join(trade_summaries)}\n"
                        self._write_to_file(aggregated)
                else:
                    # Log each trade individually in non-compact format
                    for trade in trades:
                        formatted = self._format_message("TRADE", trade, step)
                        self._write_to_file(formatted)
        
        self._trade_buffer.clear()

    def _flush_transition_buffer(self) -> None:
        """Flush buffered agent transitions, batching similar ones."""
        if not self._agent_transition_buffer:
            return
            
        for step, transitions in self._agent_transition_buffer.items():
            # Group transitions by (old_mode -> new_mode) pattern, but keep context for individuals
            transition_groups: dict[tuple[str, str], list[tuple[str, str]]] = {}  # (old, new) -> [(agent_id, context)]
            for agent_id, old_mode, new_mode, context in transitions:
                key = (old_mode, new_mode)
                if key not in transition_groups:
                    transition_groups[key] = []
                transition_groups[key].append((agent_id, context))
            
            # Log each group
            timestamp_prefix = self._format_simulation_time(step)
            step_info = f"S{step}" if step is not None else ""
            
            for (old_mode, new_mode), agent_context_pairs in transition_groups.items():
                if len(agent_context_pairs) == 1:
                    # Single transition - log with full context including reason
                    agent_id, context = agent_context_pairs[0]
                    if self.log_format == LogFormat.COMPACT:
                        # Parse context to extract reason, carrying, and target info
                        import re
                        reason_match = re.search(r'^\s*(\([^)]+\))', context) if context else None
                        reason_str = f" {reason_match.group(1)}" if reason_match else ""
                        carry_match = re.search(r'carrying: (\d+)', context) if context else None
                        target_match = re.search(r'target: \((\d+), (\d+)\)', context) if context else None
                        carry_str = f" c{carry_match.group(1)}" if carry_match else ""
                        target_str = f" @({target_match.group(1)},{target_match.group(2)})" if target_match else ""
                        formatted = f"{timestamp_prefix} {agent_id}: {old_mode}→{new_mode}{reason_str}{carry_str}{target_str}\n"
                    else:
                        # STRUCTURED format for non-compact modes
                        formatted = f"MODE|S{step}|Agent {agent_id} mode: {old_mode} -> {new_mode} {context}\n"
                    self._write_to_file(formatted)
                else:
                    # Multiple similar transitions - batch them with structured format
                    agent_ids = [agent_id for agent_id, _ in agent_context_pairs]
                    if self.log_format == LogFormat.COMPACT:
                        if len(agent_ids) <= 5:
                            # Small groups: include agent IDs in structured format
                            agents_list = ",".join(agent_ids)
                            formatted = f"{timestamp_prefix} {step_info} BATCH M: {len(agent_ids)} agents {old_mode}→{new_mode} ids=[{agents_list}]\n"
                        else:
                            # Large groups: show count only
                            formatted = f"{timestamp_prefix} {step_info} BATCH M: {len(agent_ids)} agents {old_mode}→{new_mode}\n"
                    else:
                        # STRUCTURED format for non-compact modes
                        formatted = f"MODE_BATCH|S{step}|{len(agent_ids)} agents {old_mode} -> {new_mode}\n"
                    self._write_to_file(formatted)
        
        # Clear buffers and reset deduplication (allow new cycles)
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
            agent_utilities = {}  # agent_id -> (old_util, new_util, delta)
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
                    step_info = f"S{step}" if step is not None and step >= 0 else ""
                    
                    # Base trade info
                    bundled = f"{timestamp_prefix} {step_info} T: {format_agent_id(seller_id)}↔{format_agent_id(buyer_id)} {give_type}→{recv_type} {format_delta(float(combined_delta))}"
                    
                    # Add utility details if available
                    utility_parts: list[str] = []
                    if seller_id in agent_utilities:
                        old_val, new_val, delta_val = agent_utilities[seller_id]
                        utility_parts.append(f"{format_agent_id(seller_id)}:{old_val}→{new_val} Δ{delta_val}")
                    if buyer_id in agent_utilities:
                        old_val, new_val, delta_val = agent_utilities[buyer_id]
                        utility_parts.append(f"{format_agent_id(buyer_id)}:{old_val}→{new_val} Δ{delta_val}")
                    
                    if utility_parts:
                        bundled += f" | U {'; '.join(utility_parts)}"
                    
                    bundled += "\n"
                    self._write_to_file(bundled)
        
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
            step_info = f"|S{step}" if step is not None else ""
            return f"{category}{step_info}|{message}\n"
        
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
            
        # Special handling for trade aggregation
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
            
        formatted_message = self._format_message(category, message, step)
        self._write_to_file(formatted_message)
    
    def log_agent_mode(self, agent_id: int, old_mode: str, new_mode: str, reason: str = "", step: Optional[int] = None) -> None:
        """Log agent mode transitions."""
        reason_str = f" ({reason})" if reason else ""
        message = f"Agent {agent_id} mode: {old_mode} -> {new_mode}{reason_str}"
        self.log("AGENT_MODE", message, step)
    
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
        get_gui_logger().log("PHASE", f"Phase {phase} start (Turn {turn}): {description}", turn)


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
    """Log unified periodic summary combining performance and status information."""
    logger = get_gui_logger()
    if step % 25 == 0 or logger.should_log_performance(step, steps_per_sec):
        # Use unified format: steps/sec | frame_ms | agent_count | resource_count | phase (if available)
        phase_str = f" | Phase: {phase}" if phase is not None else ""
        message = f"{steps_per_sec:.1f} steps/sec | Frame: {frame_ms:.1f}ms | Agents: {agent_count} | Resources: {resource_count}{phase_str}"
        # Use SIMULATION category to ensure visibility at EVENTS log level and above
        logger.log("SIMULATION", message, step)


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
            if logger.log_format == LogFormat.COMPACT or logger.log_level == LogLevel.PERIODIC:
                # Log every 25th step summary in compact/periodic modes
                if step % 25 == 0:
                    category = "PERIODIC_SIM"
                else:
                    return  # Skip intermediate step summaries
            else:
                category = "SIMULATION"  # Log all summaries in verbose mode
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