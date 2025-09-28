"""Launcher-specific logging system independent of simulation logging.

Provides file logging for launcher events, test execution status, and GUI operations
that occur before or outside of simulation activity. This is separate from the 
simulation-focused GUILogger system which only creates log files when simulations start.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
import threading


class LauncherLogger:
    """Launcher-specific logger for GUI events and test execution tracking."""
    
    _instance: Optional["LauncherLogger"] = None
    _lock = threading.Lock()
    
    def __init__(self) -> None:
        if LauncherLogger._instance is not None:
            raise RuntimeError("LauncherLogger is a singleton. Use get_instance() instead.")
        
        # Create launcher-specific logs directory
        self.logs_dir = Path(__file__).parent.parent.parent.parent.parent / "launcher_logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize log file immediately (unlike simulation logger which defers)
        self._initialize_log_file()
    
    @classmethod
    def get_instance(cls) -> "LauncherLogger":
        """Get singleton instance of LauncherLogger."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _initialize_log_file(self) -> None:
        """Initialize log file immediately when launcher starts."""
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H-%M-%S")
        self.log_filename = f"{timestamp} Launcher.log"
        self.log_path = self.logs_dir / self.log_filename
        
        # Write launcher log file header
        with open(self.log_path, 'w', encoding='utf-8') as f:
            f.write(f"VMT Enhanced Test Launcher Log\n")
            f.write(f"Started: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Log Level: INFO\n")
            f.write("=" * 50 + "\n\n")
        
        print(f"[LAUNCHER] 📝 Log file created: {self.log_filename}")
    
    def log(self, level: str, message: str) -> None:
        """Log a message to both console and file."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # HH:MM:SS.mmm
        log_entry = f"[{timestamp}] {level}: {message}"
        
        # Always print to console for immediate feedback
        print(f"[LAUNCHER] {log_entry}")
        
        # Write to file
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(log_entry + "\n")
                f.flush()  # Ensure immediate write for debugging
        except Exception as e:
            print(f"[LAUNCHER] ⚠️  Failed to write to log file: {e}")
    
    def info(self, message: str) -> None:
        """Log an info message."""
        self.log("INFO", message)
    
    def success(self, message: str) -> None:
        """Log a success message."""
        self.log("SUCCESS", message)
    
    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.log("WARNING", message)
    
    def error(self, message: str) -> None:
        """Log an error message."""
        self.log("ERROR", message)
    
    def test_start(self, test_id: str, test_name: str) -> None:
        """Log test execution start."""
        self.info(f"🚀 Starting test '{test_id}': {test_name}")
    
    def test_success(self, test_id: str, execution_time: float) -> None:
        """Log test execution success."""
        self.success(f"✅ Test '{test_id}' completed successfully in {execution_time:.2f}s")
    
    def test_error(self, test_id: str, error_msg: str) -> None:
        """Log test execution error."""
        self.error(f"❌ Test '{test_id}' failed: {error_msg}")
    
    def runner_init(self, method: str) -> None:
        """Log test runner initialization."""
        self.info(f"🔧 TestRunner initialized using {method}")
    
    def ui_event(self, event: str) -> None:
        """Log UI interaction events."""
        self.info(f"🖱️  UI: {event}")


def get_launcher_logger() -> LauncherLogger:
    """Get the singleton launcher logger instance."""
    return LauncherLogger.get_instance()