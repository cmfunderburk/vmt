"""Performance measurement for VMT Gate 1.

Supports both synthetic timing simulation and real widget performance testing.
"""
from __future__ import annotations

from time import perf_counter, sleep
import json
import sys
import os


def run_synthetic(duration_s: float = 2.0, target_fps: float = 60.0) -> dict[str, float]:
    """Synthetic timing simulation for harness validation."""
    frame_interval = 1.0 / target_fps
    start = perf_counter()
    frames = 0
    while True:
        now = perf_counter()
        if now - start >= duration_s:
            break
        # simulate lightweight work
        sleep(frame_interval * 0.4)  # sleep less than full interval to simulate processing
        frames += 1
    elapsed = perf_counter() - start
    return {"frames": frames, "duration_s": elapsed, "avg_fps": frames / elapsed if elapsed else 0.0}


def run_widget(duration_s: float = 5.0) -> dict[str, float]:
    """Real widget performance test using EmbeddedPygameWidget."""
    try:
        # Set offscreen for headless environments
        if not os.environ.get("DISPLAY"):
            os.environ["QT_QPA_PLATFORM"] = "offscreen"
        
        from PyQt6.QtWidgets import QApplication
        from econsim.gui.embedded_pygame import EmbeddedPygameWidget
        
        app = QApplication.instance() or QApplication(sys.argv)
        widget = EmbeddedPygameWidget()
        widget.show()
        
        # Access frame counter through widget (protected member access needed for perf testing)
        start_frames = getattr(widget, "_frame", 0)  # Use getattr for safer access
        start_time = perf_counter()
        
        # Let widget run for specified duration
        while perf_counter() - start_time < duration_s:
            app.processEvents()
            sleep(0.001)  # Small delay to avoid busy-waiting
        
        end_time = perf_counter()
        end_frames = getattr(widget, "_frame", start_frames)
        
        elapsed = end_time - start_time
        frame_count = end_frames - start_frames
        
        widget.close()
        app.processEvents()  # Process close events
        
        return {
            "frames": float(frame_count),
            "duration_s": elapsed,
            "avg_fps": frame_count / elapsed if elapsed > 0 else 0.0
        }
    except Exception:  # Broad exception for robustness
        # Return failure result with proper typing
        return {"frames": 0.0, "duration_s": duration_s, "avg_fps": 0.0}


def run(duration_s: float = 2.0, target_fps: float = 60.0) -> dict[str, float]:
    """Backward compatibility - defaults to synthetic mode."""
    return run_synthetic(duration_s, target_fps)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VMT Performance Test")
    parser.add_argument("--mode", choices=["synthetic", "widget"], default="synthetic",
                       help="Test mode: synthetic simulation or real widget")
    parser.add_argument("--duration", type=float, default=5.0,
                       help="Test duration in seconds")
    parser.add_argument("--target-fps", type=float, default=60.0,
                       help="Target FPS for synthetic mode")
    parser.add_argument("--json", action="store_true",
                       help="Output JSON format")
    
    args = parser.parse_args()
    
    if args.mode == "widget":
        result = run_widget(args.duration)
    else:
        result = run_synthetic(args.duration, args.target_fps)
    
    if args.json:
        print(json.dumps(result))
    else:
        print(f"Frames: {result['frames']:.0f}")
        print(f"Duration: {result['duration_s']:.2f}s")
        print(f"Avg FPS: {result['avg_fps']:.1f}")
        
        # Gate 1 success criteria check
        fps = result['avg_fps']
        if fps >= 30:
            print(f"✓ Gate 1 FPS requirement met (≥30 FPS: {fps:.1f})")
        else:
            print(f"✗ Gate 1 FPS requirement failed (<30 FPS: {fps:.1f})")


def main() -> None:  # pragma: no cover - simple script
    data = run()
    print(json.dumps(data))


if __name__ == "__main__":
    main()
