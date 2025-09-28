#!/usr/bin/env python3
"""
VMT Baseline Scenario Performance Test (Simplified)

Runs TEST_1_BASELINE in batch mode and extracts FPS from output file.
"""

import sys
import os
import subprocess
import json
import re
import tempfile
from pathlib import Path
from time import perf_counter


def run_baseline_scenario(duration_s: float = 8.0):
    """Run baseline scenario and extract performance metrics."""
    project_root = Path(__file__).parent.parent
    test_script = project_root / "MANUAL_TESTS" / "test_1_framework_version.py"
    
    if not test_script.exists():
        return {"error": f"Test script not found: {test_script}"}
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.log', delete=False) as f:
        log_file = Path(f.name)
    
    try:
        # Set up environment for batch mode  
        env = os.environ.copy()
        env.update({
            'ECONSIM_BATCH_UNLIMITED_SPEED': '1',
            'QT_QPA_PLATFORM': 'offscreen',
            'SDL_VIDEODRIVER': 'dummy', 
            'ECONSIM_DEBUG_FPS': '1',
            'ECONSIM_DEBUG_AGENT_MODES': '1'
        })
        
        print(f"🧪 Running baseline scenario for {duration_s}s...")
        
        # Run test and redirect output to file
        with open(log_file, 'w') as output:
            start_time = perf_counter()
            # Use timeout but handle it gracefully - we expect the timeout
            try:
                subprocess.run(
                    [sys.executable, str(test_script)],
                    env=env,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    timeout=duration_s + 8,  # 8s buffer for startup/shutdown
                    text=True
                )
            except subprocess.TimeoutExpired:
                # This is expected - the test runs until we kill it
                pass
            end_time = perf_counter()
        
        # Read output from file and check if we got anything
        with open(log_file, 'r') as f:
            output_lines = f.readlines()
        
        print(f"📊 Read {len(output_lines)} lines from log file")
        if len(output_lines) > 0:
            print(f"📝 Sample lines:")
            for i, line in enumerate(output_lines[:5]):
                if line.strip():
                    print(f"   {i}: {line.strip()[:100]}")
        else:
            print("❌ Log file was empty")
        
        # Parse FPS data
        fps_values: list[float] = []
        max_frames = 0
        
        fps_pattern = r"\[FPS\] Frames=(\d+) AvgFPS=(\d+\.?\d*)"
        
        for line in output_lines:
            match = re.search(fps_pattern, line)
            if match:
                frames = int(match.group(1))
                fps = float(match.group(2))
                fps_values.append(fps)
                max_frames = max(max_frames, frames)
        
        duration = end_time - start_time
        avg_fps = sum(fps_values) / len(fps_values) if fps_values else 0.0
        
        return {
            "frames": float(max_frames),
            "duration_s": duration,
            "avg_fps": avg_fps,
            "fps_samples": len(fps_values),
            "fps_values": fps_values[-5:] if len(fps_values) > 5 else fps_values  # Last 5 samples
        }
        
    except subprocess.TimeoutExpired:
        # This should not happen anymore since we handle it above
        return {"error": "Unexpected timeout"}
    except Exception as e:
        return {"error": f"Execution failed: {e}"}
    finally:
        if log_file.exists():
            log_file.unlink()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="VMT Baseline Performance Test")
    parser.add_argument("--duration", type=float, default=8.0, help="Duration in seconds")
    parser.add_argument("--json", action="store_true", help="JSON output")
    
    args = parser.parse_args()
    result = run_baseline_scenario(args.duration)
    
    if args.json:
        print(json.dumps(result))
    else:
        if "error" in result:
            print(f"❌ {result['error']}")
            sys.exit(1)
        
        fps = result['avg_fps']
        print(f"Baseline Scenario Results:")
        print(f"Duration: {result['duration_s']:.2f}s")  
        print(f"Max Frames: {result['frames']:.0f}")
        print(f"Avg FPS: {fps:.1f}")
        print(f"FPS Samples: {result['fps_samples']}")
        
        if fps >= 30:
            print(f"✅ Performance gate PASSED (≥30 FPS)")
        else:
            print(f"❌ Performance gate FAILED (<30 FPS)")
            sys.exit(1)


if __name__ == "__main__":
    main()