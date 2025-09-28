#!/usr/bin/env python3
"""
Batch Test Runner for VMT Framework
==================================

Professional batch test execution system with progress tracking, estimated completion time,
pause/resume capabilities, and detailed reporting. Designed for educational demonstrations
and systematic testing scenarios.

Features:
- Sequential test execution with live progress tracking
- Automatic unlimited speed for maximum batch processing efficiency
- Estimated time calculations based on test configurations
- Pause/Resume capabilities for interrupted sessions
- Detailed execution logs and reports
- Test result summaries and comparisons
- Integration with Enhanced Test Launcher

Usage:
    python batch_test_runner.py
    # Or via Enhanced Test Launcher -> Batch Runner tab
"""

import sys
import subprocess
import time
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import json
import threading
import queue

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QProgressBar, QTextEdit,
        QListWidget, QListWidgetItem, QGroupBox,
        QCheckBox, QSpinBox, QComboBox, QSplitter,
        QScrollArea, QFrame, QGridLayout, QMessageBox
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
    from PyQt6.QtGui import QFont, QColor, QPalette
except ImportError as e:
    print(f"❌ PyQt6 import failed: {e}")
    print("Please ensure PyQt6 is installed in your virtual environment.")
    sys.exit(1)

try:
    # Try new framework location first
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(repo_root, "src"))
    from econsim.tools.launcher.framework.test_configs import ALL_TEST_CONFIGS, TestConfiguration
except ImportError:
    try:
        # Fallback to old location (legacy)
        from MANUAL_TESTS.framework.test_configs import ALL_TEST_CONFIGS, TestConfiguration
    except ImportError:
        print("❌ Framework import failed. Please ensure framework is properly installed.")
        sys.exit(1)


@dataclass
class BatchTestResult:
    """Result of a single test execution in batch."""
    test_name: str
    config: TestConfiguration
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[timedelta] = None
    status: str = "pending"  # pending, running, completed, failed, skipped
    exit_code: Optional[int] = None
    log_output: str = ""
    error_message: str = ""
    
    @property
    def success(self) -> bool:
        return self.status == "completed" and self.exit_code == 0


@dataclass 
class BatchExecutionSession:
    """Complete batch execution session data."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_tests: int = 0
    completed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    results: List[BatchTestResult] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []
    
    @property
    def duration(self) -> Optional[timedelta]:
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property 
    def success_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return self.completed_tests / self.total_tests


class BatchTestExecutor(QObject):
    """Background test executor with progress signals."""
    
    # Signals for UI updates
    testStarted = pyqtSignal(str, int, int)  # test_name, current_index, total
    testCompleted = pyqtSignal(str, bool, str)  # test_name, success, message
    progressUpdated = pyqtSignal(int, int)  # completed, total
    sessionCompleted = pyqtSignal(object)  # BatchExecutionSession
    logOutput = pyqtSignal(str, str)  # test_name, output_line
    
    def __init__(self):
        super().__init__()
        self.current_process = None
        self.is_running = False
        self.is_paused = False
        self.should_stop = False
    
    def execute_batch(self, test_configs: List[tuple], session: BatchExecutionSession):
        """Execute a batch of tests sequentially."""
        self.is_running = True
        self.should_stop = False
        
        try:
            for i, (test_name, config) in enumerate(test_configs):
                if self.should_stop:
                    break
                
                # Wait if paused
                while self.is_paused and not self.should_stop:
                    time.sleep(0.1)
                
                if self.should_stop:
                    break
                
                # Start test
                self.testStarted.emit(str(test_name), i + 1, len(test_configs))
                result = self._execute_single_test(str(test_name), config)
                session.results.append(result)
                
                # Update counters
                if result.success:
                    session.completed_tests += 1
                else:
                    session.failed_tests += 1
                
                self.testCompleted.emit(str(test_name), result.success, result.error_message)
                self.progressUpdated.emit(i + 1, len(test_configs))
        
        finally:
            session.end_time = datetime.now()
            self.is_running = False
            self.sessionCompleted.emit(session)
    
    def _execute_single_test(self, test_name: str, config: TestConfiguration) -> BatchTestResult:
        """Execute a single test and return results."""
        result = BatchTestResult(
            test_name=test_name,
            config=config,
            start_time=datetime.now(),
            status="running"
        )
        
        try:
            # Construct test command
            test_file = f"test_{config.id}_framework_version.py"
            test_path = Path(__file__).parent / test_file
            
            if not test_path.exists():
                result.status = "failed"
                result.error_message = f"Test file not found: {test_file}"
                result.end_time = datetime.now()
                return result
            
            # Execute test with unlimited speed for batch processing
            cmd = [sys.executable, str(test_path)]
            
            # Set environment variable to force unlimited speed in batch mode
            test_env = os.environ.copy()
            test_env['ECONSIM_BATCH_UNLIMITED_SPEED'] = '1'
            
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=test_env
            )
            
            # Read output line by line
            output_lines = []
            while True:
                if self.should_stop:
                    self.current_process.terminate()
                    result.status = "skipped"
                    break
                
                line = self.current_process.stdout.readline()
                if not line:
                    break
                
                output_lines.append(line.strip())
                self.logOutput.emit(str(test_name), line.strip())
            
            # Wait for completion
            exit_code = self.current_process.wait()
            result.exit_code = exit_code
            result.log_output = "\n".join(output_lines)
            
            if exit_code == 0:
                result.status = "completed"
            else:
                result.status = "failed"
                result.error_message = f"Test failed with exit code {exit_code}"
        
        except Exception as e:
            result.status = "failed"
            result.error_message = str(e)
        
        finally:
            result.end_time = datetime.now()
            result.duration = result.end_time - result.start_time
            self.current_process = None
        
        return result
    
    def pause(self):
        """Pause batch execution."""
        self.is_paused = True
    
    def resume(self):
        """Resume batch execution."""
        self.is_paused = False
    
    def stop(self):
        """Stop batch execution."""
        self.should_stop = True
        if self.current_process:
            self.current_process.terminate()


class TestSelectionWidget(QWidget):
    """Widget for selecting tests to include in batch."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Select Tests for Batch Execution")
        header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Select all/none buttons
        button_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_none_btn = QPushButton("Select None")
        self.select_all_btn.clicked.connect(self.select_all)
        self.select_none_btn.clicked.connect(self.select_none)
        button_layout.addWidget(self.select_all_btn)
        button_layout.addWidget(self.select_none_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Test list with checkboxes
        self.test_list = QListWidget()
        self.test_checkboxes = {}
        
        for test_name, config in ALL_TEST_CONFIGS.items():
            item = QListWidgetItem()
            checkbox = QCheckBox(f"{test_name} - {config.description}")
            checkbox.setChecked(True)  # Default to all selected
            self.test_checkboxes[test_name] = checkbox
            self.test_list.addItem(item)
            self.test_list.setItemWidget(item, checkbox)
        
        layout.addWidget(self.test_list)
        
        # Test count summary
        self.summary_label = QLabel()
        self.update_summary()
        layout.addWidget(self.summary_label)
        
        # Connect signals
        for checkbox in self.test_checkboxes.values():
            checkbox.toggled.connect(self.update_summary)
    
    def select_all(self):
        """Select all tests."""
        for checkbox in self.test_checkboxes.values():
            checkbox.setChecked(True)
    
    def select_none(self):
        """Deselect all tests."""
        for checkbox in self.test_checkboxes.values():
            checkbox.setChecked(False)
    
    def get_selected_tests(self) -> List[tuple]:
        """Get list of selected (test_name, config) tuples."""
        selected = []
        for test_name, checkbox in self.test_checkboxes.items():
            if checkbox.isChecked():
                config = ALL_TEST_CONFIGS[test_name]
                selected.append((test_name, config))
        return selected
    
    def update_summary(self):
        """Update test count summary."""
        selected_count = sum(1 for cb in self.test_checkboxes.values() if cb.isChecked())
        total_count = len(self.test_checkboxes)
        
        # Estimate total time (rough estimate based on test complexity)
        estimated_minutes = selected_count * 3  # ~3 minutes per test average
        
        self.summary_label.setText(
            f"Selected: {selected_count}/{total_count} tests "
            f"(~{estimated_minutes} minutes estimated)"
        )


class BatchProgressWidget(QWidget):
    """Widget showing batch execution progress."""
    
    def __init__(self):
        super().__init__()
        self.current_session = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Progress header
        self.status_label = QLabel("Ready to start batch execution")
        self.status_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(self.status_label)
        
        # Overall progress
        progress_group = QGroupBox("Overall Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.overall_progress = QProgressBar()
        self.progress_label = QLabel("0 / 0 tests completed")
        progress_layout.addWidget(self.overall_progress)
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(progress_group)
        
        # Current test info
        current_group = QGroupBox("Current Test")
        current_layout = QVBoxLayout(current_group)
        
        self.current_test_label = QLabel("No test running")
        self.current_test_time = QLabel("Elapsed: 0:00")
        current_layout.addWidget(self.current_test_label)
        current_layout.addWidget(self.current_test_time)
        
        layout.addWidget(current_group)
        
        # Time estimates
        time_group = QGroupBox("Time Estimates")
        time_layout = QGridLayout(time_group)
        
        time_layout.addWidget(QLabel("Elapsed:"), 0, 0)
        self.elapsed_label = QLabel("0:00")
        time_layout.addWidget(self.elapsed_label, 0, 1)
        
        time_layout.addWidget(QLabel("Estimated Remaining:"), 1, 0)
        self.remaining_label = QLabel("Unknown")
        time_layout.addWidget(self.remaining_label, 1, 1)
        
        time_layout.addWidget(QLabel("Estimated Total:"), 2, 0)
        self.total_time_label = QLabel("Unknown")
        time_layout.addWidget(self.total_time_label, 2, 1)
        
        layout.addWidget(time_group)
        
        # Timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_times)
        self.timer.start(1000)  # Update every second
    
    def start_session(self, session: BatchExecutionSession):
        """Start tracking a new session."""
        self.current_session = session
        self.overall_progress.setMaximum(session.total_tests)
        self.overall_progress.setValue(0)
        self.status_label.setText("Batch execution in progress...")
    
    def update_progress(self, completed: int, total: int):
        """Update progress display."""
        self.overall_progress.setValue(completed)
        self.progress_label.setText(f"{completed} / {total} tests completed")
        
        if self.current_session:
            success_rate = (self.current_session.completed_tests / max(1, completed)) * 100
            status_text = f"Progress: {completed}/{total} ({success_rate:.1f}% success rate)"
            self.status_label.setText(status_text)
    
    def update_current_test(self, test_name: str, index: int, total: int):
        """Update current test display."""
        self.current_test_label.setText(f"Running: {test_name} ({index}/{total})")
        self.current_test_start = datetime.now()
    
    def session_completed(self, session: BatchExecutionSession):
        """Handle session completion."""
        self.current_session = session
        success_rate = session.success_rate * 100
        duration_str = str(session.duration).split('.')[0] if session.duration else "Unknown"
        
        self.status_label.setText(
            f"Batch completed! {session.completed_tests}/{session.total_tests} "
            f"tests successful ({success_rate:.1f}%) in {duration_str}"
        )
        self.current_test_label.setText("Batch execution completed")
    
    def update_times(self):
        """Update time displays."""
        if not self.current_session:
            return
        
        now = datetime.now()
        elapsed = now - self.current_session.start_time
        elapsed_str = str(elapsed).split('.')[0]
        self.elapsed_label.setText(elapsed_str)
        
        # Estimate remaining time
        if self.current_session.completed_tests > 0:
            avg_time_per_test = elapsed / self.current_session.completed_tests
            remaining_tests = self.current_session.total_tests - self.current_session.completed_tests
            estimated_remaining = avg_time_per_test * remaining_tests
            remaining_str = str(estimated_remaining).split('.')[0]
            self.remaining_label.setText(remaining_str)
            
            total_estimated = elapsed + estimated_remaining
            total_str = str(total_estimated).split('.')[0]
            self.total_time_label.setText(total_str)


class BatchLogWidget(QWidget):
    """Widget for displaying batch execution logs."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Log header
        header = QLabel("Execution Log")
        header.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 9))
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #444;
            }
        """)
        layout.addWidget(self.log_display)
        
        # Clear log button
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self.clear_log)
        layout.addWidget(clear_btn)
    
    def add_log_entry(self, test_name: str, message: str):
        """Add a log entry."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {test_name}: {message}"
        self.log_display.append(formatted_message)
    
    def add_test_started(self, test_name: str, index: int, total: int):
        """Log test start."""
        message = f"🚀 Starting test {index}/{total}"
        self.add_log_entry(test_name, message)
    
    def add_test_completed(self, test_name: str, success: bool, error_msg: str):
        """Log test completion."""
        if success:
            message = "✅ Test completed successfully"
        else:
            message = f"❌ Test failed: {error_msg}"
        self.add_log_entry(test_name, message)
    
    def clear_log(self):
        """Clear the log display."""
        self.log_display.clear()


class BatchTestRunner(QWidget):
    """Main batch test runner interface."""
    
    def __init__(self):
        super().__init__()
        self.executor = None
        self.executor_thread = None
        self.current_session = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("VMT Batch Test Runner")
        self.setMinimumSize(1000, 700)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("VMT Framework - Batch Test Runner")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Main splitter for sections
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Test selection and controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Test selection
        self.test_selection = TestSelectionWidget()
        left_layout.addWidget(self.test_selection)
        
        # Control buttons
        control_group = QGroupBox("Batch Controls")
        control_layout = QVBoxLayout(control_group)
        
        self.start_btn = QPushButton("Start Batch Execution")
        self.pause_btn = QPushButton("Pause")
        self.resume_btn = QPushButton("Resume")
        self.stop_btn = QPushButton("Stop")
        
        self.start_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; font-weight: bold; padding: 8px; }")
        self.pause_btn.setStyleSheet("QPushButton { background-color: #ffc107; color: black; font-weight: bold; padding: 8px; }")
        self.resume_btn.setStyleSheet("QPushButton { background-color: #17a2b8; color: white; font-weight: bold; padding: 8px; }")
        self.stop_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; font-weight: bold; padding: 8px; }")
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.resume_btn)
        control_layout.addWidget(self.stop_btn)
        
        # Initially disable pause/resume/stop
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        left_layout.addWidget(control_group)
        splitter.addWidget(left_panel)
        
        # Right panel: Progress and logs
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Progress display
        self.progress_widget = BatchProgressWidget()
        right_layout.addWidget(self.progress_widget)
        
        # Log display
        self.log_widget = BatchLogWidget()
        right_layout.addWidget(self.log_widget)
        
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
        layout.addWidget(splitter)
        
        # Connect signals
        self.start_btn.clicked.connect(self.start_batch_execution)
        self.pause_btn.clicked.connect(self.pause_execution)
        self.resume_btn.clicked.connect(self.resume_execution)
        self.stop_btn.clicked.connect(self.stop_execution)
    
    def start_batch_execution(self):
        """Start batch test execution."""
        selected_tests = self.test_selection.get_selected_tests()
        
        if not selected_tests:
            QMessageBox.warning(self, "No Tests Selected", 
                              "Please select at least one test to execute.")
            return
        
        # Create execution session
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session = BatchExecutionSession(
            session_id=session_id,
            start_time=datetime.now(),
            total_tests=len(selected_tests)
        )
        
        # Setup executor
        self.executor = BatchTestExecutor()
        self.executor_thread = QThread()
        self.executor.moveToThread(self.executor_thread)
        
        # Connect signals
        self.executor.testStarted.connect(self.on_test_started)
        self.executor.testCompleted.connect(self.on_test_completed)
        self.executor.progressUpdated.connect(self.on_progress_updated)
        self.executor.sessionCompleted.connect(self.on_session_completed)
        self.executor.logOutput.connect(self.on_log_output)
        
        # Start execution
        self.executor_thread.started.connect(
            lambda: self.executor.execute_batch(selected_tests, self.current_session)
        )
        
        # Update UI
        self.progress_widget.start_session(self.current_session)
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        
        # Start thread
        self.executor_thread.start()
        
        self.log_widget.add_log_entry("SYSTEM", f"🚀 Batch execution started with {len(selected_tests)} tests")
    
    def pause_execution(self):
        """Pause batch execution."""
        if self.executor:
            self.executor.pause()
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)
            self.log_widget.add_log_entry("SYSTEM", "⏸️ Batch execution paused")
    
    def resume_execution(self):
        """Resume batch execution."""
        if self.executor:
            self.executor.resume()
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)
            self.log_widget.add_log_entry("SYSTEM", "▶️ Batch execution resumed")
    
    def stop_execution(self):
        """Stop batch execution."""
        if self.executor:
            self.executor.stop()
            self.log_widget.add_log_entry("SYSTEM", "🛑 Stopping batch execution...")
    
    def on_test_started(self, test_name: str, index: int, total: int):
        """Handle test started signal."""
        self.progress_widget.update_current_test(test_name, index, total)
        self.log_widget.add_test_started(test_name, index, total)
    
    def on_test_completed(self, test_name: str, success: bool, error_msg: str):
        """Handle test completed signal."""
        self.log_widget.add_test_completed(test_name, success, error_msg)
    
    def on_progress_updated(self, completed: int, total: int):
        """Handle progress update signal."""
        self.progress_widget.update_progress(completed, total)
    
    def on_session_completed(self, session: BatchExecutionSession):
        """Handle session completion."""
        self.progress_widget.session_completed(session)
        
        # Update UI
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        # Cleanup thread
        if self.executor_thread:
            self.executor_thread.quit()
            self.executor_thread.wait()
            self.executor_thread = None
            self.executor = None
        
        # Show completion message
        success_rate = session.success_rate * 100
        duration_str = str(session.duration).split('.')[0] if session.duration else "Unknown"
        
        QMessageBox.information(
            self, 
            "Batch Execution Complete",
            f"Batch execution completed!\n\n"
            f"Tests completed: {session.completed_tests}/{session.total_tests}\n"
            f"Success rate: {success_rate:.1f}%\n"
            f"Duration: {duration_str}\n"
            f"Failed tests: {session.failed_tests}"
        )
        
        self.log_widget.add_log_entry("SYSTEM", f"🎉 Batch execution completed! Success rate: {success_rate:.1f}%")
    
    def on_log_output(self, test_name: str, output: str):
        """Handle log output from test execution."""
        if output.strip():  # Only log non-empty lines
            self.log_widget.add_log_entry(test_name, output)


def main():
    """Run the batch test runner as standalone application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    runner = BatchTestRunner()
    runner.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()