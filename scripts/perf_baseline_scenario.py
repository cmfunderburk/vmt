#!/usr/bin/env python3
"""
VMT Baseline Scenario Performance Test

Runs the a        # Collect output during execution
        output_lines = []
        startup_timeout = 5.0  # Allow startup time
        
        try:
            # Wait for initial startup, then run for duration
            stdout, stderr = process.communicate(timeout=duration_s + startup_timeout)
            output_lines = (stdout or '').split('\n')
            if stderr:
                output_lines.extend(stderr.split('\n'))
            
        except subprocess.TimeoutExpired:
            # This is expected - terminate after duration
            if not json_output:
                print(f"⏰ Terminating test after {duration_s}s duration...")
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=3.0)
                output_lines = []
                if stdout:
                    output_lines.extend(stdout.split('\n'))
                if stderr:
                    output_lines.extend(stderr.split('\n'))
            except subprocess.TimeoutExpired:
                if not json_output:
                    print("⚠️  Force-killing unresponsive test process...")
                process.kill()
                process.wait()ELINE configuration in batch mode and extracts 
realistic performance metrics from the debug log output for regression testing.

This replaces the synthetic stub with actual framework scenario execution,
providing more realistic performance baselines for future regression detection.
"""

import sys
import os
import subprocess
import json
import re
import tempfile
from pathlib import Path
from typing import Dict, List, Any
from time import perf_counter


def run_baseline_scenario(duration_s: float = 10.0, json_output: bool = False) -> Dict[str, Any]:
    """
    Run TEST_1_BASELINE scenario in batch mode and extract performance metrics.
    
    Args:
        duration_s: How long to run the scenario (in seconds)  
        json_output: Whether to output JSON format
        
    Returns:
        Dictionary with performance metrics: frames, duration_s, avg_fps, etc.
    """
    project_root = Path(__file__).parent.parent
    test_script = project_root / "MANUAL_TESTS" / "test_1_framework_version.py"
    
    if not test_script.exists():
        return {
            "frames": 0.0,
            "duration_s": duration_s, 
            "avg_fps": 0.0,
            "error": f"Test script not found: {test_script}"
        }
    
    # Use a temporary file to capture output
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.log', delete=False) as log_file:
        log_path = Path(log_file.name)
    
    try:
        # Set up environment for batch mode (auto-start and unlimited speed)
        env = os.environ.copy()
        env['ECONSIM_BATCH_UNLIMITED_SPEED'] = '1'
        env['QT_QPA_PLATFORM'] = 'offscreen'  # Headless for CI
        env['SDL_VIDEODRIVER'] = 'dummy'  # Headless for pygame
        
        # Enable comprehensive debug logging for performance monitoring
        env['ECONSIM_DEBUG_FPS'] = '1'
        env['ECONSIM_DEBUG_AGENT_MODES'] = '1'  # For periodic summaries
        env['ECONSIM_DEBUG_TRADES'] = '1'
        env['ECONSIM_DEBUG_UTILITIES'] = '1'
        
        if not json_output:
            print(f"🧪 Running baseline scenario for {duration_s:.1f} seconds...")
        
        start_time = perf_counter()
        
        # Run the test script in subprocess with timeout
        process = subprocess.Popen(
            [sys.executable, str(test_script)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,  # Unbuffered
            universal_newlines=True
        )
        
        # Collect output and monitor for specified duration
        output_lines = []
        try:
            # Let it run for the specified duration
            stdout, _ = process.communicate(timeout=duration_s + 5.0)  # 5s buffer for startup
            output_lines = stdout.split('\n') if stdout else []
            
        except subprocess.TimeoutExpired:
            # This is expected - terminate after duration
            process.terminate()
            try:
                stdout, _ = process.communicate(timeout=2.0)
                output_lines = stdout.split('\n') if stdout else []
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        
        end_time = perf_counter()
        actual_duration = end_time - start_time
        
        # Parse performance metrics from output
        metrics = parse_performance_metrics(output_lines, actual_duration)
        metrics['actual_duration_s'] = actual_duration
        
        # Add debug info for troubleshooting
        if not json_output:
            print(f"📊 Captured {len(output_lines)} lines of output")
            fps_lines = [line for line in output_lines if '[FPS]' in line]
            debug_lines = [line for line in output_lines if 'DEBUG' in line or '🚀' in line or '✅' in line]
            print(f"📈 Found {len(fps_lines)} FPS lines, {len(debug_lines)} debug lines")
            
            if fps_lines:
                print("📈 FPS output sample:")
                for line in fps_lines[:3]:
                    print(f"   {line[:100]}")
            elif debug_lines:
                print("� Debug output sample:")
                for line in debug_lines[:3]:
                    print(f"   {line[:100]}")
            elif len(output_lines) > 0:
                print("📝 General output sample:")
                for line in output_lines[:5]:
                    if line.strip():  # Skip empty lines
                        print(f"   {line[:100]}")
            else:
                print("❌ No output captured from subprocess")
        
        return metrics
        
    except Exception as e:
        return {
            "frames": 0.0,
            "duration_s": duration_s,
            "avg_fps": 0.0,
            "error": f"Execution failed: {str(e)}"
        }
    finally:
        # Clean up log file
        if log_path.exists():
            log_path.unlink()


def parse_performance_metrics(output_lines: List[str], duration_s: float) -> Dict[str, Any]:
    """
    Parse performance metrics from test output.
    
    Looks for periodic summary logs that contain steps_per_sec values
    and calculates average FPS across the run.
    """
    fps_values: List[float] = []
    max_turn = 0
    
    # Regex patterns for different types of performance data
    fps_pattern = r"\[FPS\] Frames=(\d+) AvgFPS=(\d+\.?\d*)"
    turn_pattern = r"Turn (\d+):"
    periodic_pattern = r"DEBUG: Periodic logging triggered at turn (\d+)"
    
    for line in output_lines:
        # Look for FPS data in format [FPS] Frames=X AvgFPS=Y
        fps_match = re.search(fps_pattern, line)
        if fps_match:
            try:
                frame_count = int(fps_match.group(1))
                fps = float(fps_match.group(2))
                if 0 < fps < 1000:  # Sanity check
                    fps_values.append(fps)
                    max_turn = max(max_turn, frame_count)  # Use frame count as turn approximation
            except (ValueError, IndexError):
                continue
        
        # Count turns processed
        turn_match = re.search(turn_pattern, line)
        if turn_match:
            try:
                turn = int(turn_match.group(1))
                max_turn = max(max_turn, turn)
            except (ValueError, IndexError):
                continue
                
        # Also count from periodic logging
        periodic_match = re.search(periodic_pattern, line)
        if periodic_match:
            try:
                turn = int(periodic_match.group(1))
                max_turn = max(max_turn, turn)
            except (ValueError, IndexError):
                continue
    
    # Calculate metrics
    if fps_values:
        avg_fps = sum(fps_values) / len(fps_values)
        frames = avg_fps * duration_s  # Estimated frames processed
    else:
        # Fallback: estimate from turns if no FPS data available
        avg_fps = max_turn / duration_s if duration_s > 0 else 0
        frames = float(max_turn)
    
    return {
        "frames": frames,
        "duration_s": duration_s,
        "avg_fps": avg_fps,
        "turns_processed": max_turn,
        "fps_samples": len(fps_values),
        "fps_values": fps_values if len(fps_values) <= 10 else fps_values[:10]  # Limit for JSON
    }


def main():
    """Main CLI interface matching original perf_stub.py."""
    import argparse
    
    parser = argparse.ArgumentParser(description="VMT Baseline Scenario Performance Test")
    parser.add_argument("--duration", type=float, default=10.0,
                        help="Test duration in seconds (default: 10.0)")
    parser.add_argument("--json", action="store_true",
                        help="Output JSON format")
    
    args = parser.parse_args()
    
    # Run the baseline scenario
    result = run_baseline_scenario(args.duration, args.json)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            sys.exit(1)
            
        print(f"Baseline Scenario Performance Results:")
        print(f"Duration: {result['duration_s']:.2f}s")
        print(f"Turns Processed: {result.get('turns_processed', 0)}")
        print(f"Avg FPS: {result['avg_fps']:.1f}")
        print(f"FPS Samples: {result.get('fps_samples', 0)}")
        
        # Performance gate check
        fps = result['avg_fps']
        if fps >= 30:
            print(f"✅ Performance gate PASSED (≥30 FPS: {fps:.1f})")
            sys.exit(0)
        else:
            print(f"❌ Performance gate FAILED (<30 FPS: {fps:.1f})")
            sys.exit(1)


if __name__ == "__main__":
    main()