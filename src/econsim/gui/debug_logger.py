"""Centralized GUI debug logging system for VMT EconSim.

Provides unified logging to timestamped files in gui_logs/ directory.
All debug output from simulation components should use this logging system
instead of direct print statements for better organization and GUI integration.

Environment Variables:
    ECONSIM_LOG_LEVEL: Controls verbosity (CRITICAL|EVENTS|PERIODIC|VERBOSE) [default: EVENTS]
    ECONSIM_LOG_FORMAT: Output format (COMPACT|STRUCTURED|LEGACY) [default: LEGACY]

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


class LogLevel(Enum):
    """Logging verbosity levels."""
    CRITICAL = "CRITICAL"
    EVENTS = "EVENTS" 
    PERIODIC = "PERIODIC"
    VERBOSE = "VERBOSE"


class LogFormat(Enum):
    """Log output formats."""
    COMPACT = "COMPACT"
    STRUCTURED = "STRUCTURED"
    LEGACY = "LEGACY"


class GUILogger:
    """Centralized debug logger for GUI simulation components."""
    
    _instance: Optional["GUILogger"] = None
    _lock = threading.Lock()
    
    def __init__(self) -> None:
        if GUILogger._instance is not None:
            raise RuntimeError("GUILogger is a singleton. Use get_instance() instead.")
        
        # Parse environment configuration
        level_str = os.environ.get("ECONSIM_LOG_LEVEL", "EVENTS").upper()
        format_str = os.environ.get("ECONSIM_LOG_FORMAT", "LEGACY").upper()
        
        try:
            self.log_level = LogLevel(level_str)
        except ValueError:
            self.log_level = LogLevel.EVENTS  # Safe default
        
        try:
            self.log_format = LogFormat(format_str)
        except ValueError:
            self.log_format = LogFormat.LEGACY  # Safe default
            
        # Performance tracking for conditional logging
        self._last_perf_log_step = 0
        self._last_steps_per_sec = 0.0
        
        # Trade aggregation buffer for grouping trades by step
        self._trade_buffer: dict[int, list[str]] = {}
        self._last_trade_step = -1
        
        # Create logs directory if it doesn't exist (at project root)
        self.logs_dir = Path(__file__).parent.parent.parent.parent / "gui_logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Generate timestamped filename and track session start
        now = datetime.now()
        self._session_start = now  # Track start time for relative timestamps
        timestamp = now.strftime("%Y-%m-%d %H-%M-%S")
        self.log_filename = f"{timestamp} GUI.log"
        self.log_path = self.logs_dir / self.log_filename
        
        # Initialize log file
        self._write_header()
    
    @classmethod
    def get_instance(cls) -> "GUILogger":
        """Get singleton instance of GUILogger."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _write_header(self) -> None:
        """Write log file header with session information."""
        with open(self.log_path, 'w', encoding='utf-8') as f:
            f.write(f"VMT EconSim GUI Debug Log\n")
            f.write(f"Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Log Level: {self.log_level.value} | Format: {self.log_format.value}\n")
            f.write("=" * 50 + "\n\n")
    
    def _should_log_category(self, category: str) -> bool:
        """Check if a message category should be logged at current level."""
        if self.log_level == LogLevel.VERBOSE:
            # In verbose mode, log everything except when COMPACT format filters some noise
            return True
        elif self.log_level == LogLevel.PERIODIC:
            return category in ["CRITICAL", "ERROR", "WARNING", "PHASE", "TRADE", "UTILITY", "MODE", "PERIODIC_PERF", "PERIODIC_SIM", "PERF", "SIMULATION"]
        elif self.log_level == LogLevel.EVENTS:
            return category in ["CRITICAL", "ERROR", "WARNING", "PHASE", "TRADE", "UTILITY", "MODE"]
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
                    trade_summaries = []
                    for trade in trades:
                        import re
                        match = re.search(r'Agent_(\d+).*?Agent_(\d+)', trade)
                        if match:
                            agent1, agent2 = match.groups()
                            trade_summaries.append(f"A{agent1}↔A{agent2}")
                    if trade_summaries:
                        aggregated = f"S{step} T: {', '.join(trade_summaries)}\n"
                        self._write_to_file(aggregated)
                else:
                    # Log each trade individually in legacy format
                    for trade in trades:
                        formatted = self._format_message("TRADE", trade, step)
                        self._write_to_file(formatted)
        
        self._trade_buffer.clear()
    
    def _write_to_file(self, formatted_message: str) -> None:
        """Write formatted message to log file."""
        with self._lock:
            try:
                with open(self.log_path, 'a', encoding='utf-8') as f:
                    f.write(formatted_message)
                    f.flush()
            except Exception:
                pass
    
    def _format_message(self, category: str, message: str, step: Optional[int] = None) -> str:
        """Format message according to current format setting."""
        # Calculate relative timestamp for compact format
        if self.log_format == LogFormat.COMPACT:
            relative_seconds = (datetime.now() - self._session_start).total_seconds()
            timestamp_prefix = f"+{relative_seconds:.1f}s"
            step_info = f"S{step}" if step is not None else ""
            if category == "MODE" or "AGENT_MODE" in category:
                # Compact format: +12.3s A002: home→forage c1 @(9,14)  
                import re
                # Handle both "Agent_X switched from Y to Z" and "Agent X mode: Y -> Z" formats
                match1 = re.search(r'Agent_(\d+) switched from (\w+) to (\w+)', message)
                match2 = re.search(r'Agent (\d+) mode: (\w+) -> (\w+)', message)
                if match1:
                    agent_id, old_mode, new_mode = match1.groups()
                    # Extract carrying and target info if present
                    carry_match = re.search(r'carrying: (\d+)', message)
                    target_match = re.search(r'target: \((\d+), (\d+)\)', message)
                    carry_str = f" c{carry_match.group(1)}" if carry_match else ""
                    target_str = f" @({target_match.group(1)},{target_match.group(2)})" if target_match else ""
                    return f"{timestamp_prefix} {step_info} A{agent_id}: {old_mode}→{new_mode}{carry_str}{target_str}\n"
                elif match2:
                    agent_id, old_mode, new_mode = match2.groups()
                    # Extract reason if present (in parentheses at end)
                    reason_match = re.search(r'\(([^)]+)\)$', message)
                    reason_str = f" ({reason_match.group(1)})" if reason_match else ""
                    return f"{timestamp_prefix} {step_info} A{agent_id}: {old_mode}→{new_mode}{reason_str}\n"
            elif category == "PERF":
                # Compact format: +12.3s P: 124.7s/s 5.1ms R122
                import re
                match = re.search(r'([0-9.]+) steps/sec.*?([0-9.]+)ms.*?Resources: (\d+)', message)
                if match:
                    steps_sec, frame_ms, resources = match.groups()
                    return f"{timestamp_prefix} {step_info} P: {steps_sec}s/s {frame_ms}ms R{resources}\n"
            elif category == "TRADE" and "gives" in message and "receives" in message:
                # Compact format: +12.3s T: A001↔A009 g2→g1 +0.1
                import re
                match = re.search(r'Agent_(\d+) gives (\w+) to Agent_(\d+); receives (\w+).*?utility: \+([0-9.-]+)', message)
                if match:
                    agent1, give, agent2, receive, utility = match.groups()
                    return f"{timestamp_prefix} {step_info} T: A{agent1}↔A{agent2} {give}→{receive} +{utility}\n"
            elif category == "UTILITY":
                # Compact format: +12.3s U: A001 4.42→4.34 Δ-0.08 (trade)
                import re
                match = re.search(r'Agent_(\d+) utility: ([0-9.]+) → ([0-9.]+) \(Δ([+-][0-9.]+)\)(.*)', message)
                if match:
                    agent_id, old_util, new_util, delta, reason = match.groups()
                    reason_str = reason.strip(' ()') if reason.strip() else ""
                    reason_str = f" ({reason_str})" if reason_str else ""
                    return f"{timestamp_prefix} {step_info} U: A{agent_id} {old_util}→{new_util} Δ{delta}{reason_str}\n"
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
        
        # LEGACY format (default) - need timestamp for this case
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        step_info = f" [Step {step}]" if step is not None else ""
        return f"[{timestamp}]{step_info} {category}: {message}\n"

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
        
        # Special handling for trade aggregation
        if category == "TRADE" and self.log_format == LogFormat.COMPACT:
            self._buffer_trade(message, step)
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
        # Flush any remaining buffered trades
        self._flush_trade_buffer()
        
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
    
    def get_current_log_path(self) -> Path:
        """Get path to current log file for GUI reading."""
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
        utility_str = f" (utility: +{utility_change:.1f})" if utility_change is not None else ""
        message = f"Agent_{agent1_id:03d} gives {resource1} to Agent_{agent2_id:03d}; receives {resource2} in exchange{utility_str}"
        get_gui_logger().log("TRADE", message, step)


def log_mode_switch(agent_id: int, old_mode: str, new_mode: str, context: str = "", step: Optional[int] = None) -> None:
    """Log agent mode transitions with context.""" 
    if os.environ.get("ECONSIM_DEBUG_AGENT_MODES") == "1":
        context_str = f" ({context})" if context else ""
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


def log_utility_change(agent_id: int, old_utility: float, new_utility: float, reason: str = "", step: Optional[int] = None) -> None:
    """Log agent utility changes from trades or other economic events."""
    if os.environ.get("ECONSIM_DEBUG_ECONOMICS") == "1":
        delta = new_utility - old_utility
        sign = "+" if delta >= 0 else ""
        reason_str = f" ({reason})" if reason else ""
        message = f"Agent_{agent_id:03d} utility: {old_utility:.2f} → {new_utility:.2f} (Δ{sign}{delta:.2f}){reason_str}"
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
                category = "SIMULATION"  # Log all summaries in legacy verbose mode
        else:
            category = "SIMULATION"
            
        logger.log(category, message, step)


def finalize_log_session() -> None:
    """Finalize the current logging session to prevent further logging noise.
    
    Call this when a test or simulation session completes to mark the end
    of useful logging data and prevent cleanup/exit noise from being recorded.
    """
    get_gui_logger().finalize_session()